"""Contract tests for the CLI (FR-7: exit codes and output)."""

import json

from smart_todo.cli import main


def run(data_file, *args):
    return main(["--file", str(data_file), *args])


def test_fr7_add_and_list(data_file, capsys):
    assert run(data_file, "add", "Buy milk", "--priority", "high", "--tag", "home") == 0
    assert "1 [todo] (high) Buy milk #home" in capsys.readouterr().out
    assert run(data_file, "list") == 0
    assert "Buy milk" in capsys.readouterr().out


def test_fr7_list_json_output(data_file, capsys):
    run(data_file, "add", "a")
    capsys.readouterr()
    assert run(data_file, "list", "--json") == 0
    parsed = json.loads(capsys.readouterr().out)
    assert parsed[0]["title"] == "a"


def test_fr7_list_filters(data_file, capsys):
    run(data_file, "add", "a", "--tag", "x")
    run(data_file, "add", "b", "--tag", "y")
    capsys.readouterr()
    run(data_file, "list", "--tag", "x", "--no-sort")
    out = capsys.readouterr().out
    assert "a" in out and " b " not in out


def test_fr7_update_status_delete(data_file, capsys):
    run(data_file, "add", "a")
    assert run(data_file, "update", "1", "--title", "b", "--tag", "z") == 0
    assert run(data_file, "status", "1", "in_progress") == 0
    assert run(data_file, "delete", "1") == 0
    assert "deleted 1" in capsys.readouterr().out


def test_fr7_domain_error_exit_1_and_stderr(data_file, capsys):
    assert run(data_file, "delete", "42") == 1
    captured = capsys.readouterr()
    assert "not found" in captured.err
    assert captured.out == ""


def test_fr7_invalid_transition_exit_1(data_file, capsys):
    run(data_file, "add", "a")
    assert run(data_file, "status", "1", "done") == 1
    assert "cannot move" in capsys.readouterr().err


def test_fr7_validation_error_exit_1(data_file, capsys):
    assert run(data_file, "add", "   ") == 1
    assert "empty" in capsys.readouterr().err


def test_fr7_usage_error_exit_2(data_file):
    try:
        run(data_file, "add", "x", "--priority", "urgent")
    except SystemExit as exc:
        assert exc.code == 2
    else:
        raise AssertionError("expected SystemExit(2)")
