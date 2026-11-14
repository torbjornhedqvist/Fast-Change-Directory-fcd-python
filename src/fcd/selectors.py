"""Interactive alias selection strategies for Fast Change Directory (fcd).

Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

Defines a :class:`Selector` strategy with two implementations:

* :class:`PromptToolkitSelector` - rich, fuzzy, live-filtering UI.
* :class:`ReadlineSelector` - stdlib ``readline`` fallback (prefix completion).

:func:`get_selector` picks the best available implementation, falling back to
readline when ``prompt_toolkit`` cannot be imported.
"""
from __future__ import annotations

import logging
import readline
from abc import ABC, abstractmethod

from fcd.matching import fuzzy_match

logger = logging.getLogger(__name__)


class Selector(ABC):
    """Strategy for reading an alias from the user with completion support."""

    def __init__(self, aliases: list[str]) -> None:
        self._aliases = aliases

    @abstractmethod
    def select(self, prefill: str, prompt: str = "fcd> ") -> str:
        """Prompt the user and return the (trimmed) entered alias.

        Args:
            prefill: Text to pre-populate the input line with.
            prompt: The prompt string shown to the user.

        Returns:
            The user's input with any trailing ``/`` removed.
        """
        raise NotImplementedError


def _trim(line: str) -> str:
    """Strip a trailing ``/`` that completion may append."""
    return line.rstrip("/")


class _TabComplete:
    """A prefix TAB completer for readline.

    Args:
        aliases: Candidate alias strings used for prefix comparison.
    """

    def __init__(self, aliases: list[str]) -> None:
        self._aliases = aliases

    def complete(self, text: str, state: int) -> str | None:
        """readline completer entry point."""
        results = [x for x in self._aliases if x.startswith(text)] + [None]
        return results[state]


class ReadlineSelector(Selector):
    """Fallback selector using the stdlib ``readline`` module (prefix match)."""

    def __init__(self, aliases: list[str]) -> None:
        super().__init__(aliases)
        self._completer = _TabComplete(aliases)

    def select(self, prefill: str, prompt: str = "fcd> ") -> str:
        """Read a line using readline prefix completion and a pre-input hook."""
        logger.debug("ReadlineSelector.select prefill=%r", prefill)
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self._completer.complete)

        def hook() -> None:
            readline.insert_text(prefill)
            readline.redisplay()

        readline.set_pre_input_hook(hook)
        try:
            line = input(prompt)
        finally:
            readline.set_pre_input_hook(None)
        return _trim(line)

    def read_command(self, prompt: str) -> str:
        """Read a free-text command line without completion."""
        readline.set_pre_input_hook(None)
        return input(prompt)


def build_fuzzy_completer(aliases: list[str]):
    """Create a prompt_toolkit completer yielding ranked fuzzy matches.

    Imported lazily so this module is importable without prompt_toolkit.

    Args:
        aliases: Candidate alias strings.

    Returns:
        A ``prompt_toolkit.completion.Completer`` instance.
    """
    from prompt_toolkit.completion import Completer, Completion

    class FuzzyAliasCompleter(Completer):
        """Completer presenting ranked fuzzy matches of the alias list."""

        def __init__(self, candidates: list[str]) -> None:
            self._candidates = candidates

        def get_completions(self, document, complete_event):
            text = document.text_before_cursor
            for match in fuzzy_match(text, self._candidates):
                # Replace the whole input with the chosen alias.
                yield Completion(
                    match.value,
                    start_position=-len(text),
                    display=match.value,
                )

    return FuzzyAliasCompleter(aliases)


class PromptToolkitSelector(Selector):
    """Rich selector using prompt_toolkit with live fuzzy filtering."""

    def __init__(self, aliases: list[str], session=None) -> None:
        super().__init__(aliases)
        if session is None:
            from prompt_toolkit import PromptSession
            session = PromptSession()
        self._session = session

    def select(self, prefill: str, prompt: str = "fcd> ") -> str:
        """Prompt with a fuzzy completion menu and return the trimmed result.

        If the typed text is not an exact alias but exactly one fuzzy candidate
        exists, that candidate is returned (single-candidate resolution).
        """
        from prompt_toolkit.shortcuts import CompleteStyle

        completer = build_fuzzy_completer(self._aliases)
        line = self._session.prompt(
            prompt,
            default=prefill,
            completer=completer,
            complete_while_typing=True,
            complete_style=CompleteStyle.MULTI_COLUMN,
        )
        line = _trim(line)
        if line not in self._aliases:
            matches = fuzzy_match(line, self._aliases)
            if len(matches) == 1:
                return matches[0].value
        return line

    def read_command(self, prompt: str) -> str:
        """Read a free-text command line (no completer)."""
        return self._session.prompt(prompt)


def get_selector(aliases: list[str]) -> Selector:
    """Return the best available selector.

    Prefers :class:`PromptToolkitSelector`; falls back to
    :class:`ReadlineSelector` if ``prompt_toolkit`` is not importable.

    Args:
        aliases: Candidate alias strings for completion.

    Returns:
        A ready-to-use :class:`Selector`.
    """
    try:
        import prompt_toolkit  # noqa: F401  pylint: disable=unused-import,import-outside-toplevel
    except ImportError:
        logger.info("prompt_toolkit unavailable; using readline fallback")
        return ReadlineSelector(aliases)
    logger.info("using prompt_toolkit selector")
    return PromptToolkitSelector(aliases)
