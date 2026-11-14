# Prompts to feed Spec Kit (Part 1A: Smart Todo)

Run these in order inside your Spec Kit project (`specify init`, then your coding agent).
Keep every generated artifact (`.specify/`, `specs/001-*/`) in this folder. Review and edit the
output yourself; the requirement IDs below (FR-1..FR-7, NFR-1..NFR-4) are what the tests cite.

## /speckit.constitution
Create principles for a small deterministic Python CLI/library called Smart Todo:
1. Code quality: `ruff check` must report zero findings; type hints on all public functions.
2. Security: `bandit` must report zero findings; no secrets in the repo; no shell/eval usage.
3. Testing: every requirement has at least one binary test; line+branch coverage >= 90%.
4. Determinism: no network, no randomness; behaviour depends only on inputs and the data file.
5. Agent guardrails: the coding agent must not weaken acceptance criteria, delete or skip
   failing tests, add lint/bandit ignores, lower the coverage threshold, or expose secrets.
   Specification changes go through the Spec Kit artifacts with change history.

## /speckit.specify
Build a Smart Todo CLI and library with these requirements:
- FR-1 Create: title (trimmed, 1-100 chars), priority low|medium|high (default medium), tags
  (lowercased, deduplicated, pattern [a-z0-9_-]{1,20}, max 10), initial status todo, integer ids
  starting at 1, incrementing, never reused after delete.
- FR-2 List: filter by tag (case-insensitive) and/or status; default order is priority
  (high, medium, low) then id; `--no-sort` orders by id.
- FR-3 Update title/priority/tags with the same validation; a failed update changes nothing.
- FR-4 Delete by id; unknown id is an error.
- FR-5 Status transitions allowed: todo->in_progress, in_progress->todo, in_progress->done,
  done->todo. Everything else (including same-state) is an error that leaves data unchanged.
- FR-6 Persistence: JSON file, atomic write, missing file means empty list, corrupt or
  wrongly-structured file is an error and is never overwritten.
- FR-7 CLI: exit 0 success, 1 domain error (message on stderr, nothing on stdout), 2 usage error.
- NFR-1 ruff clean. NFR-2 bandit clean. NFR-3 coverage >= 90%. NFR-4 no network access.
Acceptance criteria must be binary, e.g. "adding a 101-character title fails with a
validation error"; "moving a todo task directly to done fails and the task stays todo".

## /speckit.clarify
Let it ask its questions; answer them. Questions worth settling explicitly: can a done task be
reopened (yes, to todo), are ids reused (no), is tag filtering case-sensitive (no), what happens
on a corrupt data file (error, never overwrite).

## /speckit.plan
Python 3.10+, standard library only for runtime (argparse, json, dataclasses); pytest,
pytest-cov, ruff, bandit for the harness. Layout: src/smart_todo/{service,storage,cli}.py,
tests/, .harness/run_harness.py.

## /speckit.tasks  then  /speckit.analyze  then  /speckit.implement
Generate tasks, run analyze for consistency, then implement. BEFORE fixing anything, copy the
first generated implementation into evidence/initial-generation/.
