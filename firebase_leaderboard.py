import requests

# --------------------------------------------------------------
# CONFIGURATION
# --------------------------------------------------------------

# ⚠️ Replace this with your actual Render server URL:
SERVER_URL = "https://your-server-name.onrender.com"

# Optional: A shared secret key for basic protection.
# - Set this to the same SECRET_KEY you define in server.py
# - OR leave it empty ("") to disable authorization
SECRET_KEY = ""


# --------------------------------------------------------------
# INTERNAL HELPERS
# --------------------------------------------------------------

def _headers():
    """Return headers for all requests."""
    if SECRET_KEY:
        return {"Authorization": SECRET_KEY, "Content-Type": "application/json"}
    else:
        return {"Content-Type": "application/json"}


# --------------------------------------------------------------
# PUBLIC FUNCTIONS
# --------------------------------------------------------------

def submit_score(name, score):
    """
    Submit a player's score to the leaderboard.
    Automatically updates only if score is higher.
    """
    url = f"{SERVER_URL}/submit_score"

    data = {
        "name": name,
        "score": score
    }

    try:
        response = requests.post(url, json=data, headers=_headers(), timeout=5)
        response.raise_for_status()
        return response.json()  # returns top 10 leaderboard
    except requests.exceptions.RequestException as e:
        print(f"[Leaderboard Error] Could not submit score: {e}")
        return None


def get_leaderboard(limit=50):
    """
    Fetch the global top 10 leaderboard.
    """
    url = f"{SERVER_URL}/get_leaderboard"

    try:
        response = requests.get(url, headers=_headers(), timeout=5)
        response.raise_for_status()
        data = response.json() or {}  # list of (name, score)
        sorted_leaderboard = sorted(data.items(), key = lambda x: x[1], reverse=True)
        return sorted_leaderboard[:limit]

    except requests.exceptions.RequestException as e:
        print(f"[Leaderboard Error] Could not fetch leaderboard: {e}")
        return None
