"""Tests for fcd.selectors."""
import builtins

import pytest

from fcd import selectors
from fcd.selectors import (
    PromptToolkitSelector,
    ReadlineSelector,
    Selector,
    get_selector,
)

ALIASES = ["apple", "application", "banana"]


class TestReadlineSelector:
    """Tests for the readline fallback selector."""

    def test_select_trims_trailing_slash(self, mocker):
        # Arrange
        mocker.patch.object(builtins, "input", return_value="apple/")
        mocker.patch("fcd.selectors.readline")
        sel = ReadlineSelector(ALIASES)
        # Act
        result = sel.select("ap")
        # Assert
        assert result == "apple"

    def test_select_resets_hook_in_finally(self, mocker):
        # Arrange
        rl = mocker.patch("fcd.selectors.readline")
        mocker.patch.object(builtins, "input", return_value="apple")
        sel = ReadlineSelector(ALIASES)
        # Act
        sel.select("")
        # Assert: hook reset to None at the end
        rl.set_pre_input_hook.assert_called_with(None)

    def test_read_command_reads_line(self, mocker):
        # Arrange
        mocker.patch("fcd.selectors.readline")
        mocker.patch.object(builtins, "input", return_value="ls -la")
        sel = ReadlineSelector(ALIASES)
        # Act / Assert
        assert sel.read_command("cmd: ") == "ls -la"

    def test_tabcomplete_prefix(self, mocker):
        # Arrange
        mocker.patch("fcd.selectors.readline")
        sel = ReadlineSelector(ALIASES)
        comp = sel._completer  # pylint: disable=protected-access
        # Act / Assert: state 0 and 1 return the two 'app' matches, then None
        assert comp.complete("app", 0) == "apple"
        assert comp.complete("app", 1) == "application"
        assert comp.complete("app", 2) is None


class _FakeSession:
    """A stand-in for prompt_toolkit.PromptSession."""

    def __init__(self, to_return):
        self._to_return = to_return
        self.calls = []

    def prompt(self, message, **kwargs):
        self.calls.append((message, kwargs))
        return self._to_return


class TestPromptToolkitSelector:
    """Tests for the prompt_toolkit selector using an injected fake session."""

    def test_select_exact_alias(self):
        # Arrange
        session = _FakeSession("banana")
        sel = PromptToolkitSelector(ALIASES, session=session)
        # Act
        result = sel.select("ban")
        # Assert
        assert result == "banana"

    def test_select_trims_trailing_slash(self):
        # Arrange
        session = _FakeSession("banana/")
        sel = PromptToolkitSelector(ALIASES, session=session)
        # Act / Assert
        assert sel.select("") == "banana"

    def test_single_candidate_resolution(self):
        # Arrange: 'bn' fuzzy-matches only 'banana'
        session = _FakeSession("bn")
        sel = PromptToolkitSelector(ALIASES, session=session)
        # Act
        result = sel.select("")
        # Assert
        assert result == "banana"

    def test_ambiguous_returns_typed_text(self):
        # Arrange: 'app' matches two aliases -> no auto-resolution
        session = _FakeSession("app")
        sel = PromptToolkitSelector(ALIASES, session=session)
        # Act
        result = sel.select("")
        # Assert
        assert result == "app"

    def test_select_passes_prefill_as_default(self):
        # Arrange
        session = _FakeSession("apple")
        sel = PromptToolkitSelector(ALIASES, session=session)
        # Act
        sel.select("ap")
        # Assert
        assert session.calls[0][1]["default"] == "ap"

    def test_read_command_uses_session(self):
        # Arrange
        session = _FakeSession("ls -la")
        sel = PromptToolkitSelector(ALIASES, session=session)
        # Act / Assert
        assert sel.read_command("cmd: ") == "ls -la"


class TestFuzzyCompleter:
    """Tests for the prompt_toolkit fuzzy completer."""

    def test_completions_ordered(self):
        # Arrange
        from prompt_toolkit.document import Document

        completer = selectors.build_fuzzy_completer(ALIASES)
        doc = Document("app")
        # Act
        completions = list(completer.get_completions(doc, None))
        # Assert
        texts = [c.text for c in completions]
        assert texts == ["apple", "application"]
        assert completions[0].start_position == -3


class TestGetSelector:
    """Tests for the get_selector factory and fallback."""

    def test_returns_prompt_toolkit_when_available(self):
        # Act
        sel = get_selector(ALIASES)
        # Assert
        assert isinstance(sel, PromptToolkitSelector)
        assert isinstance(sel, Selector)

    def test_falls_back_to_readline_on_import_error(self, mocker):
        # Arrange: force the prompt_toolkit import to fail
        real_import = builtins.__import__

        def fake_import(name, *args, **kwargs):
            if name == "prompt_toolkit":
                raise ImportError("simulated missing")
            return real_import(name, *args, **kwargs)

        mocker.patch.object(builtins, "__import__", side_effect=fake_import)
        # Act
        sel = get_selector(ALIASES)
        # Assert
        assert isinstance(sel, ReadlineSelector)
