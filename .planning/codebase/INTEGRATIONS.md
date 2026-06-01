---
type: codebase-map
focus: tech
doc: INTEGRATIONS
generated: 2026-06-01
last_mapped_commit: 5e8d4b1773c03b4d3953200a764d658a431911de
---

# External Integrations

The only external integration is the **online leaderboard**, implemented as two Google Cloud Functions backed by Firestore. The client reaches them over plain HTTP using the Python standard library. Everything else in the game is fully local/offline.

## Integration Map

```
PyGame client (api_service.py, urllib)
        │  HTTPS (JSON)
        ▼
Google Cloud Functions (2nd gen / Cloud Run, asia-southeast1)
   ├── submit_score   (POST)  ──┐
   └── get_leaderboard (GET)  ──┤  firebase-admin SDK
                                ▼
                       Firestore: collection "leaderboard"
                       (document id = machine_id)
```

## 1. Cloud Functions HTTP API

Defined in `cloud_functions/submit_score/main.py` and `cloud_functions/get_leaderboard/main.py`. Both use `@functions_framework.http` and handle CORS preflight.

### Endpoints (URLs in `settings.py`)

| Function | Method | URL constant | Purpose |
|----------|--------|--------------|---------|
| `submit_score` | `POST` | `API_SUBMIT_SCORE_URL` = `https://pacman-991339031546.asia-southeast1.run.app` | Upsert a machine's best score |
| `get_leaderboard` | `GET` | `API_LEADERBOARD_URL` = `https://get-leaderboard-991339031546.asia-southeast1.run.app` | Top 10 scores |

> Note: the `submit_score` deployment is named **`pacman`** (its URL host is `pacman-...`), not `submit-score`.

### Client (`api_service.py`)

`ApiService` wraps both calls with `urllib.request` and a **10-second timeout**. Both methods swallow all exceptions and return `None` on any failure (offline-tolerant):

```python
def submit_score(self, machine_id, initials, score):
    try:
        data = json.dumps({"machine_id": machine_id, "initials": initials, "score": score}).encode()
        req = Request(self.submit_score_url, data=data,
                      headers={"Content-Type": "application/json"}, method="POST")
        with urlopen(req, timeout=10) as resp:
            return json.loads(resp.read())
    except Exception:
        return None
```

`get_leaderboard()` returns the parsed `entries` list, or `None` on failure.

### Request / Response Contracts

**`submit_score` request body:**
```json
{ "machine_id": "<uuid>", "initials": "JAM", "score": 5000 }
```
**`submit_score` response (200):**
```json
{ "success": true, "is_new_best": true }
```
Error responses use `{ "success": false, "error": "<reason>" }` with status `400`/`500`.

**`get_leaderboard` response (200):**
```json
{ "entries": [ { "initials": "JAM", "score": 8000 }, ... ] }
```
(Up to 10 entries, ordered by score descending.)

### Server-side validation (`submit_score`)

- `machine_id` — required, non-empty.
- `initials` — must match `^[A-Z]{3}$`.
- `score` — must be `int`, `0 <= score <= 500_000` (`MAX_SCORE`).
- Best-score upsert via Firestore `@firestore.transactional` (`_update_score`): only overwrites if the new score beats the stored one.

### CORS / Auth

- **CORS:** `Access-Control-Allow-Origin: *` on all responses; explicit `OPTIONS` preflight handling (204).
- **Auth:** **None.** The endpoints are public and unauthenticated. There is no API key, token, or signature. Identity is the client-generated `machine_id` only. (See `CONCERNS.md` — scores are forgeable.)

## 2. Firestore (Cloud Firestore via firebase-admin)

- **Collection:** `leaderboard`.
- **Document id:** the player's `machine_id` (one document per machine → one best score per machine).
- **Document shape:** `{ initials, score, machine_id, updated_at: SERVER_TIMESTAMP }`.
- **Reads:** `get_leaderboard` queries `order_by("score", DESCENDING).limit(10)`.
- **Init:** `initialize_app()` with **no explicit credentials** — relies on Application Default Credentials in the Cloud Functions runtime (the local `firebase-key.json` is for out-of-band/admin use, not referenced in code).

## 3. Identity & Local Persistence (not a remote integration)

`local_storage.py` manages two local files via `paths.data_path()`:
- `machine_id.txt` — a `uuid.uuid4()` generated once, then reused. This is the de-facto leaderboard identity.
- `player_data.json` — `{"initials": "JAP"}`. Initials are set once on first launch and are permanent (no change-initials flow is wired into `main.py`).

Both files are git-ignored and machine-local.

## Integrations NOT present

- No database client in the game client (all DB access is server-side).
- No auth provider (Firebase Auth, OAuth, etc.).
- No webhooks, message queues, analytics, telemetry, crash reporting, or payment integrations.
- No `requests`/`httpx` — HTTP is stdlib `urllib` only.
