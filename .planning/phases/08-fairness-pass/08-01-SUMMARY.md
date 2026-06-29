---
phase: 08-fairness-pass
plan: 01
subsystem: testing
tags: [settings, tunables, characterization-tests, xfail, fairness, pygame]

# Dependency graph
requires:
  - phase: 02-refactor
    provides: tests/test_ghost_micro.py headless-construction analog + conftest SDL-dummy harness
provides:
  - Four named FAIR tunable constants in settings.py (GHOST_CATCH_DISTANCE, GHOST_CHASE_SPEED_NUM/DEN, PLAYER_TURN_WINDOW_MARGIN)
  - tests/test_player_micro.py - FAIR-03 cornering-window characterization (baseline green + widened xfail)
  - tests/test_fairness_unit.py - FAIR-01 catch-helper + FAIR-02 accumulator unit proofs (all xfail strict, RED)
affects: [08-02-game-fairness, 08-03-player-cornering, 08-fairness-pass]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Wave-0 shared-dependency split: settings.py constants land first so Wave 2 game.py + player.py plans run parallel without a file conflict"
    - "Red-until-implemented proof artifacts via @pytest.mark.xfail(strict=True); the implementing plan removes each marker as its test turns green"

key-files:
  created:
    - tests/test_player_micro.py
    - tests/test_fairness_unit.py
  modified:
    - settings.py

key-decisions:
  - "All four FAIR tunables are plain integers (no float, no new import) so tests/test_determinism_guard.py stays green"
  - "PLAYER_SPEED left at 2 (D-07) - fairness moves ghost outcomes, never player control feel"
  - "Junction (board row 6, col 7) chosen for the player-cornering test: open vertical corridor (rows 5/7) crossing a horizontal corridor, so the residue band is the sole gate"
  - "FAIR-01 catch tests use integer squared-distance only (no math.sqrt, no float); corner-kiss (~41px) asserted safe per D-02"

patterns-established:
  - "xfail(strict=True) RED proof: NEW-behavior assertions are reported xfailed (never xpassed) against today's code; suite stays green at wave merge"
  - "Headless Game/Player construction reusing the test_ghost_micro screen fixture + deepcopy-board-per-case"

requirements-completed: [FAIR-01, FAIR-02, FAIR-03]

# Metrics
duration: 12min
completed: 2026-06-30
---

# Phase 8 Plan 01: Fairness-Pass Foundation Summary

**Four named arcade-faithful FAIR tunables added to settings.py plus two fast non-golden proof files (1 baseline-green test + 6 strict-xfail RED tests) that pin the post-change FAIR-01/02/03 behavior without touching the golden net.**

## Performance

- **Duration:** ~12 min
- **Completed:** 2026-06-30
- **Tasks:** 3
- **Files modified:** 3 (1 modified, 2 created)

## Accomplishments
- Added the Wave-0 shared dependency: `GHOST_CATCH_DISTANCE=15`, `GHOST_CHASE_SPEED_NUM=37`, `GHOST_CHASE_SPEED_DEN=20`, `PLAYER_TURN_WINDOW_MARGIN=6` as documented integer constants in `settings.py`, each a D-10 playtest dial; `PLAYER_SPEED` untouched.
- Authored `tests/test_player_micro.py`: a green baseline (residue 15 grants the perpendicular turn) plus a strict-xfail widened case (residue 8, in the margin-6 band but outside legacy 12..18) that turns green when Plan 08-03 widens the player window.
- Authored `tests/test_fairness_unit.py`: 4 strict-xfail catch-helper cases (same-tile / corner-kiss-safe / 15px / 16px boundary) and 1 strict-xfail accumulator case (20 chase frames sum to 37). All integer math; no `math.sqrt`, no float, no `ghost.py` import.
- Full suite stays green: new files report 1 passed + 6 xfailed (none xpassed); determinism guard still 5 passed.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add the four FAIR tunable constants to settings.py** - `66fa26a` (feat)
2. **Task 2: Author tests/test_player_micro.py (FAIR-03 cornering window)** - `b4cfaa9` (test)
3. **Task 3: Author tests/test_fairness_unit.py (FAIR-01 catch + FAIR-02 accumulator)** - `43b7171` (test)

## Files Created/Modified
- `settings.py` - appended the documented "Phase 8 - Fairness Pass tunables" block (4 integer constants)
- `tests/test_player_micro.py` - NEW; FAIR-03 cornering-window characterization (baseline + widened)
- `tests/test_fairness_unit.py` - NEW; FAIR-01 catch-helper + FAIR-02 accumulator unit proofs

## Decisions Made
- None beyond the plan. Tunable values, the test junction, and the integer-only constraints all follow 08-PATTERNS.md / 08-CONTEXT.md as written.

## Deviations from Plan

None - plan executed exactly as written.

(One in-task touch-up, not a deviation: the Task-3 docstring originally contained the literal token `math.sqrt` in a "NO math.sqrt" note, which tripped the `grep -c "math.sqrt" == 0` acceptance check. Reworded to "no square-root" before committing; no logic change.)

## Known Stubs

None in the problematic sense. The 6 `xfail(strict=True)` tests are the plan's deliberate RED proof artifacts (objective: assert NEW behavior, stay green at merge). Each references the Wave-2 plan that turns it green:
- `tests/test_player_micro.py::test_cornering_preturn_widened` -> Plan 08-03 (FAIR-03)
- `tests/test_fairness_unit.py` catch-helper x4 -> Plan 08-02 (FAIR-01, adds `Game._catches`)
- `tests/test_fairness_unit.py` accumulator x1 -> Plan 08-02 (FAIR-02, adds `Game.ghost_step_acc` step)

## Issues Encountered
None.

## TDD Gate Compliance
Tasks 2 and 3 are `tdd="true"` but produce test-only artifacts that are RED-by-design (strict xfail) against today's unmodified `game.py`/`player.py`; the GREEN transition is owned by the Wave-2 implementation plans (08-02/08-03), which remove each xfail marker. No source behavior was added in this plan, so no `feat` GREEN commit is expected here - this is the intended Wave-0 split.

## Next Phase Readiness
- `settings.py` constants are in place, unblocking the two parallel Wave-2 plans (08-02 game.py FAIR-01/02, 08-03 player.py FAIR-03).
- Each Wave-2 plan has a ready, deterministic, sub-second proof artifact: removing its xfail marker should flip the test green.
- Golden re-bless remains deferred to a single Linux/Docker pass after D-10 (unchanged).

## Self-Check: PASSED

- All 3 created/modified files exist on disk.
- All 3 task commits (66fa26a, b4cfaa9, 43b7171) present in git history.

---
*Phase: 08-fairness-pass*
*Completed: 2026-06-30*
