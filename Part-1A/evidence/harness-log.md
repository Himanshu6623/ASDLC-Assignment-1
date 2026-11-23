# Harness log: Part 1A (Smart Todo)

## 1. Generation and context
The code in the top-level `evidence/initial-generation/` is Claude's baseline from
chat, dated 2026-11-14. It is not Copilot's implementation. Copilot's
`/speckit-implement` output is in `evidence/initial-generation/agent-output/` and
dates from 2026-11-21; the exact Copilot model is not recorded in the available
evidence.

The project used the constitution and Speckit files in `specs/001-smart-todo/`.
The specification and task list were edited during clarification and analysis. The
test suite also grew from 65 tests in the initial and post-agent-check runs to 92
tests in the after-implement run. T036, which would have captured the first
Copilot-generated snapshot, remains unticked in `specs/001-smart-todo/tasks.md`:
Copilot skipped it, so I preserved `agent-output` by hand.

## 2. Harness executions
All five recorded harness runs passed every gate (Ruff, Bandit, and pytest):

| Timestamp (UTC) | Label | Tests | Coverage | Result |
| --- | --- | ---: | ---: | --- |
| 2026-11-14 03:34:41 | `initial` | 65 | 95.64% | PASS |
| 2026-11-14 05:01:31 | `post-agent-check` | 65 | 95.64% | PASS |
| 2026-11-21 03:59:19 | `after-implement` | 92 | 92.84% | PASS |
| 2026-11-21 04:06:20 | `final` | 92 | 92.84% | PASS |
| 2026-11-22 02:46:55 | `final` | 92 | 92.84% | PASS |

No harness gate failed in these five runs.

## 3. Retrospective comparison (not a repair)
The separate retrospective comparison of the baseline against the complete test
suite reported `20 failed, 72 passed`; its output is in
`evidence/harness-results/retrospective-baseline-vs-final-tests.txt`. This was not a
harness-gate failure and was not followed by a code repair. Copilot's
`agent-output` is identical to `final-generation`, so no implementation changes
were made after `/speckit-implement`. The tests, specification, and task list were
not left unchanged: the tests grew from 65 to 92, and the specification and tasks
were edited during clarification and analysis.

## 4. Final human decision and limitations
**ACCEPT.** The latest run passed Ruff, Bandit, and all 92 pytest tests with 92.84%
coverage, exceeding the 90% requirement. The final generated files are saved in
`evidence/final-generation/`.

The result is limited to the specified local JSON CLI/library: the specification
does not set performance or concurrent-writer guarantees and does not require
migration from older saved-data formats. Coverage is not 100%; the latest report
shows unexecuted entry-point code in `__main__.py` and remaining uncovered lines or
branches in the CLI, service, and storage modules. Bandit passes, though its output
includes warnings about words in comments being interpreted as test names.
