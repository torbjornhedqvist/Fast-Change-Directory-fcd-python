"""Tests for fcd.matching."""
import pytest

from fcd.matching import Match, fuzzy_match


class TestFuzzyMatch:
    """Tests for the fuzzy_match function."""

    def test_empty_query_returns_all_in_order(self):
        # Arrange
        candidates = ["banana", "apple", "cherry"]
        # Act
        result = fuzzy_match("", candidates)
        # Assert
        assert [m.value for m in result] == candidates

    def test_prefix_match(self):
        # Arrange / Act
        result = fuzzy_match("app", ["apple", "application", "banana"])
        # Assert
        assert {m.value for m in result} == {"apple", "application"}

    def test_subsequence_non_contiguous_match(self):
        # Arrange / Act
        result = fuzzy_match("dwn", ["downloads", "docs", "windows"])
        # Assert
        assert "downloads" in [m.value for m in result]
        assert "docs" not in [m.value for m in result]

    def test_no_match_returns_empty(self):
        # Act
        result = fuzzy_match("xyz", ["apple", "banana"])
        # Assert
        assert result == []

    def test_case_insensitive(self):
        # Act
        result = fuzzy_match("AP", ["apple"])
        # Assert
        assert result[0].value == "apple"

    def test_positions_highlight_indices(self):
        # Act
        result = fuzzy_match("dl", ["downloads"])
        # Assert: 'd' at 0, 'l' at 4 in 'downloads'
        assert result[0].positions == (0, 4)

    def test_prefix_first_excludes_non_prefix(self):
        # Arrange: 'p' should return ONLY aliases starting with 'p',
        # not fuzzy matches like 'ciap' (prefix-first behavior).
        result = fuzzy_match("p", ["pk", "play", "ciap", "erepos"])
        # Assert
        assert [m.value for m in result] == ["pk", "play"]

    def test_fuzzy_fallback_when_no_prefix(self):
        # Arrange: no candidate starts with 'dwn' -> fuzzy fallback engages
        result = fuzzy_match("dwn", ["downloads", "docs", "windows"])
        # Assert
        assert "downloads" in [m.value for m in result]
        assert "docs" not in [m.value for m in result]

    def test_prefix_matches_sorted_shortest_then_alpha(self):
        # Arrange / Act
        result = fuzzy_match("app", ["application", "apple", "apps"])
        # Assert: shortest first, ties alpha
        assert [m.value for m in result] == ["apps", "apple", "application"]

    def test_ranking_prefers_earlier_start_in_fuzzy_path(self):
        # Arrange: fuzzy path (no prefix). 'ab' in 'axb' starts at index 0,
        # in 'xab' at index 1. Earlier start dominates the score, so 'axb' wins
        # even though 'xab' is more contiguous.
        result = fuzzy_match("ab", ["xab", "axb"])
        # Assert
        assert result[0].value == "axb"

    def test_ranking_prefers_contiguous_when_same_start(self):
        # Arrange: both start matching at index 0; 'abc' contiguous beats 'axbc'
        result = fuzzy_match("abc", ["axbxc", "abxc"])
        # Assert: 'abxc' has fewer gaps -> ranks first
        assert result[0].value == "abxc"

    def test_fuzzy_tie_breaks_alphabetically(self):
        # Arrange: fuzzy path, same structure -> alphabetical tie-break
        result = fuzzy_match("a", ["xa", "za"])
        # Assert
        assert [m.value for m in result] == ["xa", "za"]

    def test_tie_breaks_alphabetically(self):
        # Arrange: identical structural score -> alpha order
        result = fuzzy_match("a", ["az", "ay"])
        # Assert
        assert [m.value for m in result] == ["ay", "az"]

    def test_match_dataclass_defaults(self):
        # Arrange / Act
        match = Match(value="x")
        # Assert
        assert match.positions == ()
        assert match.score == 0
