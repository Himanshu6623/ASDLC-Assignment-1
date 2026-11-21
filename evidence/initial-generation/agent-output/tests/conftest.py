import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from smart_todo.service import TodoService
from smart_todo.storage import JsonStorage


@pytest.fixture
def data_file(tmp_path):
    return tmp_path / "todo.json"


@pytest.fixture
def service(data_file):
    return TodoService(JsonStorage(data_file))
