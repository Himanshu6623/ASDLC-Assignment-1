# Tasks: Reminder Agent

**Input**: Design documents from `/specs/001-reminder-agent/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/agent-contract.md, quickstart.md

**Tests**: Unit tests are required for the schema evaluator, property evaluator, quality evaluator, evaluation runner, static runner, and provider behavior.

**Organization**: Tasks are grouped by priority user story so each increment is independently testable. Every task is labeled [TEST] or [IMPLEMENTATION].

## Format: `[ID] [P?] [Story] [TEST|IMPLEMENTATION] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks).
- **[Story]**: Which user story this task belongs to in user-story phases.
- Every task includes an exact file path.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Establish project metadata and the initial implementation layout.

- [ ] T001 [IMPLEMENTATION] Create Python 3.11+ package metadata and development dependencies (`pytest`, `ruff`, `bandit`, `jsonschema`) in `pyproject.toml`.
- [ ] T002 [P] [IMPLEMENTATION] Add package layout and public exports in `src/reminder_agent/__init__.py` and `src/reminder_agent/__main__.py`.
- [ ] T003 [IMPLEMENTATION] Create evaluation and evidence directories plus README conventions in `evals/`, `.harness/`, `prompts/`, `evidence/`, and `evidence/README.md`.
- [ ] T004 [IMPLEMENTATION] Add reusable quality configuration for Ruff and Bandit in `.harness/ruff.toml` and `.harness/bandit.yaml`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Build the shared contract, prompt, provider, dataset, thresholds, and initial implementation that every story depends on.

**WARNING**: Complete this phase before any story work or harness run.

- [ ] T005 [IMPLEMENTATION] Implement the five-field reminder input/output contract and intent-specific parsing helpers in `src/reminder_agent/contract.py`, including exactly `text`/`now` input and exactly `intent`, `title`, `datetime`, `snooze_minutes`, and `clarification_question` output fields.
- [ ] T006 [IMPLEMENTATION] Implement the Gemini REST provider client in `src/reminder_agent/provider.py` using `urllib`, `LLM_API_KEY`, `x-goog-api-key`, bounded timeouts, retries for transport/timeouts and HTTP 408/429/5xx, no retry for 400/401/402/403, and explicit error classification.
- [ ] T007 [IMPLEMENTATION] Implement the agent orchestration entry point in `src/reminder_agent/agent.py` so provider output is parsed and locally validated before return.
- [ ] T008 [IMPLEMENTATION] Create the untrusted reminder prompt in `prompts/system_prompt.md`, keeping reminder text as data and requiring clarification for missing or ambiguous dates/times.
- [ ] T009 [IMPLEMENTATION] Create the closed JSON Schema with exactly five fields, `additionalProperties: false`, intent enum, nullable payload fields, title maximum 100 characters, and snooze range in `.harness/schema/result.schema.json`.
- [ ] T010 [IMPLEMENTATION] Create the at-least-15-case traceable evaluation dataset in `evals/dataset.json`, covering normal, boundary, ambiguous, missing-information, malformed, and adversarial inputs with IDs, requirement IDs, inputs, expected intents, expected properties, and datetime fields/tolerances where applicable.
- [ ] T011 [IMPLEMENTATION] Create immutable threshold metadata in `evals/threshold.json` requiring 100% schema validity, 100% guardrail pass rate, and at least 85% overall pass rate.
- [ ] T012 [IMPLEMENTATION] Implement the first schema evaluator layer in `.harness/schema_eval.py` to parse JSON and validate exactly the closed contract and field constraints.
- [ ] T013 [IMPLEMENTATION] Implement the second invariant/property evaluator layer in `.harness/property_eval.py` to enforce intent-specific nullability, title bounds, offset-bearing future datetimes, snooze integer bounds, clarification/refusal behavior, and input requirements.
- [ ] T014 [IMPLEMENTATION] Implement the third quality/title-similarity evaluator layer in `.harness/quality_eval.py` using this title-similarity method identically: Lowercase text; tokens are runs of Unicode letters and digits (no underscores); remove the stopwords {a, an, the, to, my, me, for, of, about, remind, reminder, please}; similarity = |A intersect B| / |A union B|, and 1.0 when both sets are empty; pass at 0.5 or above.
- [ ] T015 [IMPLEMENTATION] Implement the evaluation runner in `.harness/run_eval.py` with stable ascending case-ID order, the schema -> property -> similarity stage sequence, fixed-threshold aggregation, traceable PASS/FAIL/SERVICE_ERROR outcomes, and provider errors excluded from pass-rate denominators.
- [ ] T016 [IMPLEMENTATION] Implement the static runner in `.harness/run_static.py` to run the static quality checks and produce structured evidence-compatible output.
- [ ] T017 [IMPLEMENTATION] Preserve the complete first generated implementation snapshot in `evidence/eval-runs/initial-generation/baseline/` (copy `src/`, `tests/`, `prompts/`, `evals/`, and `.harness/`) before any evaluation or static harness run.

**Checkpoint**: Contract, provider, prompt, dataset, threshold, all three evaluator layers, both runners, and the immutable initial-generation snapshot exist.

---

## Phase 3: User Story 1 - Create or Reschedule a Reminder (Priority: P1)

**Goal**: Interpret valid create/reschedule requests as stable results with non-empty titles and future offset-bearing datetimes.

**Independent Test**: Run focused create/reschedule tests and verify intent, title, future datetime, null fields, title similarity, and requirement traceability.

### Tests for User Story 1

- [ ] T018 [P] [US1] [TEST] Add unit tests for create/reschedule contract parsing, title and datetime invariants, and future-time checks in `tests/test_contract_and_agent.py`.
- [ ] T019 [P] [US1] [TEST] Add unit tests for every `create`/`reschedule` dataset boundary across the schema evaluator, invariant/property evaluator, and quality/title-similarity evaluator in `tests/test_evaluators.py`.
- [ ] T020 [P] [US1] [TEST] Add unit tests for evaluation runner case ordering, stage short-circuiting, overall/guardrail/schema aggregation, and fixed thresholds in `tests/test_runner.py`.
- [ ] T021 [P] [US1] [TEST] Add unit tests for the static runner's quality-check invocation and evidence-compatible report output in `tests/test_runner.py`.

### Implementation for User Story 1

- [ ] T022 [US1] [IMPLEMENTATION] Complete create/reschedule interpretation in `src/reminder_agent/agent.py`, using the offset in `now` unless text specifies another offset and never guessing for missing date-time details.
- [ ] T023 [US1] [IMPLEMENTATION] Add create/reschedule title extraction and strict future-datetime validation to `src/reminder_agent/contract.py`.
- [ ] T024 [US1] [IMPLEMENTATION] Run and repair only story-specific unit tests for create/reschedule in `tests/test_contract_and_agent.py` and `tests/test_evaluators.py`.

**Checkpoint**: Create/reschedule behavior passes independently and leaves title, datetime, snooze, and clarification fields with the required intent-specific values.

---

## Phase 4: User Story 2 - Snooze a Reminder (Priority: P1)

**Goal**: Accept integer snooze durations from 1 through 1440 and reject missing or invalid durations.

**Independent Test**: Supply snooze values at 1, 15, 1440, and invalid boundaries and verify integer range and null payload fields.

### Tests for User Story 2

- [ ] T025 [P] [US2] [TEST] Add parameterized snooze tests for 1, 15, 1440, zero, negative, above 1440, fractional, string-valued, and missing values in `tests/test_contract_and_agent.py`.
- [ ] T026 [P] [US2] [TEST] Add snooze property and schema evaluator tests in `tests/test_evaluators.py`.

### Implementation for User Story 2

- [ ] T027 [US2] [IMPLEMENTATION] Implement snooze parsing and validation in `src/reminder_agent/contract.py` and `src/reminder_agent/agent.py`, with all non-snooze fields null.
- [ ] T028 [US2] [IMPLEMENTATION] Run and repair only snooze-focused unit tests in `tests/test_contract_and_agent.py` and `tests/test_evaluators.py`.

**Checkpoint**: Supported snooze boundaries pass and invalid/missing durations never become valid snooze results.

---

## Phase 5: User Story 3 - Ask for Missing or Ambiguous Information (Priority: P1)

**Goal**: Ask a clear clarification instead of inventing missing or ambiguous date/time information.

**Independent Test**: Supply missing-time, vague-time, empty, and gibberish inputs and verify clarify/refuse behavior with no invented datetime.

### Tests for User Story 3

- [ ] T029 [P] [US3] [TEST] Add missing-time, ambiguous, empty, whitespace, and gibberish cases in `tests/test_contract_and_agent.py`.
- [ ] T030 [P] [US3] [TEST] Add clarify/refuse nullability and nonempty clarification-question tests in `tests/test_evaluators.py`.

### Implementation for User Story 3

- [ ] T031 [US3] [IMPLEMENTATION] Implement clarify/refuse result handling in `src/reminder_agent/agent.py` and `src/reminder_agent/contract.py`, with `clarification_question` non-null for clarify and all payload fields null for refuse.
- [ ] T032 [US3] [IMPLEMENTATION] Run and repair only clarification-focused unit tests in `tests/test_contract_and_agent.py` and `tests/test_evaluators.py`.

**Checkpoint**: Missing or ambiguous input produces clarification/refusal and never creates an invented reminder datetime.

---

## Phase 6: User Story 4 - Reject Unsafe or Out-of-Scope Requests (Priority: P1)

**Goal**: Refuse prompt injection, secret disclosure, reminder deletion/listing, and unrelated requests without following embedded instructions.

**Independent Test**: Run adversarial cases and verify every guardrail returns `refuse` with all payload fields null.

### Tests for User Story 4

- [ ] T033 [P] [US4] [TEST] Add prompt-injection, secret/prompt disclosure, instruction-change, delete/list, mixed reminder/injection, and unrelated-request cases in `tests/test_contract_and_agent.py`.
- [ ] T034 [P] [US4] [TEST] Add provider mock tests for retry classification, authentication/invalid-request no-retry behavior, malformed responses, exhausted retries, and credential-free diagnostics in `tests/test_provider.py`.
- [ ] T035 [P] [US4] [TEST] Add guardrail pass-rate and SERVICE_ERROR separation tests in `tests/test_runner.py`.

### Implementation for User Story 4

- [ ] T036 [US4] [IMPLEMENTATION] Complete provider error classification and bounded retry behavior in `src/reminder_agent/provider.py`, ensuring credentials never appear in output or logs.
- [ ] T037 [US4] [IMPLEMENTATION] Strengthen the guardrail prompt and agent refusal handling in `prompts/system_prompt.md` and `src/reminder_agent/agent.py`, treating reminder text strictly as untrusted data.
- [ ] T038 [US4] [IMPLEMENTATION] Run and repair only guardrail and provider unit tests in `tests/test_contract_and_agent.py` and `tests/test_provider.py`.

**Checkpoint**: Every guardrail case refuses and provider/service failures remain separate from functional pass rates.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Verify the complete implementation, preserve traceability, and record final evidence.

- [ ] T039 [TEST] Run the complete unit suite with `python -m pytest` and resolve any failures in `tests/`.
- [ ] T040 [TEST] Run the static runner with `python .harness/run_static.py` and confirm Ruff and Bandit report zero findings in `evidence/static-runs/`.
- [ ] T041 [TEST] Validate every dataset case has ID, requirement IDs, input, expected intent, expected properties, and applicable datetime metadata in `evals/dataset.json`.
- [ ] T042 [IMPLEMENTATION] Verify the final evaluation report is recorded under `evidence/eval-runs/` and preserves fixed 100% schema, 100% guardrail, and at least 85% overall thresholds from `evals/threshold.json`.
- [ ] T043 [TEST] Run the final evaluation with `python .harness/run_eval.py --dataset evals/dataset.json` and record the timestamped JSON report under `evidence/eval-runs/`.
- [ ] T044 [IMPLEMENTATION] Review final evidence against `specs/001-reminder-agent/spec.md`, `specs/001-reminder-agent/plan.md`, and `specs/001-reminder-agent/quickstart.md`, preserving PASS/FAIL and SERVICE_ERROR separation without editing results.
- [ ] T045 [TEST] Verify every public Python function in `src/` has parameter and return type hints using the `ast` module.
- [ ] T046 [TEST] Add a repository secret-scan gate to `.harness/run_static.py` that fails on API-key patterns and writes the scan result under `evidence/static-runs/`.

**Checkpoint**: The initial implementation is preserved, unit and static checks pass, and the final evaluation is recorded under evidence with immutable thresholds.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks every user story and all harness runs.
- **User Stories (Phases 3-6)**: Depend on the Foundation phase only; can proceed in priority order or in parallel after T017.
- **Polish (Phase 7)**: Depends on all required user stories and the preserved initial snapshot.

### User Story Dependencies

- **User Story 1 (P1)**: No dependency on US2-US4 after Foundation.
- **User Story 2 (P1)**: No dependency on US1, although it shares the contract and agent modules.
- **User Story 3 (P1)**: No dependency on US1/US2/US4.
- **User Story 4 (P1)**: No dependency on US1-US3; provider behavior is foundational and tested independently.

### Mandatory Evidence Ordering

1. Complete T001-T016.
2. Complete T017 to preserve `evidence/eval-runs/initial-generation/baseline/`.
3. Only then run any harness or final evaluation task.

---

## Parallel Opportunities

- T002 and T004 can run in parallel after T001.
- T005-T011 can run in parallel where each task writes a separate contract, provider, prompt, schema, dataset, or threshold file.
- T012-T014 can run in parallel after T009 and T011 are available.
- T018-T021 are independent unit-test tasks and can run in parallel.
- T025-T026, T029-T030, and T033-T035 are independent test groups and can run in parallel.
- US1-US4 can run in parallel after T017, with each user story retaining its own test and implementation tasks.

## Parallel Example: User Story 1

```text
T018 [TEST] Create/reschedule contract and agent tests
T019 [TEST] Create/reschedule evaluator tests
T020 [TEST] Runner aggregation tests
T021 [TEST] Static runner tests
```

## Implementation Strategy

### MVP First (User Story 1)

1. Complete Phases 1-2, including T017 evidence preservation.
2. Complete Phase 3 (US1).
3. Run T018-T024 and a focused create/reschedule harness subset.
4. Stop and validate that US1 passes independently before starting lower story phases.

### Incremental Delivery

1. Complete Foundation and preserve the initial generation.
2. Add US1, then validate create/reschedule independently.
3. Add US2, then validate snooze boundaries.
4. Add US3, then validate clarification behavior.
5. Add US4, then validate guardrails and provider failures.
6. Finish with final static and evaluation evidence.

---

## Notes

- [P] tasks are parallelizable only when they affect separate files and do not depend on incomplete tasks.
- [TEST] and [IMPLEMENTATION] labels are mandatory on every task.
- [US1]-[US4] labels appear only in their corresponding user-story phases.
- Tests must fail before implementation in a TDD workflow where that workflow is used.
- Do not edit `src/` or `tests/` during this planning task itself; implementation tasks describe the later execution phase.
