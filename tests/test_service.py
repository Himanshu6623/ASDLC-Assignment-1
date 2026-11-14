"""Spec-derived tests for the service layer. Each test cites its requirement ID."""

import pytest

from smart_todo.service import (
    InvalidTransitionError,
    NotFoundError,
    StorageError,
    TodoService,
    ValidationError,
)
from smart_todo.storage import JsonStorage


# ---- FR-1 Create ----------------------------------------------------------
def test_fr1_add_defaults(service):
    task = service.add("Write report")
    assert task.id == 1
    assert task.status == "todo"
    assert task.priority == "medium"
    assert task.tags == []
    assert task.created_at


def test_fr1_ids_increment(service):
    assert [service.add(f"t{i}").id for i in range(3)] == [1, 2, 3]


def test_fr1_ids_not_reused_after_delete(service):
    service.add("a")
    service.add("b")
    service.delete(2)
    assert service.add("c").id == 3


def test_fr1_title_is_trimmed(service):
    assert service.add("  hello  ").title == "hello"


@pytest.mark.parametrize("bad", ["", "   ", None, 123])
def test_fr1_invalid_title_rejected(service, bad):
    with pytest.raises(ValidationError):
        service.add(bad)


def test_fr1_title_length_boundary(service):
    assert service.add("x" * 100).title == "x" * 100
    with pytest.raises(ValidationError):
        service.add("x" * 101)


@pytest.mark.parametrize("p", ["low", "medium", "high"])
def test_fr1_valid_priorities(service, p):
    assert service.add("t", priority=p).priority == p


@pytest.mark.parametrize("p", ["urgent", "", "HIGH", None])
def test_fr1_invalid_priority_rejected(service, p):
    with pytest.raises(ValidationError):
        service.add("t", priority=p)


def test_fr1_tags_normalized_and_deduped(service):
    task = service.add("t", tags=[" Work ", "work", "HOME", ""])
    assert task.tags == ["work", "home"]


@pytest.mark.parametrize("bad", [["has space"], ["a" * 21], ["bad!"], "work", [1]])
def test_fr1_invalid_tags_rejected(service, bad):
    with pytest.raises(ValidationError):
        service.add("t", tags=bad)


def test_fr1_tag_count_boundary(service):
    assert len(service.add("t", tags=[f"t{i}" for i in range(10)]).tags) == 10
    with pytest.raises(ValidationError):
        service.add("t", tags=[f"t{i}" for i in range(11)])


# ---- FR-2 List / filter / sort -------------------------------------------
def test_fr2_sort_by_priority_then_id(service):
    service.add("low1", priority="low")
    service.add("high1", priority="high")
    service.add("med1", priority="medium")
    service.add("high2", priority="high")
    assert [t.title for t in service.list()] == ["high1", "high2", "med1", "low1"]


def test_fr2_no_sort_orders_by_id(service):
    service.add("low1", priority="low")
    service.add("high1", priority="high")
    assert [t.id for t in service.list(sort_by_priority=False)] == [1, 2]


def test_fr2_filter_by_tag_case_insensitive(service):
    service.add("a", tags=["work"])
    service.add("b", tags=["home"])
    assert [t.title for t in service.list(tag="WORK")] == ["a"]


def test_fr2_filter_by_status(service):
    service.add("a")
    service.add("b")
    service.set_status(2, "in_progress")
    assert [t.title for t in service.list(status="in_progress")] == ["b"]


def test_fr2_combined_filters(service):
    service.add("a", tags=["x"])
    service.add("b", tags=["x"])
    service.set_status(1, "in_progress")
    assert [t.title for t in service.list(tag="x", status="todo")] == ["b"]


def test_fr2_invalid_status_filter(service):
    with pytest.raises(ValidationError):
        service.list(status="bogus")


def test_fr2_empty_list(service):
    assert service.list() == []


# ---- FR-3 Update ----------------------------------------------------------
def test_fr3_update_fields(service):
    service.add("old", tags=["a"])
    task = service.update(1, title="new", priority="high", tags=["b"])
    assert (task.title, task.priority, task.tags) == ("new", "high", ["b"])


def test_fr3_partial_update_keeps_other_fields(service):
    service.add("old", priority="low", tags=["a"])
    task = service.update(1, title="new")
    assert (task.priority, task.tags) == ("low", ["a"])


def test_fr3_update_validates(service):
    service.add("t")
    with pytest.raises(ValidationError):
        service.update(1, title="")
    with pytest.raises(ValidationError):
        service.update(1, priority="nope")


def test_fr3_update_missing_task(service):
    with pytest.raises(NotFoundError):
        service.update(99, title="x")


def test_fr3_failed_update_does_not_change_data(service):
    service.add("keep")
    with pytest.raises(ValidationError):
        service.update(1, title="")
    assert service.get(1).title == "keep"


# ---- FR-4 Delete ----------------------------------------------------------
def test_fr4_delete(service):
    service.add("a")
    service.delete(1)
    assert service.list() == []


def test_fr4_delete_missing(service):
    with pytest.raises(NotFoundError):
        service.delete(1)


def test_fr4_get_missing(service):
    with pytest.raises(NotFoundError):
        service.get(5)


# ---- FR-5 Status transitions ---------------------------------------------
ALLOWED = [
    ("todo", "in_progress"),
    ("in_progress", "todo"),
    ("in_progress", "done"),
    ("done", "todo"),
]
FORBIDDEN = [("todo", "done"), ("done", "in_progress"), ("todo", "todo"), ("done", "done")]


def _move_to(service, task_id, target):
    path = {"todo": [], "in_progress": ["in_progress"], "done": ["in_progress", "done"]}
    for step in path[target]:
        service.set_status(task_id, step)


@pytest.mark.parametrize("src,dst", ALLOWED)
def test_fr5_allowed_transitions(service, src, dst):
    service.add("t")
    _move_to(service, 1, src)
    assert service.set_status(1, dst).status == dst


@pytest.mark.parametrize("src,dst", FORBIDDEN)
def test_fr5_forbidden_transitions(service, src, dst):
    service.add("t")
    _move_to(service, 1, src)
    with pytest.raises(InvalidTransitionError):
        service.set_status(1, dst)
    assert service.get(1).status == src


def test_fr5_unknown_status(service):
    service.add("t")
    with pytest.raises(ValidationError):
        service.set_status(1, "cancelled")


def test_fr5_status_missing_task(service):
    with pytest.raises(NotFoundError):
        service.set_status(1, "in_progress")


# ---- FR-6 Persistence -----------------------------------------------------
def test_fr6_data_survives_new_service_instance(data_file):
    TodoService(JsonStorage(data_file)).add("persist", tags=["x"])
    task = TodoService(JsonStorage(data_file)).get(1)
    assert task.title == "persist" and task.tags == ["x"]


def test_fr6_missing_file_means_empty(service):
    assert service.list() == []


def test_fr6_corrupt_json_raises_storage_error(data_file):
    data_file.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()


def test_fr6_wrong_structure_raises_storage_error(data_file):
    data_file.write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()


def test_fr6_bad_task_record_raises_storage_error(data_file):
    data_file.write_text('{"next_id": 2, "tasks": [{"bogus": 1}]}', encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()


def test_fr6_bad_next_id_raises_storage_error(data_file):
    data_file.write_text('{"next_id": "x", "tasks": []}', encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).list()


def test_fr6_no_temp_files_left_behind(service, data_file):
    service.add("a")
    service.add("b")
    assert [p.name for p in data_file.parent.iterdir()] == ["todo.json"]


def test_fr6_corrupt_file_not_overwritten_by_failed_add(data_file):
    data_file.write_text("{not json", encoding="utf-8")
    with pytest.raises(StorageError):
        TodoService(JsonStorage(data_file)).add("x")
    assert data_file.read_text(encoding="utf-8") == "{not json"


def test_fr6_write_failure_raises_storage_error(tmp_path):
    blocker = tmp_path / "blocker"
    blocker.write_text("file, not dir", encoding="utf-8")
    storage = JsonStorage(blocker / "todo.json")
    with pytest.raises((StorageError, OSError)):
        TodoService(storage).add("x")
