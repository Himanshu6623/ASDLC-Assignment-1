# CLI Contract

## Invocation

```text
todo [--file PATH] COMMAND [arguments]
```

`--file` defaults to `todo.json`. `TODO_FILE` may provide the default path. All commands apply the same library validation and persistence rules.

## Commands

### `add`

```text
todo [--file PATH] add TITLE [--priority low|medium|high] [--tag TAG]...
```

Success prints one human-readable task line. Default priority is `medium`.

### `list`

```text
todo [--file PATH] list [--tag TAG] [--status todo|in_progress|done] [--no-sort]
```

Success prints zero or more human-readable task lines. Default order is priority `high`, `medium`, `low`, then ascending ID. `--no-sort` uses ascending ID. Tag matching is case-insensitive; status and tag filters intersect. No `--json` option exists.

### `update`

```text
todo [--file PATH] update ID [--title TITLE] [--priority low|medium|high] [--tag TAG]...
```

At least one update field is required. Success prints the updated human-readable task line. Non-integer IDs are usage errors; integer IDs less than one are domain errors.

### `status`

```text
todo [--file PATH] status ID todo|in_progress|done
```

Success prints the updated human-readable task line.

### `delete`

```text
todo [--file PATH] delete ID
```

Success prints `deleted ID` as human-readable text.

## Exit codes and streams

- `0`: command completed successfully.
- `1`: domain failure (invalid task data, unknown ID, invalid transition, invalid persisted data, or persistence failure).
- `2`: usage failure (malformed command, unknown command, missing/invalid arguments, unknown status filter, or update with no fields).

Domain failures write a non-empty error message to stderr and write nothing to stdout. Usage failures are handled by the argument parser and retain argparse's usage/error convention. Successful commands do not write error text to stderr.
