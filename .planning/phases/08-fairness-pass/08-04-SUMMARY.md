---
phase: 08-fairness-pass
plan: 04
subsystem: testing
tags: [golden-master, frame-hash, docker, pygame, re-bless, determinism]

# Dependency graph
requires:
  - phase: 08-02
    provides: FAIR-01 center-distance catch + FAIR-02 integer-rational chase-step accumulator (game.py)
  - phase: 08-03
    provides: FAIR-03 pre-turn cornering window (player.py)
  - phase: 08-01
    provides: settings.py FAIR tunables + failing micro-test net
provides:
  - Single deliberate Linux/Docker golden-net re-bless covering FAIR-01+FAIR-02+FAIR-03 under the D-10-signed-off constants
  - 9 re-blessed frame_hashes.txt + 8 re-blessed trace.jsonl (box_exit integer state unchanged)
  - Empirical proof the death/ghost_eat terminals still fire (no input re-authoring needed)
  - Byte-identical ghost-decision-logic proof (ghost.py zero diff; micro + determinism green without re-bless)
affects: [09-arcade-juice, golden-net, ci]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "One deliberate re-bless per batched behavior change, in the Linux pinned env (python:3.12 Docker, effective pygame 2.6.1, SDL_*=dummy) -- never on Windows, never per-change (D-10 / Phase-3 box-fix pattern)"
    - "Verify the re-blessed frame-hash manifests by re-running the non-bless suite WITH GSD_FRAME_HASH_ENV=1 in the SAME container so frame-hash assertions actually execute"

key-files:
  created:
    - .planning/phases/08-fairness-pass/08-04-SUMMARY.md
  modified:
    - tests/golden/death/trace.jsonl
    - tests/golden/ghost_eat/trace.jsonl
    - tests/golden/win/trace.jsonl
    - tests/golden/box_edge/trace.jsonl
    - tests/golden/tunnel_wrap/trace.jsonl
    - tests/golden/eyes_return/trace.jsonl
    - tests/golden/power_chase/trace.jsonl
    - tests/golden/claude_session_01/trace.jsonl
    - tests/golden/*/frame_hashes.txt (all 9)

key-decisions:
  - "Mirrored CI's exact install (requirements.txt then requirements-dev.txt) rather than the plan's illustrative bare `pygame==2.6.1 pytest`, so the re-bless reflects the same effective env (pygame 2.6.1, installed last) that CI uses to assert -- and so the full suite can import its deps"
  - "Verified the freshly-blessed frame_hashes by re-running the suite with GSD_FRAME_HASH_ENV=1 (frame-hash assertions ON) inside the same container, not just a bare non-pinned run"
  - "No death/ghost_eat input.jsonl re-authoring: both terminals still fired under the dialed constants (catch radius UP to 24, chase = player speed), so Pitfall 2 did not trigger"

patterns-established:
  - "Single Linux/Docker re-bless covering all batched FAIR-* changes together; ghost.py held byte-identical as the decision-logic spec"

requirements-completed: [FAIR-01, FAIR-02, FAIR-03]

# Metrics
duration: 26min
completed: 2026-06-30
---

# Phase 8 Plan 04: Playtest Sign-off + Terminal Verify + Single Linux/Docker Re-bless Summary

**One deliberate Linux/Docker (`python:3.12`, effective pygame 2.6.1) golden-net re-bless of all 9 traces + frame-hash manifests under the D-10-signed-off fairness constants (24 / 40 / 20 / 6), with the death/ghost_eat terminals empirically re-verified and ghost.py held byte-identical.**

## Performance

- **Duration:** ~26 min (continuation; Task 1 D-10 checkpoint completed in a prior session)
- **Completed:** 2026-06-30
- **Tasks:** 3 (Task 1 sign-off pre-completed; Tasks 2-3 executed here)
- **Files modified:** 17 fixtures (9 frame_hashes.txt + 8 trace.jsonl) + docs

## Accomplishments
- Ran the SINGLE deliberate golden-net re-bless in a Linux `python:3.12` Docker container (effective `pygame 2.6.1`, SDL 2.28.4, `SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy`), covering FAIR-01 + FAIR-02 + FAIR-03 together -- never on Windows, never per-change (D-10).
- Regenerated all 9 `frame_hashes.txt` and 8 `trace.jsonl` (box_exit's integer state was unaffected by the constants; its frame-hash was still re-blessed) under the signed-off constants `GHOST_CATCH_DISTANCE=24`, `GHOST_CHASE_SPEED_NUM=40`, `GHOST_CHASE_SPEED_DEN=20`, `PLAYER_TURN_WINDOW_MARGIN=6`.
- Empirically verified Pitfall 2: the `death` scenario still reaches `game_over` and `ghost_eat` still registers its eat -- `assert_invariants` passed for both, so NO `input.jsonl` re-authoring was needed.
- Confirmed the fairness golden net is fully green in the pinned env: an isolated container run of `test_golden_traces.py` + `test_frame_hash.py` (asserting, `GSD_FRAME_HASH_ENV=1`) + `test_ghost_micro.py` + `test_determinism_guard.py` = **44 passed**.
- Proved the byte-identical guard WITHOUT re-bless on Windows: `.venv` ghost micro + determinism guard = **20 passed**; `ghost.py` shows ZERO diff across the entire phase.
- No float leaked into any trace (`grep -rlE '[0-9]+\.[0-9]+' tests/golden/*/trace.jsonl` -> CLEAN); positions stayed integer.

## Task Commits

1. **Task 1: D-10 Windows playtest + dial + sign-off** - `df1d084` (feat, prior session) -- dialed FAIR tunables to the signed-off 24/40/20/6.
2. **Task 2 + Task 3: Single Linux/Docker re-bless of all 9 golden fixtures** - `093b3da` (test) -- the one deliberate re-bless (17 fixtures), documenting message cites the env + dialed constants.

**Plan metadata:** (final docs commit -- SUMMARY + deferred-items + STATE + ROADMAP + REQUIREMENTS)

## Files Created/Modified
- `tests/golden/{death,ghost_eat,win,box_edge,tunnel_wrap,eyes_return,power_chase,claude_session_01}/trace.jsonl` - re-blessed integer state traces under the new constants
- `tests/golden/*/frame_hashes.txt` (all 9) - re-blessed Linux-pinned pixel-hash manifests
- `.planning/phases/08-fairness-pass/deferred-items.md` - marked the re-bless item RESOLVED; logged the out-of-scope `pygame`/`pygame-ce` `gaussian_blur` packaging conflict

## Decisions Made
- **Install env:** mirrored CI's exact two-file install (`requirements.txt` then `requirements-dev.txt`) instead of the plan's illustrative bare `pip install pygame==2.6.1 pytest`. CI is the frame-hash assertion authority; its effective `import pygame` resolves to `pygame 2.6.1` (requirements-dev installed last), and the bare command would also have left the full suite unable to import `firebase-admin`/`Pillow`. This makes the blessed frame hashes match what CI will assert.
- **Verification rigor:** re-ran the non-bless suite with `GSD_FRAME_HASH_ENV=1` in the same container so the frame-hash tests *assert* against the just-written manifests (they self-skip on non-pinned envs) -- a stronger check than the plan's reference verify command.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Used CI-exact dependency install instead of the plan's illustrative bare command**
- **Found during:** Task 2 (re-bless container setup)
- **Issue:** The plan's reference `pip install -q pygame==2.6.1 pytest` (a) would leave the full suite unable to import `firebase-admin`/`Pillow` (collection errors in cloud-function + capture tests), and (b) is not the env CI uses to assert the frame-hash manifests. Blessing under a different env than CI risks committing frame hashes CI would then reject.
- **Fix:** Installed `requirements.txt` then `requirements-dev.txt` exactly as `.github/workflows/ci.yml` does (effective `pygame 2.6.1`, SDL 2.28.4), so the bless reflects CI's assertion env and all deps are present.
- **Files modified:** none (env-only; no committed file change)
- **Verification:** Isolated container golden-net run = 44 passed (frame-hash asserting); float check CLEAN.
- **Committed in:** n/a (environment choice)

---

**Total deviations:** 1 auto-fixed (1 blocking/env). No fixture or source content beyond the planned re-bless was changed.
**Impact on plan:** Strengthens correctness (bless env == CI assertion env). No scope creep.

## Issues Encountered

- **Out-of-scope, pre-existing: `pygame` vs `pygame-ce` `gaussian_blur` packaging conflict.** The full in-container `pytest -q` showed **12 failures** (`tests/test_juice.py`, `tests/test_juice_firewall.py`, `tests/test_menu_render.py`, `tests/test_theme.py`) all raising `AttributeError: module 'pygame.transform' has no attribute 'gaussian_blur'` at `theme.py:45`. Root cause: `requirements.txt` pins `pygame-ce==2.5.7` (which *has* `gaussian_blur`) but `requirements-dev.txt` pins `pygame==2.6.1` (upstream pygame, which does NOT) -- and the latter is installed last, so the `pygame` namespace lacks the pygame-ce-only `gaussian_blur` used by the UI-redesign/Phase-9 juice code. This is independent of the fairness constants and the golden fixtures, reproduces with or without this re-bless, and is **not** part of the Phase-8 golden net (9 traces + 15 micro + frame-hash + determinism guard), which is fully green. Per the executor scope boundary it was logged to `deferred-items.md`, not fixed here. Operator action: reconcile the pygame distribution across the two requirements files (and re-verify frame hashes after any pygame-distribution change -- Pitfall 3).

## Threat Flags

None -- offline single-player fixture re-bless; no new network/auth/file/schema surface (matches the plan threat model, all `accept`/`mitigate` dispositions satisfied: T-08-03 mitigated by the Linux-only single bless; T-08-02 by the green determinism guard + integer-only traces).

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Phase 8 (Fairness Pass) is COMPLETE: the player can escape (corner-kiss safe, ghosts at player speed, snappy cornering), with ghost decision logic byte-identical and the golden net re-blessed once on Linux/Docker.
- Phase 9 (Arcade Juice) is unblocked. Standing constraint reminder (STATE.md): FEEL-* effects must ride the existing `Game.juice` firewall (default `False`) so golden/frame-hash replays stay unchanged and need NO re-bless.
- **Operator flag (out-of-scope of this phase):** reconcile the `pygame`/`pygame-ce` requirements pin before relying on a fully-green `pytest -q` in CI -- the 12 `gaussian_blur` UI/juice failures are a packaging conflict, not a fairness regression (see deferred-items.md).

---
*Phase: 08-fairness-pass*
*Completed: 2026-06-30*

## Self-Check: PASSED

- All re-blessed fixtures present (death/ghost_eat trace + frame_hashes verified).
- Commits df1d084 (Task 1 dial) and 093b3da (single re-bless) exist in history.
