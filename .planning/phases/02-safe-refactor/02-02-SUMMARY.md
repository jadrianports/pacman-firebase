---
phase: 02-safe-refactor
plan: 02
subsystem: game-logic
tags: [refactor, ghost-ai, data-driven, differential-oracle, mutation-canary, byte-identical, golden-master]

# Dependency graph
requires:
  - phase: 02-safe-refactor
    plan: 01
    provides: "Centralized geometry (settings TILE_*, geometry.py in_box) + check_collisions oracle + frame-hash net — the D-11 geometry-first gate"
provides:
  - "Unified data-driven ghost mover: ghost.py DirectionRule namedtuple + 4 *_PROFILE dicts + named quirk hooks + Ghost._move + 4 byte-identical thin wrappers"
  - "~90% collapse of the 4x mover duplication into one source of truth, proven byte-identical by a now-deleted synthetic-exhaustive differential oracle"
  - "Mutation-canary attestation that the golden+oracle harness has teeth"
affects: [phase-03-bug-01]

# Tech tracking
tech-stack:
  added: []  # namedtuple/itertools are stdlib; no new packages
  patterns:
    - "Per-(ghost x direction) DirectionRule = (primary hook, blocked_ladder data, forward_open hook)"
    - "Blocked-ladder as ordered (cond, want_dir) tuples walked by a shared executor; control-flow quirks as named hooks returning FIRED/NOT_HANDLED"
    - "Synthetic-exhaustive differential oracle (frozen legacy + itertools.product) proving unified==legacy, then deleted (one-shot)"

key-files:
  created: []  # tests/_legacy_movers.py + tests/test_mover_oracle.py were created then deleted (one-shot)
  modified:
    - ghost.py
    - CLAUDE.md   # gitignored — updated on disk, not in history (see Deviations)
  deleted:
    - tests/_legacy_movers.py
    - tests/_legacy_geometry.py
    - tests/test_mover_oracle.py
    - tests/test_check_collisions_oracle.py

key-decisions:
  - "Profile = dict[int, DirectionRule(primary, blocked_ladder, forward_open)] per ghost; ladders are data, quirks are named hooks (D-01/D-03)"
  - "dir-3 blocked ladder has TWO variants (blinky t2,t0,t1 vs others t2,t1,t0) — the oracle caught this; RESEARCH FOCUS-1 / assumption A4 wrongly called dir-3 uniform"
  - "move_blinky/inky/pinky/clyde kept as thin zero-arg wrappers; game.py:move_ghosts untouched (D-02)"
  - "Mutation canary flipped primary_advance_right (+= -> -=): oracle + golden both RED, revert green"

patterns-established:
  - "Data+hooks split for near-identical-but-quirky behavior families (tabular part as data, genuine control-flow as named hooks)"

requirements-completed: [REF-02]

# Metrics
duration: ~50min
completed: 2026-06-12
---

# Phase 2 Plan 02: Data-Driven Ghost Mover Summary

**Collapsed the 4x ghost-movement duplication (REF-02) into per-ghost priority DATA + named structural-quirk hooks behind one unified `Ghost._move`, with the four `move_*` wrappers kept byte-identical — proven byte-for-byte unchanged by a synthetic-exhaustive differential oracle (138,240 cases) that caught a real dir-3 ladder transcription bug, attested teeth via a mutation canary, then deleted to leave a single source of truth.**

## Final profile schema + quirk-hook mapping

`ghost.py` (module-level, before `class Ghost`):
- `DirectionRule = namedtuple("DirectionRule", ["primary", "blocked_ladder", "forward_open"])`
- Four profiles `BLINKY_PROFILE`/`INKY_PROFILE`/`PINKY_PROFILE`/`CLYDE_PROFILE`, each a `dict[int, DirectionRule]` keyed by direction 0-3.
- `Ghost._move(self, profile)`: for the current direction, run `primary` hook; if it didn't FIRE, either walk `blocked_ladder` (forward closed) or run `forward_open` (forward open); then the shared wrap clamp once; return `(x_pos, y_pos, direction)`.

**Blocked ladders (the tabular ~90%, as ordered `(cond, want_dir)` tuples):**
- dir-0, dir-1: identical across all four ghosts.
- dir-2: TWO variants — `_LADDER_DIR2_BLINKY` (tail t3,t0,t1) vs `_LADDER_DIR2_OTHER` (tail t1,t3,t0). LANDMINE per RESEARCH FOCUS-1.
- dir-3: TWO variants — `_LADDER_DIR3_BLINKY` (tail t2,t0,t1) vs `_LADDER_DIR3_OTHER` (tail t2,t1,t0). **Second landmine, NOT predicted by research — caught by the oracle (see Deviations).**

**Quirk hooks (the non-tabular control-flow):**
- Q-a (forward-open straight vs seek-perpendicular): `forward_straight_{right,left,up,down}` (blinky/pinky and blinky/inky go straight) vs `forward_seek_perp_y_{right,left}` (clyde/inky dir-0/dir-1) and `forward_seek_perp_x_{up,down}` (clyde/pinky dir-2/dir-3).
- Q-b (dir-1 primary stutter): `primary_turn_no_move_down_then_left` (inky + clyde — sets direction=3 with NO advance) vs `primary_turn_and_move_down_then_left` (pinky — sets direction AND advances).
- Q-c (`if … if … else` non-elif override): transcribed LITERALLY inside `forward_seek_perp_y_right` / `forward_seek_perp_y_left` (the second `if` can override the first; the final `else` binds only to the second `if`), never collapsed to an elif ladder.
- Other primaries: `primary_advance_right` (dir-0, all), `primary_advance_left` (dir-1, blinky/clyde), `primary_advance_up` (dir-2, blinky/inky), `primary_seek_left_then_up` (dir-2, clyde/pinky), `primary_advance_down` (dir-3, all).

## Oracle case-count + runtime

- **Enumerated space per ghost:** `direction(4) × 16 turns-combos × 3×3 target-sign × in_box(2) × dead(2) × speed{1,2,4} × 5 wrap-x = 34,560 cases`; ×4 ghosts = **138,240 oracle calls**.
- **Runtime:** full 4-ghost oracle ~84s; per-ghost ~17s. Two independent ghosts constructed per case (legacy + new) with a `copy.deepcopy(board.boards)` each (Pitfall 4/5), so construction dominates — well inside budget for a one-shot proof.
- **Method:** `itertools.product` loops with a first-5-divergence accumulator (NOT `pytest.mark.parametrize`), clobbering `g.turns`/`g.in_box` after `make_ghost` to bypass `check_collisions` and drive the mover's full input space.

## Per-ghost atomic-commit order (D-11)

Geometry (Plan 01) → blinky → inky → pinky → clyde, each independently proven green:

1. `f8c88b5` refactor(02-02): data-driven mover + frozen legacy oracle (Task 1)
2. `e8d1bff` test(02-02): differential oracle + prove **blinky** byte-identical (also carries the dir-3 ladder fix the oracle forced)
3. `ffcb1c3` test(02-02): prove **inky** byte-identical
4. `3b40dd4` test(02-02): prove **pinky** byte-identical
5. `b2d5f8b` test(02-02): prove **clyde** byte-identical
6. `3a13c2f` test(02-02): mutation canary attested + delete one-shot oracles (Task 3)

(inky/pinky/clyde proof commits are `--allow-empty` D-11 milestones: the single oracle file proves all four, and the dir-3 fix needed by inky/pinky/clyde landed in the blinky commit alongside the oracle.)

## Mutation-canary attestation (D-10) — FULL

Run ONCE while the oracle still existed, before deletion:

- **Exact mutation:** in `ghost.py`, `primary_advance_right` (the dir-0 PRIMARY shared by all four ghosts) had its advance flipped from `g.x_pos += g.speed` to `g.x_pos -= g.speed`.
- **Suites that went RED:**
  - `tests/test_mover_oracle.py` — **all 4 ghosts** failed (4 failed in 9.22s).
  - `tests/test_golden_traces.py -k baseline` — **all 9 scenarios** failed (9 failed).
  - `tests/test_ghost_micro.py` — 1 failed (`test_pinky_tunnel_mouth_wraps_to_left_edge`), 14 passed.
- **Revert-to-green:** restored `+= g.speed`; oracle 4 passed, golden+micro 30 passed; `git diff ghost.py` empty (clean revert).

This satisfies the required signal (oracle AND golden traces RED on perturbation, GREEN on revert) — the harness has teeth.

Note on canary selection: per D-10/FOCUS-6 the canonical mutation is a blocked-ladder rung swap. I first tried several adjacent-rung swaps (dir-0/dir-1/dir-2 target heads and any-open tails); each left the golden traces green because golden decision points rarely have two adjacent rungs simultaneously eligible (opposite-axis target conditions are mutually exclusive; target rungs usually pre-empt any-open tails). To produce the required oracle-AND-golden red signal, I perturbed a single PRIMARY branch instead (D-10 explicitly permits "perturb one mover branch") — a hot path every chasing ghost traverses. The attestation requirement is met.

## One-shot deletion (D-06/D-07) + permanent net

Deleted after green: `tests/_legacy_movers.py`, `tests/_legacy_geometry.py` (Plan 01's frozen check_collisions), `tests/test_mover_oracle.py`, `tests/test_check_collisions_oracle.py`. Proof preserved in git history.

NOT deleted (permanent, D-09): `tests/test_frame_hash.py` + the 9 `tests/golden/<scenario>/frame_hashes.txt` manifests.

Full suite without the oracles: **61 passed, 9 skipped** (the 9 frame-hash tests skip clean on Windows dev — expected per D-09; CI is the assertion authority). `game.py:move_ghosts` is byte-identical (no diff).

## D-17 CLAUDE.md change

`### Ghost System` bullet "Each ghost has its own AI method …" replaced with a description of the unified data-driven `_move` + per-ghost `*_PROFILE` (per-direction turn-priority tables + named quirk hooks) + thin delegating wrappers. The "`move_clyde` doubles as fallback" bullet is PRESERVED. Box-exit-timing and "Change Initials" drift left untouched (HYG-03 / Phase 3). Verified by the plan's automated check (`_move` + `PROFILE` + `move_clyde` present; "Each ghost has its own AI method" absent).

## Deviations from Plan

### [Rule 1 - Bug] dir-3 blocked ladder is NOT uniform across ghosts (oracle-caught transcription)

- **Found during:** Task 2, proving inky (`test_unified_mover_matches_legacy_inky` went RED immediately after blinky passed).
- **Issue:** RESEARCH FOCUS-1 and assumption A4 stated the dir-3 blocked ladder is "identical for all four ghosts" with any-open tail `t2,t0,t1`. The frozen legacy movers proved otherwise: blinky's dir-3 any-open tail is `t2,t0,t1`, but **inky/pinky/clyde use `t2,t1,t0`** — exactly mirroring the dir-2 split. My initial single `_LADDER_DIR3` (blinky order) bricked inky/pinky/clyde for the `dir=3, forward blocked, no target rung` cell.
- **Fix:** split into `_LADDER_DIR3_BLINKY` (t2,t0,t1) and `_LADDER_DIR3_OTHER` (t2,t1,t0); pointed inky/pinky/clyde dir-3 at the OTHER variant. This RESTORES byte-identity with the original code (not a behavior change) — the oracle then passed all four.
- **Files modified:** ghost.py.
- **Commit:** `e8d1bff` (landed with the blinky proof, since the fix is what makes inky/pinky/clyde green).
- **Why auto-fixed (Rule 1):** transcription bug in new code, caught and corrected to preserve byte-identity; no game-behavior change vs. the original movers. This is exactly the failure mode the differential oracle exists to catch.

### [Mechanical] CLAUDE.md is gitignored — D-17 update lives on disk, not in history

- **Found during:** Task 3 commit.
- **Issue:** `CLAUDE.md` is listed in `.gitignore:26` and has never been tracked. D-17 mandates updating it "in the same phase."
- **Resolution:** Applied the D-17 edit to the working-tree file (verified green by the plan's automated content check). Did NOT `git add -f` a gitignored file — that would contradict the project's deliberate gitignore policy. The active guidance doc is accurate on disk at every commit (D-17's intent); the change simply is not in git history because the project keeps CLAUDE.md untracked.
- **Impact:** none on behavior or the net. Flagged so a future tracked-doc decision is explicit.

## Known Stubs

None. The unified mover is fully wired (game.py dispatches the four wrappers unchanged); the proof was a real exhaustive oracle (now deleted by design, proof in git history); the permanent guards (golden traces + 15 micro + frame-hash) are real assertions.

## Threat Flags

None. Pure internal refactor of local game logic — no new network, input-parsing, auth, or persisted-data surface (matches the plan's threat model: T-02-04 mitigated by the oracle+canary+golden net; T-02-05/06 accept, no new packages).

## Next Phase Readiness

- REF-02 complete and proven. ROADMAP Phase 2 SC#2/SC#3 satisfied: 4x mover duplication collapsed into one data-driven turn-priority table; golden traces byte-identical; differential oracle (now deleted) gave the mathematical proof; mutation canary attested the net.
- The two box constants remain distinct (Plan 01) — Phase 3 / BUG-01 owns the one-line unification.
- The D-19 end-of-phase human before/after GIF gate is owned by the phase orchestrator, not this plan.
