# Part 1B: Reminder Agent (non-deterministic, Spec-Driven)

An LLM (Google Gemini) turns a reminder request plus a reference time into a structured
result with exactly five fields: `intent`, `title`, `datetime`, `snooze_minutes`,
`clarification_question`. Wording varies between runs, so correctness is judged by an
evaluation harness, not by exact string matching.

## Setup (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
$env:LLM_API_KEY="<your key>"        # never commit a key; this lasts for the current terminal only
$env:PYTHONPATH="src"
python -m reminder_agent --list-models          # pick a model that supports generateContent
$env:LLM_MODEL="<a model name from that list>"  # record the exact name in evidence/harness-log.md
```

## Try the application
```powershell
python -m reminder_agent "Remind me to call mom tomorrow at 5pm" --now 2026-11-23T10:00:00+05:30
```

## Run the evaluation harness
```powershell
python .harness/run_eval.py --label initial --ids C01,C09,C17   # quick key/model check (partial run)
python .harness/run_eval.py --label initial                    # full evaluation (22 cases)
```
Pipeline: `evals/dataset.json` -> model call -> structural (`.harness/schema_eval.py`, JSON
Schema) -> property/invariant (`property_eval.py`) -> semantic title similarity
(`quality_eval.py`) -> aggregate against `evals/threshold.json`.
The threshold (100% schema validity, 100% guardrail cases, at least 85% overall) is declared in
the specification and must not be lowered. Service errors (rate limit, network, blocked or empty
reply) are excluded from the rates and reported separately.

Results: `evidence/eval-runs/<timestamp>-<label>.json` (every run) and `evidence/eval-results.json`
(latest full run). A FAIL also writes `*-feedback.md`, the structured evidence to give the coding
agent. Exit codes: 0 PASS, 1 FAIL, 2 INCONCLUSIVE, 3 could not start.
A partial run (`--ids`) is never copied to `eval-results.json`.

## Static and unit-test gates
```powershell
python .harness/run_static.py initial     # ruff, bandit, pytest (no model or key needed)
```

## Layout
`src/reminder_agent/` application, `prompts/system_prompt.md` instructions, `evals/` dataset and
threshold, `.harness/` evaluators and runners, `tests/` unit tests (use a fake model),
`docs/` Spec Kit prompts, `evidence/` generation snapshots, results and `harness-log.md`.

## Notes on suppressions
Two inline `noqa`/`nosec` comments exist in `.harness/run_static.py` for the runner's own
`subprocess` call (constant command list, no user input). `.harness/run_eval.py` has `E402`
`noqa` comments for imports that must follow the `sys.path` setup. No suppressions in `src/`.
