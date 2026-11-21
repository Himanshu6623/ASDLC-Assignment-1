"""FR-005 and FR-012 through FR-014 CLI traceability tests."""

import pytest

from smart_todo.cli import main


def run(data_file, *args):
    return main(["--file", str(data_file), *args])


def test_fr012_fr014_add_list_success_text(data_file, capsys):
    assert run(data_file, "add", "  Buy milk  ", "--priority", "high", "--tag", "Home") == 0
    captured = capsys.readouterr()
    assert captured.out == "1 [todo] (high) Buy milk #home\n"
    assert captured.err == ""
    assert run(data_file, "list", "--tag", "HOME") == 0
    assert "Buy milk" in capsys.readouterr().out


def test_fr014_json_option_is_unavailable(data_file):
    with pytest.raises(SystemExit) as exc:
        run(data_file, "list", "--json")
    assert exc.value.code == 2


@pytest.mark.parametrize("identifier", ["abc", "1.5", ""])
def test_fr012_non_integer_id_is_usage_error(data_file, identifier):
    with pytest.raises(SystemExit) as exc:
        run(data_file, "delete", identifier)
    assert exc.value.code == 2


@pytest.mark.parametrize("identifier", ["0", "-1"])
def test_fr012_integer_non_positive_id_is_domain_error(data_file, capsys, identifier):
    assert run(data_file, "delete", identifier) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not found" in captured.err


def test_fr005_unknown_tag_is_success_empty_list(data_file, capsys):
    assert run(data_file, "add", "task") == 0
    capsys.readouterr()
    assert run(data_file, "list", "--tag", "Unknown") == 0
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""


def test_fr005_unknown_status_is_usage_error(data_file):
    with pytest.raises(SystemExit) as exc:
        run(data_file, "list", "--status", "unknown")
    assert exc.value.code == 2


def test_fr007_no_update_fields_is_usage_error_without_mutation(data_file, capsys):
    assert run(data_file, "add", "task") == 0
    capsys.readouterr()
    with pytest.raises(SystemExit) as exc:
        run(data_file, "update", "1")
    assert exc.value.code == 2
    assert run(data_file, "list") == 0
    assert "task" in capsys.readouterr().out


def test_fr012_domain_errors_are_stderr_only(data_file, capsys):
    assert run(data_file, "delete", "42") == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "not found" in captured.err


def test_fr011_corrupt_saved_data_is_domain_error(data_file, capsys):
    data_file.write_text("{bad", encoding="utf-8")
    before = data_file.read_text(encoding="utf-8")
    assert run(data_file, "list") == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err
    assert data_file.read_text(encoding="utf-8") == before


@pytest.mark.parametrize("args", [(), ("missing",), ("add",), ("status", "1"), ("update",)])
def test_fr012_malformed_commands_are_usage_errors(data_file, args):
    with pytest.raises(SystemExit) as exc:
        run(data_file, *args)
    assert exc.value.code == 2


@pytest.mark.parametrize(
    "args",
    [
        ("add", "task", "--priority", "urgent"),
        ("status", "1", "unknown"),
    ],
)
def test_fr012_invalid_choices_are_usage_errors(data_file, args):
    with pytest.raises(SystemExit) as exc:
        run(data_file, *args)
    assert exc.value.code == 2


def test_sc008_end_to_end_cli_journey(data_file, capsys):
    assert run(data_file, "add", "journey", "--tag", "demo") == 0
    capsys.readouterr()
    assert run(data_file, "list") == 0
    assert "journey" in capsys.readouterr().out
    assert run(data_file, "update", "1", "--title", "updated") == 0
    capsys.readouterr()
    assert run(data_file, "status", "1", "in_progress") == 0
    capsys.readouterr()
    assert run(data_file, "status", "1", "done") == 0
    capsys.readouterr()
    assert run(data_file, "delete", "1") == 0
    assert capsys.readouterr().out == "deleted 1\n"
