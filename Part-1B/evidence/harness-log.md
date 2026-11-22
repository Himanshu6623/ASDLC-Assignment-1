# Harness log: Part 1B (Reminder Agent)

## 1. Model and configuration

The final evaluation was run with Google's Gemini provider using `gemini-3.5-flash-lite`. It used a temperature of `0.0` and ran under Python `3.13.2`. The API key came from the `LLM_API_KEY` environment variable and was not included in any file.

The prompt and dataset hashes belong to the `after-implement` full run: `0e22f7ce221eeee8613a94e3e04be9272528e4e7be69c6beec0aedbc4c4051d2` identifies the system prompt and `6e7370df01d88246e343790fba75203f3f557412e561d9655399dfb0bf5dc692` identifies the dataset used in that run. `evidence/eval-results.json` contains the latest full-run copy.

## 2. Threshold and scoring method

The thresholds were fixed in the specification before the evaluation began. A passing implementation needed at least 100% schema validity, 100% guardrail pass rate, and at least 85% overall pass rate. For create and reschedule requests, title similarity also needed to reach at least `0.5`.

Each case was checked in three stages: JSON structure and schema, expected properties and invariants, and title similarity when a title was required. All applicable stages had to pass for the case to pass. If the provider failed or the service was unavailable, that result was recorded as a service error and kept outside the functional pass-rate calculations.

## 3. Harness results

We started with a few partial key checks to confirm that the provider and selected model were working.

The first check used `gemini-2.5-flash` at 16:04 UTC and found three HTTP 404 service errors, so no cases reached the evaluation stages. The result was inconclusive. A second check used `gemini-2.5-flash-lite` at 16:05 UTC and gave the same HTTP 404 result for all three cases.

After changing the model to `gemini-3.5-flash-lite`, the three-case check at 16:11 UTC passed all three cases with no service errors. The 16:12 UTC rerun passed the same three cases with no service errors. These short reruns checked the model twice before the complete evaluation; they do not establish repeatability across the full dataset.

The complete `after-implement` run began at 16:41 UTC. It passed all 22 cases: 22 schema checks, 22 property checks, and all applicable semantic title checks passed. There were no service errors. The reported rates were 100% for schema validity, 100% for guardrails, and 100% overall.

The static-gate evidence is also clear. The baseline run passed 57 tests with Ruff and Bandit passing. The after-implementation and final static runs each passed 67 tests; both also passed Ruff, Bandit, secret scanning, and public type-hint checks.

## 4. Problems and re-evaluation

The first problem was a service/configuration failure, not a failure of the reminder cases. Both initial model choices returned HTTP 404 responses, and the harness correctly recorded these as service errors rather than failed reminders.

Claude diagnosed the cause by patching `src/reminder_agent/provider.py` so the HTTP client surfaced Google's service message, rather than only showing `HTTP 404`. The message identified the model as no longer available to new users. The patched provider is part of the final code. Because these were service/configuration failures, no failing case was sent to the coding agent or converted into an application feedback item. The model was changed to `gemini-3.5-flash-lite`; a three-case check passed, as did a second three-case rerun, followed by the complete 22-case evaluation.

## 5. Decision and limitations

Decision: Accept

We accepted the implementation because the complete live evaluation passed all 22 cases, met every declared threshold, and the full run had no service errors. The static checks also passed and found no secrets or public-function type-hint omissions.

There are several limitations. This is only one full run, so even with temperature `0.0` it provides no stability evidence across repeated full evaluations. The 22-case dataset is small, tests only one model, and does not cover every possible user wording. The dataset and prompt were written by the same author, so a pass may partly reflect alignment between them. Title similarity is also a word-overlap heuristic rather than an independent or semantic judge, and no independent LLM judge was used.

## 6. Work attribution

The baseline code was written by Claude in chat before a Spec Kit task list existed, and it is preserved in `evidence/initial-generation/baseline`. Copilot made subsequent edits on top of that baseline, saved in `evidence/initial-generation/agent-output`. The Spec Kit artifacts, including the specification, plan, and task list, came from Copilot.
