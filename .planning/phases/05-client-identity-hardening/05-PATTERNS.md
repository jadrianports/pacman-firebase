# Phase 5: Client Identity Hardening - Pattern Map

**Mapped:** 2026-06-19
**Files analyzed:** 9 (6 modify, 2 create-or-modify tests, 1 new module)
**Analogs found:** 9 / 9 (every file has a real in-repo analog — no external pattern needed)

> Stdlib-only constraint applies to all client code: `hashlib`, `hmac`, `json`, `base64`, `os`, `sys`, `uuid` only. No new client runtime deps (api_service already proves the `urllib` stdlib pattern).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `leaderboard_crypto.py` (client, NEW) | utility/crypto | transform | `cloud_functions/submit_score/leaderboard_crypto.py` | exact (byte-for-byte oracle) |
| `local_storage.py` (MODIFY) | store | file-I/O / CRUD | itself (current `get_machine_id`/`get_initials`/`save_initials`) + client crypto module | exact (self-rework) |
| `paths.py` (MODIFY) | utility/config | file-I/O | `paths.py:5-11` `resource_path` (frozen-vs-dev branch) | exact (same-file analog) |
| `api_service.py` (MODIFY) | service | request-response | `api_service.py:10-26` `submit_score` (itself) | exact (self-extend) |
| `main.py` (MODIFY) | controller/wiring | event-driven | `main.py:15-49` (itself: load → submit → game-over) | exact (self-extend) |
| `build.py` (MODIFY) | config/build | batch | `build.py:1-10` + `.gitignore` precedent | role-match |
| `settings.py` (MODIFY) | config | (constants) | `settings.py:75-77` API URL constants | exact |
| `tests/test_leaderboard_crypto.py` (server REF / new client test) | test | transform | `tests/test_leaderboard_crypto.py` (the oracle harness) | exact |
| `tests/test_api_service.py` + `tests/test_local_storage.py` (MODIFY) | test | request-response / file-I/O | both files (mock+tmp_path patterns) | exact |

---

## Pattern Assignments

### `leaderboard_crypto.py` — NEW client module (utility/crypto, transform)

**Analog AND test oracle:** `cloud_functions/submit_score/leaderboard_crypto.py`. The client MUST reproduce `canonical_message` byte-for-byte (D-07). Copy these two functions verbatim into the client module (drop the week-math helpers — client needs only signing).

**Canonical message — reproduce EXACTLY** (`cloud_functions/submit_score/leaderboard_crypto.py:24-36`):
```python
def canonical_message(machine_id, initials, score):
    return json.dumps(
        {"machine_id": machine_id, "initials": initials, "score": score},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
```
Locked kwargs: `sort_keys=True`, `separators=(",", ":")`, `ensure_ascii=False`, `.encode("utf-8")`. `score` stays an **int** — stringifying it produces a rejected signature. Verified wire bytes (from `tests/test_leaderboard_crypto.py:44`): `b'{"initials":"BOB","machine_id":"m1","score":5000}'`.

**Sign function — client mirror of the verifier** (`leaderboard_crypto.py:57-59` shows the exact HMAC construction to mirror):
```python
expected = hmac.new(
    secret.encode("utf-8"), canonical_message(machine_id, initials, score), hashlib.sha256
).hexdigest()
```
Client `sign_submission(machine_id, initials, score, secret)` returns this `expected` hexdigest. Send it as the **`"signature"`** body field (server reads `data.get("signature")` at `cloud_functions/submit_score/main.py:122`).

**File-integrity HMAC (D-08) — same secret, domain-separated.** Reuse the same `hmac.new(secret, msg, hashlib.sha256)` shape but prefix the message (Claude's discretion, e.g. `b"identity-file-v1:" + blob_bytes`) so a file sig and a submission sig are not interchangeable. Keep a second helper (`sign_identity_blob` / `verify_identity_blob`) using `hmac.compare_digest` for the tamper check — mirror the verifier's constant-time compare (`leaderboard_crypto.py:60-63`):
```python
try:
    return hmac.compare_digest(expected, provided_sig)
except TypeError:
    return False
```

---

### `local_storage.py` (MODIFY) — store, file-I/O / CRUD

**Current API surface to preserve/wrap** (so `main.py` call sites change minimally — `local_storage.py:11-34`):
```python
def get_machine_id(path=MACHINE_ID_FILE): ...   # plaintext UUID in machine_id.txt
def get_initials(path=PLAYER_DATA_FILE): ...     # reads {"initials": ...} from player_data.json
def save_initials(initials, path=PLAYER_DATA_FILE): ...
```

**Current read/mint/write idioms to carry forward** (`local_storage.py:11-18`):
```python
if os.path.exists(path):
    with open(path, "r") as f:
        return f.read().strip()
machine_id = str(uuid.uuid4())
with open(path, "w") as f:
    f.write(machine_id)
return machine_id
```

**Defensive-read pattern already used** (`local_storage.py:24-29`) — extend its `except` to the D-05 invalid-file branch:
```python
try:
    with open(path, "r") as f:
        data = json.load(f)
    return data.get("initials")
except (json.JSONDecodeError, KeyError):
    return None
```

**Rework per decisions:**
- D-02: collapse the two files into one obfuscated, HMAC-signed `identity.dat` holding `{machine_id, initials}` under one signature (use the new crypto module's `sign_identity_blob`).
- D-10: obfuscate the blob (base64-over-XOR or similar stdlib-only reversible scheme) so it is not human-readable/hand-editable.
- D-05: a present-but-invalid file (won't decode OR HMAC mismatch) returns a "tampered/invalid" sentinel that blocks submit — do NOT auto-regenerate. A missing file mints fresh (D-04).
- D-04: migrate-then-remove — read legacy `machine_id.txt`/`player_data.json` (via the OLD `data_path` next-to-exe), write+verify-read the new blob in the LOCALAPPDATA dir, then delete the legacy files. The `^[A-Z]{3}$` validity check on legacy initials is Claude's discretion (invalid → treat as not-yet-set, prompt).
- Path source switches from `data_path(...)` to the new per-user resolver (see `paths.py` below).

---

### `paths.py` (MODIFY) — utility/config, file-I/O

**Analog: `resource_path` frozen-vs-dev branch** (`paths.py:5-11`) and `data_path` (`paths.py:14-20`):
```python
def data_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
```

**New per-user resolver (D-01)** — slot a sibling function in using the same `getattr(sys,'frozen',...)` idiom. Target `%LOCALAPPDATA%\PacMan\` on Windows (`os.environ["LOCALAPPDATA"]`), folder name exactly `PacMan`; non-Windows dev fallback (Claude's discretion, e.g. `~/.pacman` via `os.path.expanduser`). Create the dir if missing (`os.makedirs(..., exist_ok=True)`). Keep `data_path` intact — `local_storage`'s migration still needs the legacy next-to-exe path to find and delete old files. `resource_path` is unaffected.

---

### `api_service.py` (MODIFY) — service, request-response

**Analog: itself** (`api_service.py:10-26`):
```python
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
```

**Change (D-07):** accept a `signature` argument and add it to the body dict, e.g. `{..., "score": score, "signature": signature}`. Keep `score` an int in the body (the signature was computed over the int). Preserve the `try/except Exception: return None` graceful-degrade — stays no-new-deps (stdlib `urllib` only). Caller (`main.py`) computes the signature via the client crypto module and passes it in.

---

### `main.py` (MODIFY) — controller/wiring, event-driven

**Analog: itself** — startup wiring (`main.py:15-24`):
```python
api = ApiService(API_SUBMIT_SCORE_URL, API_LEADERBOARD_URL)
machine_id = get_machine_id()

if get_initials() is None:
    initials = run_initials_entry(screen, timer)
    if initials is None:
        pygame.quit(); return
    save_initials(initials)
```
**Post-run submit + game-over seam** (`main.py:44-49`):
```python
response = api.submit_score(machine_id, initials, score)
is_new_best = response is not None and response.get("is_new_best", False)
action = run_game_over_screen(screen, timer, score, is_new_best, game_won)
```

**Changes:**
- D-04 migration runs at startup before the initials check (call the new `local_storage` load/migrate entry point).
- D-05 gate: when identity is tampered/invalid, skip `api.submit_score` and pass a flag into the game-over screen instead.
- D-07: compute the signature (client crypto module + embedded secret) and pass it through `api.submit_score(machine_id, initials, score, signature)`.
- D-06: render the notice through `run_game_over_screen` (new param, see below).

---

### `run_game_over_screen` notice — D-06 (in `menu.py`, the new-best-feedback seam)

**Analog: the NEW BEST block** (`menu.py:197-201`) — the D-06 notice is a sibling render branch at the same seam:
```python
if is_new_best:
    best_text = score_font.render("NEW BEST!", True, COLOR_YELLOW)
    best_rect = best_text.get_rect(center=(WIDTH // 2, 480))
    screen.blit(best_text, best_rect)
```
**Graceful-degrade wording precedent** (`menu.py:138-142`): `"Could not connect to leaderboard."` in `COLOR_GRAY`. Mirror that tone — render a small gray line like `"Score not saved — identity error"` when an `identity_error`/`not_saved` flag is passed into `run_game_over_screen`. Add the param to the signature at `menu.py:174`. Not a modal, not a menu line.

---

### `build.py` (MODIFY) — config/build, batch

**Analog: current PyInstaller invocation** (`build.py:1-10`):
```python
import PyInstaller.__main__
PyInstaller.__main__.run([
    "main.py", "--name=pacman", "--onedir", "--windowed",
    "--add-data=assets;assets",
    "--add-data=freesansbold.ttf;.",
])
```
**Change (D-09):** before the PyInstaller call, read the gitignored secret file (e.g. `hmac_secret.local`) and bake it into the bundle non-literally (D-10: byte-array / XOR'd / split-and-reassembled — never a committed literal). Mechanism is Claude's discretion (generate a tiny module, or `--add-data` the obfuscated secret). The `--add-data=SRC;DEST` `;` separator is the established Windows form already in this file.

**Gitignore precedent (D-09):** `.gitignore` already lists per-user/secret files — `machine_id.txt`, `player_data.json`, `firebase-key.json`. Add the real secret file (`hmac_secret.local`) the same way; commit only a placeholder/example. (Note: the CONTEXT "settings.local.json from Phase 3" reference resolves in-repo to the gitignored `/.claude` settings pattern — same gitignored-local-file + committed-example model.)

---

### `settings.py` (MODIFY) — config

**Analog: existing URL constants** (`settings.py:75-77`):
```python
API_SUBMIT_SCORE_URL = "https://pacman-991339031546.asia-southeast1.run.app"
API_LEADERBOARD_URL = "https://get-leaderboard-991339031546.asia-southeast1.run.app"
```
Candidate home for new identity-path constants (blob filename `identity.dat`, folder name `PacMan`, file-HMAC domain prefix). The secret itself MUST NOT live here (D-09 — baked at build, never a committed literal).

---

## Test Patterns

### `tests/test_leaderboard_crypto.py` — the canonical oracle (server REF + new client test)

**The single most important test (success criterion 4):** a client signature over a known `{machine_id, initials, score}` with a known test secret must pass the server's `verify_signature`. The cross-check harness already exists (`tests/test_leaderboard_crypto.py:28-37`, `:54-57`):
```python
def _sign(machine_id, initials, score, secret=TEST_SECRET):
    msg = json.dumps(
        {"machine_id": machine_id, "initials": initials, "score": score},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()

def test_verify_signature_valid(monkeypatch):
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", TEST_SECRET)
    sig = _sign("m1", "BOB", 5000)
    assert verify_signature("m1", "BOB", 5000, sig) is True
```
**New client test:** import the CLIENT `sign_submission`, sign with `TEST_SECRET`, and assert the server `verify_signature("m1","BOB",5000, client_sig) is True` (set `LEADERBOARD_HMAC_SECRET` via `monkeypatch.setenv` — conftest does not patch env). Also mirror `test_canonical_message_exact_bytes` (`:42-45`) against the client `canonical_message` for byte equality.

### `tests/test_api_service.py` — mock-urlopen pattern (MODIFY)

**Analog** (`tests/test_api_service.py:12-25`):
```python
def _mock_response(data, status=200):
    mock = MagicMock()
    mock.read.return_value = json.dumps(data).encode()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return mock

with patch("api_service.urlopen", return_value=response):
    result = service.submit_score("machine-1", "JAM", 5000)
```
**Add:** assert the request body now includes a `"signature"` field (capture the `Request` passed to `urlopen` and decode its `.data`). Update `submit_score` call sites for the new `signature` arg.

### `tests/test_local_storage.py` — tmp_path file-I/O pattern (MODIFY)

**Analog** (`tests/test_local_storage.py:7-23`):
```python
@pytest.fixture
def temp_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path

def test_get_machine_id_returns_same_id_on_second_call(temp_dir):
    path = str(temp_dir / "machine_id.txt")
    assert get_machine_id(path) == get_machine_id(path)
```
**Add:** round-trip the obfuscated+signed blob (write→read→verify), tamper-detection (mutate a byte → load returns invalid sentinel, NOT a fresh identity), corrupt-file → invalid, and D-04 migration (legacy files present → blob written, legacy deleted; partial/invalid legacy initials handled).

---

## Shared Patterns

### HMAC construction (one secret, two framings)
**Source:** `cloud_functions/submit_score/leaderboard_crypto.py:57-63`
**Apply to:** client crypto module (submission sig + file-integrity sig)
```python
expected = hmac.new(secret.encode("utf-8"), message_bytes, hashlib.sha256).hexdigest()
# verify side:
try:
    return hmac.compare_digest(expected, provided_sig)
except TypeError:
    return False
```
D-08: submission message = `canonical_message(...)`; file message = domain-prefixed blob (`b"identity-file-v1:" + blob`). Same secret, distinct messages → non-interchangeable signatures.

### Fail-closed / graceful-degrade
**Source:** `api_service.py:25-26` (`except Exception: return None`), `leaderboard_crypto.py:52-55` (fail-closed on bad input/missing secret)
**Apply to:** api_service submit, local_storage load (D-05 invalid → block, don't crash), main.py submit gate. The tamper/no-submit state is just another graceful-degrade branch — game stays fully playable.

### Frozen-vs-dev path resolution
**Source:** `paths.py:5-20` (`getattr(sys, 'frozen', False)` branch)
**Apply to:** new per-user-dir resolver in paths.py.

### Gitignored-local-secret + committed-example
**Source:** `.gitignore` (`machine_id.txt`, `player_data.json`, `firebase-key.json`, `/.claude`)
**Apply to:** `hmac_secret.local` in build.py (D-09) — real value gitignored, placeholder committed.

---

## No Analog Found

None. Every Phase 5 file extends an existing in-repo pattern. The only genuinely new logic — blob obfuscation (D-10) and the domain-separation prefix (D-08) — is Claude's discretion built on the existing stdlib `hmac`/`hashlib`/`base64` + `json` idioms already present in `leaderboard_crypto.py`.

## Metadata

**Analog search scope:** repo root (`local_storage.py`, `paths.py`, `api_service.py`, `main.py`, `menu.py`, `build.py`, `settings.py`), `cloud_functions/submit_score/`, `tests/`, `.gitignore`
**Files scanned:** 12
**Pattern extraction date:** 2026-06-19
