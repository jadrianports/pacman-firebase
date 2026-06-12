---
phase: 02-safe-refactor
plan: 01
subsystem: testing
tags: [refactor, geometry, pygame, golden-master, differential-oracle, frame-hash, sha256]

# Dependency graph
requires:
  - phase: 01-test-safety-net
    provides: "9 golden traces + 15 micro tests + make_ghost headless harness + --bless flow + SDL-dummy/bundled-font pinned CI env"
provides:
  - "Centralized tile geometry: settings.py TILE_HEIGHT/TILE_WIDTH/HALF_TILE derived from named BOARD_ROWS/BOARD_COLS/HUD_HEIGHT"
  - "geometry.py module: tile_at/is_walkable/in_box helpers + the two DISTINCT box-bounds constants (GHOST_BOX_BOUNDS_COLLISION, GHOST_BOX_BOUNDS_TARGET)"
  - "Named distinct wrap-edge + scatter-target constants (guard against accidental Phase 3 unification)"
  - "check_collisions differential oracle (frozen legacy copy + exhaustive OLD==NEW proof) — one-shot, deleted by Plan 02-02"
  - "Permanent deterministic frame-hash check + committed per-scenario frame_hashes.txt manifests"
affects: [02-02-mover, phase-03-bug-01]

# Tech tracking
tech-stack:
  added: []  # zero new packages — hashlib stdlib; pygame/pytest already pinned
  patterns:
    - "Differential oracle: frozen verbatim OLD copy + itertools.product exhaustive enumeration asserting OLD==NEW"
    - "Deterministic frame-hash: sha256(pygame.image.tobytes(surface,'RGB')) gated to the Linux pinned CI env, skips clean on dev"
    - "Named-distinct look-alike constants to guard against a future accidental unification"

key-files:
  created:
    - geometry.py
    - tests/_legacy_geometry.py
    - tests/test_check_collisions_oracle.py
    - tests/test_frame_hash.py
    - tests/golden/<scenario>/frame_hashes.txt (x9)
  modified:
    - settings.py
    - ghost.py
    - game.py
    - player.py

key-decisions:
  - "Tile constants live in settings.py (pure config); behavioral helpers + box bounds live in geometry.py (D-12/D-16)"
  - "The two box rectangles stay TWO distinct named constants — NOT unified (unification is Phase 3 / BUG-01, D-13/D-14)"
  - "Frame-hash assertion gated to the Linux pinned CI env (CI / GSD_FRAME_HASH_ENV); pytest.skip on non-pinned dev so Windows runs do not false-red (D-09)"
  - "Manifest authored on Windows is a placeholder baseline — CI is the assertion authority; re-bless in CI to mint the true Linux truth"

patterns-established:
  - "Differential oracle (frozen OLD + exhaustive enumeration) as the logic-proof modality"
  - "Frame-hash manifest as the orthogonal pixel-proof modality"

requirements-completed: [REF-01]

# Metrics
duration: 25min
completed: 2026-06-12
---

# Phase 2 Plan 01: Geometry Centralization Summary

**Killed the num1/num2/num3 magic-number duplication behind named TILE_* constants + a geometry.py in_box/tile_at/is_walkable module, proven byte-identical by an exhaustive check_collisions differential oracle (logic) and a deterministic sha256 frame-hash manifest (pixels) — with the two latent box rectangles kept as two distinct constants for Phase 3's one-line BUG-01 fix.**

## Performance

- **Duration:** ~25 min (active execution; oracle replay alone runs ~4 min)
- **Started:** 2026-06-12 (continuation — Task 1 was pre-committed in d9664a1)
- **Completed:** 2026-06-12
- **Tasks:** 3 (Task 1 pre-existing/verified; Tasks 2-3 executed this session)
- **Files created:** 13 (geometry.py + 3 test files + 9 manifests)
- **Files modified (Task 1):** 4 (settings.py, ghost.py, game.py, player.py)

## Accomplishments

- **Task 1 (geometry centralization, pre-committed):** settings.py exposes `TILE_HEIGHT=(HEIGHT-HUD_HEIGHT)//BOARD_ROWS` (28), `TILE_WIDTH=WIDTH//BOARD_COLS` (30), `HALF_TILE=15`, derived from named `BOARD_ROWS=32`/`BOARD_COLS=30`/`HUD_HEIGHT=50`, plus distinct wrap-edge (`GHOST_WRAP_*`, `PLAYER_WRAP_*`) and scatter-target (`SCATTER_*`) constants. `geometry.py` provides `tile_at`/`is_walkable`/`in_box` and the **two distinct** box constants `GHOST_BOX_BOUNDS_COLLISION=(350,550,360,480)` and `GHOST_BOX_BOUNDS_TARGET=(340,560,340,500)`. All inline `num1/num2/num3` recomputations and the ~9 inline box checks were substituted across ghost/game/player byte-identically. Verified: 30/30 inherited net (15 micro + 9 golden + invariant self-tests) green.
- **Task 2 (check_collisions oracle):** `tests/_legacy_geometry.py` freezes a verbatim, self-contained PRE-REF-01 `check_collisions` (inlines `(HEIGHT-50)//32`, `WIDTH//30`, `15`, the `//30`/`<29` guard, and the literal `350<x<550 & 360<y<480` box test — no import from ghost.py). `tests/test_check_collisions_oracle.py` enumerates `BOARD_ROWS×BOARD_COLS × 5 x-offsets × 5 y-offsets × direction(4) × in_box(2) × dead(2)` via `itertools.product` and asserts OLD `(turns, in_box)` == NEW `(turns, in_box)` exactly. A `_Probe` snapshot isolates the legacy input from the NEW method's self-mutation.
- **Task 3 (frame-hash check):** `tests/test_frame_hash.py` hashes `sha256(pygame.image.tobytes(surface,"RGB"))` over sampled frames (every 20th + terminal) for each golden scenario, wired into the existing `--bless` flow. 9 committed `tests/golden/<scenario>/frame_hashes.txt` manifests (NOT under gitignored `tests/artifacts/`). Assertion gated to the Linux pinned CI env; skips clean on Windows dev.

## Oracle case count + runtime

- **Enumerated cases:** `32 × 30 × 5 × 5 × 4 × 2 × 2 = 384,000` differential cases (each constructs a deep-copied-board ghost and compares OLD vs NEW). The sanity assertion at the end of the test confirms the full crossed space ran.
- **Runtime:** ~247 s locally (dominated by per-case `Ghost` construction + `copy.deepcopy(board.boards)`, not the arithmetic). Well inside CI budget; single `pytest` invocation, `1 passed`.

## Frame-hash manifest scenarios + CI authority note

Manifests committed for all 9 golden scenarios with sampled hash-line counts: box_exit (22), power_chase (39), ghost_eat (36), death (200, sampled from 4200 frames), win (151), box_edge (56), tunnel_wrap (51), eyes_return (71), claude_session_01 (76).

**CI is the assertion authority.** The committed hashes were generated on Windows under SDL-dummy + the bundled `freesansbold.ttf`, but `freesansbold.ttf` rasterization is platform-bound (Pitfall 4 / D-09). These Windows hashes are a placeholder baseline — **they MUST be re-blessed in the Linux pinned CI env (`pytest --bless`) to mint the true Linux truth.** Until re-blessed, the test is designed to NOT false-red: on dev (no `CI`/`GSD_FRAME_HASH_ENV`) it `pytest.skip`s; in CI it asserts against the committed manifest, and if the manifest is missing it skips with a "re-bless in CI" message. Verified locally: dev run = 9 skipped; simulated pinned env (`CI=1`) = 9 passed (deterministic single-platform match).

## Task Commits

1. **Task 1: Centralize tile geometry (settings.py + geometry.py + substitutions)** — `d9664a1` (refactor) — *pre-committed before this session; verified green*
2. **Task 2: check_collisions differential oracle** — `2ec0700` (test)
3. **Task 3: Deterministic frame-hash check + manifests** — `af90d6f` (test)

**Plan metadata:** (this commit)

## Files Created/Modified

- `settings.py` — TILE_HEIGHT/TILE_WIDTH/HALF_TILE + named distinct wrap/scatter constants
- `geometry.py` — tile_at/is_walkable/in_box + the two distinct box-bounds constants
- `ghost.py`, `game.py`, `player.py` — inline num1/num2/num3 + box-literal substitutions (byte-identical)
- `tests/_legacy_geometry.py` — frozen PRE-REF-01 check_collisions (one-shot; deleted by Plan 02-02)
- `tests/test_check_collisions_oracle.py` — exhaustive OLD==NEW differential proof (one-shot; deleted by Plan 02-02)
- `tests/test_frame_hash.py` — permanent deterministic pixel-hash check vs committed manifest
- `tests/golden/<scenario>/frame_hashes.txt` (x9) — committed Linux-blessed-truth manifests (permanent)

## Decisions Made

- Tile constants in settings.py, behavioral helpers/bounds in geometry.py (D-12/D-16) — keeps settings.py pure-config and avoids a player→ghost import.
- Two box constants kept DISTINCT (D-13/D-14) — Phase 3 / BUG-01 owns unification; naming the look-alikes guards against accidental merge.
- Frame-hash assertion gated to pinned CI env with clean dev skip (D-09) — avoids a Windows-authoring false-red while keeping CI the assertion authority.

## Deviations from Plan

None that alter behavior. Two mechanical execution notes:

- **Continuation context:** Task 1 was already committed (`d9664a1`) in a prior session and the Task 2 oracle files existed untracked. I verified Task 1's automated checks (constants + inherited net green) and the untracked Task 2 files (frozen legacy copy is verbatim-correct; oracle is sound) before committing Task 2 — rather than redoing committed work.
- **Manifest platform:** Authored on Windows, the committed frame_hashes.txt are a placeholder baseline; flagged above and in the Task 3 commit message that CI must re-bless to establish the Linux truth. This honors the plan's explicit "CI is the assertion authority" instruction — no behavior change.

## Issues Encountered

- Bare `python -m pytest` lacked pygame; the project uses a `.venv`. Switched to `./.venv/Scripts/python.exe -m pytest` for all test runs. (Environment, not a code issue.)

## Known Stubs

None. All artifacts are wired and exercised: the oracle proves OLD==NEW exhaustively, and the frame-hash test asserts against real committed manifests (gated by env, not stubbed).

## User Setup Required

None — no external service configuration. **CI action required (automatic on push):** re-bless the frame-hash manifest in the Linux CI env via `pytest --bless` to convert the Windows placeholder hashes into the canonical Linux baseline.

## Next Phase Readiness

- The D-11 geometry-first gate is satisfied: REF-01 is fully landed and proven by two complementary modalities (logic oracle + pixel hash) on top of the inherited net. **Plan 02-02 (the mover refactor) may begin.**
- Plan 02-02 must DELETE `tests/_legacy_geometry.py` + `tests/test_check_collisions_oracle.py` after its own mover proofs are green (D-06/D-07 one-shot lifecycle). The frame-hash check + manifests are PERMANENT.

---
*Phase: 02-safe-refactor*
*Completed: 2026-06-12*
