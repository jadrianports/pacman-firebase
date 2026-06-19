import functions_framework
from firebase_admin import firestore, initialize_app
import firebase_admin

# leaderboard_crypto is the Plan 04-01 helper, duplicated byte-identical into this
# Gen2 function dir. At deploy time the function dir IS the import root and this module
# is loaded as a top-level module (__package__ == ""), so the bare
# `import leaderboard_crypto` resolves the co-located copy. Under the test harness this
# module is imported as the package `cloud_functions.get_leaderboard.main`, so prefer the
# package-relative import — that pins the co-located server copy even when an unrelated
# top-level `leaderboard_crypto` (e.g. the Phase 5 CLIENT copy at the repo root) shadows
# the bare name on sys.path.
if __package__:
    from . import leaderboard_crypto
else:  # pragma: no cover - exercised only at deploy time (function dir is the import root)
    import leaderboard_crypto

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

    # BOARD-02 / D-08: scope-aware read. Parse tolerantly — a reader is never 400'd
    # (T-04-12). Default + any unknown value falls back to "week" (confirmed decision:
    # default week; the shipped v1.0 exe shows the weekly board on redeploy, accepted).
    scope = (request.args.get("scope") or "week").lower()
    if scope not in ("week", "all", "last_week"):
        scope = "week"

    try:
        if scope == "all":
            # All-time path (D-08 retained, unchanged).
            query = (
                db.collection("leaderboard")
                .order_by("score", direction=firestore.Query.DESCENDING)
                .limit(10)
            )
        elif scope == "last_week":
            # BOARD-04 / D-01: last week's champ. Same weekly chain as the current-week
            # branch, but pinned to previous_week_id(current_week_id()) — both computed
            # from server time only (D-06), so the client can never request a forged
            # week. Reuses the existing `week_id ASC, score DESC` composite index.
            query = (
                db.collection("weekly")
                .where(
                    "week_id",
                    "==",
                    leaderboard_crypto.previous_week_id(
                        leaderboard_crypto.current_week_id()
                    ),
                )
                .order_by("score", direction=firestore.Query.DESCENDING)
                .limit(10)
            )
        else:
            # Weekly path: filter to the current server-time week (BOARD-01 read half).
            # week_id comes from current_week_id() only (D-06 / T-04-08) — never a client
            # value, so nobody can request a forged week. This equality+order query needs
            # the composite index `week_id ASC, score DESC`, created manually in Plan 04.
            query = (
                db.collection("weekly")
                .where("week_id", "==", leaderboard_crypto.current_week_id())
                .order_by("score", direction=firestore.Query.DESCENDING)
                .limit(10)
            )
        docs = query.stream()
        entries = []
        for d in docs:
            data = d.to_dict()
            # D-10 / T-04-11: only initials+score ship on BOTH scopes — machine_id,
            # week_id, and updated_at never leave the server.
            # Skip partial/legacy/schema-drift docs missing a projected field rather
            # than letting one malformed doc KeyError and 500 the whole board (WR-02).
            initials = data.get("initials")
            score = data.get("score")
            if initials is None or score is None:
                continue
            entries.append({"initials": initials, "score": score})
        return ({"entries": entries}, 200, headers)
    except Exception as e:
        print(f"Leaderboard fetch failed: {e}")
        return ({"entries": [], "error": "Failed to fetch leaderboard"}, 500, headers)
