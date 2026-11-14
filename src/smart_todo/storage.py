"""JSON file persistence with atomic writes (FR-6)."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any

from .service import StorageError


class JsonStorage:
    def __init__(self, path: str | os.PathLike[str]) -> None:
        self.path = Path(path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"version": 1, "next_id": 1, "tasks": []}
        try:
            with self.path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"cannot read {self.path}: {exc}") from exc
        if not isinstance(data, dict) or "tasks" not in data or "next_id" not in data:
            raise StorageError(f"unexpected structure in {self.path}")
        return data

    def save(self, data: dict[str, Any]) -> None:
        directory = self.path.parent
        directory.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(data, handle, indent=2)
            os.replace(tmp_name, self.path)
        except OSError as exc:
            if os.path.exists(tmp_name):
                os.unlink(tmp_name)
            raise StorageError(f"cannot write {self.path}: {exc}") from exc
