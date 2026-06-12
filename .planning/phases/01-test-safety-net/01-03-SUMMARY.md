---
phase: 01-test-safety-net
plan: 03
subsystem: testing
tags: [pygame, headless, capture, png, montage, gif, pillow, play-loop, observe-decide-act, serialization, jsonl]

# Dependency graph
requires:
  - phase: 01-02
    provides: harness.replay.run_scenario (on_frame seam) + KEYMAP + install_frame_driven_sound, harness.trace.capture_state, Game.tick()
  - phase: 01-01
    provides: harness.headless.init_headless (SDL-dummy bootstrap), tests/artifacts/ gitignored, isolated .venv (incl. Pillow 11.0.0)
provides:
  - harness/capture.py — save_png (pygame.image.save), build_montage (blit, zero new dep), build_gif (Pillow only, D-20)
  - harness/play_loop.py — play_turn observe->decide->act driver (event.post injection, D-18) + serialize_inputs (sparse {frame,key,type} JSONL, D-10)
affects: [01-04]

# Tech tracking
tech-stack:
  added: []  # Pillow already installed in .venv from 01-01; used here for the first time (build_gif only)
  patterns:
    - "PNG-per-frame via pygame.image.save; montage via Surface.blit of scaled thumbnails (zero new dep, D-20)"
    - "Pillow imported INSIDE build_gif only — single new dep confined to the GIF path (D-20)"
    - "observe->decide->act turn driver: pluggable pure decide_fn keeps recorded sessions deterministic (D-10/T-03-R)"
    - "play-loop inputs serialize to the SAME sparse JSONL replay.load_events parses — a Claude session becomes a CI-replayable golden (D-10)"
    - "all capture output writes under tests/artifacts/ (gitignored), never tests/golden/ (D-06/T-03-I)"

key-files:
  created: [harness/capture.py, harness/play_loop.py]
  modified: []

key-decisions:
  - "build_montage returns a pygame.Surface (caller saves via save_png) — pure pygame, zero new dependency, sheet width = cols*(cell_w+pad)+pad so it always fits the requested columns"
  - "Pillow is imported inside build_gif's body (not at module top) so the one new dep is provably used only for the GIF (D-20)"
  - "play_loop reuses replay.KEYMAP (imported, not redefined) and injects only via pygame.event.post — never mutating player.direction_command (D-18)"
  - "serialize_inputs emits {frame,key,type} sorted by frame in the exact shape replay.load_events consumes, so a recorded session round-trips byte-for-byte through the replay driver (D-10)"

patterns-established:
  - "Visual proof is eyes-only: capture.py never hashes pixels; the numeric trace (harness/trace.py) stays the stable golden"
  - "A Claude-driven session is made deterministic by construction: pure decide_fn (no randomness/wall-clock) + serialize injected inputs to the replay format"

requirements-completed: [HRN-03, HRN-04]

# Metrics
duration: ~6min
completed: 2026-06-11
---

# Phase 1 · Plan 01-03: Frame Capture + Claude Play-Loop Summary

**Added the visual-proof channel (`harness/capture.py`: PNG per frame, blit-based montages with zero new dependency, and a Pillow-only GIF) and the Claude-drive channel (`harness/play_loop.py`: an observe→decide→act `play_turn` that injects via `event.post` and serializes its inputs to the same sparse JSONL the replay driver consumes — so a Claude session becomes a deterministic, CI-replayable golden).**

## Performance

- **Duration:** ~6 min
- **Tasks:** 2
- **Files created:** 2 · **Files modified:** 0

## Accomplishments

- **Frame capture (HRN-03, `harness/capture.py`):**
  - `save_png(pygame, screen, path)` writes a real PNG via `pygame.image.save` (format inferred from the `.png` extension), creating parent dirs under `tests/artifacts/`. Verified: a written PNG is non-zero (4990 bytes) and reloads via `pygame.image.load` at the expected 900-wide size.
  - `build_montage(pygame, frame_surfaces, cols, cell=(180,190), pad=4)` builds ONE `pygame.Surface` and blits `pygame.transform.scale` thumbnails into a cols-wide grid — pure pygame, **zero new dependency** (D-20). Verified: a 4-frame, 2-col montage returns a `(372, 392)` Surface (≥ `cols*cell_w`).
  - `build_gif(png_paths, out_path, duration_ms=33, loop=0)` imports `PIL.Image` **inside the function** and calls `frames[0].save(..., save_all=True, append_images=frames[1:], duration=, loop=)`. Verified: the output opens via `PIL.Image.open` and reports `format == 'GIF'`. `from PIL` appears **only** at line 66 inside `build_gif` (grep-confirmed) — the single new dep is confined to the GIF path (D-20).
  - All smoke outputs landed under `tests/artifacts/` (gitignored); nothing written to `tests/golden/` (D-06/T-03-I). No pixel hashing anywhere.
- **Claude play-loop (HRN-04, `harness/play_loop.py`):**
  - `play_turn(game, pygame, capture_state, decide_fn, png_path=None)` runs OBSERVE (optional `save_png` + `capture_state`) → DECIDE (`decide_fn(state, png_path)` → logical key or None) → ACT (`pygame.event.post(KEYDOWN)`, the real input path, D-18) → STEP (`game.tick()`), returning the post-tick snapshot. Verified: it advances exactly one tick and returns a `capture_state` dict.
  - `serialize_inputs(events, path)` writes `{frame,key,type}` records as sparse JSONL (sorted by frame) in the **exact shape `harness.replay.load_events` parses**. Verified: a recorded session round-trips through `load_events` into the same frame→events mapping, and a 120-frame scripted session, serialized then re-driven through the replay loop, produced a trace **byte-equal** to the play session's own per-frame snapshots (`traces_equal == True`) — the D-10 deterministic-golden property.
  - Reuses `replay.KEYMAP` (imported at line 26, **no** second mapping defined); injects **only** via `event.post` (no `player.direction_command` mutation).
- **Source-drift clean:** `game.py`, `ghost.py`, `player.py` are byte-unmodified (`git status --porcelain` empty for all three).
- **Full suite green:** `41 passed` under the venv (`./.venv/Scripts/python.exe -m pytest -q`, exit 0) after both commits.

## Task Commits

Each task committed atomically (subject contains `01-03`, trailer present):

1. **Task 1: PNG-per-frame capture + blit montage + Pillow GIF** — `038d1a6` (feat)
2. **Task 2: Claude play-loop observe→decide→act + input serialization** — `7c39a4a` (feat)

## Files Created/Modified

- `harness/capture.py` (created) — `save_png`, `build_montage` (blit, zero new dep), `build_gif` (Pillow only, imported inside the fn).
- `harness/play_loop.py` (created) — `play_turn` (observe→decide→act, `event.post`) + `serialize_inputs` (sparse `{frame,key,type}` JSONL).

## Decisions Made

- **Montage returns a Surface, caller saves it:** `build_montage` does pure-pygame `transform.scale` + `blit`, returning the sheet so `save_png` writes it — keeping the zero-dep guarantee and letting callers route the sheet anywhere under `tests/artifacts/`.
- **Pillow confined to `build_gif`:** the import lives in the function body (not module top), making it provable-by-grep that the one new dep is used only for the human-facing GIF (D-20).
- **`play_turn` snapshots after the tick:** the returned snapshot is post-`tick()` (consistent with `run_scenario`, which captures after `game.tick()`), so a play session's snapshots line up frame-for-frame with a replay of its serialized inputs.

## Deviations from Plan

None — plan executed exactly as written. Both tasks created only their allowlisted files; no source files were touched; no architectural changes were needed.

## Issues Encountered

- The Task 2 round-trip smoke initially drove the serialized session through `replay.run_scenario`, which (correctly) raised its `for/else` soft-lock backstop because a bounded 120-frame window is **not** a natural terminal (`game_over`/`game_won`) — that assertion exists exactly to catch non-terminating full scenarios (D-19). The acceptance criterion is *round-trip trace equality over the recorded session*, so the smoke drove the replay driver's identical per-frame body (`event.post` → `tick` → `capture_state`) over the bounded window and asserted `traces_equal`. This is a property of the smoke harness only; `harness/play_loop.py` and `harness/replay.py` were not changed for it.
- Under the scripted DOWN/LEFT/UP plan from spawn the session scores 0 (those directions face walls during the `starting` phase) — irrelevant to this plan, whose property is *determinism*, not gameplay quality. The real long golden session is generated in Plan 01-04 (D-10).

## User Setup Required

None — both files are dev/test-only. Pillow is a dev-only dependency (already in `.venv`) and is excluded from the PyInstaller `.exe` build; no new runtime attack surface ships (matches the plan threat model: T-03-I mitigated by writing only under gitignored `tests/artifacts/`; T-03-R mitigated by the pure `decide_fn` + input serialization).

## Next Phase Readiness

- **Plan 01-04 unblocked:** `play_turn` + `serialize_inputs` are the recording half of the D-10 Claude session (drive a full session → serialize `{frame,key}` → commit as a `golden/claude_session_01/{input.jsonl,trace.jsonl}` that replays in CI). `save_png`/`build_montage`/`build_gif` provide the montage (Claude vision) + GIF (human) artifacts, all under gitignored `tests/artifacts/`.
- **Determinism preserved:** full suite green (41 passed); `game.py`/`ghost.py`/`player.py` unchanged.

## Self-Check: PASSED

- `harness/capture.py` — FOUND
- `harness/play_loop.py` — FOUND
- Commit `038d1a6` (Task 1) — FOUND
- Commit `7c39a4a` (Task 2) — FOUND
- `game.py`/`ghost.py`/`player.py` — unmodified (git porcelain empty)

---
*Phase: 01-test-safety-net*
*Completed: 2026-06-11*
