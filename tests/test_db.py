"""Tests for fcd.db."""
import json

import pytest

from fcd.db import Db, Files


class TestFiles:
    """Tests for the Files path holder."""

    def test_default_paths_in_home(self):
        # Arrange / Act
        files = Files()
        # Assert
        assert files.db_file.endswith("/.fcd.json")
        assert files.dir_file.endswith("/.fcd_dir")
        assert files.cmd_file.endswith("/.fcd_cmd")

    def test_setters_override_paths(self):
        # Arrange
        files = Files()
        # Act
        files.db_file = "/tmp/db.json"
        files.dir_file = "/tmp/dir"
        files.cmd_file = "/tmp/cmd"
        # Assert
        assert files.db_file == "/tmp/db.json"
        assert files.dir_file == "/tmp/dir"
        assert files.cmd_file == "/tmp/cmd"


class TestDbLoad:
    """Tests for Db.load."""

    def test_load_existing_database(self, tmp_path):
        # Arrange
        db_file = tmp_path / ".fcd.json"
        data = {"home": {"directory": "/home/u", "command": "ls"}}
        db_file.write_text(json.dumps(data), encoding="utf-8")
        # Act
        result = Db(str(db_file)).load()
        # Assert
        assert result == data

    def test_load_missing_file_bootstraps_dummy(self, tmp_path, capsys):
        # Arrange
        db_file = tmp_path / ".fcd.json"
        # Act
        result = Db(str(db_file)).load()
        # Assert
        assert result == {"dummy": {"directory": "/dummy", "command": ""}}
        assert db_file.exists()
        assert "first time usage" in capsys.readouterr().out

    def test_load_corrupt_json_exits(self, tmp_path):
        # Arrange
        db_file = tmp_path / ".fcd.json"
        db_file.write_text("", encoding="utf-8")
        # Act / Assert
        with pytest.raises(SystemExit):
            Db(str(db_file)).load()

    def test_load_ioerror_exits(self, tmp_path, mocker):
        # Arrange
        db_file = tmp_path / ".fcd.json"
        db_file.write_text("{}", encoding="utf-8")
        mocker.patch("fcd.db.open", side_effect=IOError("boom"))
        # Act / Assert
        with pytest.raises(SystemExit):
            Db(str(db_file)).load()


class TestDbSave:
    """Tests for Db.save."""

    def test_save_round_trip(self, tmp_path):
        # Arrange
        db_file = tmp_path / ".fcd.json"
        data = {"a": {"directory": "/a", "command": ""}}
        db = Db(str(db_file))
        # Act
        db.save(data)
        # Assert
        assert json.loads(db_file.read_text(encoding="utf-8")) == data

    def test_save_ioerror_exits(self, tmp_path, mocker):
        # Arrange
        db = Db(str(tmp_path / ".fcd.json"))
        mocker.patch("fcd.db.open", side_effect=IOError("nope"))
        # Act / Assert
        with pytest.raises(SystemExit):
            db.save({"a": 1})
