"""Shared crypto + week-math helpers for the leaderboard Cloud Functions.

Stdlib only. This module is DUPLICATED byte-for-byte into both function dirs
(submit_score/ and get_leaderboard/) because Gen2 Cloud Functions deploy from
independent source directories -- a shared top-level module would not be packaged
into either function. Keep the two copies identical; tests guard against drift.

Two concerns live here:
- HMAC verification (COMP-01): the server recomputes the signature over the
  parsed, typed values and constant-time compares it to the client-supplied one.
- Week math (BOARD-01): Monday-UTC week buckets for the weekly leaderboard.

Contract lock: canonical_message's exact json.dumps kwargs (sort_keys=True,
separators=(",", ":"), ensure_ascii=False) are the wire format the Phase 5 client
MUST reproduce byte-for-byte. Do not change them.
"""
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone


def canonical_message(machine_id, initials, score):
    """Return the canonical signed payload as UTF-8 bytes.

    Option A canonical JSON (D-04): sorted keys, compact separators, no ASCII
    escaping. Keys sort to initials, machine_id, score; score stays an int so a
    client that stringifies it would produce a different (rejected) signature.
    """
    return json.dumps(
        {"machine_id": machine_id, "initials": initials, "score": score},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def verify_signature(machine_id, initials, score, provided_sig):
    """Return True iff provided_sig matches HMAC-SHA256 over canonical_message.

    The secret is read from os.environ AT CALL TIME (never a module-level
    constant) so it is never captured in source or import-time state. The
    expected digest is computed from the parsed/typed values, never from the
    raw HTTP body. Comparison is constant-time (hmac.compare_digest) to avoid a
    timing oracle; a missing signature compares against "" and fails.
    """
    secret = os.environ["LEADERBOARD_HMAC_SECRET"].encode("utf-8")
    expected = hmac.new(secret, canonical_message(machine_id, initials, score), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided_sig or "")


def current_week_id(now=None):
    """Return the Monday (YYYY-MM-DD, UTC) of the week containing `now`.

    `now` defaults to the current UTC instant (server time only -- D-06; never
    the deprecated naive datetime.utcnow(), never a naive local now()). The
    injectable param exists so tests pin a deterministic week.
    """
    now = now or datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return monday.strftime("%Y-%m-%d")


def previous_week_id(week_id):
    """Return the Monday-date string of the week 7 days before `week_id`."""
    monday = datetime.strptime(week_id, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (monday - timedelta(days=7)).strftime("%Y-%m-%d")
