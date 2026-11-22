#!/usr/bin/env python3
"""Static and unit-test gates for Part 1B: ruff, bandit, pytest. Exit 0 only if all pass."""

from __future__ import annotations

import ast
import json
import re
import subprocess  # noqa: S404  # nosec B404 - constant command lists only
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HARNESS = ROOT / ".harness"
OUT = ROOT / "evidence" / "static-runs"
GATES = {
    "lint": [sys.executable, "-m", "ruff", "check", "--config", str(HARNESS / "ruff.toml"),
             "src", "tests", ".harness"],
    "security": [sys.executable, "-m", "bandit", "-q", "-r", "src", ".harness",
                 "-c", str(HARNESS / "bandit.yaml")],
    "tests": [sys.executable, "-m", "pytest", "-q", "tests"],
}

SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"(?i)(?:api[_-]?key|secret|token)\s*[=:]\s*[\"'][^\"']{12,}[\"']"),
)


def scan_secrets() -> tuple[bool, list[str]]:
    """Fail if source or configuration appears to contain an API key or secret."""
    findings: list[str] = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or ".venv" in path.parts or ".git" in path.parts:
            continue
        if path.suffix.lower() not in {".py", ".toml", ".yaml", ".yml", ".json", ".md", ".env"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append(str(path.relative_to(ROOT)))
    return not findings, findings


def scan_public_types() -> tuple[bool, list[str]]:
    """Require parameter and return type hints on every public Python function."""
    findings: list[str] = []
    for path in sorted((ROOT / "src").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                missing = [arg.arg for arg in (*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs)
                           if arg.arg not in {"self", "cls"} and arg.annotation is None]
                if node.args.vararg and node.args.vararg.annotation is None:
                    missing.append(node.args.vararg.arg)
                if node.args.kwarg and node.args.kwarg.annotation is None:
                    missing.append(node.args.kwarg.arg)
                if node.returns is None:
                    missing.append("return")
                if missing:
                    location = f"{path.relative_to(ROOT)}:{node.lineno}"
                    findings.append(f"{location} {node.name}: {', '.join(missing)}")
    return not findings, findings


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    results = {}
    for name, cmd in GATES.items():
        proc = subprocess.run(  # noqa: S603  # nosec B603 - constant commands, no user input
            cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        results[name] = {"passed": proc.returncode == 0, "exit_code": proc.returncode,
                         "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-2000:]}
        print(f"[{'PASS' if proc.returncode == 0 else 'FAIL'}] {name}")
    secret_ok, secret_findings = scan_secrets()
    type_ok, type_findings = scan_public_types()
    results["secret_scan"] = {"passed": secret_ok, "findings": secret_findings}
    results["public_type_hints"] = {"passed": type_ok, "findings": type_findings}
    print(f"[{'PASS' if secret_ok else 'FAIL'}] secret_scan")
    print(f"[{'PASS' if type_ok else 'FAIL'}] public_type_hints")
    overall = "PASS" if all(r["passed"] for r in results.values()) else "FAIL"
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{stamp}-{label}.json"
    path.write_text(json.dumps({"label": label, "overall": overall, "gates": results}, indent=2),
                    encoding="utf-8")
    print(f"OVERALL: {overall}  (results: {path.relative_to(ROOT)})")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
