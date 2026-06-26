---
phase: 04-server-hardening-weekly-data-model
plan: 02
subsystem: api
tags: [hmac, cloud-functions, leaderboard, weekly, permanent-initials, firestore-transaction, anti-cheat]

# Dependency graph
requires:
  - phase: 04-01
    provides: leaderboard_crypto helper (verify_signature, current_week_id, previous_week_id)
provides:
  - Hardened submit_score enforcement boundary (MAX_SCORE 50k, HMAC grace gate, permanent initials, weekly write + lazy prune in one transaction)
  - weekly Firestore collection, doc-id scheme {machine_id}_{week_id}, fields {initials, score, machine_id, week_id, updated_at}
  - REQUIRE_SIGNATURE env flag (call-time, default false) governing the P4->P5 grace window
affects: [04-03-get-leaderboard-scope, 05-client-identity-hardening, 06-in-game-weekly-boards]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Deploy-bare / harness-relative import fallback (try import leaderboard_crypto except ModuleNotFoundError: from . import ...) so the same file works at Gen2 deploy and under the test package import"
    - "Firestore transaction reads-before-writes invariant kept explicit (READS / DECIDE / WRITES phases) and documented in a comment because MagicMock tests cannot catch a violation"
    - "Multi-collection mock seam: db.collection side_effect keyed on collection name to give the all-time and weekly docs distinct snapshots"

key-files:
  created: []
  modified:
    - cloud_functions/submit_score/main.py
    - tests/test_submit_score.py

key-decisions:
  - "MAX_SCORE lowered 500_000 -> 50_000 (D-01); existing range guard enforces it, no other validation change"
  - "Grace matrix read at call time: unsigned accepted+logged when REQUIRE_SIGNATURE off, rejected 401 when on; an INVALID signature is rejected 401 regardless of the flag"
  - "Permanent initials: original locked initials kept on an existing all-time doc (never the new submission's); first submission locks; .get('initials', initials) fallback keeps existing test_is_new_best_* green"
  - "Weekly doc written only-if-higher (one best row per machine per week); week_id from server time only (D-06); week_id stored as a field for the Plan 03 composite-index query"
  - "Lazy prune deletes the two-weeks-back weekly doc per write (D-09/A4) — harmless no-op delete, no prior read, keeps current+last week"
  - "is_new_best keeps ALL-TIME semantics; weekly best computed independently and never added to the response (no consumer until Phase 6)"

patterns-established:
  - "All Firestore .get() calls precede all .set()/.delete() inside @firestore.transactional, verified by eye + documented INVARIANT comment"

requirements-completed: [COMP-01, COMP-02, COMP-03, BOARD-01]

# Metrics
duration: ~10min
completed: 2026-06-19
---

# Phase 4 Plan 02: submit_score Hardening Summary

**Turned submit_score into the real enforcement boundary: 50k sanity ceiling, HMAC grace-period gate, server-locked permanent initials, and a week-bucketed write + lazy prune — all four landing in one Firestore transaction that reads before it writes.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-19
- **Tasks:** 2 (both TDD)
- **Files modified:** 2

## Accomplishments
- **D-01 (COMP-02):** `MAX_SCORE` lowered `500_000` -> `50_000`; the existing range guard now enforces the new ceiling (50001 -> 400, 50000 accepted).
- **D-02/D-03 (COMP-01):** HMAC grace gate using the Plan-01 `verify_signature`. Unsigned + grace off -> accept and log; unsigned + `REQUIRE_SIGNATURE=true` -> 401; invalid/forged signature -> 401 regardless of the flag; valid HMAC -> accept. Flag + secret read at call time; canonical message recomputed from parsed typed values, never the raw body.
- **D-05 (COMP-03):** Permanent initials — on an existing all-time doc the originally-stored initials are kept (the new submission's differing initials are never written), the score still updates; first submission locks the initials.
- **D-06..D-09 (BOARD-01):** A successful submit writes a weekly doc `{machine_id}_{week_id}` (server-time week_id, stored as a field) only-if-higher, and lazily prunes the two-weeks-back weekly doc — all inside the same transaction as the all-time write.
- **Reads-before-writes:** `_update_score` is structured READS -> DECIDE -> WRITES/DELETES with both `.get()` calls before any `.set()`/`.delete()`, verified by eye and documented with an INVARIANT comment (MagicMock cannot catch a violation).
- Full suite green: 82 passed, 9 skipped (golden bless-only); existing `test_is_new_best_*` unchanged and green.

## Task Commits

1. **Task 1 RED** — `63b1e9c` (test): failing tests for the 50k ceiling + HMAC grace matrix.
2. **Task 1 GREEN** — `168cc1f` (feat): MAX_SCORE 50k + HMAC grace gate + helper import fallback.
3. **Task 2 RED** — `09a967b` (test): failing tests for permanent initials + weekly write + lazy prune (+ multi-doc mock seam).
4. **Task 2 GREEN** — `28bfaab` (feat): permanent initials + weekly write + lazy prune in one transaction.

_REFACTOR phase: none needed for either task — implementation was clean on first GREEN._

## Files Created/Modified
- `cloud_functions/submit_score/main.py` — MAX_SCORE constant, `leaderboard_crypto` import (deploy-bare/harness-relative fallback), HMAC grace gate after the 400 validators, rewritten `@firestore.transactional _update_score` (all-time + weekly read-modify-write + lazy prune), handler builds the weekly + stale doc refs and passes them in.
- `tests/test_submit_score.py` — boundary updated to 50001, added 50000-accepted, full HMAC grace matrix (5 tests with a self-consistent `_sign` helper), D-05 keep-original + first-lock, BOARD-01 weekly write + week_id field, D-09 lazy-prune delete; added `_wire_multi_doc` multi-collection mock helper.

## Decisions Made
See frontmatter `key-decisions`. The load-bearing one for downstream plans: the `weekly` collection doc-id is `{machine_id}_{week_id}` with `week_id` stored as a field, which is what Plan 03's `scope=week` composite-index query (`week_id == cur, order_by score desc`) will read.

## Deviations from Plan

None - plan executed exactly as written. (The deploy-bare/harness-relative import fallback in `main.py` is the import mechanism the plan called for — "add `import leaderboard_crypto` ... the helper lives in the same dir"; the try/except is required because the test harness imports `main.py` as a package member while Gen2 deploy imports from the dir root. This is the standard implementation of the plan's import instruction, not a deviation.)

## Issues Encountered
None. Baseline was green (11 submit_score tests) before any change; RED failed as expected at each step; GREEN passed first try both tasks.

## Threat Model Coverage
- **T-04-01 (forged/unsigned, Spoofing)** — mitigated: invalid sig rejected 401 always; missing sig rejected when `REQUIRE_SIGNATURE` on.
- **T-04-03 (lifted signature, Tampering)** — mitigated via the Plan-01 helper binding machine_id+initials+score into the signed material.
- **T-04-06 (impossible score, Tampering)** — mitigated: MAX_SCORE 50_000.
- **T-04-07 (tag-swap, Tampering)** — mitigated: permanent-initials lock; new differing initials never written.
- **T-04-08 (week spoofing, Spoofing)** — mitigated: week_id from `datetime.now(timezone.utc)` (helper) only; no client timestamp read.
- **T-04-10 (logging disclosure, Info Disclosure)** — mitigated: grace log emits `mid={machine_id[:3]}***`, never the secret or full machine_id.
- **T-04-09 (replay)** / **T-04-SC (dependency installs)** — accepted residuals per plan; no packages installed this phase.

## User Setup Required
None in-repo. Operational (deferred to deploy, per RESEARCH, not this plan): create `LEADERBOARD_HMAC_SECRET` in Secret Manager and reference it as an env var on the deployed function; set `REQUIRE_SIGNATURE` (default off until Phase 5 ships the signed client); create the `weekly` composite index (`week_id ASC, score DESC`) — surfaced by Plan 03's first weekly query. These have no in-repo artifact to assert.

## Next Phase Readiness
- Plan 03 (`get_leaderboard` scope) can query the `weekly` collection by `week_id == current_week_id()` ordered by score; the field shape `{initials, score, machine_id, week_id, updated_at}` is in place.
- Phase 5 client signing verifies against the same canonical-JSON contract; flipping `REQUIRE_SIGNATURE=true` after Phase 5 ships closes the grace window with no code change here.

## Self-Check: PASSED

- `cloud_functions/submit_score/main.py` exists with `MAX_SCORE = 50_000`, `collection("weekly")`, `current_week_id`, `previous_week_id`, INVARIANT comment (grep-verified).
- `tests/test_submit_score.py` exists; full suite 82 passed / 9 skipped.
- Commits 63b1e9c, 168cc1f, 09a967b, 28bfaab all present in git log.

---
*Phase: 04-server-hardening-weekly-data-model*
*Completed: 2026-06-19*
