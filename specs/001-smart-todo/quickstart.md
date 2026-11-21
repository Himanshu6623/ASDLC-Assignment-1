# Quickstart Validation

## Prerequisites

- Python 3.11+
- pytest and pytest-cov
- ruff
- bandit

## Prepare

From the repository root:

```powershell
python -m pip install -r requirements-dev.txt
```

## Run the CLI

Use a temporary data file so validation does not depend on a pre-existing collection:

```powershell
$file = Join-Path $env:TEMP "smart-todo-validation.json"
Remove-Item $file -Force -ErrorAction SilentlyContinue
python -m smart_todo --file $file add "  Buy milk  " --priority high --tag "Home"
python -m smart_todo --file $file list --tag home
python -m smart_todo --file $file status 1 in_progress
python -m smart_todo --file $file update 1 --title "Buy oat milk"
python -m smart_todo --file $file delete 1
```

Expected: creation succeeds with title `Buy milk`, priority `high`, status `todo`, and ID `1`; tag filtering is case-insensitive; status and update succeed; delete removes ID `1`. Subsequent creation IDs continue beyond `1`.

## Run tests

```powershell
python -m pytest -q tests
```

The spec-derived suite must verify service behavior and CLI exit/output behavior. Refer to [data-model.md](./data-model.md) for record invariants and [contracts/cli.md](./contracts/cli.md) for command behavior.

## Run all gates

```powershell
python .harness/run_harness.py --label plan-validation
```

Pass requires:

- ruff reports zero findings;
- bandit reports zero findings;
- all pytest tests pass;
- line and branch coverage are each at least 90%;
- one machine-readable run is written under `evidence/harness-results/`.
