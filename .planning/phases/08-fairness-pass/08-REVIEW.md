---
phase: 08-fairness-pass
reviewed: 2026-06-30T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - game.py
  - player.py
  - settings.py
  - tests/test_fairness_unit.py
  - tests/test_player_micro.py
findings:
  critical: 0
  warning: 3
  info: 3
  total: 6
status: issues_found
---

# Phase 8: Code Review Report

**Reviewed:** 2026-06-30T00:00:00Z
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found

## Summary

Reviewed the Phase 8 fairness changes against diff base `3ad5305..HEAD`:

- **FAIR-01** — `Game._catches` (game.py:425-432): integer center-to-center squared-distance catch replacing the four `player_circle.colliderect(ghost.rect)` checks.
- **FAIR-02** — integer-rational chase-step accumulator (game.py:80-83, 147-149, 364-378) plus the `GHOST_CHASE_SPEED_NUM/DEN` constants.
- **FAIR-03** — widened cornering windows in `Player.check_position` (player.py:66-85) via `PLAYER_TURN_WINDOW_MARGIN`.
- Four tunables in settings.py:116-119.

**Determinism invariants hold:** no `float`, no new imports, no `random`/wall-clock tokens were introduced — the determinism guard (tests/test_determinism_guard.py) stays green, and all 7 new unit tests pass. The integer math in FAIR-01/02/03 is arithmetically sound.

However the central FAIR-02 deliverable is **inert as configured** and its surrounding documentation is **self-contradictory**, and FAIR-01 introduces a sub-frame sampling asymmetry that did not exist in the rect-collision path. No security defects, crashes, or data-loss risks were found.

## Warnings

### WR-01: FAIR-02 chase-step accumulator is a behavioral no-op as shipped

**File:** `settings.py:117-118`, `game.py:364-378`
**Issue:** The shipped constants are `GHOST_CHASE_SPEED_NUM = 40`, `GHOST_CHASE_SPEED_DEN = 20`. With `40 // 20 == 2` and a zero remainder, the accumulator yields a step of `2` on **every single frame** — it never produces a `1`. I confirmed this at runtime: 20 consecutive `update_ghost_speeds()` calls in the chase tier produce `[2,2,...,2]`, `distinct == {2}`. The documented goal of FAIR-02 — slowing the lethal chaser to an average ~1.85 px/frame "integer-rational step in {1, 2}" (game.py:80-82, 364-367) — is **not realized**. Chasing ghosts run at the original 2.0 px/frame, so the per-ghost `ghost_step_acc` state, its reset in `reset_after_death` (game.py:147-149), and the refinement loop (game.py:372-378) are dead complexity that changes nothing. The settings comment at line 117 ("FAIR-02 reset to original chase speed") suggests this may be intentional, but if so the entire accumulator machinery and its "averaging 1.85" docs should be removed rather than left misleading.

Worse, the unit test `test_chase_accumulator_averages_to_num_over_den_frames` passes **vacuously**: an all-`2` sequence satisfies both `all(s in (1,2))` and `sum == NUM` (40), so the test never exercises the `1`-step path it claims to verify and cannot detect a regression in the mixing logic.
**Fix:** Decide the intent. If ghosts should be slowed for fairness, set `GHOST_CHASE_SPEED_NUM` to a value not divisible by `DEN` (e.g. `37`, matching the docs) so the accumulator actually emits a `{1,2}` mix. If 2.0 px/frame is the intended final speed, delete the accumulator (`ghost_step_acc`, the reset, and the lines 372-378 loop) and the "1.85"/"averaging" comments, reverting to the plain `ghost_speeds` tiers. Either way, add a test case that pins a specific `{1,2}` step *sequence* (not just the sum) so the distribution is regression-protected.

### WR-02: Contradictory and stale tuning documentation for the FAIR-02 dial

**File:** `settings.py:117-118`, `game.py:81-82`, `tests/test_fairness_unit.py:20-21,113`
**Issue:** The numbers in the docs disagree with the shipped constant and with each other. settings.py:117 says `40/20 = 2.0 px/frame`, but the very next line (settings.py:118) says `37/20 = 1.85 px/frame avg` and `+1 to NUM is ~+0.05 px/frame` — describing a `NUM` of 37, not the actual 40. game.py:81-82 likewise advertises "averaging ... (1.85)". The test docstrings (test_fairness_unit.py:20, 113) describe the post-change value as "37 -> 1.85 px/frame avg" and "summing to ... (37 -> 1.85)". A maintainer tuning this "D-10 playtest dial" gets three mutually inconsistent reference points and cannot tell whether 40 or 37 is correct.
**Fix:** Pick the real value and make every comment agree. If 40/2.0 is intended, correct settings.py:118 and game.py:81-82 and the test docstrings to read `40/20 = 2.0`. If 37/1.85 is intended, change the constant (see WR-01) and fix the settings.py:117 line.

### WR-03: `_catches` compares post-move player center against stale pre-move ghost center

**File:** `game.py:430-431`
**Issue:** `_catches` reads `self.player.center_x/center_y` — live `@property` values (player.py:24-30) — but a ghost's `center_x/center_y` are plain attributes set **once** in `Ghost.__init__` (ghost.py:284-285) and **never recomputed** after `_move()` mutates `x_pos/y_pos`. In the frame order (`create_ghosts` at game.py:582 → `move_ghosts` at 609 → `check_ghost_collisions` at 612), `player.move()` has already run, so the player center is **post-move**, while the ghost center is **pre-move** (construction-time, equal to the drawn sprite position). The old `player_circle.colliderect(...)` path used `player_circle` captured at game.py:581 *before* `player.move()` — i.e. both sides were pre-move and consistent. FAIR-01 silently shifts only the player side to post-move, creating a half-frame asymmetry of up to `PLAYER_SPEED` (2 px): the catch is evaluated against a player position ~2 px ahead of where the player sprite is actually drawn this frame. The `_catches` comment claiming it reads centers that are "always current" is true only for the player half; the ghost half is explicitly stale. In a fairness pass this skew is undesirable because, when the player moves toward a ghost, it can register a catch a frame before the sprites visually touch.
**Fix:** Sample both sides at the same sub-frame moment. Simplest: move the `check_ghost_collisions` call (and `check_collisions`) to *before* `player.move()`/`move_ghosts()` so both player and ghost centers are pre-move (matching the drawn frame and the old behavior). Alternatively, recompute `ghost.center_x/center_y` after `_move()` (make them properties off `x_pos/y_pos`) and accept post-move sampling on both sides — but verify against the golden traces before re-blessing.

## Info

### IN-01: `player_circle` parameter to `check_ghost_collisions` is now dead

**File:** `game.py:434`, call site `game.py:612`
**Issue:** After FAIR-01 routed every collision check through `self._catches(...)`, the `player_circle` parameter is no longer read anywhere in `check_ghost_collisions`. The caller still computes it (game.py:581 via `self.player.draw(...)`, whose return is otherwise unused) and passes it in. This is dead plumbing that invites confusion about which position the catch actually uses.
**Fix:** Drop the `player_circle` parameter and the unused return value at the call site (keep the `self.player.draw(...)` call for its rendering side effect, just stop capturing/passing the Rect).

### IN-02: Test module docstrings describe an xfail/RED state that no longer exists

**File:** `tests/test_fairness_unit.py:5-8,77-79,109`, `tests/test_player_micro.py:13-19,109`
**Issue:** Both modules' docstrings state the tests are "RED today", "guarded with `@pytest.mark.xfail(strict=True)`", and that "Plan 08-02/08-03 removes each marker as its target behavior turns green." The markers have in fact been removed and all tests pass green (verified: `7 passed`). The prose now actively misdescribes the file — a future reader will look for xfail markers that aren't there and may assume the behavior is still unimplemented.
**Fix:** Update the docstrings to describe the tests as green characterization tests of the shipped behavior; remove the "RED today" / "xfail(strict)" / "Plan 08-0x removes the marker" language.

### IN-03: Accumulator test hardcodes the frame count and asserts a tautology

**File:** `tests/test_fairness_unit.py:125,130`
**Issue:** The loop `for _ in range(20)` hardcodes the literal `20` while the average is governed by `GHOST_CHASE_SPEED_DEN` (also 20); the test imports `GHOST_CHASE_SPEED_NUM` but not `DEN`, so if `DEN` is retuned the loop length silently desynchronizes from the period. Separately, `sum(steps) == NUM` is mathematically guaranteed for *any* `NUM` over exactly `DEN` frames (the accumulator remainder returns to 0), so the assertion proves nothing about the per-frame distribution — it holds equally for the degenerate all-`2` sequence (see WR-01).
**Fix:** Import `GHOST_CHASE_SPEED_DEN`, drive the loop with it, and assert the exact expected `{1,2}` step *sequence* (or at least `assert 1 in steps` when a sub-2 average is intended) so the test actually constrains the mixing behavior.

---

_Reviewed: 2026-06-30T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
