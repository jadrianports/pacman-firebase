"""Unsigned best-effort last-viewed marker IO (Phase 6, D-13).

The marker is the deliberate INVERSE of the Phase-5 signed identity blob: plain
JSON, no obfuscation, no HMAC, best-effort. It records the player's tracked
this-week best and the set of initials above them at last board view, stamped with a
client-computed Monday-UTC ``week_id``. Plan 04's launch banner / board-open baseline
consumes it to compute "who passed you since you last looked" (RIVAL-01).

Design contract:
  * A missing, corrupt, or wrong-week marker is HARMLESS — read_marker returns None
    and the caller treats it as a cold start (silent re-baseline).
  * No read or write ever raises into the caller: every IO path is wrapped in
    try/except and swallows, mirroring local_storage._safe_remove's best-effort tone.
  * The marker is NOT signed or obfuscated (D-13). Do not mirror the identity-blob
    signing path here — tamper-proofing it would be security theater (a wrong banner
    is cosmetic and controls no score or server state).

The client has no server ``current_week_id`` (root leaderboard_crypto.py lacks it), so
the Monday-UTC week stamp is computed inline here, mirroring the server's math in
cloud_functions/get_leaderboard/leaderboard_crypto.current_week_id().
"""
import json
from datetime import datetime, timedelta, timezone

import paths
import settings


def client_current_week_id(now=None):
    """Return the Monday (YYYY-MM-DD, UTC) of the week containing ``now``.

    Mirrors the server's ``current_week_id`` (Monday-UTC math) so the client week
    stamp agrees with week-bucketed server scores. ``now`` defaults to the current
    UTC instant; the injectable param exists so tests pin a deterministic week.
    """
    now = now or datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return monday.strftime("%Y-%m-%d")


def write_marker(week_id, tracked_best, initials_above):
    """Persist the unsigned last-viewed marker, best-effort (never raises).

    Writes plain JSON ``{"week_id", "tracked_best", "initials_above"}`` to the marker
    file under %LOCALAPPDATA%\\PacMan\\. ``initials_above`` is a set in memory and is
    serialized as a sorted list for deterministic output (D-12). NO obfuscation, NO
    HMAC, NO {"sig","blob"} envelope — plain JSON only (D-13). Any failure (read-only
    dir, serialization error) is swallowed silently; a failed marker write is harmless.
    """
    try:
        path = paths.user_data_path(settings.MARKER_FILE_NAME)
        with open(path, "w") as f:
            json.dump(
                {
                    "week_id": week_id,
                    "tracked_best": tracked_best,
                    "initials_above": sorted(initials_above),
                },
                f,
            )
    except Exception:
        pass  # best-effort: a failed marker write must never affect gameplay


def read_marker():
    """Load the last-viewed marker, or None on cold start / corruption / stale week.

    Returns the marker dict (``initials_above`` as a list — callers wrap in set(...))
    only when the file exists, parses, and its ``week_id`` matches the current client
    week. Otherwise returns None: a missing file (cold start), malformed JSON, any IO
    error, or a stale week_id (week rollover -> silent re-baseline, D-11/D-13). Never
    raises.
    """
    try:
        path = paths.user_data_path(settings.MARKER_FILE_NAME)
        with open(path, "r") as f:
            data = json.load(f)
    except Exception:
        return None  # cold start / corrupt / unreadable -> re-baseline

    if data.get("week_id") != client_current_week_id():
        return None  # stale week -> silent re-baseline on rollover
    return data
