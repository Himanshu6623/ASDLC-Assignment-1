"""Strict atomic JSON persistence."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .service import (
    MAX_TAGS,
    MAX_TITLE_LEN,
    PRIORITIES,
    STATUSES,
    TAG_PATTERN,
    StorageError,
)


class JsonStorage:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"next_id": 1, "tasks": []}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"cannot read {self.path}: {exc}") from exc
        self._validate_document(data)
        return data

    @staticmethod
    def _is_int(value: Any) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    def _validate_document(self, data: Any) -> None:
        if not isinstance(data, dict) or set(data) != {"next_id", "tasks"}:
            raise StorageError(f"unexpected structure in {self.path}")
        next_id = data["next_id"]
        tasks = data["tasks"]
        if not self._is_int(next_id) or next_id <= 0:
            raise StorageError("next_id must be a positive integer")
        if not isinstance(tasks, list):
            raise StorageError("tasks must be an array")
        ids: set[int] = set()
        for task in tasks:
            self._validate_task(task)
            task_id = task["id"]
            if task_id in ids:
                raise StorageError("task ids must be unique")
            ids.add(task_id)
        if ids and next_id <= max(ids):
            raise StorageError("next_id must be greater than every task id")

    def _validate_task(self, task: Any) -> None:
        if not isinstance(task, dict) or set(task) != {
            "id",
            "title",
            "priority",
            "tags",
            "status",
        }:
            raise StorageError(f"unexpected task structure in {self.path}")
        task_id = task["id"]
        if not self._is_int(task_id) or task_id <= 0:
            raise StorageError("task id must be a positive integer")
        title = task["title"]
        if (
            not isinstance(title, str)
            or title.strip() != title
            or not 1 <= len(title) <= MAX_TITLE_LEN
        ):
            raise StorageError("invalid saved title")
        if task["priority"] not in PRIORITIES:
            raise StorageError("invalid saved priority")
        if task["status"] not in STATUSES:
            raise StorageError("invalid saved status")
        tags = task["tags"]
        if not isinstance(tags, list) or len(tags) > MAX_TAGS:
            raise StorageError("invalid saved tags")
        seen: set[str] = set()
        for tag in tags:
            if (
                not isinstance(tag, str)
                or tag != tag.lower()
                or not TAG_PATTERN.fullmatch(tag)
                or tag in seen
            ):
                raise StorageError("invalid saved tags")
            seen.add(tag)

    def save(self, data: dict[str, Any]) -> None:
        directory = self.path.parent
        directory.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        except OSError as exc:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise StorageError(f"cannot write {self.path}: {exc}") from exc
