"""FR-001 through FR-011 service and persistence traceability tests."""

import json

import pytest

from smart_todo.service import (
    InvalidTransitionError,
    NotFoundError,
    StorageError,
    TodoService,
    ValidationError,
)
from smart_todo.storage import JsonStorage


# FR-001/FR-002: title and priority creation validation.
@pytest.mark.parametrize(
    "title,expected",
    [("  Buy milk  ", "Buy milk"), ("x", "x"), ("x" * 100, "x" * 100)],
)
def test_fr001_fr002_title_boundaries_and_trim(service, title, expected):
    assert service.add(title).title == expected


@pytest.mark.parametrize("title", ["", "   ", "x" * 101, None, 123])
def test_fr001_invalid_titles(service, title):
    with pytest.raises(ValidationError):
        service.add(title)


def test_fr002_priority_default_and_choices(service):
    assert service.add("default").priority == "medium"
    for priority in ("low", "medium", "high"):
        assert service.add(priority, priority=priority).priority == priority


@pytest.mark.parametrize("priority", ["urgent", "", "HIGH", None, 1])
def test_fr002_invalid_priority(service, priority):
    with pytest.raises(ValidationError):
        service.add("task", priority=priority)


# FR-003: normalization and tag boundaries.
def test_fr003_tags_lowercase_deduplicate_and_whitespace_is_invalid(service):
    assert service.add("task", tags=["Home", "home", "urgent_1"]).tags == ["home", "urgent_1"]
    with pytest.raises(ValidationError):
        service.add("task", tags=["has space"])
    with pytest.raises(ValidationError):
        service.add("task", tags=[" good "])


@pytest.mark.parametrize("tag", ["", "bad!", "a" * 21, "has space", 1])
def test_fr003_invalid_tag(service, tag):
    with pytest.raises(ValidationError):
        service.add("task", tags=[tag])


def test_fr003_tag_count_boundary(service):
    assert len(service.add("ten", tags=[f"tag{i}" for i in range(10)]).tags) == 10
    with pytest.raises(ValidationError):
        service.add("eleven", tags=[f"tag{i}" for i in range(11)])


# FR-004/FR-008: monotonic IDs and deletion.
def test_fr004_initial_monotonic_ids_and_no_reuse(service):
    first = service.add("first")
    second = service.add("second")
    service.delete(second.id)
    third = service.add("third")
    assert [first.id, third.id] == [1, 3]


def test_fr008_delete_unknown_is_atomic(service):
    before = service.list()
    with pytest.raises(NotFoundError):
        service.delete(99)
    assert service.list() == before


# FR-005/FR-006: filtering and ordering.
def test_fr005_tag_status_and_intersection_filters(service):
    service.add("a", tags=["X"], priority="high")
    service.add("b", tags=["x", "y"])
    service.set_status(1, "in_progress")
    assert [t.id for t in service.list(tag="x", status="in_progress")] == [1]
    assert [t.id for t in service.list(tag="unknown")] == []
    assert [t.id for t in service.list(status="todo")] == [2]


def test_fr005_invalid_status_filter(service):
    with pytest.raises(ValidationError):
        service.list(status="unknown")


def test_fr006_priority_and_id_sorting(service):
    service.add("low", priority="low")
    service.add("high-1", priority="high")
    service.add("medium", priority="medium")
    service.add("high-2", priority="high")
    assert [t.id for t in service.list()] == [2, 4, 3, 1]
    assert [t.id for t in service.list(sort_by_priority=False)] == [1, 2, 3, 4]


# FR-007: atomic updates.
def test_fr007_update_fields_use_creation_validation(service):
    task = service.add("old", priority="low", tags=["old"])
    updated = service.update(task.id, title="  new  ", priority="high", tags=["NEW", "tag_1"])
    assert (updated.title, updated.priority, updated.tags) == ("new", "high", ["new", "tag_1"])


@pytest.mark.parametrize(
    "updates",
    [
        {"title": ""},
        {"title": "x" * 101},
        {"priority": "urgent"},
        {"tags": ["bad tag"]},
        {"tags": ["bad!"]},
        {"tags": [f"tag{i}" for i in range(11)]},
    ],
)
def test_fr007_invalid_update_changes_nothing(service, updates):
    original = service.add("keep", priority="medium", tags=["keep"])
    before = service.get(original.id)
    with pytest.raises(ValidationError):
        service.update(original.id, **updates)
    after = service.get(original.id)
    assert (after.title, after.priority, after.tags, after.status) == (
        before.title,
        before.priority,
        before.tags,
        before.status,
    )


def test_fr007_update_missing_id(service):
    with pytest.raises(NotFoundError):
        service.update(99, title="x")


# FR-009: exact transition graph and unchanged state.
@pytest.mark.parametrize(
    ("source", "destination"),
    [
        ("todo", "in_progress"),
        ("in_progress", "todo"),
        ("in_progress", "done"),
        ("done", "todo"),
    ],
)
def test_fr009_allowed_transitions(service, source, destination):
    task = service.add("task")
    if source == "in_progress":
        service.set_status(task.id, "in_progress")
    elif source == "done":
        service.set_status(task.id, "in_progress")
        service.set_status(task.id, "done")
    assert service.set_status(task.id, destination).status == destination


@pytest.mark.parametrize(
    ("source", "destination"),
    [
        ("todo", "todo"),
        ("todo", "done"),
        ("in_progress", "in_progress"),
        ("done", "done"),
        ("done", "in_progress"),
    ],
)
def test_fr009_forbidden_transitions_leave_state_unchanged(service, source, destination):
    task = service.add("task")
    if source == "in_progress":
        service.set_status(task.id, "in_progress")
    elif source == "done":
        service.set_status(task.id, "in_progress")
        service.set_status(task.id, "done")
    with pytest.raises(InvalidTransitionError):
        service.set_status(task.id, destination)
    assert service.get(task.id).status == source


def test_fr009_invalid_status_and_missing_task(service):
    task = service.add("task")
    with pytest.raises(ValidationError):
        service.set_status(task.id, "cancelled")
    with pytest.raises(NotFoundError):
        service.set_status(99, "done")


# FR-010/FR-011: persistence and strict saved JSON.
def test_fr010_missing_file_is_empty_and_restart_preserves_state(service, data_file):
    assert service.list() == []
    task = service.add("persist", priority="high", tags=["X"])
    reloaded = TodoService(JsonStorage(data_file))
    assert reloaded.get(task.id).title == "persist"
    reloaded.delete(task.id)
    assert TodoService(JsonStorage(data_file)).add("after").id == 2


@pytest.mark.parametrize(
    "document",
    [
        [],
        {},
        {"tasks": []},
        {"next_id": 1},
        {"next_id": 1, "tasks": [], "extra": True},
    ],
)
def test_fr011_rejects_wrong_top_level_shape(data_file, document):
    data_file.write_text(json.dumps(document), encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()
    assert json.loads(data_file.read_text(encoding="utf-8")) == document


@pytest.mark.parametrize(
    "task",
    [
        {"id": 1, "title": "x", "priority": "low", "tags": [], "status": "todo", "extra": 1},
        {"id": 1, "title": "x", "priority": "low", "tags": []},
    ],
)
def test_fr011_rejects_wrong_task_fields(data_file, task):
    original = json.dumps({"next_id": 2, "tasks": [task]})
    data_file.write_text(original, encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()
    assert data_file.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("next_id", [0, -1, 1.5, True, "2", None])
def test_fr011_rejects_invalid_next_id(data_file, next_id):
    original = json.dumps({"next_id": next_id, "tasks": []})
    data_file.write_text(original, encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()


def test_fr011_rejects_duplicate_ids_zero_negative_float_and_next_id_too_low(data_file):
    documents = [
        {"next_id": 3, "tasks": [
            {"id": 1, "title": "a", "priority": "low", "tags": [], "status": "todo"},
            {"id": 1, "title": "b", "priority": "low", "tags": [], "status": "todo"},
        ]},
        {"next_id": 2, "tasks": [
            {"id": 0, "title": "a", "priority": "low", "tags": [], "status": "todo"},
        ]},
        {"next_id": 2, "tasks": [
            {"id": -1, "title": "a", "priority": "low", "tags": [], "status": "todo"},
        ]},
        {"next_id": 2, "tasks": [
            {"id": 1.0, "title": "a", "priority": "low", "tags": [], "status": "todo"},
        ]},
        {"next_id": 2, "tasks": [
            {"id": 2, "title": "a", "priority": "low", "tags": [], "status": "todo"},
        ]},
    ]
    for document in documents:
        original = json.dumps(document)
        data_file.write_text(original, encoding="utf-8")
        with pytest.raises(StorageError):
            TodoService(JsonStorage(data_file)).list()
        assert data_file.read_text(encoding="utf-8") == original


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", "  untrimmed "),
        ("title", ""),
        ("title", "x" * 101),
        ("priority", "urgent"),
        ("tags", ["Bad"]),
        ("tags", ["bad", "bad"]),
        ("tags", ["bad tag"]),
        ("status", "cancelled"),
    ],
)
def test_fr011_rejects_invalid_saved_task_values(data_file, field, value):
    task = {"id": 1, "title": "valid", "priority": "low", "tags": [], "status": "todo"}
    task[field] = value
    original = json.dumps({"next_id": 2, "tasks": [task]})
    data_file.write_text(original, encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()
    assert data_file.read_text(encoding="utf-8") == original


@pytest.mark.parametrize("content", ["{not json", '{"next_id": 2, "tasks": [}'])
def test_fr011_invalid_json_is_not_overwritten(data_file, content):
    data_file.write_text(content, encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).add("would fail")
    assert data_file.read_text(encoding="utf-8") == content


def test_fr010_atomic_save_and_no_partial_files(service, data_file):
    service.add("one")
    service.add("two")
    assert data_file.exists()
    assert [p.name for p in data_file.parent.iterdir()] == ["todo.json"]
    payload = json.loads(data_file.read_text(encoding="utf-8"))
    assert payload["next_id"] == 3


def test_fr010_save_failure_raises_storage_error(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("file, not dir", encoding="utf-8")
    with pytest.raises((StorageError, OSError)):
        TodoService(JsonStorage(blocker / "todo.json")).add("x")


# FR-013/NFR-004: deterministic operations make no network calls.
def test_fr013_network_independent(monkeypatch, service):
    def forbidden(*args, **kwargs):
        raise AssertionError("network access attempted")

    monkeypatch.setattr("socket.create_connection", forbidden)
    monkeypatch.setattr("urllib.request.urlopen", forbidden)
    service.add("local")
