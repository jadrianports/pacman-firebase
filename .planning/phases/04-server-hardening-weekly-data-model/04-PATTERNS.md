# Phase 4: Server Hardening & Weekly Data Model - Pattern Map

**Mapped:** 2026-06-14
**Files analyzed:** 6 (2 modified functions, 2 modified test files, 1 new helper, 1 new ops note)
**Analogs found:** 5 / 6 (the HMAC/week-math helper is net-new; one strong analog per all other file)

All analogs live inside this same small codebase, so "match quality" reflects whether the
new work extends an existing structure (exact) or is a new shape inside an established
convention (role-match). The planner should treat the excerpts below as the literal code to
copy and extend — they are the as-shipped baseline confirmed clean at commit `38417e5`.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `cloud_functions/submit_score/main.py` (MOD) | controller + service (HTTP handler + Firestore txn) | request-response → CRUD (read-modify-write) | itself (extend in place) | exact |
| `cloud_functions/get_leaderboard/main.py` (MOD) | controller (HTTP handler + query) | request-response → read | itself (extend in place) | exact |
| `cloud_functions/<hmac_week_helper>.py` (NEW) | utility (HMAC verify + week math) | transform (pure functions) | none (new) — modeled on stdlib usage in RESEARCH | role-match (stdlib-only util) |
| `tests/test_submit_score.py` (MOD) | test | request-response assertions | itself + `tests/test_get_leaderboard.py` | exact |
| `tests/test_get_leaderboard.py` (MOD) | test | request-response assertions | itself | exact |
| `cloud_functions/DEPLOY.md` (NEW, optional) | config/ops doc | n/a | none (new) | no-analog (doc only) |

## Pattern Assignments

### `cloud_functions/submit_score/main.py` (controller + service, request-response → CRUD)

**Analog:** itself — extend in place. This is the core file of the phase. Four edits land here:
MAX_SCORE value (D-01), HMAC verify + grace flag (D-02/D-03), permanent-initials in the txn
(D-05), week-bucket write + lazy prune (D-06..D-09).

**Imports pattern** (lines 1-9) — keep this exact module-init shape; add `os, hmac, hashlib,
json, datetime` (all stdlib) for the new logic. Read secret/flag at CALL time, never as a
module-level constant (RESEARCH Pitfall 4):
```python
import functions_framework
from firebase_admin import firestore, initialize_app
import firebase_admin
import re

if not firebase_admin._apps:
    initialize_app()

db = firestore.client()
```

**Constant to change** (line 11) — the entire D-01 code change:
```python
MAX_SCORE = 500_000   # D-01: change to 50_000
```

**Transactional read-modify-write — the seam to extend** (lines 14-25). D-05 keeps stored
initials on an existing doc; D-06..D-09 add the weekly doc read + write + prune INSIDE this
same transaction. CRITICAL ordering invariant (RESEARCH Pitfall 1): all `.get()` calls must
precede all `.set()`/`.delete()` calls. Today's version overwrites initials every time — that
is the line D-05 must change:
```python
@firestore.transactional
def _update_score(transaction, doc_ref, initials, score, machine_id):
    doc = doc_ref.get(transaction=transaction)
    if doc.exists and score <= doc.to_dict().get("score", 0):
        return False
    transaction.set(doc_ref, {
        "initials": initials,                       # D-05: must become stored.get("initials", initials)
        "score": score,
        "machine_id": machine_id,
        "updated_at": firestore.SERVER_TIMESTAMP,
    })
    return True
```
Target shape for D-05 (from RESEARCH § Permanent-Initials Logic): read snapshot, if exists and
`score <= stored.score` return False; else `locked_initials = stored.get("initials", initials)`
and write `locked_initials` (NOT the new submission's initials). The `.get("initials", initials)`
fallback is what keeps the existing `test_is_new_best_*` tests green (they stub only `{"score": ...}`).

**OPTIONS / CORS preflight pattern** (lines 30-37) — preserve verbatim (Phase 7 web page
depends on it; do not refactor away):
```python
if request.method == "OPTIONS":
    return ("", 204, {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST",
        "Access-Control-Allow-Headers": "Content-Type",
    })

headers = {"Access-Control-Allow-Origin": "*"}
```

**Validation + parse pattern** (lines 39-52) — the V5 validation surface. Add a `signature`
field parse + the HMAC/grace decision (RESEARCH § Grace-Period Logic matrix) AFTER these
existing 400 checks, recomputing the canonical message from the parsed typed values (never the
raw body — RESEARCH Pitfall 3). Keep the `({"success": False, "error": ...}, 4xx, headers)`
return shape for the new reject path:
```python
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
```

**Transaction-dispatch + error-handling pattern** (lines 54-61) — keep this try/except +
`print(...)` log + `(body, status, headers)` tuple shape. D-02 grace logging ("unsigned
accepted") uses the same `print(...)` convention. The weekly doc-ref(s) are constructed
alongside the existing all-time `doc_ref` and passed into the extended `_update_score`:
```python
try:
    doc_ref = db.collection("leaderboard").document(machine_id)
    transaction = db.transaction()
    is_new_best = _update_score(transaction, doc_ref, initials, score, machine_id)
    return ({"success": True, "is_new_best": is_new_best}, 200, headers)
except Exception as e:
    print(f"Score submission failed: {e}")
    return ({"success": False, "error": "Internal error"}, 500, headers)
```
Keep `is_new_best` = all-time semantics (RESEARCH Pitfall 5); the existing tests pin this.

---

### `cloud_functions/get_leaderboard/main.py` (controller, request-response → read)

**Analog:** itself — extend in place. D-08 adds scope-awareness; the query target switches by
`?scope=week|all` (default `week` per A3, flag for user confirm).

**Imports + init + OPTIONS/CORS** (lines 1-20) — same module-init and preflight shape as
submit_score; preserve the `Access-Control-Allow-Methods: GET` header verbatim. Adding a query
param does NOT change preflight (RESEARCH § Scope Parameter):
```python
@functions_framework.http
def get_leaderboard(request):
    if request.method == "OPTIONS":
        return ("", 204, {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    headers = {"Access-Control-Allow-Origin": "*"}
```

**Query + projection + error pattern** (lines 22-36) — the read path to make scope-aware.
Branch on `scope = (request.args.get("scope") or "week").lower()` (RESEARCH § Scope Parameter);
`scope=all` keeps THIS exact `leaderboard` query, `scope=week`/default queries the `weekly`
collection `.where("week_id","==",cur).order_by("score",DESC).limit(10)`. KEEP the
`{"initials": ..., "score": ...}` projection unchanged — it is the D-10 machine_id-out-of-
responses guarantee. Keep the try/except + `({"entries": [], "error": ...}, 500, headers)`:
```python
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
except Exception as e:
    print(f"Leaderboard fetch failed: {e}")
    return ({"entries": [], "error": "Failed to fetch leaderboard"}, 500, headers)
```

---

### `cloud_functions/<hmac_week_helper>.py` (utility — NEW, no analog)

**Analog:** none in codebase. Model directly on RESEARCH § HMAC Scheme and § Week ID & Week
Math (stdlib only — `hmac`, `hashlib`, `json`, `os`, `datetime`). Planning decides whether
this is a shared module imported by both functions or inlined into `submit_score/main.py`
(note: Gen2 functions deploy from independent source dirs, so a shared module must be copied
into each function's dir or duplicated — flag this packaging detail in the plan). Pure
functions, fully unit-testable. Key signatures from RESEARCH (verified week-math):
```python
def canonical_message(machine_id, initials, score) -> bytes: ...      # Option A: canonical JSON
def verify_signature(machine_id, initials, score, provided_sig) -> bool: ...  # hmac.compare_digest
def current_week_id(now=None) -> str: ...   # Monday-date 'YYYY-MM-DD', UTC, injectable now
def previous_week_id(week_id: str) -> str: ...
```
`current_week_id(now=...)` MUST accept an injectable `now` so tests pin a deterministic week.

---

### `tests/test_submit_score.py` (test — MOD)

**Analog:** itself + `tests/test_get_leaderboard.py`. New tests follow the existing house style
exactly: build a `flask.Request`, call the entrypoint, assert on the `(body, status, headers)`
tuple. Reuse the existing helpers below.

**Request builder** (lines 28-35) — reuse verbatim for all new submit tests:
```python
def make_request(body, method="POST"):
    builder = EnvironBuilder(method=method, json=body)
    return Request(builder.get_environ())
```

**Existing-doc stub helper** (lines 99-105) — the mock seam for the transaction. D-05 tests
extend this to stub `{"initials": "BOB", "score": 4000}` (with initials present) and assert
`transaction.set` was called WITHOUT writing the new submission's initials:
```python
def _stub_existing_doc(submit_module, stored_score):
    db = submit_module._mock_client
    snap = db.collection.return_value.document.return_value.get.return_value
    snap.exists = True
    snap.to_dict.return_value = {"score": stored_score}
    return snap
```

**Boundary test to UPDATE** (lines 49-54) — D-01 change: `500001` → `50001`:
```python
def test_score_over_max_returns_400(submit_module):
    """score above MAX_SCORE (500000) -> 400 'Invalid score' (overflow guard)."""
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 500001})  # -> 50001
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid score"}
```

**Env-var injection pattern for new HMAC/flag tests** (NOT in current file — from RESEARCH §
mock seam): conftest does NOT patch `os.environ`, so use `monkeypatch.setenv(
"LEADERBOARD_HMAC_SECRET", "test-key")` and `monkeypatch.setenv("REQUIRE_SIGNATURE", "true")`
per-test. Secret/flag must be read at call time for this to work.

**Multi-doc mock wiring for weekly tests** (from RESEARCH § mock seam): the weekly doc and
all-time doc are different doc-ids (and `weekly` is a different collection). Drive
`db.collection.return_value` per collection name via `side_effect` keyed on the collection
string, and distinct `.document(id)` returns via `side_effect`, when one call touches both
`leaderboard` and `weekly`.

New tests to add (RESEARCH § New tests this phase must add): COMP-02 50001→400 / 50000→accept;
D-02 unsigned-grace-accept, unsigned-enforce-reject, invalid-sig-reject (both flag states),
valid-sig-accept; D-05 keep-original-initials + first-submission-locks; BOARD-01 week_id
boundary math + weekly write id `{machine_id}_{week_id}`; D-10 weekly response projects only
`{initials, score}`.

---

### `tests/test_get_leaderboard.py` (test — MOD)

**Analog:** itself. New scope tests reuse these helpers.

**Doc + stream stub helpers** (lines 22-45) — reuse verbatim; `_make_doc(..., extra=...)` already
supports the D-10 projection assertion. For `scope=week` the stub chain gains a `.where(...)`
link before `.order_by` — wire `db.collection.return_value.where.return_value.order_by.
return_value.limit.return_value.stream.return_value`:
```python
def make_request(method="GET"):
    builder = EnvironBuilder(method=method)
    return Request(builder.get_environ())

def _make_doc(initials, score, extra=None):
    from unittest.mock import MagicMock
    doc = MagicMock()
    data = {"initials": initials, "score": score}
    if extra:
        data.update(extra)
    doc.to_dict.return_value = data
    return doc

def _stub_stream(leaderboard_module, docs):
    db = leaderboard_module._mock_client
    chain = db.collection.return_value.order_by.return_value.limit.return_value
    chain.stream.return_value = docs
```
To pass `?scope=...` build the request with `EnvironBuilder(method="GET", query_string="scope=all")`.

**Projection-only test to mirror for weekly** (lines 61-68) — `test_leaderboard_projects_only_
initials_and_score` is the D-10 template; clone it for the weekly scope path:
```python
def test_leaderboard_projects_only_initials_and_score(leaderboard_module):
    _stub_stream(leaderboard_module, [
        _make_doc("JAM", 8000, extra={"machine_id": "m1", "updated_at": "ts"}),
    ])
    body, status, _ = leaderboard_module.get_leaderboard(make_request())
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}
```
New tests: BOARD-02 scope=all queries `leaderboard`; default + scope=week query `weekly`
filtered to current week; existing no-param tests stay green (param-less → default).

---

### `cloud_functions/DEPLOY.md` (config/ops doc — NEW, no analog, optional)

No existing ops doc to copy. If created, capture the manual Console steps (RESEARCH §
HMAC Scheme secret handoff, § Max-Instances Cap): Secret Manager `leaderboard-hmac-secret`
referenced as env var `LEADERBOARD_HMAC_SECRET`, `REQUIRE_SIGNATURE` env var (default false),
max-instances 3–5 on both functions, and the `weekly` composite index (`week_id ASC, score
DESC`). These are `checkpoint:human-verify` operational tasks — no in-repo artifact asserts them.

## Shared Patterns

### Cloud Function module skeleton (HTTP proxy, no client creds)
**Source:** `cloud_functions/submit_score/main.py:1-9`, `get_leaderboard/main.py:1-8`
**Apply to:** both functions + any new helper that imports firestore
The `if not firebase_admin._apps: initialize_app()` + module-level `db = firestore.client()`
runs at import time — the conftest fixture mocks `firestore.client` BEFORE this import. Do NOT
read secrets/flags at module level (Pitfall 4); read inside handlers.

### CORS headers (preserve exactly)
**Source:** `submit_score/main.py:30-37`, `get_leaderboard/main.py:13-20`
**Apply to:** every handler edit
OPTIONS → `("", 204, {Origin:*, Methods:<VERB>, Headers:Content-Type})`; all other returns
carry `headers = {"Access-Control-Allow-Origin": "*"}`. Phase 7 web page depends on these —
never refactor them away (RESEARCH § Scope Parameter CORS landmine).

### Return-tuple + error-handling contract
**Source:** `submit_score/main.py:39-61`, `get_leaderboard/main.py:22-36`
**Apply to:** all handler code paths (incl. new HMAC rejects, scope branches)
Every path returns `(body_dict, status_int, headers_dict)`. Failures: `try/except Exception as
e: print(f"...: {e}")` then a 500 with a generic error body. Never log the secret or full
machine_id (RESEARCH V7).

### Firestore transactional read-modify-write
**Source:** `submit_score/main.py:14-25`
**Apply to:** the combined all-time + weekly + prune logic
`@firestore.transactional` decorating `_update_score(transaction, doc_ref, ...)`; read via
`doc_ref.get(transaction=transaction)`, write via `transaction.set(doc_ref, {...})` with
`firestore.SERVER_TIMESTAMP`. INVARIANT: all reads precede all writes/deletes (Pitfall 1);
the real decorator is exercised in tests (not patched) — confirmed by the A2 spike.

### Test house style + mock seam
**Source:** `tests/test_submit_score.py:24-35,99-105`, `tests/test_get_leaderboard.py:22-45`,
`tests/conftest.py:96-128`
**Apply to:** all new/modified tests
Build a real `flask.Request` via `werkzeug.test.EnvironBuilder`; call the entrypoint; assert on
the `(body, status, headers)` tuple. `module._mock_client` IS `db` — drive
`.collection.return_value...` (NOT `.return_value.collection...`). Env vars are NOT patched by
conftest → use `monkeypatch.setenv` for `LEADERBOARD_HMAC_SECRET` / `REQUIRE_SIGNATURE`.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `cloud_functions/<hmac_week_helper>.py` | utility | transform | No existing pure-utility module in `cloud_functions/`; net-new. Build from RESEARCH § HMAC Scheme + § Week ID & Week Math (stdlib only). |
| `cloud_functions/DEPLOY.md` | ops doc | n/a | No existing ops doc; optional. Content from RESEARCH § HMAC Scheme secret handoff + § Max-Instances Cap. |

## Metadata

**Analog search scope:** `cloud_functions/**`, `tests/**`, `api_service.py`, `conftest.py`
**Files scanned:** `submit_score/main.py`, `get_leaderboard/main.py`, `api_service.py`,
`tests/conftest.py`, `tests/test_submit_score.py`, `tests/test_get_leaderboard.py` (all read in full)
**Baseline confirmed:** clean at `38417e5` per RESEARCH § Baseline Verification
**Pattern extraction date:** 2026-06-14
