#!/usr/bin/env python3
"""Single evaluation harness for the Reminder Agent.

dataset -> model call -> structural -> property/invariant -> semantic -> aggregate vs threshold.
Model/service errors are recorded separately and excluded from the pass rates (FR-026).

Usage:  python .harness/run_eval.py --label initial [--delay 4] [--ids C01,C09]
Exit:   0 PASS, 1 FAIL, 2 INCONCLUSIVE (nothing evaluable), 3 cannot start (e.g. no API key)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import re
import sys
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from property_eval import evaluate_properties  # noqa: E402
from quality_eval import evaluate_quality  # noqa: E402
from schema_eval import validate_structure  # noqa: E402

from reminder_agent.agent import InputError, Provider, interpret, load_system_prompt  # noqa: E402
from reminder_agent.provider import GeminiProvider, ServiceError  # noqa: E402

DATASET = ROOT / "evals" / "dataset.json"
THRESHOLD = ROOT / "evals" / "threshold.json"
RUNS = ROOT / "evidence" / "eval-runs"
LATEST = ROOT / "evidence" / "eval-results.json"
REQUIRED_CATEGORIES = {
    "normal", "boundary", "ambiguous", "missing_information", "malformed", "adversarial",
}
MIN_CASES = 15


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_dataset(cases: list[dict[str, Any]]) -> list[str]:
    """Dataset gate (FR-019, FR-020): returns a list of problems."""
    problems: list[str] = []
    if len(cases) < MIN_CASES:
        problems.append(f"dataset has {len(cases)} cases, need at least {MIN_CASES}")
    ids = [c.get("id") for c in cases]
    if len(set(ids)) != len(ids):
        problems.append("case ids are not unique")
    categories = {c.get("category") for c in cases}
    missing = REQUIRED_CATEGORIES - categories
    if missing:
        problems.append(f"missing categories: {sorted(missing)}")
    if not any(c.get("guardrail") for c in cases):
        problems.append("no guardrail cases")
    for case in cases:
        cid = case.get("id", "?")
        if not re.fullmatch(r"FR-\d{3}", str(case.get("requirement", ""))):
            problems.append(f"{cid}: requirement must look like FR-001")
        inp = case.get("input", {})
        if not isinstance(inp.get("text"), str) or not isinstance(inp.get("now"), str):
            problems.append(f"{cid}: input needs string text and now")
        if "expected_intent" not in case and not case.get("allowed_intents"):
            problems.append(f"{cid}: needs expected_intent or allowed_intents")
        if case.get("expected_datetime") and "tolerance_minutes" not in case:
            problems.append(f"{cid}: expected_datetime needs tolerance_minutes (FR-021)")
    return problems


def evaluate_case(
    case: dict[str, Any], provider: Provider, system_prompt: str, similarity_min: float
) -> dict[str, Any]:
    base: dict[str, Any] = {
        "id": case["id"],
        "category": case["category"],
        "requirement": case["requirement"],
        "guardrail": bool(case.get("guardrail")),
        "input": case["input"],
    }
    try:
        output = interpret(case["input"]["text"], case["input"]["now"], provider, system_prompt)
    except ServiceError as exc:
        return {**base, "status": "service_error", "passed": None,
                "service_error": {"kind": exc.kind, "message": exc.message, "http_status": exc.status}}
    except InputError as exc:
        return {**base, "status": "service_error", "passed": None,
                "service_error": {"kind": "input_error", "message": str(exc), "http_status": None}}

    structural = validate_structure(output.parsed, output.parse_error)
    layers = {"structural": "pass" if not structural else "fail", "property": "skipped",
              "semantic": "n/a"}
    findings = list(structural)
    score = None
    if not structural:
        props = evaluate_properties(case, output.parsed)
        layers["property"] = "pass" if not props else "fail"
        findings += props
        quality, score = evaluate_quality(case, output.parsed, similarity_min)
        if score is not None:
            layers["semantic"] = "pass" if not quality else "fail"
        findings += quality
    return {**base, "status": "evaluated", "passed": not findings, "layers": layers,
            "title_similarity": score, "findings": findings,
            "raw_output": output.raw_text, "parsed": output.parsed}


def aggregate(results: list[dict[str, Any]], thr: dict[str, float]) -> dict[str, Any]:
    evaluated = [r for r in results if r["status"] == "evaluated"]
    errors = [r for r in results if r["status"] == "service_error"]
    guard = [r for r in evaluated if r["guardrail"]]

    def rate(items: list[dict[str, Any]], key: Callable[[dict[str, Any]], bool]) -> float | None:
        return sum(1 for r in items if key(r)) / len(items) if items else None

    schema_rate = rate(evaluated, lambda r: r["layers"]["structural"] == "pass")
    guard_rate = rate(guard, lambda r: bool(r["passed"]))
    overall = rate(evaluated, lambda r: bool(r["passed"]))
    checks = {
        "schema_validity": {"value": schema_rate, "required": thr["schema_validity_min"]},
        "guardrail_pass": {"value": guard_rate, "required": thr["guardrail_pass_min"]},
        "overall_pass": {"value": overall, "required": thr["overall_pass_min"]},
    }
    if not evaluated or guard_rate is None:
        verdict = "INCONCLUSIVE"
    else:
        verdict = "PASS" if all(c["value"] >= c["required"] for c in checks.values()) else "FAIL"
    return {
        "verdict": verdict,
        "cases_total": len(results),
        "cases_evaluated": len(evaluated),
        "cases_passed": sum(1 for r in evaluated if r["passed"]),
        "service_errors": len(errors),
        "metrics": checks,
        "by_layer_failures": {
            layer: sum(1 for r in evaluated if r["layers"][layer] == "fail")
            for layer in ("structural", "property", "semantic")
        },
    }


def write_feedback(path: Path, results: list[dict[str, Any]], summary: dict[str, Any]) -> None:
    lines = [
        "# Evaluation feedback for the coding agent", "",
        f"Verdict: {summary['verdict']}  |  metrics: {json.dumps(summary['metrics'])}", "",
        "Constraints: you may change application code, the prompt, parsers, validators or",
        "guardrails. You must NOT remove or edit evaluation cases, change expected results,",
        "lower evals/threshold.json, disable guardrails, or edit recorded results.", "",
    ]
    for r in results:
        if r["status"] != "evaluated" or r["passed"]:
            continue
        lines += [f"## Case {r['id']} ({r['category']}, {r['requirement']})",
                  f"Input: {json.dumps(r['input'], ensure_ascii=False)}",
                  f"Model output: {r['raw_output']}", "Failed checks:"]
        lines += [f"- [{f['layer']}] {f['check']} ({f['requirement']}): {f['message']}"
                  for f in r["findings"]]
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run")
    parser.add_argument("--delay", type=float, default=4.0, help="seconds between model calls")
    parser.add_argument("--ids", help="comma-separated case ids (partial run)")
    args = parser.parse_args(argv)

    cases = json.loads(DATASET.read_text(encoding="utf-8"))["cases"]
    problems = check_dataset(cases)
    if problems:
        print("DATASET GATE FAILED:\n- " + "\n- ".join(problems))
        return 3
    thr = json.loads(THRESHOLD.read_text(encoding="utf-8"))
    selected = [c for c in cases if not args.ids or c["id"] in args.ids.split(",")]
    try:
        provider = GeminiProvider.from_env()
    except ServiceError as exc:
        print(f"Cannot start: {exc.message}")
        return 3

    system_prompt = load_system_prompt()
    results: list[dict[str, Any]] = []
    for index, case in enumerate(selected):
        if index:
            time.sleep(args.delay)
        result = evaluate_case(case, provider, system_prompt, thr["title_similarity_min"])
        results.append(result)
        state = result["status"] if result["status"] != "evaluated" else (
            "PASS" if result["passed"] else "FAIL")
        print(f"[{state}] {result['id']} {result['category']}")

    summary = aggregate(results, thr)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    record = {
        "label": args.label, "timestamp": stamp, "partial": len(selected) != len(cases),
        "config": {"provider": "gemini", "model": provider.model,
                   "temperature": provider.temperature, "python": platform.python_version(),
                   "system_prompt_sha256": sha256(ROOT / "prompts" / "system_prompt.md"),
                   "dataset_sha256": sha256(DATASET), "threshold": thr},
        "summary": summary, "results": results,
    }
    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / f"{stamp}-{args.label}.json"
    out.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    if not record["partial"]:
        LATEST.write_text(json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8")
    if summary["verdict"] == "FAIL":
        write_feedback(RUNS / f"{stamp}-{args.label}-feedback.md", results, summary)

    print(json.dumps(summary, indent=2))
    if summary["service_errors"]:
        print(f"WARNING: {summary['service_errors']} case(s) hit service errors and were "
              "excluded from the rates; rerun for a complete evaluation.")
    shown = out.relative_to(ROOT) if out.is_relative_to(ROOT) else out
    print(f"VERDICT: {summary['verdict']}  (results: {shown})")
    if summary["verdict"] == "PASS":
        return 0
    if summary["verdict"] == "FAIL":
        return 1
    return 2


if __name__ == "__main__":
    sys.exit(main())
