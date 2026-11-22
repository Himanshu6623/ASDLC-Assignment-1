# Data Model

## Task

| Field | Type | Rules |
|---|---|---|
| `id` | positive integer | Unique; allocated from `next_id`; never reused after deletion |
| `title` | string | Trim leading/trailing whitespace; 1-100 characters after trimming |
| `priority` | string | Exactly `low`, `medium`, or `high` |
| `tags` | list of strings | Lowercase; unique; each matches `[a-z0-9_-]{1,20}`; at most 10 |
| `status` | string | Exactly `todo`, `in_progress`, or `done` |

## TaskCollection

| Field | Type | Rules |
|---|---|---|
| `next_id` | positive integer | Greater than every saved task ID |
| `tasks` | list of Task | No duplicate IDs and no extra record fields |

The collection is empty with `next_id = 1` when the file is missing.

## Persisted JSON shape

```json
{
  "next_id": 3,
  "tasks": [
    {
      "id": 1,
      "title": "Buy milk",
      "priority": "medium",
      "tags": ["home"],
      "status": "todo"
    }
  ]
}
```

The top-level object and each task object must contain exactly the fields shown. No version, timestamp, or additional fields are permitted.

## Validation rules

- Task creation trims title text and rejects empty or 101-character titles.
- Priority defaults to `medium` for omitted creation input.
- Tags are lowercased before regex validation. Duplicate tags are removed. Tag whitespace is not trimmed or implicitly normalized; tags containing whitespace are invalid.
- `next_id` must be greater than all task IDs. Deleting tasks does not decrease it.
- All loaded values must already satisfy service validation; loading is not a migration or repair step.

## Status transitions

| From | Allowed to |
|---|---|
| `todo` | `in_progress` |
| `in_progress` | `todo`, `done` |
| `done` | `todo` |

A transition to the current status is always invalid.

## Failure and mutation behavior

- `ValidationError`, `NotFoundError`, `InvalidTransitionError`, and `StorageError` are domain errors.
- Validation for one operation is completed before mutation or persistence.
- A failed create, update, status change, or delete leaves the collection unchanged.
- A corrupt or wrongly structured file is not overwritten by load or failed operation.
