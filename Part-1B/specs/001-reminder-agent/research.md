# Research: Reminder Agent

## Gemini REST and `urllib`

**Decision**: POST JSON to Gemini's `/v1beta/models/{model}:generateContent` endpoint using `urllib.request.Request` and `urlopen` with an explicit timeout. Read the API key only from `LLM_API_KEY` and send it in `x-goog-api-key`. Ask Gemini for JSON output constrained by the result schema where supported, then independently parse and validate every response in Python. Keep the model identifier as deployment configuration.

**Rationale**: This follows the requested standard-library-only HTTP client and environment-based secret handling. Server-side structured output helps constrain responses but does not replace local validation of untrusted model output.

**Alternatives considered**: A Google client SDK would add a dependency and conflict with the thin `urllib` client requirement. Accepting free-form text without structured output would increase parsing ambiguity.

Sources: [Gemini `generateContent` REST API](https://ai.google.dev/api/generate-content), [Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key), [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output), [Python `urllib.request`](https://docs.python.org/3/library/urllib.request.html), [Python `urllib.error`](https://docs.python.org/3/library/urllib.error.html).

## Provider failures and retries

**Decision**: Classify authentication/configuration, invalid-request, quota/rate-limit, transport/timeout, malformed response, and exhausted-retry failures separately. Retry transient transport/timeouts and HTTP 408, 429, or 5xx responses up to three total attempts with exponential backoff and jitter. Do not retry client/authentication failures such as HTTP 400, 401, 402, or 403. Record exhausted provider failures as `SERVICE_ERROR`, keep diagnostics free of credentials, and exclude these outcomes from functional score denominators.

**Rationale**: Bounded retries can recover from temporary service instability without looping or disguising invalid requests as evaluation results. Explicit service-error outcomes preserve the constitution's separation between infrastructure and functional failures.

**Alternatives considered**: Retrying every error could repeatedly submit invalid or unauthorized requests. Counting provider outages as functional failures would conflate the implementation's behavior with availability of its dependency.

Sources: [Gemini troubleshooting and retry guidance](https://ai.google.dev/gemini-api/docs/troubleshooting), [Gemini API errors](https://ai.google.dev/gemini-api/docs/api-errors), [urllib exceptions](https://docs.python.org/3/library/urllib.error.html).

## JSON Schema and result validation

**Decision**: Define a closed JSON Schema object with exactly the five output fields, `additionalProperties: false`, enumerated intent values, nullable payload fields, and title/snooze bounds. Validate parsed model output with `jsonschema`; use Python datetime parsing and offset checks for datetime semantics, then run intent-dependent and future-time properties.

**Rationale**: JSON Schema reliably checks structure and field-level constraints. Cross-field requirements (per-intent nullability and `datetime > now`) are clearer as explicit property checks. Date-time format validation should not rely on JSON Schema format annotations alone, which are not automatically enforced by every validator configuration.

**Alternatives considered**: A handwritten-only validator duplicates structural checks and is easier to drift from the documented contract. Treating a `"format": "date-time"` annotation as the sole date-time check risks accepting invalid or offset-free values if format checking is not enabled.

Sources: [`jsonschema` validation](https://python-jsonschema.readthedocs.io/en/stable/validate/), [`jsonschema` errors](https://python-jsonschema.readthedocs.io/en/stable/errors/), [Python `json`](https://docs.python.org/3/library/json.html), [Python `datetime`](https://docs.python.org/3/library/datetime.html).

## Development and test tooling

**Decision**: Use pytest parameterization for boundary, malformed, normal, and adversarial cases; mock provider HTTP boundaries for deterministic unit tests. Configure Ruff for Python 3.11 (`target-version = "py311"`) and run lint and format checks. Run Bandit recursively over `src/`. Use `jsonschema` for schema checks.

**Rationale**: These tools align with the user's selected stack and constitution gates. Provider mocks keep unit and harness checks independent of network availability and credentials.

**Alternatives considered**: Live API calls as the only tests are nondeterministic, require secrets, and mix service reliability with functional evaluation. Adding a third-party HTTP framework would exceed the requested thin standard-library client.

Sources: [pytest parametrization](https://docs.pytest.org/en/stable/how-to/parametrize.html), [Ruff configuration](https://docs.astral.sh/ruff/configuration/), [Bandit usage](https://bandit.readthedocs.io/en/latest/start.html).

## Title similarity and evaluation ordering

**Decision**: For title scoring, lowercase the title and split it into contiguous alphanumeric tokens (punctuation and whitespace delimit tokens), convert both token sequences to sets, and compute Jaccard intersection-over-union. Use Python's Unicode-aware `str.isalnum()` character test so the implementation does not silently restrict titles to ASCII. Two empty sets score `0.0`; create/reschedule cases require `>= 0.5`. Process cases in stable ascending case-ID order. For each case, run schema validation, property/invariant checks, title similarity (when applicable), then aggregate; a failed stage marks the case failed and later case stages are not used to turn it into a pass.

**Rationale**: Unicode-aware alphanumeric runs match the specification's lowercase alphanumeric word-token rule without adding an unstated ASCII-only restriction. Stable ordering improves reproducibility, while stage ordering ensures aggregation uses only fully validated outcomes.

**Alternatives considered**: ASCII-only regex tokenization is simpler and stable, but would discard non-ASCII letters from titles. Scoring title similarity before structural and property checks could let a matching title mask invalid output.

Sources: [FR-022 and title-similarity clarification](spec.md), [Python `str.isalnum`](https://docs.python.org/3/library/stdtypes.html#str.isalnum), [Python regular expressions](https://docs.python.org/3/library/re.html).
