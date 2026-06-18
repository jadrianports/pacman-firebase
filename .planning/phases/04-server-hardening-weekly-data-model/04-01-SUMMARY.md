---
phase: 04-server-hardening-weekly-data-model
plan: 01
subsystem: api
tags: [hmac, sha256, cloud-functions, leaderboard, week-math, crypto, anti-cheat]

# Dependency graph
requires:
  - phase: 03-box-bug-fix-hygiene
    provides: reconciled cloud-function baseline (commit 38417e5) + CI-green validator tests
provides:
  - leaderboard_crypto.py shared helper (HMAC verify + Monday-UTC week math), byte-identical in both Gen2 function dirs
  - canonical_message wire-format contract (Option A canonical JSON) the Phase 5 client must reproduce
  - verify_signature / current_week_id / previous_week_id pure functions for Plans 02 and 03 to import
affects: [04-02-submit-score-hardening, 04-03-get-leaderboard-scope, 05-client-identity-hardening]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "stdlib-only crypto helper (json/hmac/hashlib/os) — no new runtime deps"
    - "Gen2 per-dir duplication: shared helper copied byte-identical into each function source dir, drift-guarded by a test"
    - "secret read at call time from os.environ (never a module constant)"

key-files:
  created:
    - cloud_functions/submit_score/leaderboard_crypto.py
    - cloud_functions/get_leaderboard/leaderboard_crypto.py
    - tests/test_leaderboard_crypto.py
  modified: []

key-decisions:
  - "Locked canonical JSON kwargs (sort_keys=True, separators=(',',':'), ensure_ascii=False) as the Phase 5 client wire-format contract"
  - "Secret read at call time inside verify_signature (Pitfall 4) — never captured at import"
  - "machine_id + initials + score all bound into the signed payload (D-03) so a signature cannot be lifted onto another identity"
  - "Helper duplicated byte-identical into both function dirs (Gen2 per-dir deploy) with a drift-guard test rather than a shared import"

patterns-established:
  - "Constant-time signature compare: hmac.compare_digest(expected, provided or ''), never =="
  - "Injectable now=None param on week-math so tests pin a deterministic week"

requirements-completed: [COMP-01, BOARD-01]

# Metrics
duration: ~12min
completed: 2026-06-19
---

# Phase 4 Plan 01: leaderboard_crypto Helper Summary

**Stdlib-only HMAC-SHA256 verification + Monday-UTC week-math helper, duplicated byte-identical into both Gen2 Cloud Function dirs, with the canonical-JSON wire format locked for the Phase 5 client.**

## Performance

- **Duration:** ~12 min
- **Started:** 2026-06-19
- **Tasks:** 2
- **Files modified:** 3 created

## Accomplishments
- `canonical_message` locks the exact byte serialization (Option A canonical JSON) the Phase 5 client must reproduce; score stays an int, keys sort to initials/machine_id/score.
- `verify_signature` does HMAC-SHA256 over the canonical payload, reads `LEADERBOARD_HMAC_SECRET` at call time, and constant-time compares — returns False for wrong/missing/lifted signatures.
- `current_week_id` / `previous_week_id` compute Monday-UTC week buckets with verified boundary behavior (Mon 00:00:00 → own Monday, Sun 23:59:59 → prior Monday, Mon 00:00:01 → new week).
- Helper duplicated byte-identical into both function dirs, guarded by a test so the copies can never silently drift.
- Baseline confirmed green (21 tests) before any source was touched.

## Task Commits

1. **Task 1: Confirm baseline green** — verification-only (no code change); `tests/test_submit_score.py tests/test_get_leaderboard.py tests/test_api_service.py` → 21 passed, cloud_functions working tree clean.
2. **Task 2 (TDD RED): failing tests for leaderboard_crypto** - `8939f60` (test)
3. **Task 2 (TDD GREEN): implement leaderboard_crypto helper** - `7aefa2a` (feat)

**Plan metadata:** see final docs commit.

_REFACTOR phase: none needed — implementation was clean on first GREEN._

## Files Created/Modified
- `cloud_functions/submit_score/leaderboard_crypto.py` - canonical copy: canonical_message, verify_signature, current_week_id, previous_week_id
- `cloud_functions/get_leaderboard/leaderboard_crypto.py` - byte-identical copy for the get_leaderboard Gen2 function dir
- `tests/test_leaderboard_crypto.py` - 11 unit tests covering exact-bytes serialization, HMAC valid/wrong/missing/machine-id-binding, week boundaries, and the cross-dir byte-identity drift guard

## Decisions Made
- Canonical JSON kwargs locked exactly (sort_keys=True, compact separators, ensure_ascii=False) as the Phase 5 client contract.
- Secret read at call time inside `verify_signature` (never a module constant) — Pitfall 4 / threat T-04-05.
- machine_id/initials/score all bound into the signed payload (D-03) — threat T-04-03.
- Byte-identical duplication into both Gen2 dirs (per-dir deploy) instead of a shared import, with a drift-guard test.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## Threat Model Coverage
All Plan-01-scoped STRIDE mitigations are implemented at the helper level:
- T-04-02 (delimiter injection) — canonical JSON, no raw `|` join.
- T-04-03 (lifted signature) — machine_id binding, cross-identity verify test asserts False.
- T-04-04 (timing oracle) — hmac.compare_digest constant-time compare.
- T-04-05 (secret in source/logs) — secret read from os.environ at call time, never a constant.
- T-04-01 (forged/unsigned) — verify_signature returns False for missing/invalid; the enforcement *decision* (rejecting the request) lands in Plan 02 as planned.

## User Setup Required
None - no external service configuration in this plan. (The `LEADERBOARD_HMAC_SECRET` env var is read at call time; provisioning it in Secret Manager is a later deploy concern, exercised in tests via monkeypatch.)

## Next Phase Readiness
- Plan 02 (submit_score hardening) and Plan 03 (get_leaderboard scope) can now `from leaderboard_crypto import ...` against a stable, tested contract.
- Phase 5 client signing has a locked canonical-JSON format to reproduce.

## Self-Check: PASSED

All 3 created files exist; all 3 task/RED/GREEN commits (8939f60, 7aefa2a, 710ee15) present in git log.

---
*Phase: 04-server-hardening-weekly-data-model*
*Completed: 2026-06-19*
