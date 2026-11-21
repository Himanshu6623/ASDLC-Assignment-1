"""Command-line interface with exit codes 0, 1, and 2."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from .service import PRIORITIES, STATUSES, Task, TodoError, TodoService
from .storage import JsonStorage

DEFAULT_FILE = "todo.json"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="todo", description="Smart Todo CLI")
    parser.add_argument(
        "--file",
        default=os.environ.get("TODO_FILE", DEFAULT_FILE),
        help="path to JSON data file (env TODO_FILE, default todo.json)",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    add_parser = subcommands.add_parser("add", help="add a task")
    add_parser.add_argument("title")
    add_parser.add_argument("--priority", default="medium", choices=PRIORITIES)
    add_parser.add_argument("--tag", action="append", dest="tags")

    list_parser = subcommands.add_parser("list", help="list tasks")
    list_parser.add_argument("--tag")
    list_parser.add_argument("--status", choices=STATUSES)
    list_parser.add_argument("--no-sort", action="store_true")

    update_parser = subcommands.add_parser("update", help="update a task")
    update_parser.add_argument("id", type=int)
    update_parser.add_argument("--title")
    update_parser.add_argument("--priority", choices=PRIORITIES)
    update_parser.add_argument("--tag", action="append", dest="tags")

    status_parser = subcommands.add_parser("status", help="change task status")
    status_parser.add_argument("id", type=int)
    status_parser.add_argument("new_status", choices=STATUSES)

    delete_parser = subcommands.add_parser("delete", help="delete a task")
    delete_parser.add_argument("id", type=int)
    return parser


def format_task(task: Task) -> str:
    tags = " ".join(f"#{tag}" for tag in task.tags)
    line = f"{task.id} [{task.status}] ({task.priority}) {task.title}"
    return f"{line} {tags}".rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "update" and all(
        value is None for value in (args.title, args.priority, args.tags)
    ):
        parser.error("update requires --title, --priority, or --tag")
    service = TodoService(JsonStorage(args.file))
    try:
        if args.command == "add":
            print(format_task(service.add(args.title, args.priority, args.tags)))
        elif args.command == "list":
            tasks = service.list(args.tag, args.status, not args.no_sort)
            for task in tasks:
                print(format_task(task))
        elif args.command == "update":
            print(format_task(service.update(args.id, args.title, args.priority, args.tags)))
        elif args.command == "status":
            print(format_task(service.set_status(args.id, args.new_status)))
        elif args.command == "delete":
            service.delete(args.id)
            print(f"deleted {args.id}")
    except TodoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
