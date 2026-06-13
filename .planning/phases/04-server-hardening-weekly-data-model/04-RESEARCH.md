# Phase 4: Server Hardening & Weekly Data Model - Research

**Researched:** 2026-06-14
**Domain:** Python Cloud Functions (Gen2 / Cloud Run), Firestore data modeling, HMAC auth, secret management
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01..D-11 — do NOT re-litigate)

- **D-01 (COMP-02):** Lower `MAX_SCORE` from `500_000` → `50_000`. Perfect run ~14,620; 50k is ~3.4× headroom.
- **D-02 (COMP-01):** Grace period + flip. Server **accepts unsigned** submissions during P4→P5 gap (and logs them), but **rejects any invalid signature**. A server flag (e.g. `REQUIRE_SIGNATURE`) gates hard enforcement, flipped to "require" only after Phase 5 signed client ships. Rejection logic is fully built and tested in Phase 4.
- **D-03 (COMP-01):** Signature covers the **full payload: machine_id + initials + score**. Binding machine_id prevents a valid signature being lifted onto a different identity/score. (Exact serialization is Claude's discretion.)
- **D-04 (COMP-01):** **No replay defense.** Submit is "only-if-higher" → replay is near-harmless. No nonce/timestamp.
- **D-05 (COMP-03):** Initials **lock on first submission**. Later submission with *different* initials → **keep the original initials, still accept the score if it's a new best**. New initials silently ignored, no error. (Today's code rewrites initials on every new best — MUST change.)
- **D-06 (BOARD-01):** Week bucketed by **Monday 00:00 UTC** reset. Buckets computed from **server time only** — never client-supplied timestamp.
- **D-07 (BOARD-01):** "This Week" = **best score per machine_id for the current week**, mirroring all-time one-row-per-machine shape.
- **D-08 (BOARD-02):** All-time board persists untouched; `get_leaderboard` becomes **scope-aware** (current week vs. all-time).
- **D-09 (Retention):** Keep **current week + last week only**. Older weeks pruned via **lazy delete-on-write** (opportunistic on submission). No Cloud Scheduler/cron. Last week's bucket MUST survive (Phase 6 "last week's champ").
- **D-10 (Privacy):** `machine_id` MUST stay out of **all** API responses.
- **D-11 (Quota):** **Cap `max-instances`** on both functions. No per-request rate-limiting state.

### Claude's Discretion (designed in this research)
1. Exact HMAC scheme (serialization, hash, secret location) — see § HMAC Scheme.
2. `get_leaderboard` scope-param shape + default — see § Scope Parameter.
3. Week-bucket storage mechanism — see § Week-Bucket Storage.
4. `week_id` format + week math — see § Week ID & Week Math.
5. `max-instances` cap mechanism — see § Max-Instances Cap.
6. Baseline verification — see § Baseline Verification.

### Deferred Ideas (OUT OF SCOPE)
- Replay-verification (COMP-F1), season-history archives (BOARD-F1), per-machine/per-IP rate-limiting, nonce/timestamp replay protection, full code obfuscation (PyArmor), friend groups (SOCL-F1).
- Client-side identity storage/obfuscation/signing → **Phase 5**. In-game weekly UI / toggle / champ / got-passed → **Phase 6**. Web page → **Phase 7**.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| COMP-01 | Server verifies HMAC signature; rejects forged/unsigned (per D-02 grace rules) | § HMAC Scheme, § Grace-Period Logic, § Security Domain |
| COMP-02 | Server rejects scores above sanity ceiling | D-01: change one constant `MAX_SCORE = 50_000`; existing validator + test already cover the path |
| COMP-03 | Permanent initials — locked on first submission | § Permanent-Initials Logic, § Firestore Transaction Pattern |
| BOARD-01 | Scores bucketed by week, Monday 00:00 UTC reset | § Week ID & Week Math, § Week-Bucket Storage |
| BOARD-02 | All-time board retained alongside weekly; scope-aware get_leaderboard | § Scope Parameter, § Week-Bucket Storage |
</phase_requirements>

## Summary

This phase hardens two existing Python Gen2 Cloud Functions (`submit_score`, `get_leaderboard`) deployed manually via the Google Cloud Console in `asia-southeast1`. The functions use the **raw `functions_framework` + `firebase_admin`** stack (NOT the `firebase-functions` Python SDK), so all secret management, max-instances, and deploy config is done through the **GCF Gen2 / Cloud Run runtime controls in the Console**, not via SDK decorators. This distinction matters: most online "Firebase Functions Python" secret docs describe `firebase_functions.params.SecretParam` / `@https_fn.on_request(secrets=[...])`, which this project does **not** use.

The four substantive code changes are: (1) HMAC-SHA256 verification with a grace-period flag (D-02), (2) the `MAX_SCORE` constant change (D-01, trivial), (3) permanent-initials lock inside the transactional read-modify-write (D-05), and (4) a week-bucketed data model with a scope-aware reader and lazy prune (D-06..D-09). The single highest-risk area is the combined **permanent-initials + week-bucket read-modify-write inside one Firestore transaction** — Firestore transactions require all reads before any writes, so the lazy-prune deletes and the two read-modify-writes (all-time doc + weekly doc) must be ordered correctly within one `@firestore.transactional` function.

The committed baseline is **clean and confirmed** (`38417e5`, working tree empty for `cloud_functions/`). The existing test harness (`tests/conftest.py`) mocks `firestore.client()` at import time and exercises the **real** `@firestore.transactional` decorator against a `MagicMock` transaction — so new transaction logic is testable without an emulator, but multi-read / multi-write transactions need careful mock wiring.

**Primary recommendation:** Canonical HMAC over a length-prefixed / JSON-canonical serialization (NOT raw `|` join), secret in **Secret Manager referenced as an env var** read via `os.environ`, week buckets as a **separate `weekly` collection keyed `{machine_id}_{week_id}`** with `week_id = Monday-date string`, scope via `?scope=week|all` defaulting to `week`, and `max-instances` set per-function in the Console runtime settings.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HMAC verification | API / Backend (Cloud Function) | — | Enforcement boundary; secret never trusted to client (D-02/D-03) |
| Score sanity ceiling | API / Backend | — | Server is sole arbiter (COMP-02) |
| Permanent initials lock | API / Backend (Firestore txn) | Database (stored `initials`) | Lock state lives in Firestore; enforced in transaction (D-05) |
| Week bucketing / week_id | API / Backend (server clock) | Database (bucket docs) | Server-time-only (D-06); client clock never trusted |
| Scope-aware read | API / Backend | Database (query) | Reads correct collection by `scope` param (D-08) |
| Lazy prune | API / Backend (on write) | Database (deletes) | Opportunistic in transaction (D-09); no scheduler tier |
| Secret storage | GCF Gen2 runtime / Secret Manager | — | Console-managed; injected as env var (Claude discretion #1) |
| max-instances cap | GCF Gen2 / Cloud Run config | — | Deploy-config, not code (D-11) |

## Standard Stack

### Core (already in use — no new dependencies needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `functions-framework` | `3.*` (pinned in requirements.txt) | HTTP entrypoint wrapper (`@functions_framework.http`) | Already deployed; Google's official local/runtime shim for Gen2 |
| `firebase-admin` | `6.*` (pinned) | Firestore client + transactions | Already deployed; server-side admin SDK, no client creds |
| `hmac` | stdlib | HMAC-SHA256 + `compare_digest` | Stdlib — no install. Constant-time compare built in |
| `hashlib` | stdlib | SHA-256 digest backend for hmac | Stdlib |
| `datetime` | stdlib | Week math (`timezone.utc`, `timedelta`) | Stdlib |
| `os` | stdlib | `os.environ` secret/flag read | Stdlib |

**No new packages.** `[VERIFIED: requirements.txt]` Both functions pin `functions-framework==3.*` and `firebase-admin==6.*`. HMAC, datetime, os, hashlib are all Python stdlib. **There is no Package Legitimacy Audit needed — this phase installs nothing.**

### Alternatives Considered (and rejected for THIS project)
| Instead of | Could Use | Why rejected here |
|------------|-----------|-------------------|
| raw `firebase_admin` | `firebase-functions` Python SDK (`@https_fn.on_request(secrets=[...])`, `SecretParam`) | Project uses raw `functions_framework`; switching SDKs is out of scope and would break the deploy model. The `secrets=[...]` decorator API does NOT apply here `[VERIFIED: cloud_functions/*/main.py]` |
| `os.environ` secret read | `google-cloud-secret-manager` client lib (runtime API fetch) | Adds a dependency + IAM call per cold start. Console "Reference a secret" → env var is simpler and the secret is small/static `[CITED: cloud.google.com/functions/docs/configuring/secrets]` |

## HMAC Scheme (Discretion #1)

### Hash & compare
- **HMAC-SHA256** via stdlib `hmac.new(key, msg, hashlib.sha256)`. `[ASSUMED]` (recommended in CONTEXT; standard choice)
- Compare with **`hmac.compare_digest(expected_hex, provided_hex)`** — constant-time, prevents timing oracle. `[CITED: docs.python.org/3/library/hmac.html]`
- Transmit signature as **lowercase hex** (`.hexdigest()`) — JSON-safe, no base64 padding ambiguity.

### Canonical serialization — AVOID raw `|` join (delimiter-injection)
A naive `f"{machine_id}|{initials}|{score}"` is **ambiguous**: `machine_id="a|BCD"` + `initials="EFG"` collides with `machine_id="a"` + `initials="BCD|EFG"`-type splits. Initials are constrained to `^[A-Z]{3}$` and score is an int, but `machine_id` is free-form client text — it can contain `|`. **Recommendation (pick ONE, lock in planning):**

**Option A — canonical JSON with sorted keys + separators (recommended):**
```python
import json, hmac, hashlib
def canonical_message(machine_id: str, initials: str, score: int) -> bytes:
    return json.dumps(
        {"machine_id": machine_id, "initials": initials, "score": score},
        sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")
```
Pro: unambiguous, trivially mirrored in the Phase 5 client (same `json.dumps` call), types are explicit (score stays an int, not stringified). Con: the client MUST reproduce the exact `separators`/`sort_keys`/`ensure_ascii` settings.

**Option B — length-prefixed fields:**
```python
def canonical_message(machine_id, initials, score) -> bytes:
    parts = [str(machine_id), str(initials), str(score)]
    return "".join(f"{len(p)}:{p}" for p in parts).encode("utf-8")
```
Pro: injection-proof without JSON. Con: client must implement the same prefixing; slightly more bespoke.

**Recommendation: Option A.** Phase 5 client already builds the JSON body (`api_service.submit_score` does `json.dumps({...})`), so reusing canonical JSON keeps client/server in lockstep with one shared helper. **Lock the exact `json.dumps` kwargs in the plan** so Phase 5 cannot drift. `[ASSUMED — needs confirmation in planning that Option A is chosen]`

> **Landmine:** the *signed* canonical form and the *transport* JSON body are different concerns. The transport body (what `api_service` POSTs) can include the `signature` field and whitespace; the *signed* canonical message must be recomputed server-side from the parsed `machine_id/initials/score` values, NOT from the raw request bytes. Never sign/verify over the raw HTTP body — parse first, then canonicalize. This avoids whitespace/key-order transport differences breaking verification.

### Verification flow (server)
```python
import os, hmac, hashlib

def verify_signature(machine_id, initials, score, provided_sig) -> bool:
    secret = os.environ["LEADERBOARD_HMAC_SECRET"].encode("utf-8")
    expected = hmac.new(secret, canonical_message(machine_id, initials, score),
                        hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, provided_sig or "")
```

### Where the secret lives (the important part)
**Recommendation: Google Secret Manager, referenced as an environment variable, read via `os.environ`.** `[CITED: cloud.google.com/functions/docs/configuring/secrets]`

Because these are **Gen2 functions deployed manually via the Console** (URLs are `*.run.app` → Cloud Run-backed Gen2), the path is:
1. Create the secret once in **Secret Manager** (Console → Security → Secret Manager → create `leaderboard-hmac-secret`, value = a long random key, e.g. `python -c "import secrets;print(secrets.token_hex(32))"`).
2. In each function's Console page → **Edit** → **Runtime, build, connections and security settings** → **Security and image repo / Variables & Secrets** tab → **Reference a secret** → env var name `LEADERBOARD_HMAC_SECRET`, secret `leaderboard-hmac-secret`, version `latest`, exposed as **environment variable**.
3. Grant the function's runtime service account `roles/secretmanager.secretAccessor` (Console prompts for this when you add the reference).
4. Code reads `os.environ["LEADERBOARD_HMAC_SECRET"]`.

**Why Secret Manager over a plain env var:** plain runtime env vars are visible in the Console function config and in deploy logs to anyone with viewer access; Secret Manager keeps the value out of the function config surface and gives rotation/versioning. `[CITED: cloud.google.com/functions/docs/configuring/secrets]` A plain env var is *acceptable* (the threat model already accepts the secret is extractable from the exe), but Secret Manager is the low-effort better default and is the same string the Phase 5 client embeds.

**Same secret → Phase 5 client.** The Phase 5 build embeds this identical key string to sign. The HMAC scheme chosen here (canonical JSON + hex) is deliberately simple so the client can reproduce it with stdlib only. Document the secret value handoff as an operational note for the user (it is NOT committed to git).

### Testability of the secret
The conftest mocks Firestore but NOT `os.environ`. Tests must set the env var (e.g. `monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", "test-key")`) **and** the secret must be read **at call time, not import time** — read `os.environ` inside the handler/verify function, not as a module-level constant, so tests can inject a known key per-test. `[VERIFIED: tests/conftest.py — env not patched; module re-imported per fixture]`

## Grace-Period Logic (D-02)

Decision matrix the server implements:

| Signature present? | Signature valid? | `REQUIRE_SIGNATURE` flag | Result |
|--------------------|------------------|--------------------------|--------|
| absent | n/a | off (grace) | **Accept** (log "unsigned accepted") |
| absent | n/a | on (enforced) | **Reject 401/403** |
| present | valid | either | **Accept** |
| present | **invalid** | **either (off OR on)** | **Reject 401/403** ← built+tested in Phase 4 |

Key subtlety: during grace, an **invalid** signature is still rejected — only a **missing** signature is tolerated. The flag only changes how *missing* is treated. The flag itself is a server config: `REQUIRE_SIGNATURE = os.environ.get("REQUIRE_SIGNATURE", "false").lower() == "true"` (read at call time so tests can flip it). Default OFF for the P4→P5 grace window; user flips it in the Console after Phase 5 ships.

> **Test target (success criterion):** an invalid/forged `curl` POST against the known test key is rejected (with flag both off and on); a missing-signature POST is accepted with flag off and rejected with flag on.

## Permanent-Initials Logic (D-05)

Today's `_update_score` does `transaction.set(doc_ref, {"initials": initials, ...})` — it **overwrites initials on every new best**. D-05 changes this to: **on an existing doc, keep the stored initials; only the score updates.**

```python
@firestore.transactional
def _update_score(transaction, doc_ref, initials, score, machine_id, ...):
    snap = doc_ref.get(transaction=transaction)
    if snap.exists:
        stored = snap.to_dict()
        if score <= stored.get("score", 0):
            return False                      # not a new best
        locked_initials = stored.get("initials", initials)   # D-05: keep original
        transaction.set(doc_ref, {
            "initials": locked_initials,      # NOT the new submission's initials
            "score": score, "machine_id": machine_id,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
    else:
        transaction.set(doc_ref, {            # first submission locks initials
            "initials": initials, "score": score, "machine_id": machine_id,
            "updated_at": firestore.SERVER_TIMESTAMP,
        })
    return True
```

> **Landmine:** the existing test `test_is_new_best_*` stubs only `{"score": ...}` in `to_dict()` (no `initials`). The `.get("initials", initials)` fallback keeps those tests green. But a NEW test must assert the keep-original behavior with an existing `initials` value present — and must assert the *new* submission's differing initials are NOT written. Use `transaction.set` call-args inspection (the mock records what was written).

## Week ID & Week Math (Discretion #4)

**Recommendation: `week_id` = the Monday-date string `YYYY-MM-DD` of the week's Monday in UTC.** Human-readable, sorts lexicographically = chronologically, trivial "last week" math (`monday - 7 days`). Verified against boundary cases:

```python
from datetime import datetime, timezone, timedelta

def current_week_id(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)        # SERVER time only (D-06)
    monday = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0)
    return monday.strftime("%Y-%m-%d")

def previous_week_id(week_id: str) -> str:
    monday = datetime.strptime(week_id, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    return (monday - timedelta(days=7)).strftime("%Y-%m-%d")
```

**Verified boundary cases** `[VERIFIED: ran via .venv/Scripts/python.exe 2026-06-14]`:
- `2026-06-08 00:00:00 UTC` (Monday) → `2026-06-08` (start of its own week ✓)
- `2026-06-07 23:59:59 UTC` (Sunday) → `2026-06-01` (still prior week ✓)
- `2026-06-08 00:00:01 UTC` → `2026-06-08` (new week ✓)
- `now` → `2026-06-08`

`datetime.weekday()` returns Monday=0 ... Sunday=6, so `now - timedelta(days=now.weekday())` lands on the week's Monday. `.replace(hour=0,...)` snaps to 00:00.

### Pitfalls (week math)
- **Why NOT `isocalendar()` week numbers:** ISO week `(2026, 24)` has year-boundary edge cases (ISO week 1 can start in the prior calendar year; week 52/53 ambiguity). The Monday-date string sidesteps all of it and is directly usable as a Firestore doc-id component.
- **Always use `datetime.now(timezone.utc)`** — never naive `datetime.now()` (server-local TZ) and never `datetime.utcnow()` (returns naive, deprecated in 3.12+). `[CITED: docs.python.org/3/library/datetime.html — utcnow deprecation]`
- **Never accept a client timestamp** (D-06). The `week_id` is computed inside the function from `datetime.now(timezone.utc)` only.
- **Testability:** make `current_week_id(now=...)` accept an injectable `now` so tests pin a deterministic week without freezing the system clock.

## Week-Bucket Storage (Discretion #3)

**Recommendation: a separate top-level `weekly` collection, doc-id = `{machine_id}_{week_id}`.** The existing all-time `leaderboard/{machine_id}` collection stays **exactly as-is** (D-08: "persists untouched").

| Option | Verdict | Reasoning |
|--------|---------|-----------|
| **Separate `weekly` collection, id `{machine_id}_{week_id}` (RECOMMENDED)** | ✓ | All-time path is literally unchanged. Per-player-per-week best is a single deterministic doc id → the read-modify-write needs no query, just `.document(f"{machine_id}_{week_id}").get()`. Lazy prune is `.document(f"{machine_id}_{old_week_id}").delete()` — also deterministic, no query. Weekly read = `order_by(score desc).limit(10)` filtered to current week (see below). |
| `week_id` field on a single doc per machine | ✗ | Can't hold current+last-week best simultaneously for one machine; clobbers history Phase 6 needs |
| Timestamp-range queries on all-time docs | ✗ | All-time docs are one-row-per-machine "best ever" — they have no per-week granularity to range over; would require append-only event docs (bigger model, indexes, no prune simplicity) |

### Weekly read query
Because the doc-id encodes both machine and week, query the `weekly` collection filtered to the current week. Two viable shapes:
- **(a)** Store `week_id` as a field too, and query `weekly.where("week_id","==",cur).order_by("score",DESC).limit(10)`. Requires a **composite index** (`week_id ASC, score DESC`) — Firestore will emit a console link to create it on first query. `[CITED: firebase.google.com/docs/firestore/query-data/indexing]`
- **(b)** Use a `collection_group` / id-prefix approach — less clean; (a) is standard.

**Recommendation: (a)** — store `week_id` as an indexed field in each weekly doc (alongside `initials`, `score`, `machine_id`), query by equality + order. **Plan must include creating the composite index** (one-time, via the auto-generated Console link or `firestore.indexes.json`). This is the single Firestore-config landmine.

### Lazy prune (D-09)
On each submission, after computing `cur = current_week_id()`, the keep-set is `{cur, previous_week_id(cur)}`. Prune any weekly doc for *this machine* whose week is older. Since the only weeks a given machine could have are ones it wrote, and ids are `{machine_id}_{week}`, the cheap prune is: when writing the current-week doc, also `delete()` `{machine_id}_{week older than last}`. You don't know all historical weeks without a query — so the pragmatic prune is **"delete `{machine_id}_{previous_week_id(previous_week_id(cur))}`"** (the week two-back) on each write, which keeps the per-machine footprint bounded at ~3 docs and never needs a query. `[ASSUMED — confirm prune scope in planning]`

> **Transaction landmine:** Firestore transactions require **all reads before all writes**. The combined operation reads: all-time doc + current-week weekly doc. It writes: all-time doc (maybe), current-week weekly doc (maybe), and a prune delete. **All `.get()` calls must come before any `.set()`/`.delete()`.** Structure `_update_score` to: (1) read both docs, (2) decide, (3) write/delete. A `delete()` of a non-existent doc is a harmless no-op in Firestore, so the prune needs no prior read. `[CITED: firebase.google.com/docs/firestore/manage-data/transactions — reads must precede writes]`

> **Independence landmine:** all-time best and weekly best are **independent** comparisons. A score can be a new weekly best but NOT a new all-time best (and vice versa). `is_new_best` in the response — decide in planning whether it reflects all-time, weekly, or both (recommend: keep `is_new_best` = all-time to preserve the existing contract/tests, optionally add `is_new_weekly_best`). The existing `test_is_new_best_*` tests assert the all-time semantics; don't break them.

## Scope Parameter (Discretion #2)

**Recommendation: `?scope=week|all`, default `week`.** `[ASSUMED — recommended in CONTEXT]`

```python
scope = (request.args.get("scope") or "week").lower()
if scope not in ("week", "all"):
    scope = "week"                      # tolerant default, never 400 a reader
if scope == "all":
    query = db.collection("leaderboard").order_by("score", DESC).limit(10)
else:
    cur = current_week_id()
    query = (db.collection("weekly")
             .where("week_id", "==", cur)
             .order_by("score", direction=firestore.Query.DESCENDING).limit(10))
```

- Parse from `request.args` (Flask `Request` — the existing functions-framework request object already supports `.args`). No new parsing dependency. `[VERIFIED: tests use werkzeug/flask Request]`
- **CORS preservation (landmine):** the existing GET handler hardcodes `Access-Control-Allow-Methods: GET` and `Access-Control-Allow-Origin: *` on both the OPTIONS preflight and the response. Adding a query param does NOT change preflight (params aren't headers), so CORS is unaffected — but the new code must keep emitting the identical headers dict so the Phase 7 web page and existing exe keep working. Don't refactor the headers away.
- **Backward compat:** existing exe calls `get_leaderboard` with **no** `scope` param. Default `week` means the deployed exe would suddenly show the weekly board. **Decide in planning:** is the default `week` (CONTEXT's recommendation, competitive focus) acceptable for the already-shipped exe, or should the no-param default be `all` to preserve current behavior until Phase 6 ships the toggle? **CONTEXT recommends `week`** — flag this as the one behavior the user should confirm, since it changes what today's exe displays the moment the function is redeployed. `[ASSUMED — surfaced for confirmation]`
- **`api_service.get_leaderboard()` (client):** currently sends no param. Phase 6 adds the scope arg. Phase 4 server must accept the param-less call (→ default). The existing `test_get_leaderboard_*` tests call with no scope and must stay green.

## Max-Instances Cap (Discretion #5 / D-11)

**Recommendation: set per-function in the Console; it is deploy-config, not in-code.** `[CITED: cloud.google.com/functions/docs — max instances; cross-checked WebSearch 2026-06-14]`

For Gen2 functions: Console → the function → **Edit** → **Runtime, build, connections and security settings** → **Runtime** → **Maximum number of instances**. Set a small bound (e.g. **3–5**) for a friends-scale board — bounds cost/blast-radius if flooded (D-11). Default is 100 (Gen2 HTTP), which is the "uncapped" risk D-11 addresses.

- This is NOT settable from the `functions_framework`/`firebase_admin` source code in this project's model — it's a Cloud Run service setting. (The `firebase-functions` SDK has `max_instances=` on the decorator, but this project doesn't use that SDK.)
- Since deploy is manual, the plan should produce an **operational checklist task** (`checkpoint:human-verify`) instructing the user to set max-instances on both functions in the Console after deploy — there is no in-repo artifact to assert it. Optionally document it in a `cloud_functions/DEPLOY.md`.
- Consider also lowering **concurrency** is unnecessary; max-instances is the relevant lever for D-11.

## Baseline Verification (Discretion #6)

**Confirmed clean and at the intended reconciled baseline** `[VERIFIED: git 2026-06-14]`:
- `git status --short cloud_functions/` → empty (working tree clean for the dir).
- Latest commit touching `cloud_functions/`: `38417e5 feat(cloud-fn): enforce MAX_SCORE cap and transactional best-score upsert` (prior `d16f97d with firebase`).
- The committed `submit_score/main.py` matches what the TST-03 tests pin (D-16): `MAX_SCORE = 500_000`, `@firestore.transactional _update_score`, initials-rewrite-on-every-best. The tests reference the WORKING-TREE files and currently pass against this state.

**Planner action:** before modifying, run `pytest tests/test_submit_score.py tests/test_get_leaderboard.py tests/test_api_service.py` once to confirm green-against-baseline, then proceed. No reconciliation needed — the "uncommitted changes flagged at v1.0 close" prerequisite is already satisfied (memory note `api-refactor-planned.md` confirms files were restored, not deleted).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Constant-time signature compare | manual `==` byte loop | `hmac.compare_digest` | Timing-attack safe, stdlib `[CITED: docs.python.org]` |
| HMAC digest | manual SHA + key concat | `hmac.new(key, msg, hashlib.sha256)` | Length-extension safe, correct construction |
| Canonical serialization | ad-hoc `|` join | canonical JSON (sorted, fixed separators) | Delimiter-injection safe |
| Week boundary math | manual day-of-week arithmetic | `datetime.weekday()` + `timedelta` | DST-irrelevant in UTC; off-by-one safe |
| Transaction atomicity | read-then-write without txn | `@firestore.transactional` | Race-free read-modify-write (already used) |
| Secret storage | hardcoded constant in source | Secret Manager → env var | Out of git; rotatable |

**Key insight:** Every primitive this phase needs is in the Python stdlib (`hmac`, `hashlib`, `datetime`, `os`, `json`) or the already-deployed `firebase_admin`. The risk is in *composition* (transaction read/write ordering, canonical serialization agreement with Phase 5), not in any missing library.

## Common Pitfalls

### Pitfall 1: Reads after writes in the transaction
**What goes wrong:** Firestore raises if a `.get()` follows a `.set()`/`.delete()` in the same transaction. The combined all-time + weekly + prune logic naturally tempts interleaving.
**How to avoid:** Read all-time doc and weekly doc up front; compute all decisions; then issue all writes/deletes last.
**Warning signs:** "read after write" / transaction errors against the emulator; mock tests won't catch this (MagicMock allows any order) — call it out so reviewers verify ordering by eye.

### Pitfall 2: Mock tests pass but real transaction ordering is wrong
**What goes wrong:** conftest drives a `MagicMock` transaction that accepts any call order, so a reads-after-writes bug is invisible in unit tests.
**How to avoid:** Keep the read/decide/write structure explicit and reviewable; consider one optional emulator-backed integration test, but CONTEXT/D-15 says NO emulator — so rely on code-review of ordering. Document the invariant in a comment.

### Pitfall 3: Signing over raw body vs. parsed values
**What goes wrong:** Server verifies HMAC over the raw request bytes; client whitespace/key-order differs → every signature fails.
**How to avoid:** Parse JSON first, then recompute canonical message from typed values. Sign/verify over the canonical form, never the wire bytes.

### Pitfall 4: Secret/flag read at import time
**What goes wrong:** Module-level `SECRET = os.environ[...]` breaks the conftest import (env not set at import) and prevents per-test key injection.
**How to avoid:** Read `os.environ` inside the handler/verify function at call time.

### Pitfall 5: `is_new_best` semantics drift
**What goes wrong:** Weekly and all-time bests diverge; changing `is_new_best` to mean "weekly" silently breaks the existing client contract and tests.
**How to avoid:** Keep `is_new_best` = all-time best (existing semantics); add a separate field if weekly-best signalling is needed.

### Pitfall 6: Default scope changes shipped-exe behavior
**What goes wrong:** Default `?scope=week` makes the already-deployed exe show the weekly board the instant the function redeploys (before Phase 6 ships the toggle).
**How to avoid:** Confirm the default with the user (CONTEXT recommends `week`; surfaced in § Scope Parameter as the one item to confirm).

## Validation Architecture

> `nyquist_validation` is `false` in config — formal Nyquist mapping is skipped. This section is included per the phase research brief (testing landmines are central to this phase). Tests run via `pytest` (use `.venv/Scripts/python.exe -m pytest` per memory note: deps live in `.venv`).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config | `tests/conftest.py` (firebase-mocked importers, no emulator) |
| Run cmd | `.venv/Scripts/python.exe -m pytest tests/test_submit_score.py tests/test_get_leaderboard.py tests/test_api_service.py` |
| Full gate | `.venv/Scripts/python.exe -m pytest` (includes CI golden net — must stay green) |

### Mock seam (from conftest — critical for new tests)
- `submit_module._mock_client` **IS** `db` directly. Drive `db.collection.return_value.document.return_value.get.return_value` (a snapshot mock with `.exists` and `.to_dict.return_value`).
- The **real** `@firestore.transactional` decorator runs against a MagicMock transaction (A2 spike resolved). New multi-doc logic: wire `.collection().document(id1)` vs `.document(id2)` — use `side_effect` or distinct return per id, since the weekly and all-time docs are different doc-ids in possibly different collections.
- Env vars are NOT patched by conftest → use `monkeypatch.setenv` for `LEADERBOARD_HMAC_SECRET` and `REQUIRE_SIGNATURE`.
- New `weekly` collection: drive `db.collection.return_value` per collection name via `side_effect` keyed on the collection string if both `leaderboard` and `weekly` are touched in one call.

### New tests this phase must add
| Behavior | Test |
|----------|------|
| COMP-02 ceiling at new value | score `50_001` → 400; score `50_000` → accepted (update existing `test_score_over_max` boundary to 50_000) |
| D-02 unsigned accepted (grace off) | no `signature`, flag off → 200 |
| D-02 unsigned rejected (enforce on) | no `signature`, `REQUIRE_SIGNATURE=true` → 401/403 |
| D-02 invalid signature rejected (both flag states) | bad `signature` → 401/403 |
| D-02 valid signature accepted | correct HMAC over test key → 200 |
| D-05 keep-original initials | existing doc `{initials:"BOB",score:4000}`, submit `{initials:"EVE",score:9000}` → stored initials stay `BOB`, score → 9000; assert `transaction.set` call did NOT write `EVE` |
| D-05 first submission locks | no existing doc → initials written as-submitted |
| BOARD-01 week_id math | `current_week_id(injected now)` boundary cases (Mon 00:00, Sun 23:59) |
| BOARD-01 weekly write | submission writes a `weekly` doc id `{machine_id}_{week_id}` |
| BOARD-02 scope=all | `?scope=all` queries `leaderboard` collection |
| BOARD-02 scope=week / default | no param + `?scope=week` query the `weekly` collection filtered to current week |
| D-10 no machine_id leak | weekly + all-time responses project only `{initials, score}` (mirror existing `test_leaderboard_projects_only_*`) |
| Existing TST-03 tests | all stay green (the `.get("initials", default)` fallback preserves `test_is_new_best_*`) |

### Wave 0 gaps
- The existing `test_score_over_max_returns_400` uses `500001` — must be updated to the new `50_000` ceiling (or a new boundary test added). This is a deliberate characterization-test change tied to D-01.
- No new conftest fixtures strictly required, but a helper to stub two distinct docs (all-time + weekly) per collection will reduce duplication.

## Security Domain

> `security_enforcement: true`, ASVS level 1, block_on: high.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | HMAC-SHA256 shared-secret signature on submit (COMP-01); accepted ceiling: secret extractable from exe (documented, deferred to replay-verification COMP-F1) |
| V3 Session Management | no | Stateless HTTP functions; no sessions |
| V4 Access Control | partial | No per-user accounts; machine_id is identity. Permanent-initials lock (D-05) is the only access control |
| V5 Input Validation | yes | Existing validators: `^[A-Z]{3}$` initials, int + range score, machine_id presence. Keep + extend for `signature` field |
| V6 Cryptography | yes | `hmac` + `hashlib.sha256` stdlib; `compare_digest` constant-time; NEVER hand-roll |
| V7 Error/Logging | partial | Log unsigned-accepted submissions (D-02) and rejections; don't log the secret or full machine_id |
| V9 Data Protection | yes | machine_id kept out of all responses (D-10); secret in Secret Manager not git |

### Threat patterns for this stack
| Pattern | STRIDE | Mitigation |
|---------|--------|-----------|
| Forged `curl` submission | Spoofing | HMAC verification (rejected when signature invalid, even in grace) |
| Signature lifted onto different identity/score | Tampering | machine_id bound into signed payload (D-03) |
| Delimiter injection in signed string | Tampering | Canonical JSON / length-prefix serialization |
| Timing oracle on signature check | Information Disclosure | `hmac.compare_digest` constant-time |
| machine_id harvested via API → impersonation | Information Disclosure | machine_id never in responses (D-10) |
| Endpoint flooding | Denial of Service | max-instances cap (D-11); accepted residual: no per-request rate limit |
| Impossible score | Tampering | sanity ceiling 50,000 (D-01) |
| Replay of valid submission | Tampering | Accepted residual (D-04) — only-if-higher makes it near-harmless |
| Secret in source/logs | Information Disclosure | Secret Manager → env var; read at runtime; never logged |

**block_on: high check:** no HIGH-severity gap introduced. The extractable-client-secret limit is a deliberately-accepted MEDIUM (documented in CONTEXT § Specific Ideas; unforgeable fix deferred as COMP-F1). No blocker.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `.venv` Python | run tests/build | ✓ | per `.venv` | use `.venv/Scripts/python.exe` (global Python is bare — memory note) |
| pytest | TST-03 tests | ✓ (in .venv) | — | — |
| `functions-framework`, `firebase-admin` | function runtime | ✓ (pinned) | 3.*, 6.* | — |
| Firestore emulator | NOT used (D-15) | n/a | — | conftest mocks `firestore.client()` |
| Google Cloud Console access | manual deploy, Secret Manager, max-instances | user-side | — | none — deploy/secret/max-instances are user operational steps |

**No in-repo dependency blocks execution.** Deploy, Secret Manager secret creation, secret reference, and max-instances are **manual Console actions by the user** — the plan must emit them as `checkpoint:human-verify` operational tasks, not code tasks. Local validator tests are the in-repo gate.

## Runtime State Inventory

> This phase adds a NEW data model rather than renaming; included for the data-migration angle.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | Existing `leaderboard/{machine_id}` docs in Firestore (all-time). New `weekly` collection is additive. | All-time untouched (D-08). New weekly docs created on next submission — no backfill needed (weekly history starts empty; acceptable). |
| Live service config | 2 deployed Gen2 functions in asia-southeast1 (Console, not git): need MAX_SCORE redeploy, HMAC secret reference, max-instances cap | Manual Console redeploy + secret + max-instances (user) |
| Secrets/env vars | NEW: `LEADERBOARD_HMAC_SECRET` (Secret Manager), `REQUIRE_SIGNATURE` (env var, default false) | Create in Console; same secret consumed by Phase 5 client |
| Firestore indexes | NEW composite index `weekly`: `week_id ASC, score DESC` | Create via auto-generated Console link on first query, or `firestore.indexes.json` |
| Build artifacts | None — Cloud Functions deployed from source dir; no compiled artifact | None |

**Note:** Existing leaderboard data has no `week_id` and is the all-time board only — that is correct and intended (D-08). The weekly board legitimately starts empty and fills as players submit. No data migration of existing docs is required.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Canonical JSON (Option A) is the chosen HMAC serialization | HMAC Scheme | Phase 5 client must match exactly; wrong choice → client/server signature mismatch. Low — both options work; lock in planning |
| A2 | HMAC-SHA256 + hex transport | HMAC Scheme | Standard; CONTEXT recommends. Very low |
| A3 | Default scope = `week` | Scope Parameter | Changes shipped-exe display on redeploy before Phase 6 toggle. **Confirm with user** |
| A4 | Lazy-prune scope = delete `{machine_id}_{week two-back}` per write | Week-Bucket Storage | Stale older weeks linger if a machine goes quiet; harmless clutter (matches D-09 "harmless until next write"). Low |
| A5 | Secret in Secret Manager (vs plain env var) | HMAC Scheme | Either works; Secret Manager is the better default. Low |
| A6 | max-instances 3–5 | Max-Instances Cap | Too low could throttle a popular moment; tune to friends-scale. Low — user sets in Console |
| A7 | `REQUIRE_SIGNATURE` env-flag name/default-false | Grace-Period Logic | Naming only; behavior is D-02-locked. Very low |

## Open Questions (RESOLVED)

1. **Default scope for the param-less call (A3).**
   - Known: existing exe sends no `scope`; CONTEXT recommends defaulting to `week`.
   - Unclear: whether showing the weekly board to the already-shipped exe (pre-Phase-6) is desired, or whether `all` should be the no-param default until the toggle ships.
   - Recommendation: go with CONTEXT's `week`, but flag for one-line user confirmation in planning/discuss.
   - **Resolution:** RESOLVED — user confirmed default `scope=week` during plan-phase (accepting the deployed exe shows the weekly board on redeploy pre-Phase-6). Locked via D-08 / 04-CONTEXT and implemented in 04-03-PLAN.

2. **`is_new_best` weekly vs all-time semantics.**
   - Known: existing tests assert all-time semantics.
   - Recommendation: keep `is_new_best` = all-time; add `is_new_weekly_best` only if a consumer needs it (none until Phase 6).
   - **Resolution:** RESOLVED — `is_new_best` keeps all-time semantics; no new field added (none needed until Phase 6). See Pitfall 5; implemented in 04-02-PLAN.

3. **Prune exactness (A4).**
   - Known: D-09 wants current + last week kept; older lazily pruned; no query/scheduler.
   - Recommendation: per-write delete of the two-weeks-back doc id keeps footprint bounded without a query; confirm this is sufficient in planning.
   - **Resolution:** RESOLVED — per-write `delete()` of the two-weeks-back doc id (`previous_week_id(previous_week_id(cur))`). Locked via A4 / D-09; implemented in 04-02-PLAN.

## Sources

### Primary (HIGH confidence)
- Codebase: `cloud_functions/submit_score/main.py`, `get_leaderboard/main.py`, `api_service.py`, `settings.py`, `tests/conftest.py`, `tests/test_*.py` — current baseline, mock seam, request shape `[VERIFIED]`
- `git log/status cloud_functions/` — clean baseline at `38417e5` `[VERIFIED 2026-06-14]`
- `.venv/Scripts/python.exe` week-math execution — boundary cases verified `[VERIFIED 2026-06-14]`
- Python stdlib docs: `hmac.compare_digest`, `datetime` utcnow deprecation `[CITED: docs.python.org]`
- cloud.google.com/functions/docs/configuring/secrets — Gen2 secret-as-env-var `[CITED]`

### Secondary (MEDIUM confidence)
- WebSearch 2026-06-14: Gen2 Console secret reference + max-instances (default 100, settable in Console/CLI) — cross-checked against Google docs links
- Context7 `/firebase/firebase-functions` resolved — confirmed the SDK exists but is NOT what this project uses (raw functions_framework), so its `secrets=[]`/`SecretParam` API does not apply here

### Tertiary (LOW confidence)
- None relied upon for load-bearing claims.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all stdlib + already-pinned deps, verified in requirements.txt
- HMAC scheme: HIGH for mechanism (stdlib), MEDIUM for serialization choice (A1, lock in planning)
- Secret/deploy: HIGH — confirmed Gen2/Cloud Run model; Console-managed
- Week math: HIGH — executed and verified against boundaries
- Data model / transaction ordering: HIGH for the pattern, the read-before-write ordering is the key review item
- Pitfalls: HIGH — derived from the actual mock seam and Firestore transaction rules

**Research date:** 2026-06-14
**Valid until:** 2026-07-14 (stable — stdlib + established GCF model; re-verify only if Google changes Gen2 Console secret UI)
