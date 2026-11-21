# Implementation Plan: Smart Todo CLI and Library

**Feature Branch**: not created (work on master; feature directory specs/001-smart-todo) | **Date**: 2026-11-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-smart-todo/spec.md`

## Summary

A standard-library Python CLI and callable library will manage validated tasks, filtering, ordering, status transitions, and atomic JSON persistence. The implementation will preserve the specified record shape exactly, isolate domain and usage failures, and be exercised through spec-derived pytest suites plus a single harness runner.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library at runtime (`argparse`, `json`, `dataclasses`, `tempfile`, `os`)

**Storage**: Local JSON file; atomic replacement with a same-directory temporary file

**Testing**: pytest, pytest-cov

**Target Platform**: Cross-platform Python command-line process

**Project Type**: Single-project callable library and CLI

**Performance Goals**: No performance requirement beyond deterministic interactive use

**Constraints**: No network access, no randomness, no shell execution, no runtime third-party dependencies

**Scale/Scope**: Small in-memory collection persisted to one JSON file

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Pre-design check: PASS. The proposed design uses only the standard library, deterministic inputs and persisted state, binary pytest cases, and the existing unweakened ruff, bandit, and 90% line/branch coverage gates.

Post-design check: PASS. The data model, CLI contract, and validation boundaries implement every functional requirement without exceptions or threshold changes.

## Project Structure

### Documentation (this feature)

```text
specs/001-smart-todo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── cli.md
```

### Source Code (repository root)

```text
src/
└── smart_todo/
    ├── __init__.py
    ├── __main__.py
    ├── service.py
    ├── storage.py
    └── cli.py

tests/
├── conftest.py
├── test_service.py
└── test_cli.py

.harness/
└── run_harness.py
```

**Structure Decision**: Use the requested `src/smart_todo/{service,storage,cli}.py` layout with a thin package entry point, pytest tests, and one `.harness/run_harness.py` runner.

## Implementation Approach

1. **Domain model**: Use dataclasses for `Task` and persisted collection state. Keep normalization and validation in service helpers.
2. **Service operations**: Load state, validate, mutate only after validation succeeds, and persist successful mutations. Preserve monotonic `next_id`.
3. **Persistence**: Reject missing fields or extra fields, invalid types, duplicate IDs, invalid task values, and `next_id <= max(task.id)`. Write with `tempfile.mkstemp`, flush/close, and `os.replace`.
4. **CLI**: Use argparse subcommands and choices. Catch domain exceptions at the command boundary; return `1` with stderr only. Let argparse return usage `2`. Reject update calls with no fields before service execution.
5. **Formatting**: Human-readable text only; task lines contain ID, status, priority, title, and normalized tags.
6. **Harness**: Run ruff, bandit, and pytest in sequence; pytest uses `--cov-branch` and `--cov-fail-under=90`; write machine-readable evidence for every run.

## Requirements-to-tests Traceability

| Requirement | Test files and intended coverage |
|---|---|
| FR-001 | `tests/test_service.py` title trim, empty/101-length boundaries, add behavior |
| FR-002 | `tests/test_service.py` default/valid/invalid priorities |
| FR-003 | `tests/test_service.py` tag lowercase/deduplication/regex/count boundaries |
| FR-004 | `tests/test_service.py` initial/monotonic ID allocation and deletion non-reuse |
| FR-005 | `tests/test_service.py`, `tests/test_cli.py` tag/status/both filtering and unknown-tag success |
| FR-006 | `tests/test_service.py`, `tests/test_cli.py` priority/ID ordering and `--no-sort` |
| FR-007 | `tests/test_service.py`, `tests/test_cli.py` atomic field validation and update-with-no-fields usage |
| FR-008 | `tests/test_service.py`, `tests/test_cli.py` delete success and unknown-ID failure |
| FR-009 | `tests/test_service.py`, `tests/test_cli.py` all allowed/forbidden transitions |
| FR-010 | `tests/test_service.py` missing file and atomic write behavior; `tests/test_cli.py` persisted command journeys |
| FR-011 | `tests/test_service.py` exact schema, types, values, corrupt data, and no overwrite |
| FR-012 | `tests/test_cli.py` exit `0`, `1`, `2`, stderr/stdout separation |
| FR-013 | `tests/test_service.py`, `tests/test_cli.py` operations and a network-access guard test |
| FR-014 | `tests/test_cli.py` human text and absence of `--json` |
| NFR-001 | `.harness/run_harness.py` ruff gate; public functions in `src/smart_todo/*.py` are explicitly typed |
| NFR-002 | `.harness/run_harness.py` bandit gate over `src` and `.harness` |
| NFR-003 | `.harness/run_harness.py` pytest `--cov-branch --cov-fail-under=90` |
| NFR-004 | `tests/test_service.py`, `tests/test_cli.py` network-independent operations; no network API is used by implementation |

## Complexity Tracking

No constitution violations or complexity exceptions require justification.
