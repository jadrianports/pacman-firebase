---
phase: 06-in-game-weekly-boards-got-passed-banner
plan: 04
subsystem: leaderboard-client-ui
tags: [menu, weekly-boards, got-passed-banner, toggle, marker, graceful-degrade]
requires:
  - "Plan 01: get_leaderboard scope=last_week server branch"
  - "Plan 02: api_service.get_leaderboard(scope=None, timeout=10)"
  - "Plan 03: marker.read_marker/write_marker/client_current_week_id + settings.MARKER_FILE_NAME/BANNER_FETCH_TIMEOUT_SECONDS/BANNER_NAME_CAP"
provides:
  - "menu.run_leaderboard(screen, timer, api_service) -> This Week/All Time toggle, last-week subtitle, per-view states; RETURNS the fetched This Week entries (board-open seam O-3)"
  - "menu.run_main_menu(screen, timer, banner_text=None) -> renders the got-passed banner"
  - "menu._UNFETCHED sentinel; menu._show_loading helper"
  - "main._format_banner(names) cap=3 banner formatter"
  - "main.py launch banner compute + submit-path tracked-best update + board-open baseline rewrite"
affects:
  - "End of phase 06 — completes BOARD-03, BOARD-04, RIVAL-01 (UI/consumer slice)"
tech-stack:
  added: []
  patterns:
    - "Per-view lazy-cached toggle with object() sentinel (unfetched vs None-offline vs []-empty vs list-data)"
    - "Return-based board-open seam (run_leaderboard returns This Week entries; main.py owns all marker IO) — no duplicate network call"
    - "Single blocking short-timeout launch fetch, no threading (DoS-bounded ~2s)"
key-files:
  created: []
  modified:
    - menu.py
    - main.py
decisions:
  - "Board-open seam = O-3 (return-based): run_leaderboard RETURNS the fetched This Week entries; main.py recomputes initials_above and rewrites the marker exactly once per board open. Chosen over the in-screen marker-write seam to keep all marker IO in main.py (mirrors the existing identity/submit ownership), keep menu.py free of marker/identity imports, and guarantee one rewrite per open with no duplicate fetch."
  - "run_leaderboard signature UNCHANGED ((screen, timer, api_service)) — the seam is the return value, so no new params and no extra call-site arg threading."
  - "Tab indicator rendered as 5 separate font runs (< / This Week / | / All Time / >) blitted left-to-right so only the active label is yellow and all separators stay gray (D-03), centered at y=128."
  - "last_week subtitle uses a separate best-effort scope=last_week fetch issued once on open; absent/[]/None -> render nothing (no placeholder, D-16)."
metrics:
  duration: ~18 min
  completed: 2026-06-19
  tasks: 3
  files: 2
  commits: 3
---

# Phase 6 Plan 04: In-Game Weekly Boards & Got-Passed Banner Summary

Wired the consumer/UI slice that makes the weekly competition visible: a This Week / All Time toggle with a last-week champion subtitle and per-view empty/offline states in the board screen, plus a launch got-passed banner that names new passers since the last board view — all riding on the wave-1 scoped API + unsigned marker, with every offline/cold-start path degrading silently and the full suite green.

## What Was Built

- **`menu.py` — `_UNFETCHED` sentinel + `_show_loading` helper:** a module-level `_UNFETCHED = object()` distinguishes "view never fetched" from the three meaningful cache states (`None`=offline, `[]`=empty, `list`=data), resolving Pitfall 1. `_show_loading` factors the existing white centered "Loading..." frame so it can be shown both on open and on the first All Time toggle.
- **`menu.py` — `run_leaderboard` reshape (Task 1):** opens on This Week (D-02); LEFT/RIGHT flip `active` between `"week"`/`"all"`; All Time is lazy-fetched once on first toggle (D-14, shows "Loading..." then caches). The last-week champion subtitle (`Last week: XXX`) renders at y=128-ish (y=152) in gray on This Week only, hidden when the `scope=last_week` fetch returns None/[] (D-16). Tab indicator `< This Week | All Time >` at y=128 with the active label yellow and separators gray (D-03). Per-view empty states: This Week → `No scores yet this week. Be the first!`, All Time → preserved `No scores yet. Be the first!` (D-17). Offline string preserved per active view (D-15). The rank-1-yellow / rest-white / 50px-pitch entry render block is preserved (re-indented only). Hint replaced with `LEFT/RIGHT: switch board   ESC/ENTER: back`. **Board-open seam (O-3):** the function RETURNS the freshly-fetched This Week entries (the same list rendered, no extra fetch) on ESC/ENTER/QUIT.
- **`menu.py` — `run_main_menu` banner (Task 2):** new `banner_text=None` param; when truthy renders the banner in `COLOR_YELLOW` at `FONT_SMALL` centered y=230 (passive-notice idiom). With `banner_text=None` the menu is byte-identical to before.
- **`main.py` — wiring (Task 3):** added `import marker` and `BANNER_FETCH_TIMEOUT_SECONDS`/`BANNER_NAME_CAP` imports, plus `_format_banner(names)` (cap=3: list all ≤3, else first 3 + ` +{K} more`, always ` passed you this week!`). Three best-effort wirings:
  1. **Launch banner compute:** `marker.read_marker()`; if absent or no `tracked_best` → no banner. Else a short-timeout `api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)`; if None/empty → no banner. Else `above_now = {initials where score > tracked_best}`, `new_passers = sorted(above_now - initials_above)`, `banner_text = _format_banner(new_passers)`.
  2. **Submit-path tracked-best update:** on a successful submit, `tracked_best = max(tracked_best or 0, score)` and `marker.write_marker(client_current_week_id(), tracked_best, initials_above)`.
  3. **Board-open baseline rewrite:** `run_leaderboard` returns This Week entries; `banner_text` is cleared and (when entries present and `tracked_best` known) `initials_above` is recomputed and the marker rewritten — the only place `initials_above` resets (D-07/D-10).
  `banner_text`/`tracked_best`/`initials_above` persist across menu re-entries (the banner survives until the board is opened).

## Board-Open Seam (O-2/O-3) — for phase verification

**Final decision: O-3, return-based.** `run_leaderboard(screen, timer, api_service)` keeps its original signature and RETURNS the fetched This Week entries (`None` if offline, `[]` if empty, `list` on success). `main.py` owns the single marker rewrite at the board call site, recomputing `initials_above` from the returned entries and calling `marker.write_marker(...)` exactly once per board open. No marker/identity imports were added to `menu.py`, and there is no duplicate network call (the screen's already-fetched This Week list is reused). The marker is therefore rewritten exactly once per board open (and never when This Week was offline or the player has no tracked this-week best).

## How It Degrades (SC-4 graceful-degrade contract)

- Cold start / no marker → `read_marker()` None → `banner_text` None → straight to menu, no error.
- Marker present but no `tracked_best` (no this-week score yet) → no banner (D-05).
- Offline / slow launch fetch → `get_leaderboard` swallows to None → no banner; bounded by `BANNER_FETCH_TIMEOUT_SECONDS` (~2s), single blocking call, no threading, no retry (T-06-13 mitigated).
- One board view offline → that view shows `Could not connect to leaderboard.`; the other cached view still renders when toggled (D-15).
- last_week subtitle fetch fails → subtitle simply absent (D-16).
- All marker IO is best-effort (`read_marker`/`write_marker` swallow); a write failure cannot break submit or board exit (T-06-16 mitigated).

## Verification

- `.venv/Scripts/python.exe -m pytest -q` → **138 passed, 9 skipped** (identical to the pre-change baseline; no regressions, CI golden net untouched — this phase touches no sim/ghost code).
- `tests/check_main_wiring.py` → OK (Phase-5 wiring tokens `load_identity`/`sign_submission`/`identity_error`/`IDENTITY_STATUS_TAMPERED`/`_load_hmac_secret` all still present).
- Task 1 verify: `_UNFETCHED`, `K_LEFT`/`K_RIGHT`, `No scores yet this week. Be the first!`, `Last week:`, `LEFT/RIGHT: switch board` all present; `menu.py` parses.
- Task 2 verify: `banner_text` in `inspect.signature(menu.run_main_menu).parameters`; `menu.py` parses.
- Task 3 verify: `main.py` imports `marker` + `BANNER_FETCH_TIMEOUT_SECONDS`/`BANNER_NAME_CAP`; calls `get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)`; contains `_format_banner` with `+...more` / `passed you this week!`; calls `run_main_menu(..., banner_text=...)` and clears `banner_text = None` after the board; calls `marker.write_marker` in both submit and board-open paths and `marker.read_marker()` once at launch; `main.py` parses.
- `git diff --diff-filter=D 64719b7 HEAD` → no deletions; only `menu.py` + `main.py` changed (matches plan `files_modified`).

## Deviations from Plan

None - plan executed exactly as written. (The seam choice O-3 vs O-2 was explicitly delegated to this plan per the plan's `artifacts_this_phase_produces` / Task 1 action; O-3 was selected and documented above.)

## Threat Surface

No new surface beyond the plan's `<threat_model>`. The launch fetch is a short-timeout best-effort read feeding only the cosmetic banner (T-06-13 mitigated via `BANNER_FETCH_TIMEOUT_SECONDS`, single blocking call, no threading); the banner shows only board-public `{initials}` (T-06-14 — no machine_id/PII); spoofed/forged board data only mis-names the cosmetic banner with no score/server impact (T-06-12 accept); the marker is unsigned by design and editing it only changes the banner (T-06-15 accept); all marker IO is best-effort and cannot break submit/board flows (T-06-16 mitigated). No package installs (T-06-SC — stdlib + already-vendored pygame only).

## Known Stubs

None. All UI elements are wired to live data sources (`api_service.get_leaderboard` scoped fetches and the `marker` module); no hardcoded empty/placeholder data flows to render.

## Commits

- `337237c` — feat(06-04): board screen This Week/All Time toggle, last-week subtitle, per-view states
- `61b1f75` — feat(06-04): render optional got-passed banner on the main menu
- `43d0f46` — feat(06-04): wire launch banner, submit tracked-best update, board-open baseline

## Self-Check: PASSED

- FOUND: menu.py (modified — _UNFETCHED, run_leaderboard toggle, run_main_menu banner_text)
- FOUND: main.py (modified — _format_banner, launch/submit/board-open marker wiring)
- FOUND: .planning/phases/06-in-game-weekly-boards-got-passed-banner/06-04-SUMMARY.md
- FOUND: commit 337237c
- FOUND: commit 61b1f75
- FOUND: commit 43d0f46
