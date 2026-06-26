---
phase: 06-in-game-weekly-boards-got-passed-banner
plan: 02
subsystem: leaderboard-client
tags: [api, leaderboard, scope, timeout, tdd]
requires:
  - "Plan 01: server-side scope allow-list (scope=last_week|all, defaults to week)"
provides:
  - "api_service.get_leaderboard(scope=None, timeout=10) — scope-aware fetch with threaded timeout"
affects:
  - "Plan 04: board screen (fetches all/last_week) and launch banner (short timeout)"
tech-stack:
  added: []
  patterns:
    - "urllib.parse.urlencode for safe query-string assembly (no hand-concatenation)"
    - "request-capture test pattern: fake urlopen(req, timeout=None) captures URL + timeout"
key-files:
  created: []
  modified:
    - "api_service.py — get_leaderboard gains scope + timeout params"
    - "tests/test_api_service.py — 3 new request-capture tests"
decisions:
  - "scope=None default omits the query param entirely so the server defaults to the current week, preserving every existing no-arg caller"
  - "timeout default stays 10 in api_service; only the launch banner (Plan 04) passes the short value — short timeout NOT hardcoded here to avoid clobbering the board screen's 10s (Pitfall 2)"
metrics:
  duration: "~4 min"
  completed: "2026-06-20"
  tasks: 1
  files: 2
---

# Phase 6 Plan 02: Scope-aware get_leaderboard Summary

Added `scope` and `timeout` parameters to `ApiService.get_leaderboard` so the board screen can request specific boards (This Week / All Time / last_week) and the launch banner can use a short timeout — both riding on one stdlib-only signature change, with the no-arg caller and its tests unchanged.

## What Was Built

`api_service.get_leaderboard(self, scope=None, timeout=10)`:
- When `scope` is truthy, the query string is assembled with `urllib.parse.urlencode({'scope': scope})` and appended as `?scope=...` (escaped, never hand-concatenated — mitigates T-06-05 tampering).
- When `scope` is `None` (default), no query param is sent — the URL stays the bare base, so the server defaults to the current week. Every existing no-arg caller (`menu.py`) is preserved.
- `timeout` (default 10) is threaded into `urlopen(req, timeout=timeout)` instead of the prior literal `10`. The interactive board screen keeps its 10s; only the launch banner (Plan 04) will pass the short `BANNER_FETCH_TIMEOUT_SECONDS` (mitigates T-06-07 DoS without spurious "Could not connect" on slow connections).
- The `try/except Exception: return None` contract and the `return data.get("entries")` success path are unchanged — `None` = offline, `[]` = empty (mitigates T-06-06; malformed/forged responses degrade to `None`).

## How It Was Verified

TDD RED → GREEN:
- RED: three new request-capture tests added and confirmed failing with `TypeError: ... unexpected keyword argument 'scope'` (correct reason — signature didn't yet accept the param).
- GREEN: implemented the signature change; full `tests/test_api_service.py` passes 11/11, including the unchanged `test_get_leaderboard_success/_empty/_network_error` no-arg tests.

`C:/Users/James/Desktop/Projects/pacman-firebase/.venv/Scripts/python.exe -m pytest tests/test_api_service.py` → 11 passed.

New tests:
- `test_get_leaderboard_sends_scope_param` — `scope="last_week"` → URL contains `scope=last_week`; `scope="all"` → `scope=all`.
- `test_get_leaderboard_no_scope_omits_param` — no-arg call → URL equals the bare base, no `scope` substring.
- `test_get_leaderboard_passes_timeout` — `timeout=2` → captured timeout 2; no-arg → captured timeout 10.

## Deviations from Plan

None - plan executed exactly as written.

## TDD Gate Compliance

- RED gate: `test(06-02)` commit `50433ac` (failing tests committed before implementation).
- GREEN gate: `feat(06-02)` commit `50c29ed` (implementation, all tests pass).
- REFACTOR gate: none needed — implementation is minimal (3 added lines + 1 import) with nothing to clean up.

## Self-Check: PASSED
