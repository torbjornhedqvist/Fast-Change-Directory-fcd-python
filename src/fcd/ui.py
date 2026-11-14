"""User-interface helpers for Fast Change Directory (fcd).

Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

Owns terminal colours and the record-listing presentation. Interactive input is
delegated to the selector strategy (see :mod:`fcd.selectors`).
"""
import logging
import sys

logger = logging.getLogger(__name__)


class Color:
    """ANSI colour codes used in terminal output."""

    def __init__(self) -> None:
        self._bright_blue = "\033[38;5;39m"
        self._red = "\033[31m"
        self._light_red = "\033[91m"
        self._light_yellow = "\033[93m"
        self._reset = "\033[0m"

    @property
    def bright_blue(self) -> str:
        """ANSI code for bright blue (256-colour, matches ls dir colour)."""
        return self._bright_blue

    @property
    def red(self) -> str:
        """ANSI code for red."""
        return self._red

    @property
    def light_red(self) -> str:
        """ANSI code for light red."""
        return self._light_red

    @property
    def light_yellow(self) -> str:
        """ANSI code for light yellow."""
        return self._light_yellow

    @property
    def reset(self) -> str:
        """ANSI code to reset to the default colour."""
        return self._reset


def _should_use_colors(explicit: bool) -> bool:
    """Decide whether colours should be emitted.

    Colours are suppressed when stdout is not a TTY (e.g. piped output), even if
    the caller requested them.

    Args:
        explicit: The caller's requested colour preference.

    Returns:
        True if colours should actually be emitted.
    """
    if not explicit:
        return False
    return sys.stdout.isatty()


def list_records(records: list, alias: str = "", show_cmd: bool = False,
                 use_colors: bool = True, color: Color | None = None) -> None:
    """Print alias/directory records to the console.

    Colours alternate between bright blue and red whenever the first character
    of the alias changes, matching the original program's visual grouping.

    Args:
        records: A list of ``[alias, directory, command]`` lists.
        alias: Only records whose alias starts with this string are printed.
        show_cmd: When True the associated command is also printed.
        use_colors: When True (and stdout is a TTY) alternating colours are used.
        color: Optional :class:`Color` instance; created if not supplied.
    """
    logger.debug("Enter")
    color = color or Color()
    use_colors = _should_use_colors(use_colors)

    first_char = ""
    current_color = color.bright_blue if use_colors else ""

    for record in records:
        if use_colors and not record[0].startswith(first_char):
            if current_color == color.bright_blue:
                current_color = color.red
            else:
                current_color = color.bright_blue
        first_char = record[0][0]

        if record[0].startswith(alias):
            if show_cmd:
                print(f"{current_color}[{record[0]}] {record[1]} : {record[2]}")
            else:
                print(f"{current_color}[{record[0]}] {record[1]}")
    if use_colors:
        print(color.reset, end="")
    logger.debug("Exit")
