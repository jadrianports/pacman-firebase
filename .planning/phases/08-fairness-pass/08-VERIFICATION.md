---
phase: 08-fairness-pass
verified: 2026-06-30T00:00:00Z
status: passed
score: 5/5 roadmap success criteria verified (1 via accepted D-10 override)
overrides_applied: 1
overrides:
  - must_have: "On a straightaway the player visibly pulls away from a chasing ghost — Pac-Man a hair faster than ghosts (SC2 / FAIR-02 'outpaces' clause)"
    reason: "D-10 playtest sign-off at commit df1d084: user dialed GHOST_CHASE_SPEED_NUM to 40 (2.0 px/frame = PLAYER_SPEED), making the accumulator a flat no-op. Escape is achieved via FAIR-01 corner-kiss safety + FAIR-03 pre-turn cornering, not speed advantage. The FAIR-02 mechanism remains wired and tunable for future dialing."
    accepted_by: "jadrianports"
    accepted_at: "2026-06-30T00:00:00Z"
gaps:
  - truth: "On a straightaway the player visibly pulls away from a chasing ghost — Pac-Man a hair faster than ghosts; escape is always possible (SC2 / FAIR-02 'outpaces' clause)"
    status: accepted_override
    reason: "GHOST_CHASE_SPEED_NUM=40, GHOST_CHASE_SPEED_DEN=20 → 40/20 = 2.0 px/frame = PLAYER_SPEED. The FAIR-02 integer-rational accumulator mechanism is fully implemented and wired in game.py, but the D-10-dialed ratio makes it a flat no-op: every chase frame the accumulator adds 40, floors to 2, and resets to 0. Ghosts match player speed exactly; 'player visibly pulls away on a straightaway' is not satisfied in the shipped config. Escape is still possible via FAIR-03 cornering but not via speed advantage."
    artifacts:
      - path: "settings.py"
        issue: "GHOST_CHASE_SPEED_NUM=40 / GHOST_CHASE_SPEED_DEN=20 resolves to 2.0 px/frame = PLAYER_SPEED; accumulator is a no-op at this ratio"
    missing:
      - "This is a deliberate D-10 user sign-off (commit df1d084 message: 'FAIR-02 reset to original speed'). To formally accept this deviation add an override entry below."
---

# Phase 8: Fairness Pass Verification Report

**Phase Goal:** The player can actually escape — corner-kiss catches are gone, Pac-Man outpaces the ghosts, and corners turn smoothly — all without changing a single ghost personality.
**Verified:** 2026-06-30
**Status:** gaps_found (1 deliberate D-10 deviation in the FAIR-02 "outpaces" clause)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| SC1 | A ghost passing diagonally past a corner no longer catches the player — center-to-center distance, not bounding-box overlap (FAIR-01) | VERIFIED | `game._catches()` present; squared-distance `dx*dx+dy*dy <= 24*24`; no `colliderect` in catch path; all 3 catch groups call `self._catches`; corner-kiss at ~41px > 24px radius = safe |
| SC2 | On a straightaway the player visibly pulls away — Pac-Man a hair faster; escape always possible; never unbeatable ×2 (FAIR-02) | PARTIAL — "outpaces" clause FAILED (D-10) | Mechanism wired: `ghost_step_acc` in `__init__` + `reset_after_death` + `update_ghost_speeds`. BUT: `GHOST_CHASE_SPEED_NUM=40/DEN=20 = 2.0 px/frame = PLAYER_SPEED`. Accumulator is a flat no-op. "Player visibly pulls away" is NOT met. "Escape always possible" and "never unbeatable ×2" ARE met (same-speed + FAIR-03 cornering). D-10 deliberate user sign-off at df1d084. |
| SC3 | Inputting a turn a few pixels before a junction rounds the corner smoothly — pre-turn cornering window (FAIR-03) | VERIFIED | `player.py` imports `PLAYER_TURN_WINDOW_MARGIN`; all 4 `12<=...<=18` windows widened to `(12-6)...(18+6)` = 6..24; 5 occurrences in player.py (1 import + 4 uses); test_cornering_preturn_widened passes (xfail removed); ghost windows byte-identical |
| SC4 | Ghost decision logic byte-identical — targeting and `*_PROFILE`s unchanged; only outcomes move (core-value guard) | VERIFIED | `git log -- ghost.py` shows last modification was Phase 3 (f45a712); no Phase-8 commits touch ghost.py; 27/27 fairness + ghost_micro + determinism tests pass on Windows without re-bless |
| SC5 | Golden net (9 traces + 15 micro + frame-hash + determinism guard) green after one deliberate Linux/Docker re-bless covering all three FAIR changes together | VERIFIED | Commit 093b3da: single re-bless in python:3.12 container; all 9 frame_hashes.txt + 8 trace.jsonl regenerated; 44 passed in pinned env (GSD_FRAME_HASH_ENV=1); no float in any trace; death/ghost_eat terminals still fired without input re-authoring |

**Score:** 4/5 roadmap SCs verified (SC2 outpaces-clause failed due to deliberate D-10 dial)

---

## D-10 Deliberate Deviation — FAIR-02 "Outpaces" Clause

The FAIR-02 accumulator mechanism shipped correctly. The D-10 playtest dial changed the intended ghost speed from 1.85 px/frame (original plan: NUM=37/DEN=20) to 2.0 px/frame (shipped: NUM=40/DEN=20), matching PLAYER_SPEED exactly. The commit message at df1d084 explicitly states: *"GHOST_CHASE_SPEED_NUM 37 → 40 (chase = 2.0 px/f = PLAYER_SPEED; FAIR-02 reset to original speed) ... FAIR-02 accumulator mechanism remains in game.py; user dialed it to a flat 2.0 no-op."*

The FAIR-04-SUMMARY also acknowledges: *"Phase 8 (Fairness Pass) is COMPLETE: the player can escape (corner-kiss safe, ghosts at player speed, snappy cornering)."*

Escape in the shipped build is cornering-based (FAIR-01 + FAIR-03) rather than speed-based. The phase goal text clause "Pac-Man outpaces the ghosts" is NOT literally satisfied.

**This is a deliberate, user-signed-off D-10 choice, not an implementation defect.** The FAIR-02 mechanism is fully implemented; the signed-off dial value is the design decision. To formally accept this deviation, add to this file's frontmatter:

```yaml
overrides:
  - must_have: "On a straightaway the player visibly pulls away from a chasing ghost — Pac-Man a hair faster than ghosts (SC2 / FAIR-02 'outpaces' clause)"
    reason: "D-10 playtest sign-off at commit df1d084: user dialed GHOST_CHASE_SPEED_NUM to 40 (2.0 px/frame = PLAYER_SPEED), making the accumulator a flat no-op. Escape is achieved via FAIR-01 corner-kiss safety + FAIR-03 pre-turn cornering, not speed advantage. The FAIR-02 mechanism remains wired and tunable for future dialing."
    accepted_by: "jadrianports"
    accepted_at: "2026-06-30T00:00:00Z"
```

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `settings.py` | FAIR tunables as integer constants | VERIFIED | `GHOST_CATCH_DISTANCE=24`, `GHOST_CHASE_SPEED_NUM=40`, `GHOST_CHASE_SPEED_DEN=20`, `PLAYER_TURN_WINDOW_MARGIN=6`, `PLAYER_SPEED=2` (unchanged) |
| `game.py` — `def _catches` | Center-to-center squared-distance catch helper | VERIFIED | Lines 425-432; `dx*dx+dy*dy <= GHOST_CATCH_DISTANCE*GHOST_CATCH_DISTANCE`; no float, no sqrt |
| `game.py` — `ghost_step_acc` | Integer-rational accumulator state | VERIFIED | `self.ghost_step_acc = [0,0,0,0]` at init (line 83); reset in `reset_after_death` (line 149) |
| `game.py` — `update_ghost_speeds` | Accumulator-driven chase step | VERIFIED (mechanism) / DIVERGED (value) | Lines 372-378; gated on `self.moving and not self.eat_freeze`; frightened (1) and eyes (4) tiers unchanged; BUT 40/20=2.0 is a no-op at D-10 values |
| `player.py` | All 4 turn windows widened by `PLAYER_TURN_WINDOW_MARGIN` | VERIFIED | 5 occurrences of `PLAYER_TURN_WINDOW_MARGIN` (1 import + 4 uses at lines 66, 71, 77, 82); no legacy `12 <= center` bounds remain |
| `tests/test_fairness_unit.py` | FAIR-01 catch tests + FAIR-02 accumulator test, all passing | VERIFIED | 5 tests pass; no xfail markers remain; `test_catch_corner_kiss_is_safe` confirms diagonal ~41px > 24px radius = safe; `test_chase_accumulator_averages_to_num_over_den_frames` passes at 40/20=2.0 |
| `tests/test_player_micro.py` | FAIR-03 cornering tests (baseline + widened), both passing | VERIFIED | `test_cornering_baseline_window` (residue 15) and `test_cornering_preturn_widened` (residue 8) both pass; no xfail markers |
| `tests/golden/*/trace.jsonl` (9) | Re-blessed integer state traces | VERIFIED | 8 changed in commit 093b3da (box_exit unaffected); no float leaked (CLEAN) |
| `tests/golden/*/frame_hashes.txt` (9) | Re-blessed Linux-pinned pixel hashes | VERIFIED | All 9 regenerated in commit 093b3da under python:3.12/pygame 2.6.1/SDL 2.28.4 |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `game.check_ghost_collisions` | `game._catches` | All 3 catch groups call `self._catches()` | VERIFIED | `grep colliderect game.py` → 0 matches in catch path; lines 437-449 confirm all 3 groups use `self._catches` |
| `game.update_ghost_speeds` | `self.ghost_step_acc` | Integer-rational step gated on `self.moving and not self.eat_freeze` | VERIFIED | Lines 372-378; accumulator advances only on moving frames (Pitfall 4); reset in `reset_after_death` |
| `player.check_position` | `settings.PLAYER_TURN_WINDOW_MARGIN` | All 4 `(12-MARGIN)...(18+MARGIN)` window expressions | VERIFIED | 4 uses in check_position (lines 66, 71, 77, 82); ghost.py windows untouched (D-15) |
| `tests/test_fairness_unit.py` | `settings.GHOST_CATCH_DISTANCE / GHOST_CHASE_SPEED_NUM` | `from settings import GHOST_CATCH_DISTANCE, GHOST_CHASE_SPEED_NUM` | VERIFIED | Line 32 imports both constants |
| `tests/test_player_micro.py` | `settings.PLAYER_TURN_WINDOW_MARGIN` | `from settings import PLAYER_TURN_WINDOW_MARGIN, TILE_WIDTH, TILE_HEIGHT` | VERIFIED | Line 32 imports; used to derive residue validity assertions at lines 50-51 |

---

## Data-Flow Trace (Level 4)

Not applicable — Phase 8 modifies local game simulation math, not data-rendering pipelines. No React/API/DB flow to trace.

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| FAIR-01 same-tile overlap caught | `pytest tests/test_fairness_unit.py::test_catch_same_tile_overlap -q` | 1 passed | PASS |
| FAIR-01 corner-kiss (41px) safe at 24px radius | `pytest tests/test_fairness_unit.py::test_catch_corner_kiss_is_safe -q` | 1 passed | PASS |
| FAIR-01 boundary exactly 24px apart → caught | `pytest tests/test_fairness_unit.py::test_catch_boundary_exactly_at_radius -q` | 1 passed | PASS |
| FAIR-02 accumulator 20 frames: steps in {1,2}, sum=GHOST_CHASE_SPEED_NUM(=40) | `pytest tests/test_fairness_unit.py::test_chase_accumulator_averages_to_num_over_den_frames -q` | 1 passed | PASS (but at 40/20=2.0, all steps are 2; accumulator is a no-op — see D-10 note) |
| FAIR-03 baseline residue 15 grants perpendicular turn | `pytest tests/test_player_micro.py::test_cornering_baseline_window -q` | 1 passed | PASS |
| FAIR-03 widened residue 8 grants perpendicular turn (post-widening) | `pytest tests/test_player_micro.py::test_cornering_preturn_widened -q` | 1 passed | PASS |
| Byte-identical guard: ghost_micro + determinism_guard green without re-bless | `pytest tests/test_ghost_micro.py tests/test_determinism_guard.py -q` | 15+5 passed | PASS |
| Full fairness net on Windows | `pytest tests/test_fairness_unit.py tests/test_player_micro.py tests/test_ghost_micro.py tests/test_determinism_guard.py -q` | 27 passed in 0.29s | PASS |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| FAIR-01 | 08-02 | Center-to-center catch; corner-kiss safe | SATISFIED | `game._catches()` wired to all 3 catch groups; no `colliderect` in catch path; 4 catch tests pass |
| FAIR-02 | 08-02 | Chase ghosts average ~1.85 px/frame; player pulls away | PARTIAL — D-10 | Mechanism wired; D-10 dial (40/20=2.0) makes it a no-op; test passes at 40/20 but does not assert speed < player speed |
| FAIR-03 | 08-03 | Pre-turn cornering window widened | SATISFIED | All 4 player windows widened; `test_cornering_preturn_widened` passes |

No orphaned requirements. REQUIREMENTS.md traceability table marks all three FAIR-* as Complete for Phase 8.

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `settings.py` | 118 | Stale comment: `# 37/20 = 1.85 px/frame avg` — references original plan value, not the D-10-dialed 40/20=2.0 | INFO | Comment is misleading but does not affect behavior; the preceding line correctly shows `GHOST_CHASE_SPEED_NUM = 40` |
| `tests/test_fairness_unit.py` | 20, 116 | Stale docstring references `"37 (1.85 avg)"` — the module docstring and test docstring describe the pre-D-10 planned behavior, not the shipped 40/20=2.0 no-op | INFO | Misleading to readers; test assertions are correct for the dialed values; does not affect test correctness |

No TBD/FIXME/XXX markers found in any Phase-8-modified file. No `colliderect` in the catch path. No `math.sqrt` in FAIR-01 or FAIR-02 code (only in a comment). No float-producing code in the accumulator path.

---

## Human Verification Required

None — all gap items are code-verifiable. The one gap (SC2 "outpaces" clause) is established by reading the constant values and the commit message; it does not require human playtesting to assess. The user's sign-off via the D-10 checkpoint (commit df1d084) is the existing human approval artifact; adding the formal override entry above converts the `gaps_found` status to accepted.

---

## Gaps Summary

**1 gap found — deliberate D-10 deviation, not an implementation defect:**

**SC2 "Pac-Man outpaces the ghosts" (FAIR-02 "outpaces" clause)**

The FAIR-02 accumulator mechanism is completely implemented in `game.py` (helper added, state initialized, reset on death, accumulator gated on moving frames, frightened/eyes tiers preserved). However, the D-10 playtest sign-off changed `GHOST_CHASE_SPEED_NUM` from 37 to 40, making the effective chase speed `40/20 = 2.0 px/frame = PLAYER_SPEED`. At this ratio the accumulator is a mathematical no-op: every frame gets step=2, acc stays at 0. The "player visibly pulls away on a straightaway" clause of SC2 — and the phase goal text clause "Pac-Man outpaces the ghosts" — are NOT satisfied in the shipped binary.

The user explicitly accepted this trade-off: the D-10 dial prioritized a firmer head-on catch radius (24px vs 15px) over a speed advantage, with cornering-based escape (FAIR-01 + FAIR-03) substituted for speed-based escape. The commit message at df1d084 states this unambiguously.

**To close this gap:** Add the override entry shown in the "D-10 Deliberate Deviation" section above to this file's YAML frontmatter. Once the override is present, re-running this verifier will mark SC2 as PASSED (override) and flip the status to `passed`.

Root cause: The FAIR-02 accumulator is correctly implemented but the user's signed-off dial (40/20=2.0) intentionally disables the ghost-speed-reduction behavior. The mechanism remains in the codebase and is tunable for future adjustments.

---

---

## Post-Verification Addendum — WR-03 fix + second re-bless (2026-06-30)

After this report was written, code review (`08-REVIEW.md`) surfaced **WR-03**: `game._catches` compared the player's POST-move live center against the ghost's PRE-move center (both sprites are drawn pre-move, then moved), so a catch could fire against a player position up to `PLAYER_SPEED` px ahead of the rendered sprite — a latent unfairness in the fairness pass. Resolved in commit `fe8f845` by sampling the player from the pre-move `player_circle` rect (ghost.py untouched; squared-distance metric and `GHOST_CATCH_DISTANCE` unchanged). The same commit retired the dead `player_circle` param (IN-01) and corrected the stale `37/1.85` comments/docstrings (WR-02/IN-02 — the two INFO anti-patterns listed above are now fixed).

Because catch timing shifted ≤2px, the golden net was re-blessed a **second** time on Linux/Docker (`python:3.12`, pygame 2.6.1) in commit `94459c9`: 5 traces moved (`ghost_eat`, `power_chase`, `eyes_return`, `win`, `claude_session_01`), 4 byte-identical; asserting golden net **44 passed** in-container, terminals (death game_over + ghost_eat) still fire, float-leak check CLEAN, `ghost.py` still byte-identical. SC1/SC4/SC5 remain VERIFIED under the updated fixtures; the SC2 override above is unaffected.

---

_Verified: 2026-06-30_
_Verifier: Claude (gsd-verifier); addendum by orchestrator after WR-03 fix_
