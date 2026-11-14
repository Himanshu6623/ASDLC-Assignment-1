"""Core domain logic for Smart Todo (FR-1 .. FR-6)."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any

PRIORITIES = ("low", "medium", "high")
PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}
STATUSES = ("todo", "in_progress", "done")
TRANSITIONS = {
    "todo": {"in_progress"},
    "in_progress": {"todo", "done"},
    "done": {"todo"},
}
MAX_TITLE_LEN = 100
MAX_TAGS = 10
TAG_PATTERN = re.compile(r"^[a-z0-9_-]{1,20}$")


class TodoError(Exception):
    """Base class for all domain errors."""


class ValidationError(TodoError):
    """Input violates a validation rule."""


class NotFoundError(TodoError):
    """Task id does not exist."""


class InvalidTransitionError(TodoError):
    """Requested status transition is not allowed."""


class StorageError(TodoError):
    """Persistence file is unreadable or corrupt."""


@dataclass
class Task:
    id: int
    title: str
    priority: str = "medium"
    status: str = "todo"
    tags: list[str] = field(default_factory=list)
    created_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_title(title: Any) -> str:
    if not isinstance(title, str):
        raise ValidationError("title must be a string")
    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("title must not be empty")
    if len(cleaned) > MAX_TITLE_LEN:
        raise ValidationError(f"title must be at most {MAX_TITLE_LEN} characters")
    return cleaned


def validate_priority(priority: Any) -> str:
    if priority not in PRIORITIES:
        raise ValidationError(f"priority must be one of {', '.join(PRIORITIES)}")
    return str(priority)


def normalize_tags(tags: Any) -> list[str]:
    if tags is None:
        return []
    if not isinstance(tags, (list, tuple)):
        raise ValidationError("tags must be a list")
    result: list[str] = []
    for raw in tags:
        if not isinstance(raw, str):
            raise ValidationError("each tag must be a string")
        tag = raw.strip().lower()
        if not tag:
            continue
        if not TAG_PATTERN.match(tag):
            raise ValidationError(f"invalid tag: {raw!r}")
        if tag not in result:
            result.append(tag)
    if len(result) > MAX_TAGS:
        raise ValidationError(f"at most {MAX_TAGS} tags per task")
    return result


class TodoService:
    """Task operations backed by a storage object with load()/save()."""

    def __init__(self, storage: Any) -> None:
        self._storage = storage

    def _load(self) -> tuple[int, list[Task]]:
        data = self._storage.load()
        try:
            tasks = [Task(**item) for item in data["tasks"]]
            next_id = int(data["next_id"])
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageError(f"invalid task data: {exc}") from exc
        return next_id, tasks

    def _save(self, next_id: int, tasks: list[Task]) -> None:
        self._storage.save(
            {"version": 1, "next_id": next_id, "tasks": [t.to_dict() for t in tasks]}
        )

    @staticmethod
    def _find(tasks: list[Task], task_id: int) -> Task:
        for task in tasks:
            if task.id == task_id:
                return task
        raise NotFoundError(f"task {task_id} not found")

    def add(
        self,
        title: str,
        priority: str = "medium",
        tags: list[str] | None = None,
    ) -> Task:
        clean_title = validate_title(title)
        clean_priority = validate_priority(priority)
        clean_tags = normalize_tags(tags)
        next_id, tasks = self._load()
        task = Task(
            id=next_id,
            title=clean_title,
            priority=clean_priority,
            status="todo",
            tags=clean_tags,
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        tasks.append(task)
        self._save(next_id + 1, tasks)
        return task

    def get(self, task_id: int) -> Task:
        _, tasks = self._load()
        return self._find(tasks, task_id)

    def list(
        self,
        tag: str | None = None,
        status: str | None = None,
        sort_by_priority: bool = True,
    ) -> list[Task]:
        _, tasks = self._load()
        if tag is not None:
            wanted = normalize_tags([tag])
            if wanted:
                tasks = [t for t in tasks if wanted[0] in t.tags]
        if status is not None:
            if status not in STATUSES:
                raise ValidationError(f"status must be one of {', '.join(STATUSES)}")
            tasks = [t for t in tasks if t.status == status]
        if sort_by_priority:
            return sorted(tasks, key=lambda t: (PRIORITY_RANK[t.priority], t.id))
        return sorted(tasks, key=lambda t: t.id)

    def update(
        self,
        task_id: int,
        title: str | None = None,
        priority: str | None = None,
        tags: list[str] | None = None,
    ) -> Task:
        next_id, tasks = self._load()
        task = self._find(tasks, task_id)
        if title is not None:
            task.title = validate_title(title)
        if priority is not None:
            task.priority = validate_priority(priority)
        if tags is not None:
            task.tags = normalize_tags(tags)
        self._save(next_id, tasks)
        return task

    def set_status(self, task_id: int, new_status: str) -> Task:
        if new_status not in STATUSES:
            raise ValidationError(f"status must be one of {', '.join(STATUSES)}")
        next_id, tasks = self._load()
        task = self._find(tasks, task_id)
        if new_status not in TRANSITIONS[task.status]:
            raise InvalidTransitionError(
                f"cannot move task {task_id} from {task.status} to {new_status}"
            )
        task.status = new_status
        self._save(next_id, tasks)
        return task

    def delete(self, task_id: int) -> None:
        next_id, tasks = self._load()
        task = self._find(tasks, task_id)
        tasks.remove(task)
        self._save(next_id, tasks)
