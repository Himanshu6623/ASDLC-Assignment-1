"""Command-line interface. Exit codes: 0 success, 1 domain error, 2 usage error."""

from __future__ import annotations

import argparse
import json
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
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="add a task")
    add.add_argument("title")
    add.add_argument("--priority", default="medium", choices=PRIORITIES)
    add.add_argument("--tag", action="append", default=[], dest="tags")

    lst = sub.add_parser("list", help="list tasks")
    lst.add_argument("--tag")
    lst.add_argument("--status", choices=STATUSES)
    lst.add_argument("--no-sort", action="store_true", help="order by id")
    lst.add_argument("--json", action="store_true", dest="as_json")

    upd = sub.add_parser("update", help="update a task")
    upd.add_argument("id", type=int)
    upd.add_argument("--title")
    upd.add_argument("--priority", choices=PRIORITIES)
    upd.add_argument("--tag", action="append", dest="tags")

    stat = sub.add_parser("status", help="change task status")
    stat.add_argument("id", type=int)
    stat.add_argument("new_status", choices=STATUSES)

    dele = sub.add_parser("delete", help="delete a task")
    dele.add_argument("id", type=int)
    return parser


def format_task(task: Task) -> str:
    tags = " ".join(f"#{t}" for t in task.tags)
    line = f"{task.id} [{task.status}] ({task.priority}) {task.title}"
    return f"{line} {tags}".rstrip()


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    service = TodoService(JsonStorage(args.file))
    try:
        if args.command == "add":
            print(format_task(service.add(args.title, args.priority, args.tags)))
        elif args.command == "list":
            tasks = service.list(args.tag, args.status, not args.no_sort)
            if args.as_json:
                print(json.dumps([t.to_dict() for t in tasks], indent=2))
            else:
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
