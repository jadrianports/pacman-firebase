import json
from urllib.request import urlopen, Request


class ApiService:
    def __init__(self, submit_score_url, leaderboard_url):
        self.submit_score_url = submit_score_url.rstrip("/")
        self.leaderboard_url = leaderboard_url.rstrip("/")

    def submit_score(self, machine_id, initials, score):
        try:
            data = json.dumps({
                "machine_id": machine_id,
                "initials": initials,
                "score": score,
            }).encode()
            req = Request(
                self.submit_score_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=10) as resp:
                return json.loads(resp.read())
        except Exception:
            return None

    def get_leaderboard(self):
        try:
            req = Request(self.leaderboard_url, method="GET")
            with urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read())
                return data.get("entries")
        except Exception:
            return None
