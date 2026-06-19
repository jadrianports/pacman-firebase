"""Tests for the Phase 6 unsigned last-viewed marker IO (D-13).

The marker is the deliberate INVERSE of the Phase-5 signed identity blob: plain
JSON, no obfuscation, no HMAC, best-effort. A missing/corrupt/wrong-week marker is
harmless and silently re-baselines. It holds the player's tracked this-week best and
the set of initials above them at last board view, stamped with a client-computed
Monday-UTC ``week_id``.

These tests cover: cold-start (absent file -> None), malformed JSON -> None,
same-week round-trip, stale-week silent re-baseline (-> None), write-never-raises,
and client/server week-id parity.
"""
import json
import os
from datetime import datetime, timezone

import pytest

import marker
import paths


@pytest.fixture
def tmp_marker_dir(tmp_path, monkeypatch):
    """Point the marker storage at an isolated tmp dir.

    paths.user_data_dir() resolves under %LOCALAPPDATA%/PacMan, so setting
    LOCALAPPDATA to tmp_path redirects the marker file into the test sandbox.
    """
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    return tmp_path


# --- client_current_week_id ------------------------------------------------------

def test_client_current_week_id_is_a_monday():
    """For the live UTC instant the returned date parses to a Monday (weekday 0)."""
    result = marker.client_current_week_id()
    assert datetime.strptime(result, "%Y-%m-%d").weekday() == 0


def test_client_current_week_id_matches_server():
    """Client week math must agree with the server's Monday-UTC math for a pinned instant."""
    import cloud_functions.get_leaderboard.leaderboard_crypto as server
    pinned = datetime(2026, 6, 17, 12, 30, tzinfo=timezone.utc)  # a Wednesday
    assert marker.client_current_week_id(pinned) == server.current_week_id(pinned)


def test_client_current_week_id_injectable_now():
    """Passing an explicit instant pins a deterministic week (Mon 2026-06-15)."""
    wednesday = datetime(2026, 6, 17, tzinfo=timezone.utc)
    assert marker.client_current_week_id(wednesday) == "2026-06-15"


# --- read_marker: cold start / corruption ----------------------------------------

def test_read_marker_absent_returns_none(tmp_marker_dir):
    """Cold start: no marker file on disk -> None, never raises."""
    assert marker.read_marker() is None


def test_read_marker_malformed_json_returns_none(tmp_marker_dir):
    """Garbage bytes in the marker file -> None, never raises."""
    path = paths.user_data_path(marker.settings.MARKER_FILE_NAME)
    with open(path, "wb") as f:
        f.write(b"\x00\x01not json at all{{{")
    assert marker.read_marker() is None


# --- round-trip ------------------------------------------------------------------

def test_write_then_read_round_trips_same_week(tmp_marker_dir):
    """write_marker then read_marker returns the stored dict when the week matches."""
    week = marker.client_current_week_id()
    marker.write_marker(week, 12345, {"BBB", "AAA", "CCC"})
    loaded = marker.read_marker()
    assert loaded is not None
    assert loaded["week_id"] == week
    assert loaded["tracked_best"] == 12345
    # initials_above persisted as a sorted JSON list (deterministic, D-12).
    assert loaded["initials_above"] == ["AAA", "BBB", "CCC"]


def test_write_marker_persists_plain_unsigned_json(tmp_marker_dir):
    """On disk the marker is plain JSON with exactly the three keys — no sig envelope."""
    week = marker.client_current_week_id()
    marker.write_marker(week, 999, {"ZZZ"})
    path = paths.user_data_path(marker.settings.MARKER_FILE_NAME)
    with open(path, "r") as f:
        raw = json.load(f)
    assert set(raw.keys()) == {"week_id", "tracked_best", "initials_above"}
    assert "sig" not in raw and "blob" not in raw


# --- stale week -> silent re-baseline ---------------------------------------------

def test_read_marker_stale_week_returns_none(tmp_marker_dir):
    """A marker stamped with a different week_id is discarded (silent re-baseline)."""
    marker.write_marker("1999-01-04", 50, {"AAA"})  # a Monday, but long past
    assert marker.read_marker() is None


# --- write never raises ----------------------------------------------------------

def test_write_marker_never_raises_on_dump_failure(tmp_marker_dir, monkeypatch):
    """If json.dump blows up, write_marker swallows and returns — never propagates."""
    def boom(*args, **kwargs):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(marker.json, "dump", boom)
    # Must not raise.
    marker.write_marker("2026-06-15", 1, {"AAA"})


def test_write_marker_never_raises_on_open_failure(tmp_marker_dir, monkeypatch):
    """If open() fails (e.g. read-only dir), write_marker swallows and returns."""
    def boom(*args, **kwargs):
        raise OSError("read-only filesystem")

    monkeypatch.setattr("builtins.open", boom)
    marker.write_marker("2026-06-15", 1, {"AAA"})


# --- no signing/obfuscation on the marker ----------------------------------------

def test_marker_module_has_no_signing_imports():
    """The marker is unsigned by design — it must not import the identity signing seam."""
    src = open(marker.__file__).read()
    assert "obfuscate" not in src
    assert "sign_identity_blob" not in src
    assert "sign_submission" not in src
    assert "hmac" not in src
