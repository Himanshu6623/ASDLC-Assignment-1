#!/usr/bin/env python3
"""Static and unit-test gates for Part 1B: ruff, bandit, pytest. Exit 0 only if all pass."""

from __future__ import annotations

import json
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


def main() -> int:
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    results = {}
    for name, cmd in GATES.items():
        proc = subprocess.run(  # noqa: S603  # nosec B603 - constant commands, no user input
            cmd, cwd=ROOT, capture_output=True, text=True, check=False)
        results[name] = {"passed": proc.returncode == 0, "exit_code": proc.returncode,
                         "stdout": proc.stdout[-4000:], "stderr": proc.stderr[-2000:]}
        print(f"[{'PASS' if proc.returncode == 0 else 'FAIL'}] {name}")
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
