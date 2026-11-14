"""Tests for fcd.core."""
import json

import pytest

from fcd.core import Fcd
from fcd.db import Db, Files


class StubSelector:
    """A scripted Selector returning queued answers."""

    def __init__(self, answers):
        self._answers = list(answers)
        self.command_answer = ""

    def select(self, prefill, prompt="fcd> "):
        return self._answers.pop(0)

    def read_command(self, prompt):
        return self.command_answer


@pytest.fixture
def setup(tmp_path):
    """Create a Files/Db pointing at tmp files with a known database."""
    db_file = tmp_path / ".fcd.json"
    dir_file = tmp_path / ".fcd_dir"
    cmd_file = tmp_path / ".fcd_cmd"
    database = {
        "apple": {"directory": str(tmp_path), "command": ""},
        "avocado": {"directory": str(tmp_path), "command": "ls -la"},
        "banana": {"directory": str(tmp_path), "command": ""},
    }
    db_file.write_text(json.dumps(database), encoding="utf-8")
    files = Files()
    files.db_file = str(db_file)
    files.dir_file = str(dir_file)
    files.cmd_file = str(cmd_file)
    return files, tmp_path


def _make_fcd(files, answers):
    db_handler = Db(files.db_file)
    return Fcd(files=files, db_handler=db_handler, selector=StubSelector(answers))


class TestAliasHandler:
    """Tests for alias_handler."""

    def test_exact_alias_writes_dir_file(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, [])
        # Act
        fcd.alias_handler("apple", fcd._records())  # pylint: disable=protected-access
        # Assert: sentinel dir file has path + trailing newline
        assert (tmp_path / ".fcd_dir").read_text(encoding="utf-8") == f"{tmp_path}\n"

    def test_command_record_writes_cmd_file(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, [])
        # Act
        fcd.alias_handler("avocado", fcd._records())  # pylint: disable=protected-access
        # Assert
        assert (tmp_path / ".fcd_cmd").read_text(encoding="utf-8") == "ls -la\n"

    def test_partial_alias_uses_selector(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, ["banana"])
        # Act
        fcd.alias_handler("ban", fcd._records())  # pylint: disable=protected-access
        # Assert
        assert (tmp_path / ".fcd_dir").exists()

    def test_trailing_slash_trimmed(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, [])
        # Act
        fcd.alias_handler("apple/", fcd._records())  # pylint: disable=protected-access
        # Assert
        assert (tmp_path / ".fcd_dir").exists()

    def test_missing_directory_exits(self, setup, mocker):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        mocker.patch("fcd.core.os.path.isdir", return_value=False)
        # Act / Assert
        with pytest.raises(SystemExit):
            fcd.alias_handler("apple", fcd._records())  # pylint: disable=protected-access

    def test_invalid_alias_type_raises(self, setup):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        # Act / Assert
        with pytest.raises(ValueError):
            fcd.alias_handler(123, [])

    def test_invalid_records_type_raises(self, setup):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        # Act / Assert
        with pytest.raises(ValueError):
            fcd.alias_handler("apple", "notalist")


class TestAddHandler:
    """Tests for add_handler."""

    def test_add_new_alias(self, setup, mocker):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, [])
        mocker.patch("fcd.core.os.getcwd", return_value=str(tmp_path))
        # Act
        fcd.add_handler("newone")
        # Assert
        saved = json.loads((tmp_path / ".fcd.json").read_text(encoding="utf-8"))
        assert saved["newone"]["directory"] == str(tmp_path)

    def test_add_existing_alias_exits(self, setup):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        # Act / Assert
        with pytest.raises(SystemExit):
            fcd.add_handler("apple")

    def test_add_slash_in_name_exits(self, setup):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        # Act / Assert
        with pytest.raises(SystemExit):
            fcd.add_handler("a/b")

    def test_add_invalid_type_raises(self, setup):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        # Act / Assert
        with pytest.raises(ValueError):
            fcd.add_handler(123)


class TestDeleteHandler:
    """Tests for delete_handler."""

    def test_delete_exact(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, [])
        # Act
        fcd.delete_handler("apple", fcd._records())  # pylint: disable=protected-access
        # Assert
        saved = json.loads((tmp_path / ".fcd.json").read_text(encoding="utf-8"))
        assert "apple" not in saved

    def test_delete_interactive_true(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, ["banana"])
        # Act
        fcd.delete_handler(True, fcd._records())  # pylint: disable=protected-access
        # Assert
        saved = json.loads((tmp_path / ".fcd.json").read_text(encoding="utf-8"))
        assert "banana" not in saved

    def test_delete_partial_uses_selector(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, ["apple"])
        # Act
        fcd.delete_handler("app", fcd._records())  # pylint: disable=protected-access
        # Assert
        saved = json.loads((tmp_path / ".fcd.json").read_text(encoding="utf-8"))
        assert "apple" not in saved

    def test_delete_invalid_type_raises(self, setup):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        # Act / Assert
        with pytest.raises(ValueError):
            fcd.delete_handler(123, fcd._records())  # pylint: disable=protected-access


class TestCommandHandler:
    """Tests for command_handler."""

    def test_preselected_alias_with_inline_command(self, setup):
        # Arrange
        files, tmp_path = setup
        fcd = _make_fcd(files, [])
        # Act
        fcd.command_handler({"add": "apple", "command": "ls -A"},
                            fcd._records())  # pylint: disable=protected-access
        # Assert
        saved = json.loads((tmp_path / ".fcd.json").read_text(encoding="utf-8"))
        assert saved["apple"]["command"] == "ls -A"

    def test_interactive_select_and_prompt_command(self, setup):
        # Arrange
        files, tmp_path = setup
        selector = StubSelector(["banana"])
        selector.command_answer = "pwd"
        fcd = Fcd(files=files, db_handler=Db(files.db_file), selector=selector)
        # Act
        fcd.command_handler({"add": None, "command": True},
                            fcd._records())  # pylint: disable=protected-access
        # Assert
        saved = json.loads((tmp_path / ".fcd.json").read_text(encoding="utf-8"))
        assert saved["banana"]["command"] == "pwd"

    def test_invalid_args_type_raises(self, setup):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        # Act / Assert
        with pytest.raises(ValueError):
            fcd.command_handler("notadict", fcd._records())  # pylint: disable=protected-access


class TestCleanUpAndArgs:
    """Tests for clean_up and args_handler dispatch."""

    def test_clean_up_removes_sentinels(self, setup):
        # Arrange
        files, tmp_path = setup
        (tmp_path / ".fcd_dir").write_text("x", encoding="utf-8")
        (tmp_path / ".fcd_cmd").write_text("y", encoding="utf-8")
        fcd = _make_fcd(files, [])
        # Act
        fcd.clean_up()
        # Assert
        assert not (tmp_path / ".fcd_dir").exists()
        assert not (tmp_path / ".fcd_cmd").exists()

    def test_args_handler_keyboardinterrupt_exits(self, setup, mocker):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        mocker.patch.object(fcd, "alias_handler", side_effect=KeyboardInterrupt)
        mocker.patch("fcd.core.sys.argv", ["fcd", "apple"])
        # Act / Assert
        with pytest.raises(SystemExit):
            fcd.args_handler({"alias": "apple"})

    def test_args_handler_add_dispatch(self, setup, mocker):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        add = mocker.patch.object(fcd, "add_handler")
        # Act
        fcd.args_handler({"alias": None, "add": "x", "delete": None,
                          "command": None})
        # Assert
        add.assert_called_once_with("x")

    def test_args_handler_delete_dispatch(self, setup, mocker):
        # Arrange
        files, _ = setup
        fcd = _make_fcd(files, [])
        delete = mocker.patch.object(fcd, "delete_handler")
        # Act
        fcd.args_handler({"alias": None, "add": None, "delete": "x",
                          "command": None})
        # Assert
        delete.assert_called_once()
