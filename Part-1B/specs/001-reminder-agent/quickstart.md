# Quickstart: Reminder Agent Validation

This guide describes the intended implementation workflow. Run it after implementation; planning does not create source or test directories.

## Prerequisites

- Python 3.11 or newer.
- An API key available as the `LLM_API_KEY` environment variable for live Gemini evaluation. Never put the key in source, fixtures, or logs.
- Install the project development dependencies: `pytest`, `ruff`, `bandit`, and `jsonschema`.

## Validate locally

From the repository root, install the project and development dependencies using the finalized project metadata, then run:

```powershell
python -m pytest
python -m ruff check .
python -m ruff format --check .
python -m bandit -r src
```

Run the evaluation harness from the repository root:

```powershell
python .harness/run_evals.py --dataset evals/dataset.json
```

The harness validates each result in this order: JSON schema, invariant/property checks, then title similarity for create/reschedule cases. It aggregates only after case-level checks and reports service errors separately from case outcomes.

## Expected evaluation report

- Schema validity is at least 100%.
- Guardrail-case pass rate is 100%.
- Overall pass rate is at least 85%.
- Transient service errors receive bounded retries; exhausted errors are reported separately and excluded from functional pass-rate denominators.
- The report preserves case IDs and requirement IDs so every result is traceable.

See [agent-contract.md](contracts/agent-contract.md) for the interface and provider boundary, and [data-model.md](data-model.md) for field and evaluation-record rules.
