"""Fuzzy subsequence matching for Fast Change Directory (fcd).

Copyright (C) Torbjorn Hedqvist - All Rights Reserved
You may use, distribute and modify this code under the
terms of the MIT license. See LICENSE file in the project
root for full license information.

Provides a dependency-free fuzzy matcher. A query matches a candidate when the
query characters appear in the candidate in order (not necessarily contiguous),
case-insensitively. Matches are ranked so that more "prefix-like" and more
contiguous matches sort first, which gives intuitive ordering in the UI.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Match:
    """A single fuzzy match result.

    Attributes:
        value: The candidate string that matched.
        positions: Indices in ``value`` that the query characters matched,
            usable for highlighting.
        score: Ranking score; lower is a better match.
    """

    value: str
    positions: tuple[int, ...] = field(default_factory=tuple)
    score: int = 0


def _match_one(query: str, candidate: str) -> Match | None:
    """Attempt to match ``query`` against a single ``candidate``.

    Uses a greedy left-to-right subsequence scan (case-insensitive).

    Args:
        query: The (already lower-cased) search string.
        candidate: The candidate string to test.

    Returns:
        A :class:`Match` if every query character is found in order, else None.
    """
    lowered = candidate.lower()
    positions: list[int] = []
    search_from = 0
    for char in query:
        index = lowered.find(char, search_from)
        if index == -1:
            return None
        positions.append(index)
        search_from = index + 1

    # Scoring (lower is better):
    #  - first match index: earlier start preferred (prefix-like).
    #  - span minus query length: fewer gaps (more contiguous) preferred.
    #  - candidate length: shorter candidate preferred as a tie-breaker.
    first = positions[0]
    span = positions[-1] - positions[0] + 1
    gaps = span - len(query)
    score = first * 100 + gaps * 10 + len(candidate)
    return Match(value=candidate, positions=tuple(positions), score=score)


def fuzzy_match(query: str, candidates: list[str]) -> list[Match]:
    """Return ranked matches of ``query`` over ``candidates``.

    Matching is **prefix-first with fuzzy fallback**:

    * An empty query returns every candidate in the original order.
    * If any candidate starts with ``query`` (case-insensitive), only those
      prefix matches are returned, ranked. This keeps short queries intuitive
      (e.g. ``p`` returns only aliases beginning with ``p``).
    * Otherwise the matcher falls back to fuzzy subsequence matching so queries
      like ``dwn`` still match ``downloads``.

    Results are sorted by ascending score then alphabetically for stability.

    Args:
        query: The search string (any case).
        candidates: Candidate strings to match against.

    Returns:
        A list of :class:`Match` ordered best-first.
    """
    logger.debug("fuzzy_match query=%r candidates=%d", query, len(candidates))
    lowered_query = query.lower()

    if lowered_query == "":
        return [Match(value=c, positions=(), score=0) for c in candidates]

    # Prefix-first: prefer candidates that literally start with the query.
    prefix_matches: list[Match] = []
    for candidate in candidates:
        if candidate.lower().startswith(lowered_query):
            positions = tuple(range(len(lowered_query)))
            # Shorter candidates rank first; ties broken alphabetically below.
            prefix_matches.append(
                Match(value=candidate, positions=positions, score=len(candidate))
            )
    if prefix_matches:
        return sorted(prefix_matches, key=lambda m: (m.score, m.value))

    # Fuzzy fallback: subsequence matching across all candidates.
    matches: list[Match] = []
    for candidate in candidates:
        match = _match_one(lowered_query, candidate)
        if match is not None:
            matches.append(match)
    return sorted(matches, key=lambda m: (m.score, m.value))
