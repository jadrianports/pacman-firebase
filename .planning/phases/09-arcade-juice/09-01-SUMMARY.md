---
phase: 09-arcade-juice
plan: 01
subsystem: testing
tags: [pygame, tdd, golden-master, headless, settings, juice-firewall]

# Dependency graph
requires:
  - phase: 08-fairness-pass
    provides: juice firewall (Game.juice default False), golden net (golden_traces + frame_hash + determinism guard), headless harness (init_headless, install_frame_driven_sound), Phase-8 pure-int settings block
provides:
  - "settings.py FEEL tunables: DEATH_ANIM_FRAMES (75), FRIGHT_FLASH_START (480), FRIGHT_FLASH_INTERVAL (8)"
  - "RED failing-test net targeting the exact symbols 09-02/03/04 will build (death_anim_frame/_draw_death, play_eat_ghost, blink_white/spooked_white_img)"
  - "GREEN characterization guards pinning shipped FEEL-02 (eat-freeze popup) and FEEL-05 (READY! beat)"
affects: [09-02-death-wedge, 09-03-fright-flash, 09-04-eat-sound, 09-05-asset-playtest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Failing-test-first net (Phase-8 pattern): RED tests committed before the implementation plans that turn them GREEN, targeting exact not-yet-built symbols"
    - "Characterization guards pin already-shipped behavior so new work cannot silently regress it"
    - "Pure-int settings dials (no float/import) keep the determinism guard green"

key-files:
  created:
    - tests/test_death_anim.py
    - tests/test_eat_ghost_sound.py
    - tests/test_fright_flash.py
    - tests/test_feel_regression.py
  modified:
    - settings.py

key-decisions:
  - "FEEL tunables added as pure ints in a Phase-9 block mirroring the Phase-8 fairness block so determinism guard stays green"
  - "RED net targets the literal future API (death_anim_frame/_draw_death, play_eat_ghost on Channel(2), Ghost blink_white/spooked_white_img kwargs) so failures point at missing symbols, not collection errors"
  - "FEEL-02/05 guards are characterization-only (game.py untouched) — capture current behavior, do not prescribe new"

patterns-established:
  - "Eat-branch trigger in tests: place a ghost center coincident with the player_circle center (ghost x=player.x+1, y=player.y+2) to fire _catches() deterministically"
  - "READY! beat assertion via dual-edition-safe screen.get_at yellow-pixel scan (no gaussian_blur — Pitfall 5)"

requirements-completed: [FEEL-01, FEEL-02, FEEL-03, FEEL-04, FEEL-05]

# Metrics
duration: 6min
completed: 2026-06-29
---

# Phase 9 Plan 01: Failing-Test Net + FEEL Tunables Summary

**Stood up the phase's golden-safe test scaffold — three RED feature tests targeting the exact 09-02/03/04 symbols, two GREEN characterization guards pinning shipped FEEL-02/FEEL-05, and three pure-int settings dials — with golden traces, firewall, and determinism guard all green and no re-bless.**

## Performance

- **Duration:** ~6 min
- **Started:** 2026-06-29T23:06:51Z
- **Completed:** 2026-06-29T23:12:24Z
- **Tasks:** 3
- **Files modified:** 5 (1 modified, 4 created)

## Accomplishments
- Added `DEATH_ANIM_FRAMES=75`, `FRIGHT_FLASH_START=480`, `FRIGHT_FLASH_INTERVAL=8` to `settings.py` as inert pure ints (determinism guard green).
- Created the RED failing-test net (`test_death_anim.py`, `test_eat_ghost_sound.py`, `test_fright_flash.py`) — collects cleanly, fails on the exact missing symbols (AttributeError/TypeError), with a juice=False dying firewall guard that is already GREEN.
- Created GREEN characterization guards (`test_feel_regression.py`) pinning the shipped eat-freeze popup (FEEL-02, 45-frame freeze + doubling score) and the READY! beat (FEEL-05).
- Confirmed golden state traces + frame-hash firewall + determinism guard stay green with NO `--bless` (SC5 honored).

## Task Commits

Each task was committed atomically:

1. **Task 1: Add FEEL tunables to settings.py** - `25a86b0` (feat)
2. **Task 2: Failing-test net for FEEL-01/03/04** - `306814f` (test — TDD RED)
3. **Task 3: GREEN regression guards for FEEL-02 + FEEL-05** - `c17b175` (test)

_Note: Task 2 is the RED half of the cross-plan TDD cycle; the GREEN/feat commits land in 09-02/03/04, by design._

## Files Created/Modified
- `settings.py` - Phase-9 Arcade Juice tunables block (3 pure-int dials: DEATH_ANIM_FRAMES, FRIGHT_FLASH_START, FRIGHT_FLASH_INTERVAL).
- `tests/test_death_anim.py` - FEEL-01 wedge tests: `test_dying_juice_frame_ok` (RED on death_anim_frame/_draw_death) + juice=False dying firewall guard (GREEN).
- `tests/test_eat_ghost_sound.py` - FEEL-03 tests: `play_eat_ghost` on dedicated Channel(2) + eat-branch spy (RED on play_eat_ghost).
- `tests/test_fright_flash.py` - FEEL-04 tests: blink_white distinct-pixel blit + `test_blink_off_under_juice_false` (RED on Ghost blink_white/spooked_white_img).
- `tests/test_feel_regression.py` - FEEL-02 eat-freeze guard + FEEL-05 READY!-beat guard (GREEN characterization).

## Decisions Made
- None beyond the plan — followed the plan as specified. Tunable values, target symbols, and test IDs (`test_dying_juice_frame_ok`, `test_blink_off_under_juice_false`) match the plan and 09-VALIDATION test map exactly.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Git emitted LF→CRLF warnings when staging the new test files (repo `core.autocrlf` normalization). Harmless for pytest collection and execution; not a test concern (the CRLF/must_haves parse caveat applies to PLAN.md, not test files).

## Known Stubs
The three new feature test files are intentionally RED (failing) — this is the planned cross-plan TDD design, not a stub defect. They target symbols 09-02 (`death_anim_frame`/`_draw_death`), 09-03 (`blink_white`/`spooked_white_img`), and 09-04 (`play_eat_ghost`) will build. Each failure is an AttributeError/TypeError on the missing symbol (or an AssertionError on the not-yet-wired eat-branch call), proving they target the right API. They turn GREEN in their respective plans.

## Verification
- `.venv/Scripts/python.exe -m pytest tests/test_feel_regression.py tests/test_golden_traces.py tests/test_juice_firewall.py tests/test_determinism_guard.py -q` → 26 passed (GREEN).
- `.venv/Scripts/python.exe -m pytest tests/test_death_anim.py tests/test_eat_ghost_sound.py tests/test_fright_flash.py -q` → 5 failed, 1 passed (exit 1, RED as expected).
- No `--bless` run anywhere (SC5 golden-safe).

## Next Phase Readiness
- 09-02 can implement `Game.death_anim_frame` + `Game._draw_death` against `test_death_anim.py`.
- 09-03 can add `Ghost(blink_white=, spooked_white_img=)` + `create_ghosts` blink computation against `test_fright_flash.py`.
- 09-04 can add `SoundManager.play_eat_ghost` (Channel 2) + wire the eat-branch call against `test_eat_ghost_sound.py`.
- All three must keep the FEEL-02/05 guards and the golden/firewall/determinism net green with no re-bless.

## Self-Check: PASSED

---
*Phase: 09-arcade-juice*
*Completed: 2026-06-29*
