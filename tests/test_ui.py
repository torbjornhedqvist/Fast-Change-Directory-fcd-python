"""Tests for fcd.ui."""
from fcd.ui import Color, list_records


RECORDS = [
    ["apple", "/apple", "ls"],
    ["avocado", "/avocado", ""],
    ["banana", "/banana", "ll"],
]


class TestColor:
    """Tests for the Color codes."""

    def test_codes_present(self):
        # Arrange / Act
        color = Color()
        # Assert
        assert color.bright_blue.startswith("\033")
        assert color.reset == "\033[0m"
        assert color.red and color.light_red and color.light_yellow


class TestListRecords:
    """Tests for list_records output behaviour."""

    def test_no_color_when_not_tty(self, mocker, capsys):
        # Arrange
        mocker.patch("fcd.ui.sys.stdout.isatty", return_value=False)
        # Act
        list_records(RECORDS, use_colors=True)
        out = capsys.readouterr().out
        # Assert: no ANSI escape sequences emitted
        assert "\033" not in out
        assert "[apple] /apple" in out

    def test_color_toggles_on_first_char_group(self, mocker, capsys):
        # Arrange
        mocker.patch("fcd.ui.sys.stdout.isatty", return_value=True)
        # Act
        list_records(RECORDS, use_colors=True)
        out = capsys.readouterr().out
        # Assert: both bright_blue and red appear (a->b change toggles)
        color = Color()
        assert color.bright_blue in out
        assert color.red in out

    def test_filter_by_alias_prefix(self, mocker, capsys):
        # Arrange
        mocker.patch("fcd.ui.sys.stdout.isatty", return_value=False)
        # Act
        list_records(RECORDS, alias="ban", use_colors=False)
        out = capsys.readouterr().out
        # Assert
        assert "banana" in out
        assert "apple" not in out

    def test_show_cmd_includes_command(self, mocker, capsys):
        # Arrange
        mocker.patch("fcd.ui.sys.stdout.isatty", return_value=False)
        # Act
        list_records(RECORDS, show_cmd=True, use_colors=False)
        out = capsys.readouterr().out
        # Assert
        assert "/apple : ls" in out

    def test_use_colors_false_no_escapes(self, capsys):
        # Act
        list_records(RECORDS, use_colors=False)
        out = capsys.readouterr().out
        # Assert
        assert "\033" not in out
