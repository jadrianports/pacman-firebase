---
phase: 02-safe-refactor
reviewed: 2026-06-12T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - game.py
  - geometry.py
  - ghost.py
  - player.py
  - settings.py
  - tests/test_frame_hash.py
findings:
  critical: 0
  warning: 1
  info: 3
  total: 4
status: issues_found
---

# Phase 2: Code Review Report

**Reviewed:** 2026-06-12
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Phase 2 is a deliberately behavior-preserving refactor: (REF-01) centralizing tile/box
geometry into `settings.py` + `geometry.py`, and (REF-02) collapsing the four near-identical
ghost movers into a data-driven `Ghost._move` + per-ghost `*_PROFILE` tables + named quirk
hooks. I reviewed every changed file against the pre-refactor source at `f868d5f` line-by-line,
with primary attention on the two highest-risk vectors flagged in the review brief:
divergence between the data-driven mover and the original per-ghost control flow, and
non-byte-identical magic-number substitution.

**Bottom line: the behavioral refactor is faithful.** I traced all four ghosts across all four
directions and all three branch classes (PRIMARY / BLOCKED-ladder / FORWARD-OPEN) against the
original `move_blinky/inky/pinky/clyde`, and every constant substitution in `check_collisions`
(ghost) and `check_position` (player) against the original `num1/num2/num3`. I found **no
correctness regression and no BLOCKER**. The findings below are quality/robustness issues,
the most material being dead public API in `geometry.py`.

### Verified faithful (no defect) — high-risk areas that passed scrutiny

These are recorded because the brief asked to specifically rule them out; each was checked and
is correct, not merely assumed:

- **Constant mapping is byte-identical.** Original `num1=(HEIGHT-50)//32=28` maps to
  `TILE_HEIGHT` (28, the row/y divisor); `num2=WIDTH//30=30` to `TILE_WIDTH` (30, the col/x
  divisor); `num3=15` to `HALF_TILE`. No transposition. The asymmetric band offsets in
  `player.check_position` are preserved exactly: the dir-2/3 horizontal probes use a
  `TILE_WIDTH` (was `num2`=30) offset (player.py:71-73), while the dir-0/1 vertical probes use
  a `TILE_HEIGHT` (was `num1`=28) offset (player.py:77-79) — these two distinct offsets were
  NOT collapsed.
- **Blocked-ladder orderings match verbatim**, including the documented dir-2 and dir-3
  blinky-vs-other any-open-tail divergence (`_LADDER_DIR2_BLINKY` t3,t0,t1 vs `_OTHER`
  t1,t3,t0; `_LADDER_DIR3_BLINKY` t2,t0,t1 vs `_OTHER` t2,t1,t0).
- **The Q-c `if … if … else` quirk** (inky/clyde dir-0 and dir-1 forward-open) is transcribed
  as a literal double-`if` with the trailing `else` bound to the *second* `if`
  (`forward_seek_perp_y_right/left`), not flattened into an `elif` ladder — matching the
  original's override semantics.
- **`_go` always sets `g.direction`**, matching every original blocked-ladder branch (all of
  which set `self.direction` before moving); the primaries that did NOT set direction in the
  original (e.g. `primary_advance_right/left`, `primary_advance_down`) correctly omit it.
- **inky dir-1 "turn, no move"** (`primary_turn_no_move_down_then_left` sets direction=3 with no
  position change) vs **pinky dir-1 "turn and move"** (`primary_turn_and_move_down_then_left`)
  preserves the genuine one-line difference between the two originals.
- **`_move` branch structure** (`if primary != FIRED: if not turns[d]: ladder; elif turns[d]:
  forward_open`) is equivalent to the original single `if/elif not turns[d]/elif turns[d]`
  chain, including for the two-part primaries.
- **No shared-mutable-state aliasing**: ladders are tuples-of-tuples, `DirectionRule` is a
  namedtuple, and the `*_PROFILE` dicts are module-level and never mutated.
- **`geometry.in_box` tuple-unpack order** `(x_lo, x_hi, y_lo, y_hi)` with `x_lo < x < x_hi and
  y_lo < y < y_hi` correctly reproduces the original `350 < x_pos < 550 and 360 < y_pos < 480`
  (collision) and `340 < x < 560 and 340 < y < 500` (target) strict-inequality checks.
- **frame-hash terminal/double-count logic**: the line-110 "guarantee last frame" append only
  fires when `hashes[-1][0] != last_frame`, so a terminal frame that is also a sample multiple
  is not double-recorded; `replayed == committed` compares like-typed `(int, hexstr)` tuples.

## Warnings

### WR-01: `geometry.tile_at` and `geometry.is_walkable` are dead public API

**File:** `geometry.py:23-30`
**Issue:** `tile_at` and `is_walkable` are defined and documented as the shared replacements for
the inline `level[cy//num1][cx//num2]` and `< 3` idioms (and the plan/SUMMARY assert they are
"imported by game/ghost/player"). In the actual implementation **neither is imported anywhere** —
`game.py` and `ghost.py` import only `in_box` (+ a box constant), and `ghost.check_collisions` /
`player.check_position` / `game.check_collisions` all kept their inline tile reads. So these two
functions are unused exports that drift from the inline code they nominally describe; a future
maintainer could "wire them in" and silently lose the gate-tile-9 special case that
`check_collisions` relies on (`is_walkable` only encodes the bare `< 3` test, not the `== 9 and
(in_box or dead)` clause). This is the D-15 landmine pre-staged as live-looking-but-unused code.

Note: keeping the inline reads was the *correct* call for byte-identity (the gate-9 logic is not
expressible by `is_walkable` alone). The defect is shipping the two helpers as public API anyway.

**Fix:** Either remove `tile_at`/`is_walkable` until a consumer actually needs them, or downgrade
them to clearly-marked unused scaffolding. If kept, add a one-line note that `is_walkable`
deliberately does NOT cover the gate-9-in-box/dead exception, so it must not be substituted into
`check_collisions`:
```python
def is_walkable(tile_code):
    """``< 3`` walkability ONLY. NOTE: does not model the gate(9)-when-in_box/dead
    exception in Ghost.check_collisions — do not substitute it there."""
    return tile_code < 3
```

## Info

### IN-01: Magic numbers escaped centralization in the ghost wrap-clamp and box-detect

**File:** `ghost.py:411-414` (and `ghost.py:284-285`, `ghost.py:343` band literals)
**Issue:** REF-01 named the wrap thresholds as `GHOST_WRAP_LEFT=-30` / `GHOST_WRAP_RIGHT=900` in
`settings.py`, but `Ghost._move` still hardcodes the same literals: `if self.x_pos < -30:
self.x_pos = 900 / elif self.x_pos > 900: self.x_pos = -30`. The named constants are therefore
defined but not used by the ghost wrap (they are real magic numbers that survived the pass).
Likewise the `+ 22` center offset (ghost.py:284-285) and the `12 <= ... <= 18` alignment band
(ghost.py:343 etc.) remain inline. Behavior is unchanged; this is an internal-consistency gap
between "we named these constants" and "we still use the literals."
**Fix:** Use the constants in the clamp: `if self.x_pos < GHOST_WRAP_LEFT: self.x_pos =
GHOST_WRAP_RIGHT` etc. (import them in `ghost.py`). Low priority — purely cosmetic, and any such
edit must stay byte-identical and be re-blessed.

### IN-02: `_sampled` has unused parameters

**File:** `tests/test_frame_hash.py:75-77`
**Issue:** `_sampled(frame, frame_cap, is_terminal)` ignores `frame_cap` entirely; the body is
`frame % _SAMPLE_EVERY == 0 or is_terminal`. The dead parameter is misleading at the call site
(it implies a cap-relative sampling rule that does not exist).
**Fix:** Drop `frame_cap` from the signature and the call at line 104, or document why it is a
placeholder.

### IN-03: frame-hash CI gate can pass vacuously when run before the first bless

**File:** `tests/test_frame_hash.py:155-165`
**Issue:** The skip ladder is: non-pinned dev → skip; pinned env but manifest missing → skip
("re-bless in CI"). This is the intended bless lifecycle, but it means the test is only ever an
*assertion* once a Linux-blessed manifest exists AND the env vars are set. On a fresh CI before
the first `--bless`, every scenario skips green, so a geometry byte-shift introduced in the same
PR that first mints the manifest would be blessed-in rather than caught. The committed
`tests/golden/*/frame_hashes.txt` files exist, which mitigates this for the current state, but
the gate's teeth depend entirely on `CI`/`GSD_FRAME_HASH_ENV` actually being exported in the
workflow.
**Fix:** No code change required if `.github/workflows/ci.yml` reliably sets `CI` (it does by
default on GitHub Actions) and the manifests stay committed. Consider asserting that at least one
scenario was actually compared (not all-skipped) in the pinned env, so a misconfigured CI that
silently skips everything fails loudly instead of passing green.

---

_Reviewed: 2026-06-12_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
