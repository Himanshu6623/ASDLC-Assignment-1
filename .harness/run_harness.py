#!/usr/bin/env python3
"""Deterministic harness runner for Part 1A.

Gates (all mandatory): lint (ruff), security (bandit), tests + coverage (pytest).
Writes machine-readable results and a feedback file for the coding agent.
Exit code 0 only if every gate passes.

Usage: python .harness/run_harness.py [--label NAME]
"""

from __future__ import annotations

import argparse
import json
import subprocess  # noqa: S404  # nosec B404 - fixed, trusted command lists only
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / ".harness"
RESULTS = ROOT / "evidence" / "harness-results"
COVERAGE_MIN = 90

GATES = [
    {
        "name": "lint",
        "description": "Ruff static analysis (style, bugs, security-adjacent rules)",
        "cmd": [sys.executable, "-m", "ruff", "check", "--config", str(HARNESS / "ruff.toml"),
                "src", "tests", ".harness"],
    },
    {
        "name": "security",
        "description": "Bandit SAST on src/ and .harness/",
        "cmd": [sys.executable, "-m", "bandit", "-q", "-r", "src", ".harness",
                "-c", str(HARNESS / "bandit.yaml")],
    },
    {
        "name": "tests",
        "description": f"pytest spec-derived tests, coverage >= {COVERAGE_MIN}%",
        "cmd": [sys.executable, "-m", "pytest", "-q", "--cov=smart_todo", "--cov-branch",
                "--cov-report=term-missing", f"--cov-fail-under={COVERAGE_MIN}", "tests"],
    },
]


def run_gate(gate: dict) -> dict:
    proc = subprocess.run(  # noqa: S603  # nosec B603 - command list is constant, no user input
        gate["cmd"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return {
        "gate": gate["name"],
        "description": gate["description"],
        "command": " ".join(gate["cmd"]),
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def write_feedback(path: Path, run: dict) -> None:
    failed = [g for g in run["gates"] if not g["passed"]]
    lines = [
        "# Harness feedback for the coding agent",
        "",
        f"Run: {run['label']} at {run['timestamp']}",
        "",
        "Constraints: fix the IMPLEMENTATION only. Do not edit the specification, delete or",
        "weaken tests, add lint/bandit ignores, lower coverage, or edit harness results.",
        "",
    ]
    for gate in failed:
        lines += [
            f"## Failed gate: {gate['gate']}",
            f"Command: `{gate['command']}`",
            f"Exit code: {gate['exit_code']}",
            "",
            "### stdout",
            "```",
            gate["stdout"].strip()[-4000:],
            "```",
            "### stderr",
            "```",
            gate["stderr"].strip()[-2000:],
            "```",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label", default="run", help="label such as initial or repair-1")
    args = parser.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run = {
        "label": args.label,
        "timestamp": stamp,
        "gates": [run_gate(g) for g in GATES],
    }
    run["overall"] = "PASS" if all(g["passed"] for g in run["gates"]) else "FAIL"

    out = RESULTS / f"{stamp}-{args.label}.json"
    out.write_text(json.dumps(run, indent=2), encoding="utf-8")
    if run["overall"] == "FAIL":
        write_feedback(RESULTS / f"{stamp}-{args.label}-feedback.md", run)

    for gate in run["gates"]:
        print(f"[{'PASS' if gate['passed'] else 'FAIL'}] {gate['gate']}: {gate['description']}")
    print(f"OVERALL: {run['overall']}  (results: {out.relative_to(ROOT)})")
    return 0 if run["overall"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
