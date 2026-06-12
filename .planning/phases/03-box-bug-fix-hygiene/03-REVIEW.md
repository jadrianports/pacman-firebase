---
phase: 03-box-bug-fix-hygiene
reviewed: 2026-06-12T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - geometry.py
  - game.py
  - ghost.py
  - menu.py
  - requirements.txt
  - CLAUDE.md
findings:
  critical: 0
  warning: 0
  info: 2
  total: 2
status: issues_found
---

# Phase 3: Code Review Report

**Reviewed:** 2026-06-12T00:00:00Z
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found (info-only — no blockers, no warnings)

## Summary

Phase 3 performs the BUG-01 ghost-box constant collapse plus three hygiene edits. The
review traced the unification end-to-end and confirms it is correct, complete, and
isolated to the sanctioned box-targeting path. Both info findings are non-blocking
observations, not defects in the phase work.

**BUG-01 verification (the high-value focus):**

- **geometry.py** — Old `GHOST_BOX_BOUNDS_COLLISION (350,550,360,480)` and
  `GHOST_BOX_BOUNDS_TARGET (340,560,340,500)` are collapsed into a single
  `GHOST_BOX_BOUNDS = (350,550,360,480)` (the tighter collision box wins, per D-01).
  The `in_box(x, y, bounds)` predicate is byte-unchanged (strict `x_lo < x < x_hi and
  y_lo < y < y_hi`). The only remaining `340/560/500` literals in the file live inside
  the historical-divergence comment (documentation, not live code) — verified via grep.
- **game.py** — All 8 `get_targets` call sites (lines 240, 249, 258, 267, 275, 282,
  289, 296) consistently use the unified `GHOST_BOX_BOUNDS`, import repointed at line 18.
  This is the intended behavior-delta: an eaten ghost in the ~10px x / ~20px y ring
  between the two old rectangles now switches from `SCATTER_EATEN_TARGET` to chase-player
  a touch sooner. Change is confined to this targeting heuristic; surrounding control flow
  (powerup/non-powerup branches, runaway logic, return-target) is untouched.
- **ghost.py** — Single `check_collisions` call site (line 384) repointed to
  `GHOST_BOX_BOUNDS`. Value is identical to the old `_COLLISION` constant
  (350,550,360,480), so this is a name-only rename: in_box flag, turn-legality, box-exit
  timing, and dead-ghost revival are byte-identical by construction. No second behavior
  change leaked in.
- **No lingering references:** grep across all non-planning source/test files confirms
  zero remaining `GHOST_BOX_BOUNDS_TARGET` / `GHOST_BOX_BOUNDS_COLLISION` usages. Only
  `.planning/` artifacts retain the old names (expected, out of scope).
- **settings.py out-of-scope constants confirmed unchanged:** `BOX_EXIT_DELAY_INKY=0`,
  `BOX_EXIT_DELAY_PINKY=30`, `BOX_EXIT_DELAY_CLYDE=60` (not in the diff). Neither
  `get_targets` nor `check_collisions` depends on a changed value.

**Hygiene edits:**

- **requirements.txt** — Pins `pygame==2.6.1`, `pyinstaller==6.20.0`. Both are real
  released versions; pinning is correct and reduces build drift.
- **menu.py** — Docstring drops the dead "Change Initials" option. Verified correct:
  `settings.MENU_OPTIONS = ["Play", "Leaderboard", "Quit"]` has no such entry, and
  initials entry is reached via a direct `run_initials_entry` call in main.py, not a menu
  option. Pure docstring fix, no behavior change.
- **CLAUDE.md** — Box-exit prose now reads "Pinky after ~0.5 sec, Clyde after ~1 sec",
  which matches PINKY=30 / CLYDE=60 frames at FPS=60. Accurate.

All correctness, security, and edge-case checks pass. No SQL/command injection, no
secrets, no unsafe deserialization surface in the reviewed files (geometry/box logic only).

## Info

### IN-01: `run_initials_entry` has a now-unreachable `current_initials` branch (pre-existing)

**File:** `menu.py:47-57`
**Issue:** `run_initials_entry(screen, timer, current_initials=None)` still carries a
`current_initials` parameter and the branch `if current_initials and
len(current_initials) == 3:` (lines 53-55), but the only caller (`main.py:20`) invokes it
as `run_initials_entry(screen, timer)` with no third argument. Combined with the
"initials are permanent / set once" design noted in CLAUDE.md, the populated-initials
branch is dead — `letters` always initializes to `[0, 0, 0]`. This is pre-existing state,
not introduced by Phase 3, and consistent with the "Change Initials" removal the phase
documents; flagging only as a cleanup opportunity.
**Fix:** Optional — drop the `current_initials` parameter and collapse to
`letters = [0, 0, 0]`, or leave as-is if a future "edit initials" flow is anticipated. No
action required for this phase.

### IN-02: geometry.py docstring retains old box literals in prose

**File:** `geometry.py:20-23`
**Issue:** The historical-divergence comment intentionally preserves the old tuples
`(340,560,340,500)` and `(350,550,360,480)` as a "do NOT re-split" guard. This is
deliberate and helpful, but means a future grep for the old magnitude `340`/`560`/`500`
will hit this file. Confirmed these are comment-only — `tile_at`, `is_walkable`, and
`in_box` reference none of them, and the live constant is the single
`GHOST_BOX_BOUNDS = (350, 550, 360, 480)`.
**Fix:** None required. Noted so downstream readers know the literals are documentation,
not a missed call site.

---

_Reviewed: 2026-06-12T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
