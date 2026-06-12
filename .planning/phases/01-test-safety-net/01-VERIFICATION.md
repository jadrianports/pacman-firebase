---
phase: 01-test-safety-net
verified: 2026-06-11T08:45:00Z
status: passed
score: 8/8 must-haves verified
overrides_applied: 0
re_verification: null
gaps: []
deferred: []
human_verification: []
---

# Phase 1: Test Safety Net — Verification Report

**Phase Goal:** Establish a comprehensive, continuously-enforced test safety net that FREEZES today's
Pac-Man behavior (ghost AI decisions, cloud-fn validators) byte-for-byte, so Phase 2's refactor can be
proven non-regressive. "Maximum paranoia" bar: golden traces + per-ghost micro tests + determinism guard
+ CI merge-gate.

**Verified:** 2026-06-11T08:45:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                               | Status     | Evidence                                                                                              |
|----|-------------------------------------------------------------------------------------|------------|-------------------------------------------------------------------------------------------------------|
| 1  | Full suite passes under the venv (61 tests)                                         | VERIFIED   | `.venv/Scripts/python.exe -m pytest -q` → `61 passed in 67.85s`                                      |
| 2  | `Game.tick()` is steppable; `run()` retains `timer.tick`; `tick()` has no throttle  | VERIFIED   | `inspect.getsource(Game.tick)` → `timer.tick` absent in tick, present in run; `self.tick()` in run    |
| 3  | `ghost.py` and `player.py` byte-unmodified since `a229153`                          | VERIFIED   | `git diff a229153..HEAD --name-only -- ghost.py player.py` → empty output                             |
| 4  | 9 golden-master scenarios committed (manifest + input.jsonl + trace.jsonl per dir)  | VERIFIED   | `tests/golden/manifest.json` lists 9 scenarios; all 9 dirs have both files; manifest parsed cleanly  |
| 5  | `test_golden_traces.py` replays all goldens byte-for-byte; `test_determinism_guard.py` exists | VERIFIED | All 15 golden-trace tests pass; determinism guard 5/5 pass                                    |
| 6  | 15 ghost micro-characterization tests pin per-ghost decisions (TST-02)              | VERIFIED   | `test_ghost_micro.py` has exactly 15 `def test_` functions; all 15 pass                               |
| 7  | Cloud-fn validator/upsert tests pass (TST-03)                                       | VERIFIED   | `test_submit_score.py` (11 tests) + `test_get_leaderboard.py` (4 tests) = 15 cloud-fn tests, all pass |
| 8  | CI green on run 27331943685; branch protection on `main` requires `test` check      | VERIFIED   | `gh run view 27331943685` → `conclusion: success`; `gh api .../branches/main/protection --jq '.required_status_checks.contexts'` → `["test"]` |

**Score:** 8/8 truths verified

---

## Required Artifacts

| Artifact                               | Expected                                                        | Status     | Details                                              |
|----------------------------------------|-----------------------------------------------------------------|------------|------------------------------------------------------|
| `requirements-dev.txt`                 | Pinned deps (firebase-admin==6.5.0, functions-framework==3.8.1) | VERIFIED  | All 5 deps pinned; firebase-admin major 6 confirmed  |
| `harness/__init__.py`                  | Package marker                                                  | VERIFIED   | Exists                                               |
| `harness/headless.py`                  | `init_headless()` sets SDL env before import pygame             | VERIFIED   | SDL_VIDEODRIVER set on line 17, `import pygame` on line 19; 27 lines |
| `harness/trace.py`                     | `capture_state`, `write_jsonl`, `read_jsonl`, `traces_equal`, `diff_traces` | VERIFIED | 104 lines; all five functions present     |
| `harness/replay.py`                    | `load_events`, `run_scenario`, soft-lock backstop               | VERIFIED   | 124 lines; `AssertionError` raised on frame_cap exhaustion |
| `harness/capture.py`                   | PNG/montage/GIF functions                                       | VERIFIED   | 79 lines; smoke test passes                          |
| `harness/play_loop.py`                 | `play_turn`, `serialize_inputs` (Claude observe-decide-act)     | VERIFIED   | 64 lines; used to record `claude_session_01`         |
| `game.py` (tick extraction)            | `def tick` present; `timer.tick` absent from tick body          | VERIFIED   | Confirmed via `inspect.getsource`                    |
| `tests/conftest.py`                    | sys.path, SDL dummy, --bless flag, firebase mock fixtures       | VERIFIED   | `pytest_addoption` present; SDL setdefault; firebase patch confirmed |
| `.gitignore`                           | `tests/artifacts/` rule                                         | VERIFIED   | Rule present with explanatory comment                |
| `tests/golden/manifest.json`           | 9 scenarios registered                                          | VERIFIED   | Parsed: 9 entries with correct names                 |
| `tests/golden/*/input.jsonl` (×9)      | Sparse input files for all 9 scenarios                          | VERIFIED   | All 9 present                                        |
| `tests/golden/*/trace.jsonl` (×9)      | Frozen golden traces for all 9 scenarios                        | VERIFIED   | All 9 present; replay byte-identical                 |
| `tests/test_golden_traces.py`          | Parametrized replay + invariants + --bless + capture smoke      | VERIFIED   | 15 tests; all pass; getoption("--bless") wired       |
| `tests/test_determinism_guard.py`      | Static forbidden-token scan of game/ghost/player (D-12)         | VERIFIED   | 5 tests; comment-strip + code-detect self-tested     |
| `tests/test_ghost_micro.py`            | 15 characterization tests for check_collisions + 4 move_*       | VERIFIED   | 15 tests; all pass; deepcopy confirmed               |
| `tests/test_submit_score.py`           | Validator 400s + is_new_best upsert (firebase mocked)           | VERIFIED   | 11 tests covering all acceptance criteria            |
| `tests/test_get_leaderboard.py`        | success/empty paths via mocked query.stream()                   | VERIFIED   | 4 tests; all pass                                    |
| `.github/workflows/ci.yml`             | Headless pytest on ubuntu-latest/py3.12, push-any-branch + PR   | VERIFIED   | SDL dummy env, python-version 3.12, actions pinned to majors |

---

## Key Link Verification

| From                              | To                                              | Via                               | Status   | Details                                                  |
|-----------------------------------|-------------------------------------------------|-----------------------------------|----------|----------------------------------------------------------|
| `game.py run()`                   | `game.py tick()`                                | `self.tick()` inside while loop   | WIRED    | Confirmed via `inspect.getsource(Game.run)`              |
| `harness/replay.py`               | `game.tick()`                                   | `game.tick()` each frame          | WIRED    | `run_scenario` calls `.tick()` per frame                 |
| `harness/replay.py`               | `pygame.event.post`                             | sparse event injection            | WIRED    | `event.post` present; no direct `player.direction_command` mutation |
| `tests/test_golden_traces.py`     | `harness.replay.run_scenario`                   | replay each manifest scenario     | WIRED    | `run_scenario` call + `traces_equal` assertion           |
| `tests/test_golden_traces.py`     | `request.config.getoption('--bless')`           | re-bless mode                     | WIRED    | `getoption("--bless")` on line 195 + 221                 |
| `tests/test_determinism_guard.py` | `game.py/ghost.py/player.py` source             | forbidden-token scan              | WIRED    | Reads source text; 5 tests pass green                    |
| `tests/test_ghost_micro.py`       | `ghost.Ghost.move_blinky/inky/pinky/clyde`      | construct Ghost headless, call    | WIRED    | `move_blinky/inky/pinky/clyde` called with exact asserts |
| `tests/test_submit_score.py`      | `cloud_functions.submit_score.main.submit_score`| flask.Request via EnvironBuilder  | WIRED    | All validator + upsert paths exercised                   |
| `.github/workflows/ci.yml`        | `pytest -q` (full suite)                        | CI runs the test job              | WIRED    | `pytest` step present; SDL dummy env set; CI run 27331943685 = success |

---

## Data-Flow Trace (Level 4)

Not applicable — this phase produces test infrastructure, not data-rendering UI components.

---

## Behavioral Spot-Checks

| Behavior                                      | Command                                           | Result                              | Status  |
|-----------------------------------------------|---------------------------------------------------|-------------------------------------|---------|
| Full suite passes under venv                  | `.venv/Scripts/python.exe -m pytest -q`           | `61 passed in 67.85s`               | PASS    |
| tick() has no timer.tick; run() delegates tick | `inspect.getsource` via Python                   | timer.tick absent in tick, present in run | PASS |
| ghost.py/player.py unmodified since a229153   | `git diff a229153..HEAD --name-only -- ghost.py player.py` | Empty output               | PASS    |
| 9 golden scenarios each have input+trace      | `ls tests/golden/` per scenario                   | All 9: input=YES trace=YES          | PASS    |
| 15 ghost micro tests pass                     | `.venv/Scripts/python.exe -m pytest tests/test_ghost_micro.py -v` | `15 passed`             | PASS    |
| 15 cloud-fn tests pass                        | `.venv/Scripts/python.exe -m pytest tests/test_submit_score.py tests/test_get_leaderboard.py` | `15 passed` | PASS    |
| CI run 27331943685 green                      | `gh run view 27331943685 --json status,conclusion` | `conclusion: success`              | PASS    |
| Branch protection requires 'test' check       | `gh api .../branches/main/protection --jq '.required_status_checks.contexts'` | `["test"]` | PASS    |
| Capture smoke (PNG/montage/GIF)               | `.venv/Scripts/python.exe -m pytest tests/test_golden_traces.py -k capture` | `1 passed`       | PASS    |
| Claude session replays green                  | `.venv/Scripts/python.exe -m pytest tests/test_golden_traces.py -k claude_session` | `2 passed` | PASS  |

---

## Probe Execution

No probes declared in PLAN.md files. Spot-checks above serve as behavioral verification.

---

## Requirements Coverage

| Requirement | Source Plans             | Description                                                                      | Status    | Evidence                                                              |
|-------------|--------------------------|----------------------------------------------------------------------------------|-----------|-----------------------------------------------------------------------|
| HRN-01      | 01-01, 01-02             | Game runs headless and is steppable via extracted `tick()`                       | SATISFIED | `Game.tick()` exists; `timer.tick` absent from tick body; SDL dummy   |
| HRN-02      | 01-02, 01-04             | Record/replay captures full per-frame trace; replays deterministically           | SATISFIED | `harness/trace.py` + `harness/replay.py`; 9 goldens replay byte-identical |
| HRN-03      | 01-03, 01-04             | Frames captured to PNG/montage/GIF                                               | SATISFIED | `harness/capture.py` exists; capture smoke test passes; `test_capture_smoke_png_montage_gif` PASS |
| HRN-04      | 01-03, 01-04             | Claude drives the game in observe-decide-act loop                                | SATISFIED | `harness/play_loop.py` + `claude_session_01` recorded and replays green |
| TST-01      | 01-01, 01-04             | Golden-master traces of current behavior recorded and frozen                     | SATISFIED | 9 scenarios committed; `test_baseline_golden[*]` all 9 pass           |
| TST-02      | 01-05                    | Micro tests assert per-ghost decisions (check_collisions, move_blinky/inky/pinky/clyde) | SATISFIED | 15 tests in `test_ghost_micro.py`; all pass; exact (x,y,dir) tuples pinned |
| TST-03      | 01-01, 01-06             | Cloud-fn validator tests (initials regex, score range, upsert)                   | SATISFIED | 11 submit_score tests + 4 get_leaderboard tests; all pass; firebase mocked |
| TST-04      | 01-07                    | CI runs the full suite headless on push; green                                   | SATISFIED | CI run 27331943685 = success; branch protection requires 'test' check  |

All 8 Phase 1 requirements (HRN-01 through TST-04) are SATISFIED. REF-01, REF-02, BUG-01, HYG-01 through HYG-04 are Phase 2/3 scope — correctly pending.

---

## Anti-Patterns Found

None blocking. Observations:

| File              | Pattern                                                  | Severity | Impact                                                                                        |
|-------------------|----------------------------------------------------------|----------|-----------------------------------------------------------------------------------------------|
| `REQUIREMENTS.md` | All 8 Phase 1 requirements still show `Pending` status   | INFO     | The traceability table was not updated to reflect completion — documentation debt, not behavioral |

No `TBD`, `FIXME`, or `XXX` markers found in modified files. No stub implementations detected.

---

### Deviation Notes (not gaps)

**Flee-vs-chase tests use target tuple, not `powerup=True`:** The plan acceptance criterion says "at least one flee-vs-chase test sets powerup True." The implemented tests vary the `target` parameter instead — which is the correct mechanism, because `move_*` methods read only `self.target` (not `self.powerup`) for directional decisions. `powerup` only affects which target `game.get_targets()` passes into the Ghost constructor. The 01-05 SUMMARY documents this decision explicitly. The behavior is correctly characterized.

**`eyes_return` does not reach `box=True` after death:** The criterion assumed dead ghosts re-enter the box (`box=True`). The real game never satisfies this (dead ghost settles 2 px outside the box predicate). The golden captures actual behavior. Documented in 01-04 SUMMARY as a faithful capture.

**`win` uses `fixed_frames` terminal:** True `game_won` requires clearing all 246 dots — impractical to script. Frozen as 3000-frame window. Permitted by plan's `fixed_frames` terminal taxonomy.

**Cloud-fn source modified (commit 38417e5):** `submit_score` gained MAX_SCORE cap and transactional upsert before tests were locked in. This is a coherence commit documented in 01-07 SUMMARY. Plan 06 tests the working-tree code as-is (D-16 honored). The tests now characterize the improved production code.

---

## Human Verification Required

None. All must-haves are verifiable programmatically and have been verified.

---

## Gaps Summary

No gaps. All 8 must-haves verified against the actual codebase:

1. 61 tests pass under the venv — confirmed by running the suite.
2. `tick()` extraction is correct — no throttle in tick, throttle retained in run, delegation confirmed.
3. Cardinal Rule upheld — `ghost.py` and `player.py` have zero diffs since baseline commit `a229153`.
4. 9 golden scenarios committed with both input.jsonl and trace.jsonl — all replay byte-identical.
5. Determinism guard exists and passes — 3 source files scanned, comment stripping and detection self-tested.
6. 15 ghost micro tests pin all 4 `move_*` methods plus `check_collisions` at decisive states — all pass.
7. Cloud-fn tests cover the full TST-03 contract — validator 400s, score range, upsert, mocked firebase — all pass.
8. CI green on ubuntu-latest run 27331943685; `main` branch protection requires `test` check confirmed via GitHub API.

The safety net is genuine, green, and continuously enforced.

---

_Verified: 2026-06-11T08:45:00Z_
_Verifier: Claude (gsd-verifier)_
