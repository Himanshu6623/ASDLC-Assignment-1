# Phase 0 Research

## Runtime and dependencies

- **Decision**: Implement with Python 3.11+ and the standard library only.
- **Rationale**: The specification and constitution require a deterministic CLI/library with no runtime third-party dependencies.
- **Alternatives considered**: Third-party CLI or JSON libraries; rejected because they add dependencies and provide no feature benefit.

## Domain boundaries

- **Decision**: Use `TodoError` subclasses for domain failures and `argparse` for usage failures. Non-integer IDs are usage failures; integer IDs less than one are domain failures.
- **Rationale**: This maps the specification's exit-code contract directly and keeps validation failures separate from command syntax failures.
- **Alternatives considered**: Returning tuples or exceptions for both classes; rejected because usage and domain behavior differ at the CLI boundary.

## Persistence

- **Decision**: Store exactly `{"next_id": int, "tasks": [...]}`. Task records contain exactly `id`, `title`, `priority`, `tags`, and `status`. Load missing files as an empty collection. Validate the entire document before constructing service state. Write through a same-directory `tempfile.mkstemp` followed by `os.replace`.
- **Rationale**: Exact structure makes corruption detectable, and atomic replacement prevents partial documents.
- **Alternatives considered**: Including version/time fields or in-place rewrites; rejected by FR-011 and FR-010.

## Determinism

- **Decision**: No clocks, randomness, network APIs, or shell commands in the implementation. Tag matching and normalization use lowercase exact strings.
- **Rationale**: The persisted form and behavior must be stable across runs and the constitution prohibits ambient inputs.
- **Alternatives considered**: Timestamped records or network-backed storage; rejected.

## Validation and state changes

- **Decision**: Normalize/validate title, priority, tags, status, and ID in pure helpers before mutating loaded state. Apply updates to a copy or only after every update field validates.
- **Rationale**: The specification requires rejected operations to leave complete state unchanged.
- **Alternatives considered**: Mutating fields incrementally; rejected because later validation failures could cause partial updates.

## CLI contract

- **Decision**: Support `add`, `list`, `update`, `status`, and `delete`. Print human-readable task lines or human-readable deletion text on success. Do not add `--json`. Unknown status filters and malformed/missing arguments are usage exit 2.
- **Rationale**: This satisfies FR-012 through FR-014 and the clarified behavior.
- **Alternatives considered**: JSON success output or positive-integer argparse type for IDs; rejected.

## Harness

- **Decision**: One `.harness/run_harness.py` invokes ruff, bandit, and pytest. It records machine-readable results under `evidence/harness-results/` and runs pytest with branch coverage and a 90% threshold.
- **Rationale**: Centralizes all mandatory gates and makes outcomes auditable.
- **Alternatives considered**: Separate scripts or generated PASS reports; rejected because one runner and genuine gate exit codes are required.
