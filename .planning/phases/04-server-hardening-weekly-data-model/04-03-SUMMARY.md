---
phase: 04-server-hardening-weekly-data-model
plan: 03
subsystem: api
tags: [cloud-functions, firestore, leaderboard, weekly, scope, cors]

# Dependency graph
requires:
  - phase: 04-01
    provides: leaderboard_crypto.current_week_id (Monday-UTC week buckets, injectable now)
  - phase: 04-02
    provides: weekly collection docs ({machine_id}_{week_id}) carrying a week_id field for the composite-index query
provides:
  - Scope-aware get_leaderboard (?scope=week|all; default + unknown -> week)
  - Weekly read path filtering the weekly collection on week_id == current_week_id() (BOARD-01 read half)
  - All-time read path retained unchanged (BOARD-02 / D-08)
  - {initials, score}-only projection preserved on both scopes (D-10)
affects: [06-in-game-weekly-boards, 07-web-leaderboard-page]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tolerant query-param parsing: a reader endpoint never 400s on bad scope, falls back to week (T-04-12)"
    - "Server-time-only week filter via leaderboard_crypto.current_week_id() — no client-supplied week (T-04-08 / D-06)"

key-files:
  created: []
  modified:
    - cloud_functions/get_leaderboard/main.py
    - tests/test_get_leaderboard.py

key-decisions:
  - "Default scope = week (confirmed user decision): shipped v1.0 exe shows the weekly board on redeploy, accepted"
  - "Unknown/garbage scope falls back to week without a 400 (never crash the public reader)"
  - "Projection loop unchanged for both scopes — only {initials, score} ship; machine_id/week_id/updated_at never serialized (D-10)"
  - "Weekly query is equality(week_id)+order_by(score desc) — requires composite index week_id ASC, score DESC, created manually in Plan 04 Console (noted in a code comment)"

patterns-established:
  - "Scope branch in the read handler: scope=all keeps collection('leaderboard').order_by(score).limit(10); scope=week uses collection('weekly').where('week_id','==',cur).order_by(score).limit(10)"
  - "Test mock seam: weekly chain drives collection().where().order_by().limit().stream(); all-time chain drives collection().order_by().limit().stream()"

requirements-completed: [BOARD-01, BOARD-02]

# Metrics
duration: 8min
completed: 2026-06-19
---

# Phase 4 Plan 03: Scope-aware get_leaderboard Summary

**get_leaderboard now serves both the current-week board (default) and the all-time board via `?scope=week|all`, with the weekly path filtered to current_week_id() and the {initials, score} projection preserved on every path so machine_id never leaks.**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-18T22:29:33Z (approx, plan execution)
- **Completed:** 2026-06-19
- **Tasks:** 1 (TDD)
- **Files modified:** 2

## Accomplishments
- Scope-aware reader: `?scope=all` keeps the all-time query untouched (D-08); `?scope=week`, the param-less default, and any unknown/garbage value all query the `weekly` collection filtered to the current server-time week (BOARD-01 read half).
- Wired the weekly filter to `leaderboard_crypto.current_week_id()` (the 04-01 helper copy already in `get_leaderboard/`) — no reimplemented week-math, week id is server-time only (D-06 / T-04-08).
- Preserved the `{initials, score}` projection on BOTH scopes and the verbatim CORS headers + 500 error-tuple contract (Phase 7 dependency).
- Added 6 new scope tests (and rewired the 4 param-less tests onto the default-week chain); a weekly projection test proves machine_id/week_id/updated_at never leak. Full suite green: 88 passed, 9 skipped.

## Task Commits

TDD cycle (test -> feat; no refactor needed):

1. **Task 1 (RED): failing scope-aware tests** - `70789db` (test)
2. **Task 1 (GREEN): scope-aware get_leaderboard** - `0dfe916` (feat)

**Plan metadata:** committed separately (docs).

## Files Created/Modified
- `cloud_functions/get_leaderboard/main.py` - Added tolerant `scope` parse (default/unknown -> week), branched the query (all-time `leaderboard` vs weekly `weekly.where(week_id==current_week_id())`), imported `leaderboard_crypto` with the deploy/test dual-import fallback, kept the projection loop, CORS headers, OPTIONS 204, and 500 error tuple unchanged.
- `tests/test_get_leaderboard.py` - Rewired `_stub_stream` onto the weekly default chain, added `_stub_all_stream` for the all-time chain, added `query_string` to `make_request`, and added tests for scope=all, scope=week, default=week, garbage->week, OPTIONS preflight, and weekly-path projection.

## Decisions Made
- Default scope = week (confirmed user decision in the plan): the already-shipped v1.0 exe will display the weekly board on redeploy, before the Phase 6 toggle — accepted.
- Garbage/unknown scope falls back to week with no 400 (T-04-12 — never crash the public reader).
- The weekly equality+order query depends on the composite index `week_id ASC, score DESC`; this is created manually in Plan 04 (Console), documented in a code comment in `main.py` — not an in-repo artifact.

## Deviations from Plan

None - plan executed exactly as written. (The only judgment call: the existing param-less tests now exercise the default-week path, so `_stub_stream` was rewired onto the weekly chain and a separate `_stub_all_stream` helper added for scope=all — this is exactly the re-wiring the plan's `<action>` calls for, not a deviation.)

## Issues Encountered
None.

## User Setup Required
None in this plan. The weekly query's composite index (`weekly`: `week_id ASC, score DESC`) is a manual Console step tracked by Plan 04 — without it, live `?scope=week` queries will fail until the index is built. No in-repo config asserts it.

## Next Phase Readiness
- Read half of the weekly board is live: Phase 6 (in-game weekly boards / got-passed banner) and Phase 7 (web leaderboard page) can consume `?scope=week` and `?scope=all` against this endpoint.
- CORS headers preserved verbatim for the Phase 7 web page dependency.
- Blocker for live use (not for code): the weekly composite index must be created in Plan 04 before `?scope=week` returns data in production.

## Self-Check: PASSED
- `cloud_functions/get_leaderboard/main.py` — FOUND (modified)
- `tests/test_get_leaderboard.py` — FOUND (modified)
- Commit `70789db` (test) — present
- Commit `0dfe916` (feat) — present

---
*Phase: 04-server-hardening-weekly-data-model*
*Completed: 2026-06-19*
