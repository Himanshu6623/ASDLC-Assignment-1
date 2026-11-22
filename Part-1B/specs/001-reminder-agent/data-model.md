# Data Model: Reminder Agent

## Reminder Request

One invocation input supplied to the agent.

| Field | Type | Constraints |
|---|---|---|
| `text` | string | Untrusted natural-language content; do not execute or follow instructions embedded in it. |
| `now` | string | ISO-8601 datetime with a UTC offset; required to resolve relative dates and compare instants. |

## Structured Reminder Result

One result returned for every successfully interpreted request. The JSON object has exactly the five fields below.

| Field | Type | Constraints |
|---|---|---|
| `intent` | string enum | `create`, `reschedule`, `snooze`, `clarify`, or `refuse`. |
| `title` | string or null | At most 100 characters; required for `create` and `reschedule`. |
| `datetime` | string or null | Offset-bearing ISO-8601 datetime; required and strictly later than `now` for `create` and `reschedule`. |
| `snooze_minutes` | integer or null | Integer in the inclusive range 1–1440 for `snooze`. |
| `clarification_question` | string or null | Non-empty for `clarify`. |

Intent-specific nullability is normative:

| Intent | Required non-null fields | Required null fields |
|---|---|---|
| `create` | `title`, `datetime` | `snooze_minutes`, `clarification_question` |
| `reschedule` | `title`, `datetime` | `snooze_minutes`, `clarification_question` |
| `snooze` | `snooze_minutes` | `title`, `datetime`, `clarification_question` |
| `clarify` | `clarification_question` | `title`, `datetime`, `snooze_minutes` |
| `refuse` | None | `title`, `datetime`, `snooze_minutes`, `clarification_question` |

The offset for a parsed datetime is inherited from `now` unless the request explicitly specifies a different timezone or offset. Missing or ambiguous date/time information results in `clarify`, not a guessed datetime.

## Evaluation Case

Each dataset entry is an independent, traceable evaluation record.

| Field | Type | Constraints |
|---|---|---|
| `id` | string | Unique and stable case identifier. |
| `requirement_ids` | array of strings | One or more IDs from FR-001 through FR-027. |
| `category` | string | Normal, boundary, ambiguous, missing-information, malformed, or adversarial. |
| `input` | Reminder Request | Same shape and constraints as the agent input. |
| `expected_intent` | string enum | One of the five permitted intents. |
| `expected_properties` | object | Expected field values and/or invariant predicates for the case. |
| `expected_datetime` | string, optional | Expected offset-bearing datetime for datetime cases. |
| `datetime_tolerance_seconds` | number, optional | Allowed absolute difference when comparing instants. |
| `expected_title` | string, optional | Reference title for create/reschedule similarity scoring. |
| `guardrail` | boolean | Marks cases subject to the 100% guardrail threshold. |

## Evaluation Outcome

The runner records case-level functional outcomes separately from service outcomes.

| Field | Type | Constraints |
|---|---|---|
| `case_id` | string | References an evaluation case. |
| `status` | string enum | `PASS`, `FAIL`, or `SERVICE_ERROR`. |
| `stage` | string | Schema, property, similarity, or service. |
| `details` | string or object | Diagnostic information; must not contain credentials or secret request headers. |

`SERVICE_ERROR` cases are retried according to the provider policy, reported separately, and excluded from functional pass-rate denominators. A completed evaluation report retains fixed thresholds from FR-023 through FR-027 and reports schema validity, guardrail pass rate, overall pass rate, and service errors separately.
