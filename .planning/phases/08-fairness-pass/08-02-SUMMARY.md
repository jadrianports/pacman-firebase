---
phase: 08-fairness-pass
plan: 02
subsystem: testing
tags: [pygame, collision, ghost-speed, fairness, integer-rational, determinism]

# Dependency graph
requires:
  - phase: 08-fairness-pass (Plan 01)
    provides: settings.GHOST_CATCH_DISTANCE, GHOST_CHASE_SPEED_NUM/DEN + the strict-xfail FAIR-01/02 proof tests
  - phase: 02-refactor
    provides: ghost.py unified data-driven mover (consumes self.speed; left byte-identical here)
provides:
  - Game._catches - integer center-to-center squared-distance catch (corner-kiss-safe, FAIR-01)
  - Game.ghost_step_acc - per-ghost integer-rational chase-step accumulator (1.85 px/frame avg, FAIR-02)
  - update_ghost_speeds lethal-chase tier refinement gated to moving frames
affects: [08-03-player-cornering, 08-fairness-pass, golden-rebless]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "All-integer game-sim math (squared distance + integer-rational accumulator) so tests/test_determinism_guard.py stays green - no sqrt/float/random/wall-clock"
    - "Fairness changes ghost OUTCOMES from inside Game; ghost.py decision/targeting logic stays byte-identical (oracle-scoped)"

key-files:
  created: []
  modified:
    - game.py
    - tests/test_fairness_unit.py

key-decisions:
  - "_catches reads live centers off self.player (not the passed player_circle, stale during eat_freeze) per 08-RESEARCH"
  - "Lethal chaser identified uniquely by ghost_speeds[i]==2 after the base/eaten/dead tiers, so the accumulator covers both default-chase and eaten-revived-during-powerup (D-04/A2) without touching frightened(1) or eyes(4)"
  - "Accumulator advanced/reset only on moving frames (self.moving and not self.eat_freeze) + reset_after_death, so no phantom chase credit banks across pauses/lives (Pitfall 4)"
  - "Golden-trace re-bless deferred to a single Linux/Docker pass after D-10 (out of this plan's scope); 10 baseline traces intentionally diverge"

patterns-established:
  - "xfail->green flip: the implementing plan removes each strict-xfail marker as its target behavior turns green, keeping the suite green at every commit"
  - "Headless full-Game construction fixture needs display+font+mixer init (mirrors harness/headless.py), not display alone"

requirements-completed: [FAIR-01, FAIR-02]

# Metrics
duration: 6min
completed: 2026-06-30
---

# Phase 8 Plan 02: Game Fairness (FAIR-01 + FAIR-02) Summary

**Corner-kisses are now SAFE (integer center-to-center squared-distance catch vs GHOST_CATCH_DISTANCE) and the lethal chase tier averages 1.85 px/frame via a per-ghost integer-rational step accumulator - both implemented entirely in game.py with ghost.py left byte-identical.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-30
- **Completed:** 2026-06-30
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- **FAIR-01:** Added `Game._catches(ghost)` returning `dx*dx + dy*dy <= GHOST_CATCH_DISTANCE * GHOST_CATCH_DISTANCE` (integer, no sqrt/float) and replaced every `player_circle.colliderect(...)` across all three catch groups (normal kill, powerup already-eaten kill, eat-the-frightened-ghost loop). A diagonal one-tile corner-kiss (~41px) now reads SAFE; 15px catches, 16px does not. Centers are read off the always-live `self.player`, not the stale `player_circle`.
- **FAIR-02:** Added `self.ghost_step_acc = [0,0,0,0]` and refined only the lethal-chase tier (`ghost_speeds[i] == 2`) inside `update_ghost_speeds` into an integer-rational `{1,2}` step that sums to `GHOST_CHASE_SPEED_NUM` (37) over `GHOST_CHASE_SPEED_DEN` (20) frames = 1.85 px/frame average, while every ghost position stays a strict integer. Gated on moving frames and reset on death; frightened (1) and eyes-return (4) tiers untouched (D-08).
- **Proof:** `tests/test_fairness_unit.py` flipped from 5 strict-xfail to 5 passing; `tests/test_ghost_micro.py` + `tests/test_determinism_guard.py` stay green; `ghost.py` is byte-identical (zero diff).

## Task Commits

Each task was committed atomically:

1. **Task 1: FAIR-01 center-to-center squared-distance catch** - `eae7ad8` (feat)
2. **Task 2: FAIR-02 integer-rational chase-step accumulator** - `4cbcdd9` (feat)

_TDD note: the RED proof artifacts (strict-xfail tests) were authored in Plan 08-01; this plan owns the GREEN flip, so each task is a single `feat` commit that removes the matching xfail marker as the behavior turns green._

## Files Created/Modified
- `game.py` - settings imports extended (GHOST_CATCH_DISTANCE, GHOST_CHASE_SPEED_NUM/DEN); `_catches` helper; `colliderect` removed from all three catch groups; `ghost_step_acc` init + reset; lethal-chase tier accumulator in `update_ghost_speeds`
- `tests/test_fairness_unit.py` - removed all 5 xfail markers (4 catch + 1 accumulator); `screen` fixture now also inits font + mixer so a full `Game` constructs headless

## Decisions Made
- None beyond the plan. Helper shape, the `== 2` tier selector, moving-frame gating, and the reset point all follow 08-PATTERNS.md / 08-RESEARCH.md as written.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Headless `screen` fixture could not construct a full `Game`**
- **Found during:** Task 1 (running the now-non-xfail FAIR-01 catch tests)
- **Issue:** The Plan 08-01 `screen` fixture only called `pygame.display.init()`. `Game.__init__` also loads a font (`pygame.font.Font`) and builds `SoundManager` (`pygame.mixer.Sound`), so construction raised `pygame.error: font not initialized` then `mixer not initialized`. This was previously masked because all five tests were strict-xfail (the fixture error read as the expected RED); removing the markers surfaced it as a hard blocker to GREEN.
- **Fix:** Added `pygame.font.init()` and `pygame.mixer.init()` to the fixture, mirroring the canonical `harness/headless.py` init order (SDL_*=dummy keeps it windowless/silent). Test-harness only; no game behavior change.
- **Files modified:** tests/test_fairness_unit.py
- **Verification:** `Game` constructs; all 5 fairness tests pass; ghost-micro + determinism guard still green.
- **Committed in:** `eae7ad8` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking, test-harness only)
**Impact on plan:** Necessary to reach the planned GREEN state; zero production-code or scope impact. ghost.py byte-identical as required.

## Known Stubs
None. Both behaviors are fully wired into the live `check_ghost_collisions` and `update_ghost_speeds` paths.

## Issues Encountered
- The full suite shows **10 expected golden-trace failures** (`tests/test_golden_traces.py`). These are the recorded deterministic baselines diverging because the chase tier is now 1.85 (not 2) and a corner-kiss no longer kills Pac-Man - the deliberate behavior change of this phase. Per project memory + 08-RESEARCH, golden re-bless is a separate operator step on **Linux/Docker only**, deferred to after the D-10 playtest so the tunables settle first. Logged in `.planning/phases/08-fairness-pass/deferred-items.md`. This plan's verification scope (fairness unit + ghost micro + determinism guard) is fully green.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- FAIR-01/FAIR-02 done; Plan 08-03 (FAIR-03 player cornering window, `player.py`) remains - its `test_player_micro.py::test_cornering_preturn_widened` is still the one expected xfail.
- ghost.py byte-identical confirmed (`git diff --stat ghost.py` empty), so the core-value guard for this phase stays trivially satisfied.
- **Operator action pending:** golden-trace re-bless on Linux/Docker after the D-10 dial playtest (see deferred-items.md).

## TDD Gate Compliance
RED was established in Plan 08-01 (strict-xfail proofs against unmodified game.py). This plan owns the GREEN transition: each `feat` commit removes the matching xfail marker only once the behavior passes. No REFACTOR commit was needed. The fast deterministic proofs (`test_fairness_unit.py`) gate both behaviors sub-second, independent of the golden net.

---
*Phase: 08-fairness-pass*
*Completed: 2026-06-30*
