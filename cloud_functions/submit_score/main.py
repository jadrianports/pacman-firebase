import functions_framework
from firebase_admin import firestore, initialize_app
import firebase_admin
import os
import re

# leaderboard_crypto is the Plan 04-01 helper, duplicated byte-identical into this
# Gen2 function dir. At deploy time the function dir IS the import root, so the bare
# `import leaderboard_crypto` works; under the test harness this module is imported as
# the package `cloud_functions.submit_score.main`, so fall back to the relative import.
try:
    import leaderboard_crypto
except ModuleNotFoundError:  # pragma: no cover - exercised only under the test harness
    from . import leaderboard_crypto

if not firebase_admin._apps:
    initialize_app()

db = firestore.client()

MAX_SCORE = 50_000


@firestore.transactional
def _update_score(transaction, all_time_ref, weekly_ref, stale_weekly_ref,
                  initials, score, machine_id, week_id):
    """Combined all-time + weekly read-modify-write + lazy prune in ONE transaction.

    INVARIANT: all .get() calls precede all .set()/.delete() calls — Firestore
    transactions require reads before writes; MagicMock tests do NOT catch a
    violation, so verify this ordering by eye. The three phases below are kept
    explicit (READS, then DECIDE, then WRITES/DELETES) to make that reviewable.

    Returns is_new_best with ALL-TIME semantics (RESEARCH Pitfall 5) — the weekly
    best is computed independently and never leaks into the response.
    """
    # --- (1) READS: every .get() happens here, before any write/delete ---
    all_time_snap = all_time_ref.get(transaction=transaction)
    weekly_snap = weekly_ref.get(transaction=transaction)

    # --- (2) DECIDE: pure computation, no Firestore mutation ---
    if all_time_snap.exists:
        stored_all = all_time_snap.to_dict()
        all_time_best = score > stored_all.get("score", 0)
        # D-05: keep the originally-locked initials; the .get(..., initials) fallback
        # keeps the existing test_is_new_best_* stubs (which omit initials) green.
        locked_initials = stored_all.get("initials", initials)
    else:
        all_time_best = True
        locked_initials = initials  # first submission locks the initials

    if weekly_snap.exists:
        weekly_best = score > weekly_snap.to_dict().get("score", 0)
    else:
        weekly_best = True

    # --- (3) WRITES / DELETES: nothing above this line may .set()/.delete() ---
    if all_time_best:
        transaction.set(all_time_ref, {
            "initials": locked_initials,  # D-05: NOT the new submission's initials
            "score": score,
            "machine_id": machine_id,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })

    if weekly_best:
        # D-06..D-08: one best row per machine per week; week_id is server-time only
        # and stored as a field for the Plan 03 composite-index query.
        transaction.set(weekly_ref, {
            "initials": locked_initials,  # weekly board shows the locked tag too
            "score": score,
            "machine_id": machine_id,
            "week_id": week_id,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })

    # D-09 / A4: lazy prune the week-two-back doc. A delete of a non-existent doc is a
    # harmless Firestore no-op, so no prior read is needed — issued in the WRITES phase.
    transaction.delete(stale_weekly_ref)

    return all_time_best


@functions_framework.http
def submit_score(request):
    if request.method == "OPTIONS":
        return ("", 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    headers = {"Access-Control-Allow-Origin": "*"}

    data = request.get_json(silent=True)
    if not data:
        return ({"success": False, "error": "Invalid JSON"}, 400, headers)

    machine_id = data.get("machine_id", "")
    initials = data.get("initials", "")
    score = data.get("score", 0)

    if not machine_id:
        return ({"success": False, "error": "Missing machine_id"}, 400, headers)
    if not re.match(r"^[A-Z]{3}$", initials):
        return ({"success": False, "error": "Invalid initials"}, 400, headers)
    # bool subclasses int, so reject it explicitly (WR-01): `"score": true` must
    # not slip through isinstance(score, int) and be stored as a 1-point score.
    if isinstance(score, bool) or not isinstance(score, int) or score < 0 or score > MAX_SCORE:
        return ({"success": False, "error": "Invalid score"}, 400, headers)

    # D-02/D-03 HMAC grace-period gate (COMP-01). Runs AFTER the 400 validators so
    # malformed input still 400s before any signature logic. The flag is read at CALL
    # TIME (never a module constant) so tests can flip it and so it tracks Console config.
    # Grace matrix (RESEARCH § Grace-Period Logic):
    #   absent  + grace off -> accept (log)
    #   absent  + require on -> reject 401
    #   present + invalid    -> reject 401 (ALWAYS, even in grace)
    #   present + valid      -> accept
    # The canonical message is recomputed by the helper from the parsed typed values,
    # never from the raw request body (RESEARCH Pitfall 3).
    signature = data.get("signature")
    require_sig = os.environ.get("REQUIRE_SIGNATURE", "false").lower() == "true"
    if signature is None:
        if require_sig:
            return ({"success": False, "error": "Signature required"}, 401, headers)
        # Grace accept: log without leaking the secret or the full machine_id (V7).
        print(f"unsigned submission accepted (grace period) mid={machine_id[:3]}***")
    elif not leaderboard_crypto.verify_signature(machine_id, initials, score, signature):
        return ({"success": False, "error": "Invalid signature"}, 401, headers)

    try:
        # week_id is computed from server time only (D-06) — never a client timestamp.
        week_id = leaderboard_crypto.current_week_id()
        stale_week = leaderboard_crypto.previous_week_id(
            leaderboard_crypto.previous_week_id(week_id)
        )  # two weeks back: keep-set is {current, last week} (D-09)

        all_time_ref = db.collection("leaderboard").document(machine_id)
        weekly_ref = db.collection("weekly").document(f"{machine_id}_{week_id}")
        stale_weekly_ref = db.collection("weekly").document(f"{machine_id}_{stale_week}")

        transaction = db.transaction()
        is_new_best = _update_score(
            transaction, all_time_ref, weekly_ref, stale_weekly_ref,
            initials, score, machine_id, week_id,
        )
        return ({"success": True, "is_new_best": is_new_best}, 200, headers)
    except Exception as e:
        print(f"Score submission failed: {e}")
        return ({"success": False, "error": "Internal error"}, 500, headers)
