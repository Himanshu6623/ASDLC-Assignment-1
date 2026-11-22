# Feature Specification: Smart Todo CLI and Library

**Feature Branch**: not created (work on master; feature directory specs/001-smart-todo)

**Created**: 2026-11-14

**Status**: Draft

**Input**: User description: "Create a Smart Todo CLI/library with validated task creation and updates, filtering and ordering, controlled status transitions, JSON persistence, defined CLI exit codes, and quality requirements."

## Clarifications

### Session 2026-11-21

- Q: Can a done task be reopened? → A: Yes, a task may transition only from `done` to `todo`.
- Q: Are deleted task IDs reused? → A: No; ID allocation is monotonic and deleted IDs are never reused.
- Q: Is tag filtering case-sensitive? → A: No; tag filtering is case-insensitive.
- Q: What happens when the saved data file is corrupt or wrongly structured? → A: The operation fails with a domain error and the file is never overwritten.
- Q: Should saved task records include created_at or version fields? → A: No; records contain exactly `id`, `title`, `priority`, `tags`, and `status`.
- Q: What output format should CLI commands print, and should there be a `--json` option? → A: CLI success output is human-readable text only; there is no `--json` option.
- Q: How should task IDs that are not positive integers be classified? → A: A non-integer ID is usage error 2; a zero or negative integer ID is domain error 1.
- Q: How should `list` classify an unknown status or tag filter value? → A: An unknown status is usage error 2; an unknown tag is a valid filter that returns no matches with success 0.
- Q: Should an update with no fields supplied succeed or fail? → A: It fails as usage error 2 and does not change the task.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Create and review tasks (Priority: P1)

A user creates a task with a title and optional priority and tags, then lists tasks to review their current work.

**Why this priority**: Creating and finding tasks is the minimum useful workflow.

**Independent Test**: Create tasks with and without optional values, then list them and verify their saved values and order.

**Acceptance Scenarios**:

1. **Given** an empty task list, **When** a user creates a task with title `"  Buy milk  "` and omits priority and tags, **Then** the task has title `"Buy milk"`, priority `medium`, no tags, status `todo`, and ID `1`.
2. **Given** an empty task list, **When** a user creates a task with valid title, priority `high`, and tags `["Home", "home", "urgent_1"]`, **Then** its tags are `["home", "urgent_1"]`.
3. **Given** an empty task list, **When** a user creates a task with a title that is empty after trimming, a title longer than 100 characters after trimming, an unsupported priority, an invalid tag, or more than 10 distinct tags, **Then** creation fails and no task is added.
4. **Given** tasks with different priorities and IDs, **When** a user lists without specifying an order override, **Then** tasks are ordered by priority `high`, `medium`, `low`, and then by ascending ID within each priority.
5. **Given** tasks with different priorities, **When** a user lists with `--no-sort`, **Then** tasks are ordered by ascending ID.
6. **Given** tasks with varied tags and statuses, **When** a user filters by tag, status, or both, **Then** the result contains exactly the tasks matching the requested tag case-insensitively and the requested status; when both are supplied, a task must match both.

### User Story 2 - Update and complete tasks (Priority: P1)

A user updates task details and moves tasks through valid work statuses without losing data after an invalid operation.

**Why this priority**: Users need to keep task details accurate and reflect progress safely.

**Independent Test**: Create a task, update each editable field, exercise every allowed and disallowed status transition, and compare task data before and after each failed operation.

**Acceptance Scenarios**:

1. **Given** an existing task, **When** a user updates its title, priority, and tags with valid values, **Then** the new values are saved and all other task fields remain unchanged.
2. **Given** an existing task, **When** an update contains an invalid title, priority, or tag set, **Then** the update fails and every field of that task remains unchanged.
3. **Given** a task in `todo`, **When** a user changes its status to `in_progress`, **Then** its status becomes `in_progress`.
4. **Given** a task in `in_progress`, **When** a user changes its status to `todo` or `done`, **Then** its status becomes the requested status.
5. **Given** a task in `done`, **When** a user changes its status to `todo`, **Then** its status becomes `todo`.
6. **Given** a task in `todo`, **When** a user changes its status to `done` or `todo`, **Then** the operation fails and the status remains `todo`.
7. **Given** a task in `in_progress`, **When** a user changes its status to `in_progress`, **Then** the operation fails and the status remains `in_progress`.
8. **Given** a task in `done`, **When** a user changes its status to `in_progress` or `done`, **Then** the operation fails and the status remains `done`.

### User Story 3 - Delete tasks and retain saved work (Priority: P1)

A user removes tasks they no longer need and can rely on saved tasks and ID allocation across runs.

**Why this priority**: Removal and durable, predictable task records are necessary for the task list to remain trustworthy.

**Independent Test**: Create, delete, restart, and create tasks while verifying persisted contents and ID allocation; separately attempt to load invalid saved data.

**Acceptance Scenarios**:

1. **Given** a task with ID `1`, **When** a user deletes ID `1`, **Then** that task is removed.
2. **Given** no task has ID `99`, **When** a user deletes ID `99`, **Then** deletion fails and the task list is unchanged.
3. **Given** a task has been deleted, **When** the user creates another task, **Then** the new task receives the next never-before-used ID rather than the deleted ID.
4. **Given** a valid saved task list, **When** the user starts a new process and lists tasks, **Then** the saved tasks and their values are present.
5. **Given** no saved file exists, **When** the user lists tasks, **Then** the result is an empty list.
6. **Given** a saved file contains invalid JSON or does not match the specified saved-data structure, **When** the user performs an operation, **Then** the operation reports an error and leaves the saved file byte-for-byte unchanged.
7. **Given** a saved file containing valid data, **When** a save is interrupted, **Then** the saved file remains either the previous complete data or the new complete data, never a partial document.

### User Story 4 - Receive clear command outcomes (Priority: P2)

A CLI user can distinguish successful commands, rejected task operations, and invalid command usage by exit status.

**Why this priority**: Scripts and interactive users need a deterministic way to recognize command outcomes.

**Independent Test**: Invoke successful commands, domain-invalid operations, and malformed commands separately and verify exit status and output streams.

**Acceptance Scenarios**:

1. **Given** a valid CLI command that succeeds, **When** the command finishes, **Then** it exits with code `0`.
2. **Given** a syntactically valid command that fails due to invalid task data, an unknown ID, an invalid status transition, or invalid saved data, **When** the command finishes, **Then** it exits with code `1`, writes an error message to stderr, and writes nothing to stdout.
3. **Given** a malformed command or invalid/missing command arguments, **When** the command finishes, **Then** it exits with code `2`.

### Edge Cases

- A title containing only whitespace is rejected; title length is measured after trimming, and lengths of 1 and 100 are accepted while 0 and 101 are rejected.
- A tag must, after lowercasing, contain 1-20 characters from `[a-z0-9_-]`; whitespace is not implicitly trimmed.
- Duplicate tags are removed after lowercasing; the maximum of 10 tags is measured after deduplication.
- IDs remain unique positive integers; deleting the highest-numbered task does not make its ID reusable.
- A non-integer task ID is a usage error (exit code 2); an integer ID of zero or less is a domain error (exit code 1).
- An unknown status filter is a usage error (exit code 2). A valid tag filter that matches no tasks returns an empty successful list (exit code 0).
- An update that supplies no title, priority, or tag fields is a usage error (exit code 2) and does not change the task.
- Filtering by both tag and status uses an intersection, not a union.
- A JSON document that parses but has missing, extra, or invalidly typed required fields is rejected and not overwritten.
- A failed create, update, transition, or delete leaves the in-memory task data and persisted data unchanged.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST create a task only when its title, after trimming leading and trailing whitespace, contains 1-100 characters.
- **FR-002**: The system MUST accept only the priorities `low`, `medium`, and `high`; it MUST use `medium` when priority is omitted.
- **FR-003**: The system MUST lowercase task tags, remove duplicates after lowercasing, accept only tags matching `[a-z0-9_-]{1,20}` after lowercasing, and reject more than 10 distinct tags.
- **FR-004**: The system MUST assign each created task the initial status `todo` and a unique positive integer ID, starting at 1 and increasing for each successful creation. An ID MUST NOT be reused after deletion.
- **FR-005**: The system MUST list tasks filtered by tag, status, or both. Tag matching MUST be case-insensitive, and supplying both filters MUST return only tasks matching both.
- **FR-006**: The system MUST order lists by priority (`high`, `medium`, `low`) and then ascending ID by default. With `--no-sort`, it MUST order tasks by ascending ID.
- **FR-007**: The system MUST allow updates to title, priority, and tags using the same validation rules as creation. If any part of an update is invalid, no task field may change.
- **FR-008**: The system MUST delete a task by ID. Deleting an unknown ID MUST fail without changing task data.
- **FR-009**: The system MUST permit only these status transitions: `todo` to `in_progress`, `in_progress` to `todo`, `in_progress` to `done`, and `done` to `todo`. Every other transition, including a transition to the current status, MUST fail without changing task data.
- **FR-010**: The system MUST persist tasks in a JSON file using atomic writes. A missing file MUST be treated as an empty task list.
- **FR-011**: The saved JSON document MUST be an object with exactly `next_id` and `tasks` fields. `next_id` MUST be a positive integer greater than every saved task ID; `tasks` MUST be an array of task objects with exactly `id`, `title`, `priority`, `tags`, and `status` fields. IDs MUST be unique positive integers. Saved titles MUST already be trimmed and 1-100 characters; priorities MUST be `low`, `medium`, or `high`; tags MUST be normalized, unique, and satisfy FR-003; statuses MUST be `todo`, `in_progress`, or `done`. Invalid JSON or any other structure MUST produce an error and MUST NOT be overwritten.
- **FR-012**: The CLI MUST exit with code `0` on success, code `1` on a domain error, and code `2` on a usage error. On a domain error, it MUST write an error message to stderr and no output to stdout.
- **FR-013**: The CLI and library MUST perform all specified task operations without network access.
- **FR-014**: CLI success output MUST use human-readable text. The CLI MUST NOT provide a `--json` output option.

### Non-Functional Requirements

- **NFR-001**: `ruff` MUST report zero findings for the project, and every public function MUST have explicit type hints.
- **NFR-002**: `bandit` MUST report zero findings for the project.
- **NFR-003**: The project MUST maintain at least 90% line coverage and at least 90% branch coverage.
- **NFR-004**: The CLI and library MUST make no network requests.

### Key Entities

- **Task**: A user-managed item containing an integer ID, trimmed title, priority, normalized unique tags, and current status.
- **Task collection**: The saved set of tasks and the next ID to allocate; it is empty when no saved file exists.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of the acceptance scenarios in this specification pass, including the boundary cases for title length, tag format and count, ID allocation, filtering, and status transitions.
- **SC-002**: After every rejected operation, the complete task collection is identical to its state immediately before the operation.
- **SC-003**: After a successful save and restart, 100% of task fields and the next ID match their values before restart.
- **SC-004**: A CLI caller can distinguish success, domain failure, and usage failure solely from exit codes `0`, `1`, and `2`; every domain failure has empty stdout and a non-empty stderr message.
- **SC-005**: The project's test report shows at least 90% line coverage and at least 90% branch coverage.
- **SC-006**: `ruff` reports zero findings and `bandit` reports zero findings for the project.
- **SC-007**: No network request is made while executing or testing any specified task operation.
- **SC-008**: A user can complete the create, list, update, status-change, and delete journeys without manually editing the saved task data.

## Assumptions

- The feature supports both a callable library and a command-line interface, and both apply the same task validation and state rules.
- Priority and status values are accepted only in the exact lowercase forms listed; only tags are explicitly lowercased.
- The maximum tag count applies to distinct tags after case normalization and deduplication.
- The JSON shape in FR-011 is the canonical on-disk format. No migration from another format is required.
- A missing saved file is read as an empty collection; the file need not be created until a successful operation requires persistence.
- Malformed commands, unknown commands, and invalid or missing command arguments are usage errors; valid commands rejected by task rules or saved data are domain errors.
- Performance targets and concurrent access behavior are outside this feature's specified scope.
