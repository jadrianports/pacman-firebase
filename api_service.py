import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request


class ApiService:
    def __init__(self, submit_score_url, leaderboard_url):
        self.submit_score_url = submit_score_url.rstrip("/")
        self.leaderboard_url = leaderboard_url.rstrip("/")

    def submit_score(self, machine_id, initials, score, signature=None, timeout=10):
        try:
            data = json.dumps({
                "machine_id": machine_id,
                "initials": initials,
                "score": score,
                "signature": signature,
            }).encode()
            req = Request(
                self.submit_score_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read())
        except Exception:
            return None

    def get_leaderboard(self, scope=None, timeout=10):
        try:
            url = self.leaderboard_url
            if scope:
                url += f"?{urlencode({'scope': scope})}"
            req = Request(url, method="GET")
            with urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read())
                return data.get("entries")
        except Exception:
            return None
