"""Unit tests for the shared leaderboard_crypto helper (Phase 4 Plan 01).

Covers the four pure functions both Cloud Functions consume:
- canonical_message  -- the exact byte serialization the Phase 5 client must reproduce
- verify_signature   -- HMAC-SHA256 verification (constant-time, machine_id-bound)
- current_week_id    -- Monday-UTC week bucket
- previous_week_id   -- the week 7 days prior

Env note: tests/conftest.py does NOT patch environment variables, so signature
tests set LEADERBOARD_HMAC_SECRET via monkeypatch.setenv.
"""
import hashlib
import hmac
import json
from datetime import datetime, timezone

# Helper under test lives in the submit_score function dir (canonical copy).
from cloud_functions.submit_score.leaderboard_crypto import (
    canonical_message,
    current_week_id,
    previous_week_id,
    verify_signature,
)

TEST_SECRET = "test-key"


def _sign(machine_id, initials, score, secret=TEST_SECRET):
    """Recompute the expected HMAC hexdigest the same way the helper does, so
    the valid-signature assertion is self-consistent (no hardcoded digest)."""
    msg = json.dumps(
        {"machine_id": machine_id, "initials": initials, "score": score},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


# --- canonical_message -------------------------------------------------------

def test_canonical_message_exact_bytes():
    # sorted keys -> initials, machine_id, score; score stays an int (not "5000")
    expected = b'{"initials":"BOB","machine_id":"m1","score":5000}'
    assert canonical_message("m1", "BOB", 5000) == expected


def test_canonical_message_returns_bytes():
    assert isinstance(canonical_message("m1", "BOB", 5000), bytes)


# --- verify_signature --------------------------------------------------------

def test_verify_signature_valid(monkeypatch):
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", TEST_SECRET)
    sig = _sign("m1", "BOB", 5000)
    assert verify_signature("m1", "BOB", 5000, sig) is True


def test_verify_signature_wrong_sig(monkeypatch):
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", TEST_SECRET)
    assert verify_signature("m1", "BOB", 5000, "deadbeef") is False


def test_verify_signature_missing_sig(monkeypatch):
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", TEST_SECRET)
    assert verify_signature("m1", "BOB", 5000, None) is False


def test_verify_signature_lifted_to_other_machine(monkeypatch):
    # D-03 machine_id binding: a sig valid for m1 must NOT verify for m2.
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", TEST_SECRET)
    sig_for_m1 = _sign("m1", "BOB", 5000)
    assert verify_signature("m2", "BOB", 5000, sig_for_m1) is False


# --- current_week_id ---------------------------------------------------------

def test_current_week_id_monday_start():
    # Monday 00:00:00 UTC -> that Monday's own date.
    now = datetime(2026, 6, 8, 0, 0, 0, tzinfo=timezone.utc)
    assert current_week_id(now) == "2026-06-08"


def test_current_week_id_sunday_end():
    # Sunday 23:59:59 UTC -> the prior Monday (week has not rolled yet).
    now = datetime(2026, 6, 7, 23, 59, 59, tzinfo=timezone.utc)
    assert current_week_id(now) == "2026-06-01"


def test_current_week_id_just_after_monday_start():
    # Monday 00:00:01 UTC -> new week's Monday.
    now = datetime(2026, 6, 8, 0, 0, 1, tzinfo=timezone.utc)
    assert current_week_id(now) == "2026-06-08"


# --- previous_week_id --------------------------------------------------------

def test_previous_week_id():
    assert previous_week_id("2026-06-08") == "2026-06-01"


# --- drift guard: both function-dir copies are byte-identical -----------------

def test_function_dir_copies_are_byte_identical():
    import os

    repo_root = os.path.dirname(os.path.dirname(__file__))
    submit_copy = os.path.join(
        repo_root, "cloud_functions", "submit_score", "leaderboard_crypto.py"
    )
    leaderboard_copy = os.path.join(
        repo_root, "cloud_functions", "get_leaderboard", "leaderboard_crypto.py"
    )
    with open(submit_copy, "rb") as fh:
        submit_bytes = fh.read()
    with open(leaderboard_copy, "rb") as fh:
        leaderboard_bytes = fh.read()
    assert submit_bytes == leaderboard_bytes
