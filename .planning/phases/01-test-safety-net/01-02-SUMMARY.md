---
phase: 01-test-safety-net
plan: 02
subsystem: testing
tags: [pygame, headless, record-replay, characterization, trace, jsonl, tick-extraction, refactor]

# Dependency graph
requires:
  - phase: 01-01
    provides: harness.headless.init_headless (SDL-dummy bootstrap), tests/artifacts/ gitignored, isolated .venv with pinned deps
provides:
  - Game.tick() — a steppable, sleep-independent one-frame seam extracted byte-identically from run()
  - harness/trace.py — D-03 per-frame trace schema (capture_state + write/read JSONL + traces_equal/diff_traces)
  - harness/replay.py — sparse {frame,key} record/replay driver (event.post injection, frame-cap soft-lock backstop) + frame-driven sound shim
affects: [01-03, 01-04, 01-05, 01-06, 01-07]

# Tech tracking
tech-stack:
  added: []  # no new deps — all from 01-01
  patterns:
    - baseline-trace-first behavior-preserving extraction (capture from UNMODIFIED loop, assert byte-identical)
    - thin-reader trace schema (capture_state reads only existing Game/Ghost state; frame index set externally as g._frame)
    - sparse-event replay via pygame.event.post through the real handle_events path (D-18)
    - for/else frame-cap soft-lock backstop (D-19)
    - frame-driven sound shim for deterministic headless playback-gating

key-files:
  created: [harness/trace.py, harness/replay.py]
  modified: [game.py]

key-decisions:
  - "Extracted run()'s while-body verbatim into tick() (statement order preserved, player_circle guard untouched); validated byte-for-byte against a baseline captured from the unmodified loop"
  - "timer.tick(FPS) stays in run() ONLY; tick() never reads the throttle (D-17)"
  - "Added a harness-only frame-driven sound shim (in replay.py) because the SDL dummy audio driver reports a played sound as 'playing' forever, which would soft-lock the starting phase — no game.py change"

patterns-established:
  - "Behavior-preserving extraction is proven, never assumed: baseline-trace-first then assert traces_equal byte-for-byte"
  - "Harness is a thin reader/driver around the unmodified game; the frame index lives on the driver as g._frame, not in game.py"
  - "Headless determinism: drive sound-phase gates by frame count via a harness shim, leaving game.py logic intact"

requirements-completed: [HRN-01, HRN-02]

# Metrics
duration: ~8min
completed: 2026-06-11
---

# Phase 1 · Plan 01-02: Steppable tick() + Trace Schema + Replay Driver Summary

**Extracted a steppable, sleep-independent `Game.tick()` from `run()` byte-identically (proven against a baseline trace captured from the UNMODIFIED loop), and built the D-03 trace schema (`harness/trace.py`) plus the sparse `{frame,key}` record/replay driver (`harness/replay.py`).**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-06-11T05:06:53Z
- **Completed:** 2026-06-11T05:14:47Z
- **Tasks:** 3
- **Files created:** 2 · **Files modified:** 1

## Accomplishments
- **Byte-identical tick() extraction (the phase's most delicate change):** moved `run()`'s while-body verbatim into `Game.tick()` (same statement order, `player_circle` guard preserved), kept the FPS throttle in `run()` only (D-17), and proved the extracted `tick()` reproduces a baseline trace captured from the *unmodified* `run()` loop **byte-for-byte** (`traces_equal == True`, `diff_traces` empty, 601 frames, `score_last=120`).
- **D-03 trace schema (`harness/trace.py`):** `capture_state(g)` is a pure reader producing exactly the 9 top-level keys (frame, pacman, 4 ghosts incl. target, score, lives, powerup, dots_remaining, game_over, game_won) with NO D-04 internal counters; plus `write_jsonl`/`read_jsonl` (sort_keys, line-diffable) and `traces_equal`/`diff_traces`.
- **Record/replay driver (`harness/replay.py`):** `load_events` (sparse JSONL, missing `type` → KEYDOWN), `KEYMAP`, and `run_scenario` that injects events via `pygame.event.post` (real `handle_events` path, D-18 — never mutates `direction_command`), steps `game.tick()`, captures the trace, breaks on natural terminal (D-19), and raises a loud `AssertionError` naming the cap on a frame-cap soft-lock (T-02-D).
- **Source-drift clean:** among source files, ONLY `game.py` changed (98+/90-); `ghost.py` and `player.py` are byte-unmodified. `grep -c capture_state game.py` == 0.
- **Full suite green:** `41 passed` under the venv after the change — the 15 ghost-micro characterization tests and the determinism guard all still pass.

## Task Commits

Each task was committed atomically (subject contains `01-02`, trailer present):

1. **Task 1: D-03 trace schema + baseline capture** — `0d2ca37` (feat)
2. **Task 2: extract steppable tick() from run() (byte-identical)** — `96c3b9d` (refactor)
3. **Task 3: record/replay driver (event injection + soft-lock cap)** — `4ccd521` (feat)

## Files Created/Modified
- `harness/trace.py` (created) — `capture_state(g)`, `write_jsonl`, `read_jsonl`, `traces_equal`, `diff_traces` (D-03/D-04/D-05).
- `harness/replay.py` (created) — `load_events`, `KEYMAP`, `run_scenario` (D-18/D-19) + `install_frame_driven_sound` (headless sound-gating shim).
- `game.py` (modified) — extracted `Game.tick()` (verbatim loop body, returns `running`); slimmed `Game.run()` to loop scaffolding + `timer.tick(FPS)` + `self.tick()`.

## Decisions Made
- **Baseline-trace-first, never re-bless:** the baseline came from the unmodified `run()` (driven via a transient monkeypatch of `pygame.display.flip` that captured state after each real flip, then a posted QUIT to exit `run()` naturally). The extracted `tick()` was then asserted byte-identical. No instrumentation was left in `game.py`.
- **`timer.tick(FPS)` stays in `run()` only (D-17):** `tick()` never calls the throttle, so the harness is sleep-independent by construction.
- **`player_circle` guard preserved exactly:** defined only inside `if not self.eat_freeze:` and referenced only inside `if not self.dying and not self.eat_freeze and not self.starting:` — not hoisted, not pre-initialized.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Frame-driven sound shim for the SDL dummy audio driver**
- **Found during:** Task 1 (baseline capture)
- **Issue:** Under SDL `dummy` audio, a played `Sound` reports `get_num_channels() > 0` *forever* (the dummy driver never advances playback time). The game gates its `starting`/`dying` phases on `is_start_playing()`/`is_death_playing()`, so the simulation soft-locked permanently in the `starting` phase — Pac-Man never moved, ghosts never exited the box, and any captured trace was a frozen no-op. This blocked capturing a meaningful box_exit baseline.
- **Fix:** Added `install_frame_driven_sound(game)` (a harness-only shim, placed in `harness/replay.py`) that makes `is_start_playing()`/`is_death_playing()` advance by frame count (sound real length × FPS, using the driver-maintained `g._frame`). It is installed identically for the baseline capture and the `tick()` replay, so the byte-for-byte comparison still detects any statement reorder. **No change to `game.py`/`ghost.py`/`player.py`.**
- **Files modified:** `harness/replay.py` (the shim is part of the replay driver module, within the plan's commit allowlist).
- **Verification:** With the shim, the box_exit baseline genuinely exercises movement (`score=120`, dots eaten) and ghost box-exit (Inky travels from `(440,388)` to `(384,646)`); the `tick()` replay reproduces it byte-for-byte.
- **Committed in:** `4ccd521` (Task 3 commit, with the driver).

---

**Total deviations:** 1 auto-fixed (Rule 3 — blocking environment issue).
**Impact on plan:** The shim was necessary to produce a non-trivial baseline; it lives outside game logic and is applied symmetrically to both sides of the comparison, so the "byte-identical" proof is fully preserved. No scope creep — the plan's allowlisted files were the only ones created/modified.

## Issues Encountered
- `pygame.time.Clock.tick` is read-only and cannot be monkeypatched; used a tiny no-throttle clock stub object for the baseline capture instead (behaviorally irrelevant to the numeric trace).
- The captured `*_box` field is the persistent `g.{name}_box` Game attribute (not the per-frame `Ghost.in_box`); the box_exit scenario is validated by ghost *movement out of the box region*, which it exercises.

## User Setup Required
None — no external service configuration required. All work is dev/test-only (no shipped runtime surface; `game.py` change is an internal behavior-preserving refactor).

## Next Phase Readiness
- **Wave 3+ unblocked:** `tick()` is the steppable seam Plan 03 (capture) and Plan 04 (goldens) drive; `harness/trace.py` is the golden-master format; `harness/replay.py` is the deterministic replay driver. `run_scenario` accepts a per-call `frame_cap` and an `on_frame` hook (Plan 03 saves PNGs there).
- **Determinism preserved:** full suite green (41 passed), ghost personalities byte-unchanged, `ghost.py`/`player.py` untouched.
- **Note for harness consumers:** scenarios that depend on the `starting`/`dying` phases must call `install_frame_driven_sound(game)` before replay (the headless determinism shim), and set `game._frame` each frame (run_scenario does this).

## Self-Check: PASSED

- `harness/trace.py` — FOUND
- `harness/replay.py` — FOUND
- `game.py` (tick extraction) — FOUND
- Commit `0d2ca37` (Task 1) — FOUND
- Commit `96c3b9d` (Task 2) — FOUND
- Commit `4ccd521` (Task 3) — FOUND

---
*Phase: 01-test-safety-net*
*Completed: 2026-06-11*
