---
phase: 04-server-hardening-weekly-data-model
verified: 2026-06-19T08:00:00Z
status: passed
score: 5/5 must-haves verified
human_verified: "2026-06-19 — all 3 live UAT checks passed on revisions pacman-00006-ltj / get-leaderboard-00004-rfr (see 04-HUMAN-UAT.md)"
overrides_applied: 0
human_verification:
  - test: "Confirm the live submit_score service (pacman) rejects a POST with a VALID but intentionally incorrect HMAC signature — i.e. a properly formed hex signature computed under a WRONG key — returning 401."
    expected: "HTTP 401 {success: false, error: 'Invalid signature'}"
    why_human: "The orchestrator smoke-checked bogus signatures; verifier cannot re-run live curl against the deployed Cloud Run service. The valid-signing path (correct key) is deferred to Phase 5 by design."
  - test: "Confirm the live get_leaderboard service returns a non-empty weekly board once at least one score is submitted through the hardened path (weekly collection populated). Use the param-less GET URL."
    expected: "HTTP 200 with entries array containing at least one {initials, score} object, no machine_id or week_id fields present"
    why_human: "Verifier cannot submit a score live (no signed client yet; grace mode only). The weekly board correctly returned empty at smoke-check time because no weekly-bucketed scores exist yet. This check confirms the data path end-to-end once a score arrives."
---

# Phase 4: Server Hardening & Weekly Data Model — Verification Report

**Phase Goal:** The Cloud Functions become the real enforcement boundary and the single source of weekly/all-time score data that every other feature consumes.
**Verified:** 2026-06-19T08:00:00Z
**Status:** passed (human verification completed 2026-06-19 — all 3 live checks green; see 04-HUMAN-UAT.md)
**Re-verification:** No — initial verification

## Goal Achievement

The phase goal requires the Cloud Functions to be (a) the enforcement boundary — rejecting forged/invalid/over-ceiling/initials-swap attempts — and (b) the single source of weekly and all-time data. All five success criteria are verified in the codebase and locally testable code. Live deployment evidence from the runtime_evidence block and commit history corroborates production readiness. Two items require human confirmation because they involve live Cloud Run behavior that cannot be exercised programmatically without the signed client.

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A submission whose HMAC signature is missing or invalid (raw curl) is rejected and does not appear on any board | VERIFIED | `submit_score/main.py` lines 123-130: `signature is None + require_sig=True -> 401`; `verify_signature() returns False -> 401` regardless of grace flag. `test_unsigned_rejected_when_required`, `test_invalid_signature_rejected_when_grace`, `test_invalid_signature_rejected_when_required` all pass. Runtime evidence: POST with bogus signature -> HTTP 401 confirmed live. |
| 2 | A score above the sanity ceiling (MAX_SCORE=50_000) is rejected and not recorded | VERIFIED | `submit_score/main.py` line 21: `MAX_SCORE = 50_000`; line 109: `bool or not isinstance int or score < 0 or score > MAX_SCORE -> 400`. `test_score_over_max_returns_400` (50001 -> 400) and `test_score_at_max_accepted` (50000 -> 200) both pass. WR-01 bool-score also rejected (post-review fix commit a152189). |
| 3 | Once a machine has submitted initials, a later submission cannot change those initials (original retained) | VERIFIED | `_update_score` (main.py lines 42-50): `locked_initials = stored_all.get("initials", initials)` on an existing doc; new submission initials never written. `test_keep_original_initials_on_later_submission` asserts `written["initials"] == "BOB"` and `!= "EVE"`; `test_first_submission_locks_initials` asserts lock on first write. Both pass. |
| 4 | Scores are week-bucketed (Monday 00:00 UTC reset); get_leaderboard returns current-week OR all-time top scores by requested scope | VERIFIED | `current_week_id()` in leaderboard_crypto.py lines 66-77 verified by boundary tests (Mon 00:00:00, Sun 23:59:59, Mon 00:00:01). `submit_score/main.py` writes `weekly/{machine_id}_{week_id}` from server time only. `get_leaderboard/main.py` lines 34-56: scope-aware branch (`week` queries `weekly.where(week_id==)`, `all` queries `leaderboard`). 46/46 phase test suite tests pass. Runtime evidence: param-less GET -> 200 `{"entries":[]}` (empty this week); `?scope=all` -> 200 with existing all-time entries. Composite index Enabled (id `CICAgOjXh4EK`). |
| 5 | The v1.0 cloud-function validator tests (TST-03) still pass and the CI golden net (ghost-AI traces + determinism guard) stays green | VERIFIED | Full suite: 92 passed, 9 skipped. The 9 skipped are the golden bless-only tests (unchanged from pre-phase baseline). Ghost-AI traces and determinism guard are untouched — no ghost-AI code was modified in this phase. |

**Score:** 5/5 truths verified

### Deferred Items

None. The "valid signed submission accepted" half of criterion 1 is a documented design decision (Phase 5 ships the signing client; Phase 4 proves the rejection path against the known key with REQUIRE_SIGNATURE=false grace window). This is not a gap — it is an explicit seam stated in the runtime_evidence.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cloud_functions/submit_score/leaderboard_crypto.py` | HMAC verify + week math helper | VERIFIED | 84 lines; all 4 functions present: `canonical_message`, `verify_signature`, `current_week_id`, `previous_week_id`. Secret read via `os.environ.get` at call time (post-review fix: fail-closed for non-string/non-ASCII sig and missing secret). |
| `cloud_functions/get_leaderboard/leaderboard_crypto.py` | Byte-identical copy for get_leaderboard | VERIFIED | Byte-identical to submit_score copy; confirmed by `test_function_dir_copies_are_byte_identical` (PASS) and direct file read — every line matches. |
| `tests/test_leaderboard_crypto.py` | Unit tests for helper + boundary cases | VERIFIED | 14 tests: canonical message exact bytes, verify signature (valid/wrong/missing/lifted/non-string/non-ASCII/missing-secret), week boundary cases, byte-identity drift guard. All pass. |
| `cloud_functions/submit_score/main.py` | Hardened submit_score: MAX_SCORE 50k, HMAC gate, permanent initials, weekly write + lazy prune | VERIFIED | `MAX_SCORE = 50_000` (line 21). HMAC grace matrix lines 122-130. Permanent initials D-05 in `_update_score` (lines 42-50). Weekly write lines 66-75. Lazy prune line 79. INVARIANT comment documents reads-before-writes. |
| `tests/test_submit_score.py` | Extended validator + HMAC + permanent-initials + weekly-write tests | VERIFIED | 24 tests total. Includes HMAC grace matrix (5 cells + valid-signature path), bool-score reject (WR-01), D-05 keep-original/first-lock, BOARD-01 weekly write + field check, D-09 lazy-prune delete. All pass. |
| `cloud_functions/get_leaderboard/main.py` | Scope-aware leaderboard read (week\|all), machine_id-out projection | VERIFIED | Scope parse lines 34-35 (default/garbage -> week). `all` branch line 39-45 (leaderboard collection). `week` branch lines 46-56 (weekly.where(week_id==).order_by.limit). Projection line 63: `{initials, score}` only. |
| `tests/test_get_leaderboard.py` | Scope=all / scope=week / default / projection tests | VERIFIED | 11 tests; 6 new scope tests + rewired default-week chain. `test_weekly_path_projects_only_initials_and_score` proves machine_id never leaks on weekly path. All pass. |
| `cloud_functions/DEPLOY.md` | Operational deploy/secret/index/max-instances checklist | VERIFIED | All 6 steps present. Contains `LEADERBOARD_HMAC_SECRET`, `REQUIRE_SIGNATURE`, `leaderboard-hmac-secret`, `week_id ASC, score DESC`, max-instances. Secret value not committed. Phase 5 seam noted. gcloud path appended. |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `submit_score/main.py` | `leaderboard_crypto.verify_signature` | try/except import fallback + call at line 129 | WIRED | `leaderboard_crypto.verify_signature(machine_id, initials, score, signature)` called in HMAC gate |
| `submit_score/main.py` | `leaderboard_crypto.current_week_id` | call at line 134 | WIRED | `week_id = leaderboard_crypto.current_week_id()` — server time only |
| `submit_score/main.py` | `leaderboard_crypto.previous_week_id` | call at lines 135-137 | WIRED | Used twice to compute two-weeks-back stale doc |
| `submit_score/main.py` | `collection("weekly")` doc `{machine_id}_{week_id}` | `db.collection("weekly").document(...)` line 140 | WIRED | Weekly write inside `_update_score` transaction |
| `submit_score/leaderboard_crypto.py` | `os.environ.get("LEADERBOARD_HMAC_SECRET")` | read at call time inside `verify_signature` line 54 | WIRED | Post-review fix uses `.get()` (fail-closed) not subscript; no module-level capture |
| `get_leaderboard/main.py` | `leaderboard_crypto.current_week_id` | call at line 53 | WIRED | `leaderboard_crypto.current_week_id()` in weekly `where` filter |
| `get_leaderboard/main.py` | `collection("weekly").where("week_id", ...)` | line 52-53 | WIRED | Weekly query with equality filter on `week_id` |
| `cloud_functions/DEPLOY.md` | Secret Manager secret `leaderboard-hmac-secret` | documented Console/gcloud procedure | WIRED | Step 1-2 document creation + env reference; live deploy confirmed `leaderboard-hmac-secret:latest` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `submit_score/main.py` | `is_new_best` (response field) | `_update_score` reads `all_time_snap.to_dict()` from Firestore; returns `all_time_best` bool | Yes — score comparison against live Firestore all-time doc | FLOWING |
| `submit_score/main.py` | `locked_initials` (written to weekly + all-time docs) | `stored_all.get("initials", initials)` from `all_time_snap` | Yes — reads from existing Firestore doc; falls back to submission value on first submit | FLOWING |
| `get_leaderboard/main.py` | `entries` (response body) | `query.stream()` against either `leaderboard` or `weekly` Firestore collection | Yes — real Firestore queries (index-backed for weekly path; confirmed Enabled per DEPLOY.md / runtime evidence) | FLOWING |

### Behavioral Spot-Checks

Step 7b: These are Cloud Run services — cannot invoke live HTTP without the running service URL being curl-accessible from this environment. The runtime_evidence block serves as the authoritative behavioral record (provided by orchestrator at verification time):

| Behavior | Evidence Source | Result | Status |
|----------|----------------|--------|--------|
| POST with bogus signature -> 401 | Orchestrator runtime_evidence: `POST with bogus signature -> HTTP 401 {"success":false,"error":"Invalid signature"}` | HTTP 401, correct body | PASS |
| GET param-less (weekly default) -> 200 | Orchestrator runtime_evidence: `GET get_leaderboard (param-less weekly default) -> HTTP 200 {"entries":[]}` | HTTP 200, index serving | PASS |
| GET `?scope=all` -> 200 with initials+score only | Orchestrator runtime_evidence: `GET ?scope=all -> HTTP 200 [{"initials":"JAP","score":7540},{"initials":"JEM","score":4140}]` | HTTP 200, no machine_id | PASS |
| 92 local tests pass | Direct: `.venv/Scripts/python.exe -m pytest --tb=no -q` | `92 passed, 9 skipped` | PASS |

### Probe Execution

No `scripts/*/tests/probe-*.sh` probes declared or conventional for this phase type. Step 7c: SKIPPED (no probe scripts; phase is a manual-deploy phase with human-verify checkpoints as the gate).

### Requirements Coverage

| Requirement | Source Plan(s) | Description | Status | Evidence |
|-------------|---------------|-------------|--------|---------|
| COMP-01 | 04-01, 04-02, 04-04 | Server verifies HMAC; rejects forged/unsigned | SATISFIED | `verify_signature` in leaderboard_crypto; HMAC grace matrix in submit_score/main.py; live 401 smoke check confirmed |
| COMP-02 | 04-02 | Server rejects scores above sanity ceiling (50k) | SATISFIED | `MAX_SCORE = 50_000`; `isinstance(score, bool) or not isinstance(score, int) or score > MAX_SCORE -> 400`; tests pass |
| COMP-03 | 04-02 | Server enforces permanent initials — locked on first submission | SATISFIED | `_update_score` D-05 logic; `test_keep_original_initials_on_later_submission` passes |
| BOARD-01 | 04-01, 04-02, 04-03, 04-04 | Scores week-bucketed; weekly board resets Monday 00:00 UTC | SATISFIED | `current_week_id()` Monday-UTC math; weekly write in transaction; scope=week query; Enabled composite index |
| BOARD-02 | 04-03, 04-04 | All-time board retained alongside weekly | SATISFIED | `scope=all` branch in get_leaderboard queries `leaderboard` collection unchanged; `test_scope_all_queries_leaderboard` passes; live `?scope=all` returns all-time entries |

No orphaned requirements: REQUIREMENTS.md traceability table maps COMP-01, COMP-02, COMP-03, BOARD-01, BOARD-02 all to Phase 4. All 5 are accounted for and satisfied.

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| (none) | — | — | — |

No `TBD`, `FIXME`, or `XXX` markers found in any phase-modified file (`cloud_functions/submit_score/main.py`, `cloud_functions/submit_score/leaderboard_crypto.py`, `cloud_functions/get_leaderboard/main.py`, `cloud_functions/get_leaderboard/leaderboard_crypto.py`, `tests/test_leaderboard_crypto.py`, `tests/test_submit_score.py`, `tests/test_get_leaderboard.py`, `cloud_functions/DEPLOY.md`).

Code review findings CR-01 (verify_signature fail-closed) and WR-01 (bool score reject) were both fixed in commits 0f48f55 and a152189 before this verification. The remaining review findings (WR-02 through WR-05, IN-01 through IN-03) are warnings/info flagged in 04-REVIEW.md — WR-02, WR-03 are input validation improvements not required for Phase 4 success criteria and are not phase-blocking.

### Human Verification Required

### 1. Live invalid-signature rejection (COMP-01 enforcement path — complete cell)

**Test:** POST to the live submit_score URL (`https://pacman-991339031546.asia-southeast1.run.app`) with a body containing a well-formed HMAC hex digest computed under a WRONG key (not the real `leaderboard-hmac-secret`). Example: compute `hmac.new(b"wrong-key", canonical_msg, sha256).hexdigest()` and include as `"signature"`.
**Expected:** HTTP 401 `{"success": false, "error": "Invalid signature"}`. The score must NOT appear in the all-time or weekly board.
**Why human:** Verifier cannot programmatically curl a live Cloud Run service without network access. The orchestrator smoke-checked a bogus non-hex string; this check confirms the HMAC comparison path specifically (not just the type-check fast path).

### 2. Weekly board populated end-to-end after a live submission

**Test:** Submit a score through the grace path (no signature required while `REQUIRE_SIGNATURE=false`). Then perform a param-less GET to `https://get-leaderboard-991339031546.asia-southeast1.run.app` and verify the weekly board reflects the submitted score.
**Expected:** HTTP 200 with `{"entries": [...]}` containing the submitted `{initials, score}`, no `machine_id` or `week_id` in any entry.
**Why human:** The smoke-check weekly GET returned `{"entries":[]}` because no weekly-bucketed scores existed at that moment. This confirms the write-then-read data path end-to-end under the live weekly model.

---

### Gaps Summary

No gaps. All 5 success criteria are verifiably implemented and tested in the codebase. The two human verification items above are operational confidence checks for the live deployment, not code gaps.

The code review findings that were blockers (CR-01, WR-01) have been fixed and are verified green in the test suite. Remaining review findings (WR-02 through WR-05, IN-01 through IN-03) are hardening recommendations for future phases, none of which are required by Phase 4's success criteria.

---

_Verified: 2026-06-19T08:00:00Z_
_Verifier: Claude (gsd-verifier)_
