# Smart Todo Constitution

## Core Principles

### I. Code Quality
All Smart Todo code must be high quality and maintainable. `ruff check` must report zero findings for the project, and every public function must include explicit type hints. Code must be clear, consistent, and readable, with no avoidable complexity or dead code.

### II. Security
Smart Todo must be secure by default. `bandit` must report zero findings. No secrets, credentials, or sensitive values may be committed to the repository. The code must not invoke shell commands or use `eval`/`exec`-style execution patterns that create command injection or unsafe behavior.

### III. Testing (NON-NEGOTIABLE)
Testing is mandatory and cannot be relaxed. Every requirement must have at least one binary test that validates the behavior as pass/fail. Line and branch coverage must be at least 90% for the project. Any requirement without a corresponding binary test is incomplete, and any test failure must be resolved before completion.

### IV. Determinism
Smart Todo must be deterministic. The implementation must not access the network, use randomness, or depend on ambient external state. Behavior must depend only on the provided inputs and the persisted data file.

### V. Agent Guardrails
The coding agent must not weaken acceptance criteria, delete or skip failing tests, add lint or bandit ignores, lower the coverage threshold, or expose secrets. Specification changes must go through the Spec Kit artifacts with a clear change history and must not bypass the recorded requirements.
The agent MUST NOT edit recorded harness results to obtain a PASS.

## Quality Gates
All changes must pass the project quality gates before merge or completion:
- `ruff check` returns zero findings.
- `bandit` returns zero findings.
- All required tests pass.
- Every requirement has at least one binary test.
- Project coverage remains at or above 90% line and branch coverage.
- No network access or randomness is introduced.
- Public APIs remain consistent with the approved specification.

## Development Workflow
The workflow for Smart Todo must preserve traceability and correctness:
1. Capture or update requirements in the Spec Kit artifacts before implementation changes.
2. Validate behavior with tests that capture the required acceptance criteria.
3. Implement the smallest deterministic change that satisfies the requirement.
4. Run the project quality gates (`ruff`, `bandit`, and relevant tests) before considering the work complete.
5. If a failing test or quality gate exists, fix it before proceeding; do not ignore or remove it.
6. Record any specification or requirement changes through the approved Spec Kit process with change history.
7. Preserve the first generated implementation (evidence/initial-generation/) before any harness-driven repair.

## Governance
This Constitution governs all work on Smart Todo. It supersedes informal shortcuts, local exceptions, and ad hoc rule weakening. Any exception to these requirements must be documented as a formal specification change with corresponding artifact updates and review history. Compliance is required for implementation, testing, and review.

**Version**: 1.0.0 | **Ratified**: 2026-11-14 | **Last Amended**: 2026-11-14
