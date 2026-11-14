"""Tests for fcd.cli."""
import pytest

from fcd import cli, VERSION


class TestParseArgs:
    """Tests for argument parsing."""

    def test_positional_alias(self, mocker):
        # Arrange
        mocker.patch("sys.argv", ["fcd", "myalias"])
        # Act
        args = cli.parse_args()
        # Assert
        assert args["alias"] == "myalias"

    def test_add_flag(self, mocker):
        # Arrange
        mocker.patch("sys.argv", ["fcd", "-a", "newalias"])
        # Act
        args = cli.parse_args()
        # Assert
        assert args["add"] == "newalias"

    def test_delete_without_value(self, mocker):
        # Arrange
        mocker.patch("sys.argv", ["fcd", "-d"])
        # Act
        args = cli.parse_args()
        # Assert
        assert args["delete"] is True

    def test_add_and_delete_mutually_exclusive(self, mocker):
        # Arrange
        mocker.patch("sys.argv", ["fcd", "-a", "x", "-d", "y"])
        # Act / Assert
        with pytest.raises(SystemExit):
            cli.parse_args()

    def test_command_flag_const(self, mocker):
        # Arrange
        mocker.patch("sys.argv", ["fcd", "-c"])
        # Act
        args = cli.parse_args()
        # Assert
        assert args["command"] is True


class TestMain:
    """Tests for the main entry point."""

    def test_version_prints_and_exits(self, mocker, capsys):
        # Arrange
        mocker.patch("sys.argv", ["fcd", "--version"])
        # Act / Assert
        with pytest.raises(SystemExit) as exc:
            cli.main()
        assert exc.value.code == 0
        assert capsys.readouterr().out.strip() == f"v{VERSION}"

    def test_main_builds_fcd_and_dispatches(self, mocker):
        # Arrange
        mocker.patch("sys.argv", ["fcd", "apple"])
        fake_fcd = mocker.Mock()
        mocker.patch("fcd.cli.Fcd", return_value=fake_fcd)
        # Act
        cli.main()
        # Assert
        fake_fcd.clean_up.assert_called_once()
        fake_fcd.args_handler.assert_called_once()
