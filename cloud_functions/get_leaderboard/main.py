import functions_framework
from firebase_admin import firestore, initialize_app
import firebase_admin

if not firebase_admin._apps:
    initialize_app()

db = firestore.client()


@functions_framework.http
def get_leaderboard(request):
    if request.method == "OPTIONS":
        return ("", 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    headers = {"Access-Control-Allow-Origin": "*"}

    try:
        query = (
            db.collection("leaderboard")
            .order_by("score", direction=firestore.Query.DESCENDING)
            .limit(10)
        )
        docs = query.stream()
        entries = []
        for d in docs:
            data = d.to_dict()
            entries.append({"initials": data["initials"], "score": data["score"]})
        return ({"entries": entries}, 200, headers)
    except Exception:
        return ({"entries": [], "error": "Failed to fetch leaderboard"}, 500, headers)
