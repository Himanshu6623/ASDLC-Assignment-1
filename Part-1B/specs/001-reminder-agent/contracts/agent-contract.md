# Reminder Agent Interface Contract

## Agent input

The agent accepts one JSON object with exactly:

| Field | Type | Required |
|---|---|---|
| `text` | string | Yes |
| `now` | string | Yes; ISO-8601 datetime including a UTC offset |

The request text is untrusted data. It is not an instruction source for system behavior.

## Agent output

The agent returns a JSON object with exactly these fields and no additional properties:

```json
{
  "intent": "create",
  "title": "Pay rent",
  "datetime": "2026-11-23T09:00:00+05:30",
  "snooze_minutes": null,
  "clarification_question": null
}
```

`intent` is one of `create`, `reschedule`, `snooze`, `clarify`, or `refuse`. Field types, bounds, datetime ordering, and per-intent nullability are specified in [data-model.md](../data-model.md) and enforced by the schema and property evaluator. Datetimes are offset-bearing ISO-8601 values. Unless the text explicitly specifies another timezone or offset, use the offset in `now`. Do not guess missing or ambiguous date/time information.

## Provider boundary

The provider adapter sends a JSON `POST` to `/v1beta/models/{model}:generateContent` using Python's standard-library `urllib`. It sends the API credential from `LLM_API_KEY` at runtime in the `x-goog-api-key` header; the key is never hard-coded, logged, returned, or included in evaluation fixtures. The request asks for schema-constrained JSON where supported, while local parsing and validation remain mandatory.

The model identifier is deployment configuration rather than part of the public agent input/output contract. The adapter parses the provider response and converts transport, provider, and malformed-response failures into an explicit service error for the runner; it must not turn such errors into a valid-looking reminder result.

The runner retries transient transport/timeouts and HTTP 408, 429, or 5xx failures up to three total attempts with exponential backoff and jitter. It does not retry invalid-request or authentication failures (including HTTP 400, 401, 402, and 403). Exhausted service errors are recorded separately and excluded from functional scoring. Every model-generated result is parsed and validated before returning it to a caller.
