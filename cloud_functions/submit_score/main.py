import functions_framework
from firebase_admin import firestore, initialize_app
import firebase_admin
import re

if not firebase_admin._apps:
    initialize_app()

db = firestore.client()


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
    if not isinstance(score, int) or score < 0:
        return ({"success": False, "error": "Invalid score"}, 400, headers)

    doc_ref = db.collection("leaderboard").document(machine_id)
    doc = doc_ref.get()

    if doc.exists:
        existing_score = doc.to_dict().get("score", 0)
        if score <= existing_score:
            return ({"success": True, "is_new_best": False}, 200, headers)

    doc_ref.set({
        "initials": initials,
        "score": score,
        "machine_id": machine_id,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    return ({"success": True, "is_new_best": True}, 200, headers)
