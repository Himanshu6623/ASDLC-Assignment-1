# Tasks: Smart Todo CLI and Library

**Input**: Design documents from `/specs/001-smart-todo/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/cli.md](./contracts/cli.md)

**Task types**:

- **[TEST]**: Test-only task that changes or adds coverage under `tests/`.
- **[IMPLEMENTATION]**: Production-code task that changes files under `src/`.
- Harness or evidence tasks are labeled `[IMPLEMENTATION]` only when they execute project code/configuration.

## Phase 1: Setup

**Purpose**: Confirm shared planning and implementation inputs.

- [X] T001 Review `specs/001-smart-todo/spec.md`, `specs/001-smart-todo/plan.md`, `specs/001-smart-todo/data-model.md`, and `specs/001-smart-todo/contracts/cli.md` for requirement and traceability inputs.
- [X] T002 Review `specs/001-smart-todo/research.md` and confirm the standard-library-only, atomic-persistence, and deterministic harness decisions.

---

## Phase 2: Foundational

**Purpose**: Establish the test and implementation baseline before story-specific work.

- [X] T003 [TEST] Re-map all existing service tests in `tests/test_service.py` to cite FR-001 through FR-014 and NFR-001 through NFR-004 in test names or nearby comments, preserving one binary pass/fail assertion per requirement. Map network/determinism coverage to FR-013 and NFR-004.

- [X] T004 [TEST] Re-map all existing CLI tests in `tests/test_cli.py` to cite FR-012, FR-014, and any related FR/NFR IDs in test names or nearby comments.

**Checkpoint**: Existing tests have explicit requirement traceability and provide the baseline for implementation.

---

## Phase 3: User Story 1 - Create and review tasks (Priority: P1) 🎯 MVP

**Goal**: Ensure task creation, tag normalization, filtering, and ordering match FR-001 through FR-006.

**Independent Test**: Create tasks with default and explicit values, verify normalization and boundaries, filter by tag/status/both, and verify priority and ID ordering.

### Tests for User Story 1

- [X] T005 [P] [US1] [TEST] Add service tests in `tests/test_service.py` for title trimming and exact 1/100/101-character boundaries required by FR-001.
- [X] T006 [P] [US1] [TEST] Add service tests in `tests/test_service.py` for whitespace in tags being invalid rather than implicitly trimmed, lowercase duplicate removal, and exactly 10 versus 11 distinct tags, covering FR-003.
- [X] T007 [P] [US1] [TEST] Add or strengthen service tests in `tests/test_service.py` for default `medium`, priority choices, status and tag intersection filtering, unknown-tag success, and priority/ID versus `--no-sort` ordering, covering FR-002, FR-005, and FR-006.
- [X] T008 [P] [US1] [TEST] Add service tests in `tests/test_service.py` for monotonic positive IDs starting at 1 and never reusing deleted IDs, covering FR-004.

### Implementation for User Story 1

- [X] T009 [US1] [IMPLEMENTATION] Update `src/smart_todo/service.py` to trim titles, enforce 1-100 characters, default priority to `medium`, accept only `low`, `medium`, and `high`, and reject invalid or over-limit input covering FR-001 and FR-002.
- [X] T010 [US1] [IMPLEMENTATION] Update `src/smart_todo/service.py` to lowercase tags, reject tag whitespace, remove duplicates after lowercasing, validate `[a-z0-9_-]{1,20}`, and enforce at most 10 distinct tags, covering FR-003.
- [X] T011 [US1] [IMPLEMENTATION] Update `src/smart_todo/service.py` to allocate initial `todo` tasks monotonically from positive IDs and never reuse deleted IDs, covering FR-004.
- [X] T012 [US1] [IMPLEMENTATION] Update `src/smart_todo/service.py` to support case-insensitive tag filters, status filters, combined intersection filters, priority-first ordering, and ascending-ID `--no-sort` behavior, covering FR-005 and FR-006.

**Checkpoint**: User Story 1 is independently testable with creation, normalization, filtering, and ordering passing.

---

## Phase 4: User Story 2 - Update and complete tasks (Priority: P1)

**Goal**: Ensure atomic updates and the exact status transition graph leave state unchanged after failures.

**Independent Test**: Update all and individual fields, verify invalid updates do not mutate tasks, and verify every allowed and forbidden status transition.

### Tests for User Story 2

- [X] T013 [P] [US2] [TEST] Add service tests in `tests/test_service.py` for title/priority/tag updates using creation validation and for no partial mutation after any invalid update field, covering FR-007.
- [X] T014 [P] [US2] [TEST] Add service tests in `tests/test_service.py` for all allowed transitions and all forbidden/current-state transitions, with complete task state unchanged after each failure, covering FR-009.

### Implementation for User Story 2

- [X] T015 [US2] [IMPLEMENTATION] Update `src/smart_todo/service.py` to validate every title, priority, and tag supplied in an update before mutating task fields, preserving creation rules and failed-operation state, covering FR-007.
- [X] T016 [US2] [IMPLEMENTATION] Update `src/smart_todo/service.py` to permit only `todo -> in_progress`, `in_progress -> todo/done`, and `done -> todo`, rejecting every other transition including current-state transitions, covering FR-009.

**Checkpoint**: User Story 2 is independently testable with atomic updates and controlled transitions.

---

## Phase 5: User Story 3 - Delete tasks and retain saved work (Priority: P1)

**Goal**: Ensure delete, restart persistence, strict saved-file structure, and atomic writes are reliable.

**Independent Test**: Create/delete/restart tasks, preserve `next_id`, reject malformed documents byte-for-byte without overwrite, and verify successful or previous complete state after writes.

### Tests for User Story 3

- [X] T017 [P] [US3] [TEST] Add strict FR-011 service tests in `tests/test_service.py` that reject extra or missing top-level fields and extra or missing task fields in the saved JSON document.
- [X] T018 [P] [US3] [TEST] Add strict FR-011 service tests in `tests/test_service.py` for duplicate IDs, zero/negative/non-integer IDs, task arrays with invalid types, and `next_id` that is not positive or is not greater than every saved ID.
- [X] T019 [P] [US3] [TEST] Add strict FR-011 service tests in `tests/test_service.py` for untrimmed 101-character titles, invalid priorities, unnormalized/duplicate/invalid tags, and invalid statuses.
- [X] T020 [P] [US3] [TEST] Add persistence tests in `tests/test_service.py` for missing-file empty state, no overwrite of corrupt or wrongly structured files, successful restart, monotonic ID preservation, delete unknown-ID failure, and atomic-write/no-partial-file behavior, covering FR-008, FR-010, and FR-011.

### Implementation for User Story 3

- [X] T021 [US3] [IMPLEMENTATION] Update `src/smart_todo/service.py` to fail unknown deletions without mutating task state and preserve monotonic `next_id`, covering FR-008 and FR-004.
- [X] T022 [US3] [IMPLEMENTATION] Update `src/smart_todo/storage.py` to treat a missing file as `next_id = 1` and an empty task list; use only atomic same-directory temporary-file replacement for saves, covering FR-010.
- [X] T023 [US3] [IMPLEMENTATION] Update `src/smart_todo/storage.py` to validate saved JSON exactly against FR-011: top-level object with exactly `next_id` and `tasks`, positive integer greater than every ID, task objects with exactly `id/title/priority/tags/status`, unique positive IDs, already-trimmed valid titles, valid priorities/tags/statuses, and no repair or overwrite on failure.

**Checkpoint**: User Story 3 is independently testable with delete and durable strict persistence.

---

## Phase 6: User Story 4 - Receive clear command outcomes (Priority: P2)

**Goal**: Ensure clarified CLI exit codes, output streams, malformed arguments, and text-only success output match FR-012 and FR-014.

**Independent Test**: Invoke success, domain, and usage cases and verify exit code 0/1/2 plus stdout/stderr behavior.

### Tests for User Story 4

- [X] T024 [P] [US4] [TEST] Add CLI tests in `tests/test_cli.py` proving a non-integer ID exits 2, while integer zero and negative IDs exit 1 and produce stderr only, covering FR-012.
- [X] T025 [P] [US4] [TEST] Add CLI tests in `tests/test_cli.py` proving an unknown `list --status` value exits 2, an unknown tag filter returns exit 0 with an empty human-readable list, and no update fields exits 2 without mutation, covering FR-005 and FR-012.
- [X] T026 [P] [US4] [TEST] Add CLI tests in `tests/test_cli.py` proving success text is human-readable, `--json` is unavailable, success output is deterministic, and domain errors return 1 with non-empty stderr and empty stdout, covering FR-012 and FR-014.
- [X] T027 [P] [US4] [TEST] Add CLI tests in `tests/test_cli.py` for malformed/missing commands and arguments, invalid priority/status choices, and corrupt saved data as the specified usage/domain exit classes, covering FR-011 and FR-012.

### Implementation for User Story 4

- [X] T028 [US4] [IMPLEMENTATION] Update `src/smart_todo/cli.py` so task IDs are parsed as integers (non-integer exits 2 via argparse), zero/negative IDs reach the service and exit 1 as not found, list --status is restricted to todo/in_progress/done (unknown exits 2), an unknown tag filter returns an empty list with exit 0, and the --json option is removed, covering FR-005, FR-012 and FR-014.
- [X] T029 [US4] [IMPLEMENTATION] Update `src/smart_todo/cli.py` so an update with no title/priority/tag exits 2 as a usage error without touching saved data, covering FR-007 and FR-012.
- [X] T030 [US4] [IMPLEMENTATION] Update `src/smart_todo/cli.py` so domain errors, including corrupt saved data, print a message to stderr, nothing to stdout, and exit 1, while successes print deterministic human-readable text and exit 0, covering FR-011, FR-012 and FR-014.
- [X] T037 [P] [US4] [TEST] Add an end-to-end CLI journey test in `tests/test_cli.py` that runs add, list, update, status (todo -> in_progress -> done) and delete against one data file through main(), checking exit codes and stdout at each step and never editing the data file by hand, covering SC-008.

**Checkpoint**: User Story 4 is independently testable with deterministic exit codes and output streams.

---

## Phase 7: Cross-Cutting Quality and Harness

**Purpose**: Complete network, coverage, lint, security, and recorded evidence gates.

- [X] T031 [P] [TEST] Add or verify tests in `tests/test_service.py` and `tests/test_cli.py` that exercise only local/deterministic operations and assert no network request is made, covering FR-013 and NFR-004.
- [X] T032 [P] [TEST] Verify all FR-001 through FR-014 and NFR-001 through NFR-004 have at least one binary pass/fail test mapped in `tests/test_service.py`, `tests/test_cli.py`, or `.harness/run_harness.py`, with a final traceability review in `specs/001-smart-todo/plan.md`.
- [X] T033 [IMPLEMENTATION] Update `src/smart_todo/service.py`, `src/smart_todo/storage.py`, and `src/smart_todo/cli.py` for explicit public type hints, no avoidable complexity, no network calls, no shell/eval/exec usage, and no lint or Bandit suppressions, covering NFR-001, NFR-002, FR-013, and NFR-004.
- [X] T034 [IMPLEMENTATION] Update `.harness/run_harness.py` if needed to run ruff, Bandit, and pytest with `--cov-branch` and `--cov-fail-under=90`, record each gate result under `evidence/harness-results/`, and avoid editing recorded PASS/FAIL results, covering NFR-001 through NFR-003.
- [ ] T036 [IMPLEMENTATION] After /speckit-implement finishes and before running the harness or any harness-driven repair, copy the first generated `src/` and `tests/` into `evidence/initial-generation/agent-output/` (covering the constitution's preservation rule).
- [ ] T035 [IMPLEMENTATION] Run `python .harness/run_harness.py --label final` and preserve the generated machine-readable result under `evidence/harness-results/` plus genuine gate output, covering FR-001 through FR-014 and NFR-001 through NFR-004.

---

## Dependencies & Execution Order

### Phase Dependencies

- Phase 1 is read-only setup and has no dependencies.
- Phase 2 foundational test traceability should complete before story test and implementation work.
- User Stories 1-4 may proceed independently after foundation, but execute tests before implementation within each story.
- Phase 7 cross-cutting gates depend on all desired story implementation tasks.

### User Story Dependencies

- **US1 (P1)**: Independent; it establishes creation/filter/order behavior.
- **US2 (P1)**: Depends on the US1 service model for task state but can be implemented and tested independently.
- **US3 (P1)**: Depends on the US1/US2 collection model and strict persistence contract.
- **US4 (P2)**: Depends on the CLI contract and service/domain exceptions established by US1-US3.

### Within Each Story

- Add or remap tests before production implementation.
- Implement shared service behavior before dependent CLI behavior.
- Complete and verify each story checkpoint before starting the next priority.

---

## Parallel Opportunities

- T005-T008 test tasks may be prepared in parallel because they use separate test sections in `tests/test_service.py`.
- T013-T014 test tasks may be prepared in parallel.
- T017-T020 persistence test tasks may be prepared in parallel.
- T024-T027 CLI test tasks may be prepared in parallel.
- T031-T032 cross-cutting tests may be prepared in parallel.
- The implementation tasks for independent files may be parallelized only when the test dependency for that file is complete.

## Parallel Example: User Story 3

```text
Prepare T017 strict top-level/task-field tests.
Prepare T018 ID and next_id invariant tests.
Prepare T019 title/priority/tag/status saved-value tests.
Prepare T020 persistence and atomic-write tests.
Then implement T021-T023 in service.py and storage.py.
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 setup and Phase 2 traceability remapping.
2. Complete Phase 3 (US1) tests and implementation.
3. Stop and verify US1 independently.
4. Continue US2, US3, then US4.
5. Finish with Phase 7 harness and recorded evidence.

### Incremental Delivery

1. Complete shared test remapping.
2. Deliver create/list behavior.
3. Add update/status behavior.
4. Add persistence/delete behavior.
5. Add CLI outcome behavior.
6. Run all quality gates and preserve evidence.

## Notes

- Every test task is explicitly marked `[TEST]`; every production-code task is explicitly marked `[IMPLEMENTATION]`.
- User-story tasks include `[US1]`, `[US2]`, `[US3]`, or `[US4]`.
- `[P]` marks independent work within a phase and never indicates dependency-free cross-phase work.
- No source or test file is modified by task generation; implementation tasks instruct later implementation to do so.
