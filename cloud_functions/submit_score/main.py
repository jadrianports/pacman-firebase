import functions_framework
from firebase_admin import firestore, initialize_app
import firebase_admin
import re

if not firebase_admin._apps:
    initialize_app()

db = firestore.client()

MAX_SCORE = 500_000


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

    try:
        doc_ref = db.collection("leaderboard").document(machine_id)
        transaction = db.transaction()
        is_new_best = _update_score(transaction, doc_ref, initials, score, machine_id)
        return ({"success": True, "is_new_best": is_new_best}, 200, headers)
    except Exception as e:
        print(f"Score submission failed: {e}")
        return ({"success": False, "error": "Internal error"}, 500, headers)
