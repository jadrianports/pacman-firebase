---
phase: 09-arcade-juice
plan: 03
subsystem: rendering
tags: [pygame, feel, fright-flash, juice-firewall, golden-safe, tdd]

# Dependency graph
requires:
  - phase: 09-arcade-juice
    plan: 01
    provides: "RED test_fright_flash.py (Ghost.blink_white / spooked_white_img symbols) + settings.FRIGHT_FLASH_START/FRIGHT_FLASH_INTERVAL tunables"
  - phase: 09-arcade-juice
    plan: 02
    provides: "Juice-gated draw-only firewall pattern (new visual lives behind self.juice; juice=False byte-identical)"
provides:
  - "Ghost(..., blink_white=False, spooked_white_img=None): keyword-default ctor params (appended after level); spooked-branch blit selects white when blink_white"
  - "Game.spooked_white_img: one-time BLEND_RGB_ADD white-tinted copy of spooked_img built in __init__"
  - "Game.create_ghosts blink_white compute: juice-gated, frame-counter-driven (FRIGHT_FLASH_START/INTERVAL), threaded as keyword args into all four Ghost calls"
affects: [09-05-asset-playtest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dumb-ghost / smart-Game (D-06): all juice + threshold + cadence logic lives in Game.create_ghosts; Ghost receives one precomputed bool + a pre-tinted surface via keyword-defaults"
    - "Keyword-default ctor extension (Pitfall 2): new params appended AFTER the last positional arg so every positional caller + test_ghost_micro stay green"
    - "Juice-gated frame-counter blink: (self.juice and ... (power_counter // INTERVAL) % 2 == 0) -> juice=False always False -> golden-safe with no re-bless"
    - "One-time sprite tint: spooked_img.copy() + fill(add-color, BLEND_RGB_ADD) in __init__ (no new asset, dual-edition-safe)"

key-files:
  created: []
  modified:
    - ghost.py
    - game.py

key-decisions:
  - "Tint add-color is (90, 90, 120, 0) via BLEND_RGB_ADD — a placeholder white-lean, to be dialed in the 09-05 playtest (D-07); chosen because BLEND_RGB_ADD exists in both pygame editions (Pitfall 5)"
  - "blink_white computed once before the four Ghost constructions and passed identically to all four (single source of truth; ghost stays dumb per D-06)"

patterns-established:
  - "Extend a per-frame-rebuilt dumb object with keyword-default params and compute all state in the owning smart object — keeps positional caller/test contracts intact"

requirements-completed: [FEEL-04]

# Metrics
duration: 5min
completed: 2026-06-29
---

# Phase 9 Plan 03: Fright Flash (FEEL-04) Summary

**Frightened ghosts now alternate blue<->white over the last ~2s of the power window (`power_counter > FRIGHT_FLASH_START`, toggling every `FRIGHT_FLASH_INTERVAL` frames) so the player knows it is no longer safe to chase — gated strictly behind `self.juice` (D-08) so the juice=False spooked render is byte-identical and golden/frame-hash/firewall stay green with no re-bless.**

## Performance
- **Duration:** ~5 min
- **Started:** 2026-06-29T23:26:56Z
- **Completed:** 2026-06-29T23:32:00Z
- **Tasks:** 2
- **Files modified:** 2 (ghost.py, game.py)

## Accomplishments
- Extended `Ghost.__init__` with keyword-defaults `blink_white=False, spooked_white_img=None` appended after `level`; both stored BEFORE the construction-time `self.draw()` (ghost.py:300) so the first blit sees them.
- `Ghost.draw` spooked branch now selects `img = self.spooked_white_img if self.blink_white else self.spooked_img` — the default (blink_white False) path is byte-identical to the prior `spooked_img` blit (D-08).
- Built `Game.spooked_white_img` once in `__init__`: `spooked_img.copy()` then `.fill((90,90,120,0), special_flags=pygame.BLEND_RGB_ADD)` — no new sprite asset, dual-edition-safe.
- `Game.create_ghosts` computes a single juice-gated, frame-counter-driven `blink_white` and threads it (plus `spooked_white_img`) as keyword args into all four Ghost constructions. Imported `FRIGHT_FLASH_START`/`FRIGHT_FLASH_INTERVAL` from settings.
- Turned both 09-01 RED tests in `tests/test_fright_flash.py` GREEN (incl. `test_blink_off_under_juice_false`) without weakening them.

## Task Commits
Each task was committed atomically:

1. **Task 1: Ghost keyword-default params + white-tint blit selection** - `7650283` (feat)
2. **Task 2: Build spooked_white_img once + compute blink_white in create_ghosts** - `cda55e9` (feat)

## Files Created/Modified
- `ghost.py` - ctor signature + `self.blink_white`/`self.spooked_white_img` stores before draw(); spooked-branch white-blit selection.
- `game.py` - settings import extended (`FRIGHT_FLASH_START`, `FRIGHT_FLASH_INTERVAL`); `self.spooked_white_img` built in `__init__`; juice-gated `blink_white` compute + keyword threading into all four `create_ghosts` Ghost calls.

## Decisions Made
- **Tint add-color `(90, 90, 120, 0)` via `BLEND_RGB_ADD`** — a white-leaning placeholder to be dialed in the 09-05 playtest (D-07). `BLEND_RGB_ADD` chosen over alpha/gaussian approaches because it exists in both pygame editions (Pitfall 5).
- **`blink_white` computed once, passed to all four ghosts identically** — single source of truth in the smart `Game`; the per-frame-rebuilt `Ghost` stays dumb (D-06).

## Deviations from Plan
None - plan executed exactly as written. (No determinism-guard token rephrasing was needed; the `create_ghosts` comment uses "no nondeterministic timing source" and avoids forbidden tokens.)

## Known Stubs
None — FEEL-04 is fully implemented and its tests are GREEN. The 2 still-RED tests in `tests/test_eat_ghost_sound.py` are the intentional cross-plan RED net for 09-04 (FEEL-03 eat sound) — out of scope, not a stub defect.

## Golden Safety (SC5)
- `tests/test_fright_flash.py tests/test_ghost_micro.py tests/test_golden_traces.py tests/test_frame_hash.py tests/test_juice_firewall.py tests/test_determinism_guard.py` -> **41 passed, 9 skipped** (frame-hash skips on Windows `.venv`; Linux CI is the authority). NO `--bless` run anywhere.
- `blink_white` includes `self.juice and ...`, so under `juice=False` it is always False -> identical `spooked_img` blit. T-09-01 (golden/firewall tampering) and T-09-02 (ctor contract) both mitigated: keyword-defaults kept `test_ghost_micro` green.

## Verification
- `.venv/Scripts/python.exe -m pytest tests/test_fright_flash.py -q` -> 2 passed (was 2 failed RED).
- Full plan verification suite -> 41 passed, 9 skipped, NO `--bless`.
- `tests/test_eat_ghost_sound.py` -> 2 failed, the pre-existing cross-plan RED net for 09-04 (not a regression).

## Next Phase Readiness
- 09-04 (FEEL-03 eat sound) remains RED by design and is unblocked.
- 09-05 playtest will dial the white-tint add-color and confirm the ~2s blink window against the real power-window length (D-07).

## Self-Check: PASSED

---
*Phase: 09-arcade-juice*
*Completed: 2026-06-29*
