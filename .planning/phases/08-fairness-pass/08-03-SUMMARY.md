---
phase: 08-fairness-pass
plan: 03
subsystem: gameplay
tags: [player, cornering, fairness, FAIR-03, pygame, tunables]

# Dependency graph
requires:
  - phase: 08-fairness-pass
    provides: settings.PLAYER_TURN_WINDOW_MARGIN + tests/test_player_micro.py xfail proof (Plan 08-01)
provides:
  - player.py check_position with all four pre-turn windows widened by PLAYER_TURN_WINDOW_MARGIN (FAIR-03)
  - tests/test_player_micro.py::test_cornering_preturn_widened now green (xfail removed)
affects: [08-04-rebless, 08-fairness-pass]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Symmetric window widening: (12 - MARGIN) <= residue <= (18 + MARGIN), one integer tunable, no new float/import (D-09)"
    - "Player-only affordance: the look-alike ghost.py windows stay byte-identical (D-15, core-value guard)"

key-files:
  created: []
  modified:
    - player.py
    - tests/test_player_micro.py

key-decisions:
  - "Used replace_all on the two identical TILE_WIDTH and two identical TILE_HEIGHT window expressions - all four sites widened symmetrically in one pass"
  - "Single feat (GREEN) commit: the RED proof (strict-xfail test) was authored in Plan 08-01; this plan owns only the GREEN transition"

requirements-completed: [FAIR-03]

# Metrics
duration: 4min
completed: 2026-06-30
---

# Phase 8 Plan 03: Player Cornering (FAIR-03) Summary

**Widened the four player-only `12 <= center % TILE <= 18` pre-turn windows in `Player.check_position` to the symmetric `(12 - PLAYER_TURN_WINDOW_MARGIN) .. (18 + PLAYER_TURN_WINDOW_MARGIN)` band so a queued turn registers ~4-6px early, flipping the FAIR-03 cornering test green while leaving the ghost windows byte-identical.**

## Performance

- **Duration:** ~4 min
- **Completed:** 2026-06-30
- **Tasks:** 1
- **Files modified:** 2 (both modified)

## Accomplishments
- Added `PLAYER_TURN_WINDOW_MARGIN` to `player.py`'s existing `from settings import (...)` block.
- Replaced all four window bounds (the two `centerx % TILE_WIDTH` and two `centery % TILE_HEIGHT` expressions) with the symmetric widened form per D-09 / RESEARCH Pattern 3 — band is now 6..24 vs the legacy 12..18.
- Left the inner `level[...] < 3` wall guards and turn-setting bodies exactly as written: only the timing window widened, no illegal turn into a wall is enabled.
- Removed the `@pytest.mark.xfail` from `test_cornering_preturn_widened`; it now reports passed alongside the still-green baseline.
- `ghost.py` byte-identical (`git diff --stat ghost.py` empty); ghost micro-tests + determinism guard green.

## Task Commits

1. **Task 1: FAIR-03 — widen the four player-only pre-turn windows** — `7ebd1c4` (feat)

## Files Created/Modified
- `player.py` — imported `PLAYER_TURN_WINDOW_MARGIN`; widened all four pre-turn window bounds in `check_position`.
- `tests/test_player_micro.py` — removed the strict-xfail marker on `test_cornering_preturn_widened` (now green).

## Acceptance Criteria Verification
- `grep -c "PLAYER_TURN_WINDOW_MARGIN" player.py` = 5 (1 import + 4 windows; >= 4 required).
- `grep -c "12 <= center" player.py` = 0 (no legacy hard-coded bound remains).
- `.venv/Scripts/python.exe -m pytest tests/test_player_micro.py -q -rxX` → 2 passed (no xfail/xpass).
- Full verify set (`test_player_micro` + `test_ghost_micro` + `test_determinism_guard`) → 22 passed.
- `git diff --stat ghost.py` → zero changes (D-15 byte-identical guard held).

## Decisions Made
- None beyond the plan. Implementation follows 08-RESEARCH Pattern 3 / 08-PATTERNS as written.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Issues Encountered
None. (Git reported the usual LF→CRLF warning on commit; first-party files, no functional impact.)

## TDD Gate Compliance
Task 1 is `tdd="true"`. The RED gate (the strict-xfail `test_cornering_preturn_widened`) was authored in Plan 08-01's Wave-0 split; this plan owns the GREEN transition. A single `feat(08-03)` commit (`7ebd1c4`) carries the implementation plus the xfail removal — the test went from xfailed to passed against the same case. No separate `test` RED commit is expected here (it lives in 08-01's history); this is the intended Wave-2 GREEN.

## Next Phase Readiness
- All three FAIR-* behavior changes (08-02 game.py FAIR-01/02, 08-03 player.py FAIR-03) are now landed on `main`.
- Golden traces are expected RED until the single Linux/Docker re-bless in Plan 08-04 (D-10) — not addressed here by design.

## Self-Check: PASSED

- Both modified files (`player.py`, `tests/test_player_micro.py`) exist on disk.
- Task commit `7ebd1c4` present in git history.

---
*Phase: 08-fairness-pass*
*Completed: 2026-06-30*
