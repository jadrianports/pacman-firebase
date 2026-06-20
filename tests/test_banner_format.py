"""Tests for main._format_banner — the got-passed banner copy/cap logic (RIVAL-01, D-06).

_format_banner receives an already-sorted, deduped list of passer initials and
returns the single banner string that the in-game overlay displays, or None when
there are no passers.

UI-SPEC cap rule (BANNER_NAME_CAP = 3):
  - Empty list              -> None  (no banner)
  - len <= cap              -> all names comma-joined + " passed you this week!"
  - len >  cap              -> first 3 + " +{K} more passed you this week!"

The cap boundary (len == cap vs len == cap+1) is pinned explicitly because the
off-by-one is the most likely regression point.
"""
import pytest

from main import _format_banner
from settings import BANNER_NAME_CAP


# ---------------------------------------------------------------------------
# Empty list
# ---------------------------------------------------------------------------

def test_format_banner_empty_list_returns_none():
    """An empty passer list produces no banner (None), not an empty string."""
    assert _format_banner([]) is None


# ---------------------------------------------------------------------------
# Single name
# ---------------------------------------------------------------------------

def test_format_banner_single_name():
    """A single passer is displayed without a comma and with the standard suffix."""
    result = _format_banner(["AAA"])
    assert result == "AAA passed you this week!"


# ---------------------------------------------------------------------------
# Multiple names within cap
# ---------------------------------------------------------------------------

def test_format_banner_two_names_under_cap():
    """Two names (below cap) are comma-joined with no '+more' clause."""
    result = _format_banner(["AAA", "BBB"])
    assert result == "AAA, BBB passed you this week!"


# ---------------------------------------------------------------------------
# At-cap boundary: all names listed, no "+more"
# ---------------------------------------------------------------------------

def test_format_banner_at_cap_lists_all_no_more():
    """Exactly BANNER_NAME_CAP names -> all listed, no '+K more' appended."""
    names = ["AAA", "BBB", "CCC"]
    assert len(names) == BANNER_NAME_CAP, "fixture must equal the cap"
    result = _format_banner(names)
    assert result == "AAA, BBB, CCC passed you this week!"
    assert "+more" not in result and "more" not in result


# ---------------------------------------------------------------------------
# One over cap: cap+1 triggers "+1 more"
# ---------------------------------------------------------------------------

def test_format_banner_one_over_cap_shows_plus_one_more():
    """cap+1 names -> first BANNER_NAME_CAP listed + '+1 more' suffix."""
    names = ["AAA", "BBB", "CCC", "DDD"]
    assert len(names) == BANNER_NAME_CAP + 1, "fixture must be exactly cap+1"
    result = _format_banner(names)
    assert result == "AAA, BBB, CCC +1 more passed you this week!"


# ---------------------------------------------------------------------------
# Two over cap: cap+2 triggers "+2 more"
# ---------------------------------------------------------------------------

def test_format_banner_two_over_cap_shows_plus_two_more():
    """cap+2 names -> first BANNER_NAME_CAP listed + '+2 more' suffix."""
    names = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    assert len(names) == BANNER_NAME_CAP + 2, "fixture must be exactly cap+2"
    result = _format_banner(names)
    assert result == "AAA, BBB, CCC +2 more passed you this week!"


# ---------------------------------------------------------------------------
# Overflow names are not visible in the output
# ---------------------------------------------------------------------------

def test_format_banner_overflow_names_not_in_output():
    """Names beyond the cap must not appear anywhere in the returned string."""
    names = ["AAA", "BBB", "CCC", "DDD", "EEE"]
    result = _format_banner(names)
    assert "DDD" not in result
    assert "EEE" not in result


# ---------------------------------------------------------------------------
# Return type is always str (when non-empty) or None
# ---------------------------------------------------------------------------

def test_format_banner_returns_str_for_nonempty():
    """Non-empty input always returns a str, never another falsy value."""
    result = _format_banner(["AAA"])
    assert isinstance(result, str)
