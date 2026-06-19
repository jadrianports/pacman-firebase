---
phase: 06-in-game-weekly-boards-got-passed-banner
plan: 01
subsystem: leaderboard-backend
tags: [cloud-functions, get_leaderboard, weekly-boards, read-path, tdd]
requires:
  - "weekly collection retains last week's bucket (Phase 4 D-09)"
  - "leaderboard_crypto.previous_week_id / current_week_id (Phase 4 week math)"
  - "weekly composite index: week_id ASC, score DESC (Phase 4 D-11)"
provides:
  - "scope=last_week read branch on get_leaderboard returning previous week's top-10"
affects:
  - "cloud_functions/get_leaderboard/main.py"
tech-stack:
  added: []
  patterns:
    - "Tolerant scope allow-list parse (unknown -> week, never 400) extended in place"
    - "Server-time-only week selection (no client-supplied week_id) carried to last_week"
key-files:
  created: []
  modified:
    - cloud_functions/get_leaderboard/main.py
    - tests/test_get_leaderboard.py
decisions:
  - "last_week is the weekly chain with previous_week_id(current_week_id()) as the equality value; everything else (projection loop, return shape, index) reused unchanged"
  - "leaderboard_crypto.py left byte-for-byte unchanged — no new week math was needed (previous_week_id already existed)"
metrics:
  duration: ~5 min
  completed: 2026-06-19
  tasks: 1
  files: 2
  commits: 2
---

# Phase 6 Plan 01: get_leaderboard scope=last_week Read Branch Summary

Added a `scope=last_week` read branch to the `get_leaderboard` Cloud Function so the client can fetch the previous week's champion through the HTTP API (BOARD-04, D-01) — a pure read-path addition reusing the existing `previous_week_id(current_week_id())` week math, the `weekly` composite index, and the shared `{initials,score}`-only projection, with no data-model change.

## What Was Built

- **`cloud_functions/get_leaderboard/main.py`** — extended the tolerant scope allow-list from `("week", "all")` to `("week", "all", "last_week")`, and inserted a new `elif scope == "last_week":` branch between the `all` and weekly `else` branches. The branch queries `db.collection("weekly").where("week_id", "==", leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())).order_by("score", DESC).limit(10)`, binding the same `query` variable so the shared `query.stream()` + projection loop + return tuple are reused unchanged. Helper called module-qualified, exactly mirroring the weekly branch's `current_week_id()` call.
- **`tests/test_get_leaderboard.py`** — two new validator tests:
  - `test_scope_last_week_queries_weekly_with_previous_week` — asserts 200, `collection("weekly")`, and `where("week_id", "==", previous_week_id(current_week_id()))`.
  - `test_scope_last_week_projects_only_initials_and_score` — asserts a doc with extra `machine_id`/`week_id`/`updated_at` fields is stripped to `{initials, score}` (D-10).

## How It Works

The branch is the current-week weekly query with one substitution: the equality value is `previous_week_id(current_week_id())` instead of `current_week_id()`. Both are computed from server time only (D-06), so the client cannot forge a week. Unknown/garbage scopes still silently fall back to `week` (never a 400) because `last_week` is now a *recognized* value while genuinely unknown strings are not. The response shape is identical across all three scopes: `{entries: [{initials, score}]}`.

## TDD Cycle

- **RED** (`c0e9c6e`): added both tests. `test_scope_last_week_queries_weekly_with_previous_week` failed with `Expected: where('week_id','==','2026-06-08')  Actual: where('week_id','==','2026-06-15')` — confirming the unrecognized `last_week` was falling back to the current week.
- **GREEN** (`17db9dc`): added the allow-list entry + `elif` branch; full suite (12 tests) green.
- **REFACTOR**: none needed — the branch is minimal and clones the existing weekly pattern.

## Verification

- `.venv/Scripts/python.exe -m pytest tests/test_get_leaderboard.py` → **12 passed**.
- `grep -v '^#' main.py | grep -c last_week` → 2 (allow-list + branch).
- `main.py` contains `elif scope == "last_week":` and `leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())`.
- Scope guard reads `if scope not in ("week", "all", "last_week"):`.
- `git diff --stat cloud_functions/get_leaderboard/leaderboard_crypto.py` → empty (byte-for-byte duplication invariant with submit_score's copy preserved).
- Dual-import block (main.py lines 13-16) unchanged.

## Deviations from Plan

None - plan executed exactly as written.

## Threat Surface

No new surface beyond the plan's `<threat_model>`. The branch adds no write path; the queried week is server-computed (T-06-03 mitigated), the scope is allow-list-gated (T-06-01 mitigated), and the projection strips all fields except `{initials, score}` (T-06-02 mitigated, verified by `test_scope_last_week_projects_only_initials_and_score`).

## Operator Note (not blocking this plan)

Live `scope=last_week` behavior requires a manual `get_leaderboard` redeploy (Google Cloud Console / Cloud Shell, per the api-refactor spec). The in-repo gate is the validator tests only; live BOARD-04 depends on the operator deploying. Surfaced for phase verification.

## Commits

- `c0e9c6e` — test(06-01): add failing tests for scope=last_week branch
- `17db9dc` — feat(06-01): add scope=last_week read branch to get_leaderboard

## Self-Check: PASSED
- FOUND: cloud_functions/get_leaderboard/main.py
- FOUND: tests/test_get_leaderboard.py
- FOUND: commit c0e9c6e
- FOUND: commit 17db9dc
