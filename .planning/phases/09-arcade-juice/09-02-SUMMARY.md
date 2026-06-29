---
phase: 09-arcade-juice
plan: 02
subsystem: rendering
tags: [pygame, feel, death-animation, juice-firewall, golden-safe, tdd]

# Dependency graph
requires:
  - phase: 09-arcade-juice
    plan: 01
    provides: "RED test_death_anim.py (death_anim_frame/_draw_death symbols) + settings.DEATH_ANIM_FRAMES tunable"
provides:
  - "Game.death_anim_frame: juice-gated dying-phase frame cursor (reset in __init__/start_dying/reset_after_death; not a captured-state field)"
  - "Game._draw_death(anim_frame=None): classic arcade wedge-collapse overlay (pygame.draw.polygon + math)"
  - "juice-gated dying render branch in tick() — wedge replaces player.draw only under dying and juice (D-05)"
affects: [09-05-asset-playtest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Juice-gated draw-only overlay: new visual lives in if ... self.juice branch over the unchanged juice=False path (firewall pattern)"
    - "Juice-gated frame counter: death_anim_frame increments only inside the juice branch, never enters captured state -> golden-safe with no re-bless"
    - "Wedge geometry: filled circle minus a mouth whose half-angle grows 0->pi via a frame-progress ratio (no random/wall-clock)"

key-files:
  created: []
  modified:
    - game.py

key-decisions:
  - "_draw_death signature is _draw_death(self, anim_frame=None) defaulting to self.death_anim_frame, so the test's no-arg g._draw_death() call AND the render branch's explicit pass both work"
  - "death_anim_frame increment lives strictly inside the if self.dying and self.juice branch (not before it), so juice=False dying sim/render is byte-identical (SC5)"
  - "Wedge drawn with pygame.draw.polygon (filled, both pygame editions); no draw.pie (nonexistent) / gaussian_blur (vanilla-pygame CI lacks it)"

patterns-established:
  - "Reword any source docstring/string that names a forbidden determinism token (random/time.time/get_ticks/...) — the guard only skips lines starting with '#', not triple-quoted strings"

requirements-completed: [FEEL-01]

# Metrics
duration: 4min
completed: 2026-06-29
---

# Phase 9 Plan 02: Death Wedge Collapse (FEEL-01) Summary

**Replaced the held player sprite during the dying phase with a classic arcade wedge-spin collapse, drawn programmatically via pygame.draw.polygon and gated strictly behind `dying and juice` (D-05) so the death golden state trace + frame-hash manifest + firewall stay green with no re-bless.**

## Performance

- **Duration:** ~4 min
- **Started:** 2026-06-29T23:17:23Z
- **Completed:** 2026-06-29T23:21:18Z
- **Tasks:** 2
- **Files modified:** 1 (game.py)

## Accomplishments
- Added `Game.death_anim_frame` (int) initialized to 0 and reset to 0 in `__init__`, `start_dying`, and `reset_after_death` — a juice-gated, non-captured dying cursor.
- Added `Game._draw_death(anim_frame=None)`: a filled-circle-minus-growing-mouth wedge whose mouth half-angle grows 0->pi across `DEATH_ANIM_FRAMES`, returns early once fully collapsed (vanished), and uses only `pygame.draw.polygon`, `math`, and `self.player.center_x/center_y/direction`.
- Wired the render branch at the player-draw site: `if self.dying and self.juice:` increments the cursor and calls `_draw_death`; `else:` keeps the unchanged `player_circle = self.player.draw(self.counter)`.
- Turned the 09-01 RED `test_dying_juice_frame_ok` GREEN while keeping the juice=False dying firewall guard GREEN; golden traces + firewall + determinism guard all green with NO `--bless` (SC5 honored).

## Task Commits

Each task was committed atomically:

1. **Task 1: Add death_anim_frame state + _draw_death wedge method** - `3dc484b` (feat)
2. **Task 2: Wire the juice-gated dying render branch** - `1745c2a` (feat)

## Files Created/Modified
- `game.py` - settings import extended with `DEATH_ANIM_FRAMES`; `self.death_anim_frame` state field (init + two resets); `_draw_death()` wedge method; juice-gated dying render branch in `tick()`.

## Decisions Made
- **`_draw_death` is `(self, anim_frame=None)`** — the 09-01 RED test calls `g._draw_death()` with no argument (line 50), while the render branch passes `self.death_anim_frame` explicitly. A default of `None` resolving to `self.death_anim_frame` satisfies both. The PLAN sketched `_draw_death(anim_frame)` (no default); the optional default is the minimal reconciliation with the committed test contract and is not a behavior change.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Reworded `_draw_death` docstring to avoid the determinism token "random"**
- **Found during:** Task 1 (running `tests/test_determinism_guard.py`)
- **Issue:** The determinism guard scans for forbidden tokens (`random`, `time.time`, `get_ticks`, ...) on every line that does not start with `#`. It does NOT exempt triple-quoted docstrings. My first `_draw_death` docstring contained the phrase "no random/wall-clock (Pitfall 3)", which tripped the guard at the docstring line (`game.py` line 439 -> 'random').
- **Fix:** Reworded the docstring to "with no nondeterministic timing source, so the determinism guard stays green (Pitfall 3)" — same meaning, no forbidden token. Code logic unchanged.
- **Files modified:** game.py
- **Commit:** `3dc484b` (folded into Task 1)

## Issues Encountered
- None beyond the documented deviation. Git emitted the usual LF/CRLF normalization warnings on staging (harmless).

## Known Stubs
None — FEEL-01 is fully implemented and its tests are GREEN. (The 4 still-RED tests in `tests/test_eat_ghost_sound.py` and `tests/test_fright_flash.py` are the intentional cross-plan RED net for 09-04/09-03 respectively — out of scope for this plan, not a stub defect.)

## Golden Safety (SC5)
- `tests/test_death_anim.py tests/test_golden_traces.py tests/test_juice_firewall.py tests/test_determinism_guard.py tests/test_frame_hash.py` -> **26 passed, 9 skipped** (frame-hash skips on Windows `.venv`; Linux CI is the authority). NO `--bless` run anywhere.
- The death_anim_frame counter increments only inside the `if self.dying and self.juice:` branch, so under `juice=False` the dying sim and render are byte-identical — the death golden trace + frame-hash net needs no re-bless. T-09-01 and T-09-03 (threat register) both mitigated.

## Verification
- `.venv/Scripts/python.exe -m pytest tests/test_death_anim.py -q` -> 2 passed (was 1 failed / 1 passed RED before).
- `.venv/Scripts/python.exe -m pytest tests/test_golden_traces.py tests/test_juice_firewall.py tests/test_determinism_guard.py tests/test_frame_hash.py -q` -> green (frame-hash skipped on Windows, asserted on Linux CI).
- Full suite: `188 passed, 9 skipped, 4 failed` — the 4 failures are the pre-existing cross-plan RED tests for 09-03 (`Ghost.blink_white`) and 09-04 (`play_eat_ghost`), not regressions.

## Next Phase Readiness
- 09-03 (FEEL-04 fright flash) and 09-04 (FEEL-03 eat sound) remain RED by design and are unblocked.
- 09-05 playtest will dial `DEATH_ANIM_FRAMES` to the real `death.wav` length (D-04) — the frame-counter machinery is now in place to honor it.

## Self-Check: PASSED

---
*Phase: 09-arcade-juice*
*Completed: 2026-06-29*
