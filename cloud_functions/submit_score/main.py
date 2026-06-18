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
def _update_score(transaction, doc_ref, initials, score, machine_id):
    doc = doc_ref.get(transaction=transaction)
    if doc.exists and score <= doc.to_dict().get("score", 0):
        return False
    transaction.set(doc_ref, {
        "initials": initials,
        "score": score,
        "machine_id": machine_id,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    return True


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
    if not isinstance(score, int) or score < 0 or score > MAX_SCORE:
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
        doc_ref = db.collection("leaderboard").document(machine_id)
        transaction = db.transaction()
        is_new_best = _update_score(transaction, doc_ref, initials, score, machine_id)
        return ({"success": True, "is_new_best": is_new_best}, 200, headers)
    except Exception as e:
        print(f"Score submission failed: {e}")
        return ({"success": False, "error": "Internal error"}, 500, headers)
