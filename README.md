# Part 1A: Smart Todo (deterministic, Spec-Driven)

A CLI and library for tasks: CRUD, tag filtering, priority sorting, status transitions and
atomic JSON persistence. Requirement IDs (FR-1..FR-7) are cited in the tests.

## Setup
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
```

## Use
```bash
export PYTHONPATH=src            # Windows PowerShell: $env:PYTHONPATH="src"
python -m smart_todo add "Write report" --priority high --tag work
python -m smart_todo list --tag work
python -m smart_todo status 1 in_progress
python -m smart_todo update 1 --title "Write final report"
python -m smart_todo delete 1
```
Data file: `todo.json` (override with `--file` or `TODO_FILE`).

## Run the harness
```bash
python .harness/run_harness.py --label initial
```
Gates: **lint** (ruff), **security** (bandit), **tests** (pytest, coverage >= 90%).
Results go to `evidence/harness-results/`; a failed run also writes a `*-feedback.md`
to hand to the coding agent. Exit code 0 means all gates passed.

## Layout
`src/` code, `tests/` spec-derived tests, `.harness/` gates and runner, `docs/speckit-prompts.md`
inputs for Spec Kit, `evidence/` generation snapshots, results and `harness-log.md`.

## Notes on suppressions
Two inline `noqa`/`nosec` comments exist in `.harness/run_harness.py` for the runner's own
`subprocess` call (constant command list, no user input). No suppressions exist in `src/`.
