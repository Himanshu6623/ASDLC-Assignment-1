# Implementation Plan: Reminder Agent

**Branch**: `001-reminder-agent` | **Date**: 2026-11-22 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-reminder-agent/spec.md`

## Summary

Implement a Python natural-language reminder agent that accepts untrusted reminder text plus an offset-bearing reference datetime and returns the fixed five-field JSON contract. A thin Google Gemini REST adapter built on `urllib` supplies interpretation; `LLM_API_KEY` is read from the environment. Every provider result is parsed and validated before use. A deterministic evaluation harness runs schema validation, invariant/property checks, title similarity, and only then aggregates against the immutable specification thresholds. Transient service errors are retried and reported separately, never counted as functional case passes or failures.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: Python standard library; thin Gemini REST adapter using `urllib`; `jsonschema` for output/schema validation.

**Storage**: None; input cases, prompts, schemas, and evaluation reports are repository files.

**Testing**: `pytest`; `ruff` and `bandit` quality checks; `jsonschema` for schema validation.

**Target Platform**: Python 3.11+ environments with network access for live provider calls.

**Project Type**: Python package plus command-line evaluation harness.

**Performance Goals**: No latency or throughput target is specified; provider calls use bounded timeouts and retry limits.

**Constraints**: Secrets are read only from `LLM_API_KEY`; no reminder identity or persistence; exactly five output fields; date-time and per-intent invariants are enforced; service failures are distinct from evaluation failures; evaluation thresholds in FR-023..FR-027 are fixed.

**Scale/Scope**: Single request/response agent and an evaluation dataset of at least 15 traceable cases; no database, web service, or multi-user state.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle / gate | Plan decision | Status |
|---|---|---|
| I. Code quality | Public Python functions will be type-annotated; Ruff and Bandit are required quality checks. | PASS |
| II. Secrets | Gemini credential is read from `LLM_API_KEY`, excluded from fixtures and logs, and not embedded in source. | PASS |
| III. Testability | Each requirement FR-001..FR-027 maps to evaluation case(s) or a harness-level binary check in the traceability matrix below. | PASS |
| IV. Untrusted model output | Parse and validate the model response against the closed JSON schema and property invariants before use or return. | PASS |
| V. Safety | System instructions stay separate from untrusted reminder text; missing or ambiguous time information produces clarification rather than a guess. | PASS |
| VI. Agent guardrails | Initial generation is preserved under `evidence/initial-generation/`; case sets and 100%/100%/85% thresholds are protected from silent weakening. | PASS |
| VII. Failure separation | Transient provider failures are retried; exhausted service errors are reported separately and excluded from functional score denominators. | PASS |

No constitution gate violations or unresolved requirements block the design.

## Evaluation Design

The `.harness/` runner loads `evals/dataset.json` and processes cases in stable ascending case-ID order with this strict per-case order:

1. **Schema validation**: Parse the model result as JSON and require an object with exactly the five output fields, valid types, permitted intent, and schema constraints. A schema failure ends that case's functional checks.
2. **Invariant/property checks**: Verify intent-specific nullability and bounds, datetime parseability and future ordering, expected intent/properties, and relevant missing-time/guardrail behavior.
3. **Title similarity**: For create/reschedule cases, tokenize lowercase alphanumeric words into sets and compute Jaccard similarity; two empty sets score zero. Require a score of at least 0.5.
4. **Aggregation**: After case checks, report schema validity, guardrail pass rate, and overall pass rate against fixed thresholds of 100%, 100%, and at least 85%. Provider errors are separately tallied and excluded from case-rate denominators.

The Gemini adapter uses the REST `generateContent` endpoint and the `x-goog-api-key` header populated from `LLM_API_KEY`. It requests schema-constrained JSON where available but still validates the parsed response locally. Retry transient transport/timeouts and HTTP 408, 429, or 5xx failures up to three total attempts with exponential backoff and jitter. Do not retry invalid-request or authentication failures (including 400, 401, 402, and 403). See [research.md](research.md) for source-backed decisions.

The dataset includes at least 15 cases spanning normal, boundary, ambiguous, missing-information, malformed, and adversarial inputs. Each case carries its case ID and requirement IDs. Date-time cases include an expected datetime and tolerance.

## Requirements-to-Cases Traceability

`CASE-*` identifiers below are planned dataset IDs; `HARNESS-*` identifiers are binary checks against dataset metadata, evaluation stages, or report behavior. All IDs must be preserved in test/evaluation output.

| Requirement | Planned case/check IDs | Coverage |
|---|---|---|
| FR-001 | `CASE-INPUT-VALID`, `CASE-INPUT-NOW-MALFORMED` | Input fields, string type, and offset-bearing `now` validation. |
| FR-002 | `CASE-SCHEMA-*`, `HARNESS-EXACT-KEYS` | Exactly five output fields; no extras or omissions. |
| FR-003 | `CASE-SCHEMA-INTENT-*`, `HARNESS-INTENT-ENUM` | Permitted intent enum and rejection of other values. |
| FR-004 | `CASE-TITLE-BOUNDARY-*`, `HARNESS-TITLE-TYPE-LENGTH` | Nullable/string type, nonempty where required, and 100-character maximum. |
| FR-005 | `CASE-DATETIME-VALID`, `CASE-DATETIME-MALFORMED`, `HARNESS-DATETIME-OFFSET` | Offset-bearing ISO-8601 datetime or null. |
| FR-006 | `CASE-CREATE-FUTURE`, `CASE-RESCHEDULE-FUTURE`, `CASE-DATETIME-PAST` | Required title and datetime, with datetime later than `now`. |
| FR-007 | `CASE-CREATE-BASIC`, `CASE-CREATE-NULLS` | Create interpretation and create-specific nullability. |
| FR-008 | `CASE-RESCHEDULE-NO-ID`, `CASE-RESCHEDULE-TITLE` | Reschedule without reminder identity; title extracted from text and future datetime. |
| FR-009 | `CASE-SNOOZE-MIN`, `CASE-SNOOZE-MAX`, `CASE-SNOOZE-INVALID-*` | Integer snooze range and snooze-specific nullability. |
| FR-010 | `CASE-CLARIFY-MISSING-TIME`, `CASE-CLARIFY-AMBIGUOUS`, `CASE-CLARIFY-NULLS` | Nonempty clarification and clarify-specific nullability. |
| FR-011 | `CASE-REFUSE-GUARDRAIL-*`, `CASE-REFUSE-NULLS` | Refuse intent and all four payload fields null. |
| FR-012 | `CASE-MISSING-DATE`, `CASE-MISSING-TIME`, `CASE-VAGUE-PART-OF-DAY` | Clarify when date/time is absent or ambiguous; never invent a datetime. |
| FR-013 | `CASE-EMPTY`, `CASE-WHITESPACE`, `CASE-GIBBERISH` | Empty or gibberish is clarify/refuse, never create. |
| FR-014 | `CASE-INJECTION-INSTRUCTION-CHANGE` | Refuse attempts to change agent instructions. |
| FR-015 | `CASE-REQUEST-PROMPT`, `CASE-REQUEST-KEY` | Refuse requests for prompt or credentials. |
| FR-016 | `CASE-DELETE-REMINDERS`, `CASE-LIST-REMINDERS` | Refuse deletion/listing requests. |
| FR-017 | `CASE-OUT-OF-SCOPE` | Refuse unrelated requests. |
| FR-018 | `CASE-MIXED-REMINDER-INJECTION` | Reminder text remains untrusted even when it combines a reminder with injected instructions. |
| FR-019 | `HARNESS-CASE-METADATA` | Every case has ID, requirement IDs, input, expected intent, and expected properties. |
| FR-020 | `HARNESS-DATASET-COVERAGE` | Dataset has at least 15 cases and all six required input categories. |
| FR-021 | `HARNESS-DATETIME-ORACLE` | Every datetime case supplies expected datetime and tolerance. |
| FR-022 | `HARNESS-STAGE-ORDER`, `CASE-TITLE-SIMILARITY-*` | Schema, properties, then Jaccard title similarity >= 0.5; all required checks must pass. |
| FR-023 | `HARNESS-SCHEMA-THRESHOLD` | Aggregate schema-validity threshold is exactly 100%. |
| FR-024 | `HARNESS-GUARDRAIL-THRESHOLD` | Guardrail pass-rate threshold is exactly 100%. |
| FR-025 | `HARNESS-OVERALL-THRESHOLD` | Overall pass-rate threshold is at least 85%. |
| FR-026 | `HARNESS-SERVICE-ERROR-RETRY`, `HARNESS-SERVICE-ERROR-REPORT` | Retry and separately report provider/service failures; exclude from functional rates. |
| FR-027 | `HARNESS-THRESHOLD-IMMUTABLE` | Thresholds remain fixed; no failure-responsive reduction is allowed. |

## Project Structure

### Documentation (this feature)

```text
specs/001-reminder-agent/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    └── agent-contract.md
```

### Planned implementation layout (not created by this planning workflow)

```text
pyproject.toml
src/
└── reminder_agent/
    ├── __init__.py
    ├── agent.py
    ├── gemini_client.py
    └── models.py
prompts/
└── reminder-agent.txt
evals/
└── dataset.json
.harness/
├── schema/
│   └── reminder-result.schema.json
├── property_evaluator.py
├── quality_evaluator.py
└── run_evals.py
tests/
├── unit/
├── integration/
└── harness/
evidence/
├── initial-generation/
└── evaluations/
```

**Structure Decision**: Use the requested single Python source package at `src/reminder_agent/`, with prompts, evaluation data, harness, tests, and evidence kept in their requested top-level locations. The harness is one runner backed by separate schema, property, and quality-evaluation modules. No `src/`, `tests/`, or other implementation directories are created during planning; the tree above records intended implementation structure only.

## Phase 0 and Phase 1 Artifacts

- `research.md`: technology and integration decisions, rationale, and alternatives.
- `data-model.md`: request, result, evaluation-case, and evaluation-outcome records.
- `contracts/agent-contract.md`: agent JSON contract and provider boundary.
- `quickstart.md`: post-implementation validation commands and expected score report.

## Complexity Tracking

No constitution violations require justification.
