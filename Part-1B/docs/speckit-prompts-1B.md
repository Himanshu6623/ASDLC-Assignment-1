# Remaining Spec Kit prompts (Part 1B)

Already done by you: constitution, specify, clarify. Keep the Clarifications section in spec.md
consistent with the reference code (see "Alignment checks" below).

## /speckit-plan
Create the technical plan for specs/001-reminder-agent/spec.md. Write plan.md and supporting
files in that folder only. Do not create src/ or tests/. Tech: Python 3.11+. Runtime: standard
library plus a thin Google Gemini REST client using http.client; the key comes from the
LLM_API_KEY environment variable and the model from LLM_MODEL. Dev/harness: pytest, ruff,
bandit, jsonschema. Layout: src/reminder_agent/, prompts/system_prompt.md, evals/dataset.json,
evals/threshold.json, .harness/ (schema, property and quality evaluators plus one runner),
tests/, evidence/. Harness order: structural (JSON Schema), property/invariant, semantic title
similarity, aggregate against the fixed threshold. Service errors are retried and reported
separately and excluded from the score. Include a requirements-to-cases traceability section
covering FR-001..FR-027.

## /speckit-tasks
Generate tasks.md in specs/001-reminder-agent/. Do not modify src/ or tests/. Mark each task
[TEST] or [IMPLEMENTATION]. Include: dataset and threshold files; the JSON Schema; the three
evaluator layers; the evaluation runner and static runner; the provider client with retry and
error classification; the prompt; unit tests for every evaluator layer and for the runner;
a task that preserves the first generated implementation in evidence/initial-generation/ BEFORE
the first harness run; a final evaluation run recorded under evidence/.

## /speckit-analyze
Analyze consistency across spec.md, plan.md and tasks.md. Do not modify any files.
Fix CRITICAL and HIGH findings in the artifacts (not in code) and commit with a message
that records the change.

## /speckit-implement
Implement tasks.md in order, tests before implementation. Rules: do not modify spec.md,
plan.md or tasks.md (tick tasks only); do not delete or weaken evaluation cases; do not lower
evals/threshold.json; do not disable guardrails; do not add noqa/nosec in src/; never write the
API key anywhere; do not run .harness/run_eval.py or edit anything under evidence/. You may run
pytest, ruff and bandit while working.

## Alignment checks between the reference code and YOUR spec
The reference code assumes these decisions. If your spec says otherwise, change the code, not
the spec, and note it in your log.
1. A vague part of the day ("tomorrow evening", "later") is NOT a time: intent `clarify`.
2. create/reschedule: snooze_minutes and clarification_question are null.
3. snooze: datetime and clarification_question are null.
4. clarify: datetime and snooze_minutes are null.
5. refuse: all four of title, datetime, snooze_minutes, clarification_question are null.
6. The returned datetime may use any offset (same instant is accepted); the prompt asks for the
   offset of `now`.
7. Title similarity is Jaccard word overlap with a small stopword list, pass at 0.5 or above.
