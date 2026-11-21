"""Core domain logic for Smart Todo."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
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
TASK_FIELDS = {"id", "title", "priority", "tags", "status"}


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
    tags: list[str] = field(default_factory=list)
    status: str = "todo"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_title(title: Any) -> str:
    if not isinstance(title, str):
        raise ValidationError("title must be a string")
    cleaned = title.strip()
    if not cleaned:
        raise ValidationError("title must not be empty")
    if len(cleaned) > MAX_TITLE_LEN:
        raise ValidationError("title must be at most 100 characters")
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
        tag = raw.lower()
        if not TAG_PATTERN.fullmatch(tag):
            raise ValidationError(f"invalid tag: {raw!r}")
        if tag not in result:
            result.append(tag)
    if len(result) > MAX_TAGS:
        raise ValidationError("at most 10 tags per task")
    return result


def validate_status(status: Any) -> str:
    if status not in STATUSES:
        raise ValidationError(f"status must be one of {', '.join(STATUSES)}")
    return str(status)


class TodoService:
    """Task operations backed by a storage object."""

    def __init__(self, storage: Any) -> None:
        self._storage = storage

    def _load(self) -> tuple[int, list[Task]]:
        data = self._storage.load()
        try:
            next_id = data["next_id"]
            tasks = [Task(**item) for item in data["tasks"]]
            if not isinstance(next_id, int) or isinstance(next_id, bool) or next_id <= 0:
                raise StorageError("invalid next_id")
            if any(
                not isinstance(task.id, int)
                or isinstance(task.id, bool)
                or task.id <= 0
                for task in tasks
            ):
                raise StorageError("invalid task id")
        except (KeyError, TypeError, ValueError) as exc:
            raise StorageError(f"invalid task data: {exc}") from exc
        return next_id, tasks

    def _save(self, next_id: int, tasks: list[Task]) -> None:
        self._storage.save(
            {"next_id": next_id, "tasks": [task.to_dict() for task in tasks]}
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
        tags: list[str] | tuple[str, ...] | None = None,
    ) -> Task:
        clean_title = validate_title(title)
        clean_priority = validate_priority(priority)
        clean_tags = normalize_tags(tags)
        next_id, tasks = self._load()
        task = Task(
            id=next_id,
            title=clean_title,
            priority=clean_priority,
            tags=clean_tags,
            status="todo",
        )
        tasks.append(task)
        self._save(next_id + 1, tasks)
        return task

    def get(self, task_id: int) -> Task:
        if not isinstance(task_id, int) or isinstance(task_id, bool) or task_id <= 0:
            raise NotFoundError(f"task {task_id} not found")
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
            tasks = [task for task in tasks if wanted and wanted[0] in task.tags]
        if status is not None:
            clean_status = validate_status(status)
            tasks = [task for task in tasks if task.status == clean_status]
        if sort_by_priority:
            return sorted(tasks, key=lambda task: (PRIORITY_RANK[task.priority], task.id))
        return sorted(tasks, key=lambda task: task.id)

    def update(
        self,
        task_id: int,
        title: str | None = None,
        priority: str | None = None,
        tags: list[str] | tuple[str, ...] | None = None,
    ) -> Task:
        clean_title = validate_title(title) if title is not None else None
        clean_priority = validate_priority(priority) if priority is not None else None
        clean_tags = normalize_tags(tags) if tags is not None else None
        next_id, tasks = self._load()
        task = self._find(tasks, task_id)
        if clean_title is not None:
            task.title = clean_title
        if clean_priority is not None:
            task.priority = clean_priority
        if clean_tags is not None:
            task.tags = clean_tags
        self._save(next_id, tasks)
        return task

    def set_status(self, task_id: int, new_status: str) -> Task:
        clean_status = validate_status(new_status)
        next_id, tasks = self._load()
        task = self._find(tasks, task_id)
        if clean_status not in TRANSITIONS[task.status]:
            raise InvalidTransitionError(
                f"cannot move task {task_id} from {task.status} to {clean_status}"
            )
        task.status = clean_status
        self._save(next_id, tasks)
        return task

    def delete(self, task_id: int) -> None:
        if not isinstance(task_id, int) or isinstance(task_id, bool) or task_id <= 0:
            raise NotFoundError(f"task {task_id} not found")
        next_id, tasks = self._load()
        task = self._find(tasks, task_id)
        tasks.remove(task)
        self._save(next_id, tasks)
