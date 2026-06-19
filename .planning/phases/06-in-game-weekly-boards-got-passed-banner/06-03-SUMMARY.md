---
phase: 06-in-game-weekly-boards-got-passed-banner
plan: 03
subsystem: client-marker-io
tags: [marker, got-passed-banner, weekly-boards, week-id, best-effort-io]
requires:
  - paths.user_data_path (Phase 5 — %LOCALAPPDATA%\PacMan\ storage seam)
  - cloud_functions/get_leaderboard/leaderboard_crypto.current_week_id (week-math parity reference)
provides:
  - settings.MARKER_FILE_NAME
  - settings.BANNER_FETCH_TIMEOUT_SECONDS
  - settings.BANNER_NAME_CAP
  - marker.client_current_week_id
  - marker.write_marker
  - marker.read_marker
affects:
  - Plan 06-04 (launch banner + board-open baseline consumes read_marker/write_marker)
tech-stack:
  added: []
  patterns:
    - "best-effort local IO (try/except, never raise) — mirrors local_storage._safe_remove"
    - "inline Monday-UTC week math mirroring the server (client has no server current_week_id)"
    - "unsigned plain-JSON marker — deliberate inverse of the signed identity blob (D-13)"
key-files:
  created:
    - marker.py
    - tests/test_marker.py
  modified:
    - settings.py
decisions:
  - "Marker is plain unsigned JSON {week_id, tracked_best, initials_above} — no HMAC/obfuscation (D-13); a wrong/edited marker is harmless (cosmetic banner only)."
  - "initials_above serialized as a sorted list for deterministic output (D-12); callers wrap back in set()."
  - "Week stamp computed inline mirroring server Monday-UTC math; verified byte-equal to server current_week_id for a pinned instant."
  - "read_marker discards stale-week markers (week_id != client_current_week_id) for a silent re-baseline on rollover."
metrics:
  duration: ~10min
  completed: 2026-06-20
  tasks: 2
  files: 3
---

# Phase 6 Plan 03: Last-Viewed Marker IO Summary

Unsigned best-effort last-viewed marker (`marker.py`) plus its three Phase-6 settings constants — plain-JSON `{week_id, tracked_best, initials_above}` IO that never raises, silently re-baselines on cold-start / corruption / week rollover, and computes a Monday-UTC week id byte-equal to the server's.

## What Was Built

- **`settings.py`** — three grouped Phase-6 constants under a D-13/D-09/D-06 comment: `MARKER_FILE_NAME = "last_viewed.json"`, `BANNER_FETCH_TIMEOUT_SECONDS = 2`, `BANNER_NAME_CAP = 3`. No new COLOR_*/FONT_* tokens (Phase 6 reuses existing ones per UI-SPEC).
- **`marker.py`** (new, stdlib-only: `json`, `datetime`, `paths`, `settings`):
  - `client_current_week_id(now=None)` — Monday-UTC `%Y-%m-%d`, injectable instant, mirrors the server's `current_week_id`.
  - `write_marker(week_id, tracked_best, initials_above)` — plain JSON to `paths.user_data_path(MARKER_FILE_NAME)`; `initials_above` serialized as a sorted list (D-12); entire body wrapped in try/except → swallows and returns. No obfuscation, no HMAC, no `{sig,blob}` envelope.
  - `read_marker()` — `None` on FileNotFoundError / JSONDecodeError / any exception (cold start) and on stale `week_id` (silent re-baseline, D-11/D-13); otherwise returns the marker dict. Never raises.
- **`tests/test_marker.py`** (new, 11 tests) — cold-start→None, malformed-JSON→None, same-week round-trip, plain-unsigned-JSON shape, stale-week→None, write-never-raises (dump failure + open failure), week-id Monday assertion, client/server week-id parity, no-signing-imports guard.

## How It Works

Plan 04's launch banner / board-open baseline reads the marker to compute "who passed you since you last looked" (RIVAL-01). Because the root client `leaderboard_crypto.py` has no `current_week_id`, the Monday-UTC stamp is computed inline in `marker.py`, mirroring the server helper exactly (verified by a pinned-instant parity test). The marker is the deliberate inverse of the Phase-5 signed identity blob: it controls no score and no server state, so it is intentionally unsigned — a missing/corrupt/wrong-week marker just triggers a one-time harmless re-baseline.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Hardened the no-signing test to scan executable code, not docstring prose**
- **Found during:** Task 2 (GREEN phase)
- **Issue:** The first version of `test_marker_module_has_no_signing_imports` substring-matched the whole source file for `obfuscate`/`hmac`/etc. It failed because `marker.py`'s docstring legitimately *explains* (in prose) that the marker is "unsigned or obfuscated" and references "HMAC" — the words appear only in documentation, never in code. The plan's intent (acceptance criterion: "does NOT import or call obfuscate/sign_identity_blob/sign_submission") is about code-level references, not prose.
- **Fix:** Rewrote the test to `ast.parse` the module and collect actual `Name`/`Attribute`/`Import`/`ImportFrom` identifiers, asserting the forbidden signing names are absent from executable code. This preserves the security intent while allowing the explanatory docstring.
- **Files modified:** tests/test_marker.py
- **Commit:** 3778883

## Threat Model Compliance

- **T-06-09 (DoS — marker IO crashing startup):** mitigated — both `read_marker` and `write_marker` wrap all IO in try/except and return silently (verified by `test_write_marker_never_raises_on_dump_failure` and `..._on_open_failure`).
- **T-06-10 (Tampering — malformed marker on load):** mitigated — `read_marker` returns `None` on any parse/IO error (verified by `test_read_marker_malformed_json_returns_none`).
- **T-06-08 / T-06-11 (accepted):** the marker is intentionally unsigned and stores only the player's own already-public board data; no signing path was added (verified by `test_marker_module_has_no_signing_imports`).

## Verification

- `marker.py` tests: `11 passed`.
- Full suite: `133 passed, 9 skipped in 61.72s` (the 9 skips are pre-existing; no regressions).
- Plan acceptance checks all pass: `import settings` prints `last_viewed.json 2 3`; week-id parity (`marker.client_current_week_id(n) == server.current_week_id(n)` for pinned `2026-06-17`) prints ok; no sig-bearing code names in `marker.py`; `marker` imports `paths` + `settings` and defines all three functions.

## Self-Check: PASSED

- FOUND: marker.py
- FOUND: tests/test_marker.py
- settings.py contains all 3 constants (grep count 6 = 3 defs + 3 comment mentions)
- FOUND commit f67210a (settings constants)
- FOUND commit 3f2555c (RED test)
- FOUND commit 3778883 (GREEN implementation)

## TDD Gate Compliance

- RED gate: `3f2555c test(06-03): add failing tests ...` (failed with ModuleNotFoundError: marker — confirmed before implementation).
- GREEN gate: `3778883 feat(06-03): implement unsigned best-effort last-viewed marker IO`.
- REFACTOR gate: none needed — implementation was minimal and clean.
