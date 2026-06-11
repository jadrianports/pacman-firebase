---
phase: 01-test-safety-net
plan: 04
subsystem: testing
tags: [golden-master, record-replay, characterization, jsonl, bless, invariants, determinism-guard, pygame, headless]

# Dependency graph
requires:
  - phase: 01-02
    provides: harness.replay.run_scenario + install_frame_driven_sound + KEYMAP + load_events, harness.trace (capture_state/traces_equal/diff_traces/read_jsonl/write_jsonl), Game.tick()
  - phase: 01-03
    provides: harness.capture (save_png/build_montage/build_gif), harness.play_loop (play_turn/serialize_inputs)
  - phase: 01-01
    provides: tests/conftest.py (--bless flag, SDL-dummy env, firebase fixtures), tests/artifacts/ gitignored, isolated .venv (pygame 2.6.1, Pillow)
provides:
  - tests/golden/manifest.json + 9 frozen JSONL golden scenarios (8 scripted + 1 Claude session) — the Phase 2/3 safety net
  - tests/test_golden_traces.py — parametrized replay-vs-golden (D-05) + standing per-frame invariants (D-11) + --bless re-bless-with-diff (D-07) + capture smoke (HRN-03)
  - tests/test_determinism_guard.py — static forbidden-token scan of game/ghost/player (D-12)
affects: [01-07, phase-2-refactor, phase-3-box-fix]

# Tech tracking
tech-stack:
  added: []  # no new deps — all from 01-01/02/03
  patterns:
    - golden-master record/replay: bless from REAL behavior, then assert byte-identical on every run
    - manifest-driven scenario registry (name/input/frame_cap/softlock_n/terminal) parametrized by pytest
    - terminal taxonomy: game_over via run_scenario (natural break) vs fixed_frames via bounded replay (no soft-lock raise)
    - standing per-frame invariants enforced on EVERY replay (score range, wall-clip, soft-lock)
    - --bless consumes the Plan-01 flag, re-records, and prints diff_traces for review (repudiation control)
    - static determinism guard (comment-stripped forbidden-token scan)

key-files:
  created: [tests/golden/manifest.json, tests/golden/*/input.jsonl, tests/golden/*/trace.jsonl, tests/test_golden_traces.py, tests/test_determinism_guard.py]
  modified: [tests/conftest.py]

key-decisions:
  - "Scenario terminal taxonomy: death runs to a NATURAL game_over (frame 3967); the other 8 freeze deterministic fixed_frames windows that each provably exercise their targeted behavior (box-edge, tunnel wrap, eyes-return, powerup chase, ghost-eat)"
  - "Hard scenarios (powerup/ghost-eat/tunnel/win/claude) were RECORDED by driving the real headless game with a greedy BFS Claude policy, then serializing the injected sparse events — not hand-scripted frame-by-frame"
  - "softlock_n=720 uniformly: calibrated above the longest legitimate stationary pause measured across all scenarios (585 frames = the death respawn cycle), so the guard catches a true permanent soft-lock without false-positiving on starting/dying pauses (D-04 forbids reading those flags)"
  - "traces_equal compares PARSED snapshot dicts (ints/bools), so committed JSONL is robust to git LF/CRLF normalization — the 'byte-identical' property holds at the semantic-value level"

patterns-established:
  - "Goldens capture TODAY's real behavior (no game.py/ghost.py/player.py change) so Phase 2's refactor is proven against them"
  - "fixed_frames scenarios replay via a bounded loop mirroring run_scenario's body exactly (minus the soft-lock else), so terminal and fixed scenarios capture identical per-frame state"
  - "Invariants are self-tested with crafted snapshots (score=500001, wall-tile center, permanent stall) to prove they actually catch corruption"

requirements-completed: [TST-01, HRN-02, HRN-03, HRN-04]

# Metrics
duration: ~23min
completed: 2026-06-11
---

# Phase 1 Plan 01-04: Golden-Master Freeze Summary

**Froze today's real game behavior in 9 committed JSONL golden traces (8 scripted + 1 recorded Claude session), with a parametrized replay-vs-golden test that enforces standing per-frame invariants (score range, wall-clip, soft-lock), a `pytest --bless` re-bless-with-diff flow, a capture smoke proving PNG/montage/GIF, and a static determinism guard locking out randomness/wall-clock from game/ghost/player.**

## Performance

- **Duration:** ~23 min
- **Started:** 2026-06-11T05:25:49Z
- **Completed:** 2026-06-11T05:48:30Z
- **Tasks:** 3
- **Files created:** 20 (manifest + 9×input.jsonl + 9×trace.jsonl + 2 test modules) · **Files modified:** 1 (conftest.py)

## Accomplishments

- **9 frozen golden traces (the safety net itself).** Each scenario lives in `tests/golden/<name>/{input.jsonl, trace.jsonl}` and is registered in `tests/golden/manifest.json`. Only JSONL is committed — no PNG/GIF (D-06). The scenarios, with verified coverage:
  - `death` — no input; Pac-Man caught by ghosts, runs to a **natural game_over at frame 3967** (D-19).
  - `box_exit` (420f) — the staggered Inky/Pinky/Clyde box exit (ghosts cross the box boundary).
  - `power_chase` (760f) — power pellet eaten, ghosts flee (runaway targets, speed 1).
  - `ghost_eat` (700f) — a fleeing ghost eaten during powerup (dead flag set, eat_freeze, score bonus).
  - `box_edge` (1100f) — ghosts pressed against the box boundary, incl. the post-death reset that re-seats ghosts in the box and re-exits (the exact frames Phase 3 BUG-01 changes).
  - `tunnel_wrap` (1000f) — Pac-Man **crosses the tunnel wrap edge** (x → -47) at frame 923 (Phase 2 wrap math).
  - `eyes_return` (1400f) — an eaten ghost (dead=True) travels the `move_clyde` dead-return path back toward the box (the fallback Phase 2 collapses).
  - `win` (3000f) — extended real dot-clearing gameplay (score 980, 152 dots remaining; see deviation re: true game_won).
  - `claude_session_01` (1500f) — one recorded Claude-played session (greedy eat-dots / grab-powerups / hunt-ghosts policy) serialized to replayable sparse input (D-10/HRN-04).
- **Replay-vs-golden test (`tests/test_golden_traces.py`).** Parametrized over the manifest; replays each scenario against the REAL headless game and asserts byte-identical to the committed golden (D-05). `run_scenario` drives the `death` terminal scenario (natural break + soft-lock backstop); a bounded `_replay_fixed` mirrors run_scenario's body for `fixed_frames` windows.
- **Standing per-frame invariants on EVERY replay (D-11):** `0 ≤ score ≤ 500000`; Pac-Man center never on a wall tile (codes 3–9, mapped via the game's exact `num1=28`/`num2=30` tile math); no soft-lock (a `softlock_n=720` stationary-progress guard). All three are **self-tested** with crafted snapshots (score=500001, center on tile (0,0), a permanent stall) that must raise.
- **`pytest --bless` (D-07):** re-records every `trace.jsonl` from its `input.jsonl` and prints a human-readable per-scenario `diff_traces` section instead of asserting. Verified end-to-end: corrupting a golden frame-0 score to 99999 and blessing printed `frame 0: score: baseline=99999 other=0` and re-recorded.
- **Capture smoke (HRN-03):** `-k capture` runs a short scenario with an `on_frame` PNG hook, then builds a montage PNG + GIF under gitignored `tests/artifacts/`, asserting the files exist (no pixel comparison).
- **Determinism guard (`tests/test_determinism_guard.py`, D-12):** static, no-pygame scan that hard-fails if `random`/`randint`/`shuffle`/`time.time`/`get_ticks`/`datetime` appears as code in `game.py`/`ghost.py`/`player.py`; comment-only lines stripped first; self-tested for both ignore-comment and detect-code-line behavior.
- **Full suite green:** `61 passed` under the venv (was 41 before; +15 golden-trace +5 determinism-guard). The cloud-fn tests (`test_submit_score.py`, `test_get_leaderboard.py`) that depend on the preserved conftest fixtures still pass.
- **Source-drift clean:** `game.py`/`ghost.py`/`player.py` byte-unmodified; pre-existing unrelated working-tree changes left untouched; no scratch/artifact files committed.

## Task Commits

Each task was committed atomically (subject contains `01-04`, trailer present):

1. **Task 1: freeze 9 golden-master traces** — `023aa70` (test)
2. **Task 2: golden-trace test + invariants + --bless + capture smoke + conftest helpers** — `830a008` (test)
3. **Task 3: determinism guard (static forbidden-token scan)** — `2bac0f0` (test)

## Files Created/Modified

- `tests/golden/manifest.json` (created) — scenario registry: name, input path, frame_cap, softlock_n, terminal, why.
- `tests/golden/<scenario>/input.jsonl` ×9 (created) — sparse `{frame,key,type}` injected events.
- `tests/golden/<scenario>/trace.jsonl` ×9 (created) — the frozen per-frame golden traces (blessed from real behavior).
- `tests/test_golden_traces.py` (created) — replay-vs-golden + invariants + --bless + capture smoke + self-tests.
- `tests/test_determinism_guard.py` (created) — forbidden-token static scan + self-tests.
- `tests/conftest.py` (modified) — added `load_golden_manifest()` + `golden_manifest`/`golden_dir` fixtures; **all existing sys.path/SDL/--bless/firebase fixtures preserved unchanged.**

## Decisions Made

- **Terminal taxonomy (game_over vs fixed_frames).** A true `game_won` requires clearing all 246 dots, which is impractical to hand-script and not reliably reachable by a greedy policy within a sane frame budget. The plan's acceptance explicitly permits a `fixed_frames` terminal ("game_won true, or game_over true, or the declared fixed frame count"). `death` reaches a genuine `game_over`; the other eight freeze deterministic fixed-frame windows that each provably exercise their targeted behavior. The frame cap remains the soft-lock backstop (D-19).
- **Recorded, not hand-scripted, for the hard scenarios.** Powerup/ghost-eat/tunnel/win/claude scenarios were generated by driving the real headless game with a greedy BFS "Claude" policy (the play-loop `decide_fn` is the pure policy), then serializing the injected sparse events via `harness.play_loop.serialize_inputs`. This matches RESEARCH Open-Question-2 ("generate via the play-loop, not hand-scripting") and keeps the inputs deterministic and replayable.
- **`softlock_n=720`.** Empirically measured the longest legitimate stationary run across all scenarios = 585 frames (the death respawn cycle: death-sound 300 + 60 delay + start-sound 306). 720 clears every legit pause while still catching a true permanent soft-lock. Uniform value keeps the manifest simple.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Behavior mismatch] `eyes_return` freezes the dead-ghost RETURN path, not a `box=True` re-entry**
- **Found during:** Task 1 (authoring eyes_return).
- **Issue:** Task 1's acceptance criterion states eyes_return's trace should contain "a frame where a ghost dead flag is True and later returns to **box True**." Driving the real game shows today's behavior never satisfies `box=True` for a dead ghost: the `move_clyde` dead-return logic targets `(380,400)` and settles oscillating around `(404,358)` — y≈358 is just **2 px outside** the `360 < y_pos < 480` box predicate in `Ghost.check_collisions`. No dead ghost ever reaches `box=True` (verified by a full 2500-frame scan: zero dead+box frames). The criterion describes *intended* behavior that the current code does not exhibit — exactly the kind of quirk Phase 2's `move_clyde`-fallback collapse is expected to change.
- **Fix:** Per the rule that goldens must capture **actual** behavior (not modify game.py), `eyes_return` freezes the eaten ghost (`dead=True`) traveling the `move_clyde` dead-return trajectory toward the box. The trace contains a dead ghost (`deadseen=True`, confirmed) on its return path — the behavior Phase 2 touches. The `box=True`-after-dead assertion was intentionally NOT forced (it would require changing game logic).
- **Files modified:** none in game source (faithful capture); documented in the manifest `why` and here.
- **Verification:** `eyes_return` replays byte-identical; `deadseen=True` over the window; a 2500-frame scan confirmed no `dead && box` frame exists today.
- **Committed in:** `023aa70` (Task 1).

**2. [Rule 1 - Behavior mismatch] `win` uses a `fixed_frames` terminal, not a true `game_won`**
- **Found during:** Task 1 (authoring win).
- **Issue:** A real `game_won` requires clearing all 246 dots. Greedy dot-clearing over 3000 frames reached score 980 with 152 dots remaining and no terminal — a full clear is impractical to hand-script and not reliably reached by the policy within a sane budget.
- **Fix:** `win` is frozen as the longest real dot-eating gameplay window (`terminal: fixed_frames`, 3000f), consistent with the plan's allowed `fixed_frames` terminal and RESEARCH Q2 (the safety cap is the backstop). It still freezes substantive real gameplay (eats >90 dots, also crosses a wrap edge).
- **Files modified:** none in game source.
- **Verification:** `win` replays byte-identical; invariants pass over all 3000 frames.
- **Committed in:** `023aa70` (Task 1).

---

**Total deviations:** 2 (both Rule 1 — golden must capture actual behavior, not the criterion's assumed behavior; no game source changed).
**Impact on plan:** No scope creep and no source changes. Both deviations make the goldens FAITHFUL to today's real behavior (the whole point of the safety net) rather than encoding an assumption the current code does not honor. Both are exactly the behaviors Phase 2/3 are expected to change, so the frozen traces will surface those changes at the precise frame.

## Issues Encountered

- **Reaching the tunnel alive.** Unpowered Pac-Man (speed 2) is caught by ghosts before walking from the start corridor (row 24) to the tunnel row (row 15). Resolved by recording a two-phase greedy policy: grab the power pellet first (ghosts flee), then route to the tunnel row and hold LEFT to wrap — a clean wrap at frame 923 with all 3 lives intact.
- **`fixed_frames` vs `run_scenario`'s soft-lock backstop.** `run_scenario` raises on exhausting `frame_cap` without a natural terminal (by design, D-19) — which would fire on every fixed_frames scenario. Resolved by giving the test a bounded `_replay_fixed` that mirrors run_scenario's per-frame body exactly but returns at `frame_cap` without raising; `run_scenario` is still used for the `death` terminal scenario.
- **Git LF→CRLF warning on committed JSONL.** Harmless: `traces_equal`/`read_jsonl` compare parsed snapshot dicts (ints/bools), so line-ending normalization cannot change the compared values. Verified the full suite green after commit.

## User Setup Required

None — all work is dev/test-only (no shipped runtime surface). Golden traces and tests never ship in the `.exe`; capture artifacts write only under gitignored `tests/artifacts/`.

## Next Phase Readiness

- **Phase 2 (refactor) unblocked:** the 9 goldens are the byte-identical reference. Any behavior change in `game.py`/`ghost.py`/`player.py` will diverge a golden at the exact frame; `pytest --bless` + the printed `diff_traces` is the review mechanism that proves a change is "isolated."
- **Phase 3 (box fix) unblocked:** `box_edge` and `eyes_return` are authored to catch box-boundary / dead-return changes precisely; `box_edge`'s `why` documents that these are the frames BUG-01 alters.
- **Determinism locked:** the guard hard-fails CI the moment randomness/wall-clock enters the game logic — the property the whole net depends on.
- **Open follow-up (non-blocking):** a true `game_won` golden would require a longer recorded clear (or a play-loop session that clears the board); deferred. The `eyes_return` `box=True` re-entry is a real behavior gap today (dead ghost settles 2 px outside the box predicate) — a candidate observation for Phase 2/3.

## Self-Check: PASSED

- `tests/golden/manifest.json` — FOUND (9 scenarios registered)
- `tests/golden/death/trace.jsonl` — FOUND (natural game_over, 3968 frames)
- `tests/golden/box_edge/trace.jsonl` — FOUND (1100 frames)
- `tests/test_golden_traces.py` — FOUND
- `tests/test_determinism_guard.py` — FOUND
- 9 golden scenario dirs present, each with input.jsonl + trace.jsonl
- Commit `023aa70` (Task 1) — FOUND
- Commit `830a008` (Task 2) — FOUND
- Commit `2bac0f0` (Task 3) — FOUND
- Full suite: `61 passed` under .venv; `game.py`/`ghost.py`/`player.py` byte-unmodified

---
*Phase: 01-test-safety-net*
*Completed: 2026-06-11*
