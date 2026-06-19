---
phase: 06-in-game-weekly-boards-got-passed-banner
fixed_at: 2026-06-19T18:51:18Z
review_path: .planning/phases/06-in-game-weekly-boards-got-passed-banner/06-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 6: Code Review Fix Report

**Fixed at:** 2026-06-19T18:51:18Z
**Source review:** .planning/phases/06-in-game-weekly-boards-got-passed-banner/06-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4 (all Warning; 0 Critical)
- Fixed: 4
- Skipped: 0

Scope was `critical_warning`, so the 4 Info findings (IN-01..IN-04) were intentionally
out of scope and not addressed. The full test suite was run after the fixes:
**138 passed, 9 skipped** via `.venv/Scripts/python.exe -m pytest tests/`.

## Fixed Issues

### WR-04: `submit_score` timeout is hardcoded while `get_leaderboard` made it configurable

**Files modified:** `api_service.py`
**Commit:** 333caa8
**Applied fix:** Added a `timeout=10` parameter to `ApiService.submit_score` (mirroring
`get_leaderboard`) and threaded it into `urlopen(req, timeout=timeout)`. Default stays
10s so existing callers are unaffected; the submit path can now tune the timeout the same
way the launch-banner fetch does. The existing `submit_score` tests (whose
`_fake_urlopen(req, timeout=None)` already accept a timeout kwarg) continue to pass.

### WR-02: Leaderboard rows raise KeyError if a Firestore doc lacks `initials`/`score`

**Files modified:** `cloud_functions/get_leaderboard/main.py`
**Commit:** b67310e
**Applied fix:** Replaced the direct `data["initials"]`/`data["score"]` subscripting in
the projection loop with `data.get(...)` plus a guard that `continue`s past any document
missing either field. One malformed/partial/legacy doc is now skipped instead of raising
`KeyError`, being caught by the surrounding `try/except`, and 500-ing the whole board for
every reader. The projection still ships only `initials`+`score` (D-10), so all existing
`test_get_leaderboard.py` projection/scope tests still pass.

### WR-03: Negative dot-fill width when rank/initials/score exceed the 30-char budget

**Files modified:** `settings.py`, `menu.py`
**Commit:** fbdbdb6
**Applied fix:** Introduced a named `LEADERBOARD_LINE_WIDTH = 30` constant in
`settings.py` (documented as the row character budget), imported it in `menu.py`, and
changed the dot-fill computation in `run_leaderboard` to
`fill = max(0, LEADERBOARD_LINE_WIDTH - len(rank) - len(initials) - len(score))` before
`dots = "." * fill`. This removes the reliance on "negative repeat count yields empty
string" and documents the previously-magic `30`. No behavioral change for in-budget rows.

### WR-01: Window-close (QUIT) is swallowed while the leaderboard is open

**Files modified:** `menu.py`, `main.py`
**Commit:** 0b9df79
**Status note:** fixed — requires human verification (control-flow/logic change; syntax,
the full pytest suite, and the `check_main_wiring.py` AST check all pass, but the
runtime quit-while-board-open behavior is not exercised by an automated test).
**Applied fix:** Gave `run_leaderboard` an out-of-band quit signal by changing its return
to a `(quit_requested, week_entries)` tuple — `True` on `pygame.QUIT`, `False` on
ESC/ENTER — keeping the existing `_UNFETCHED`-guarded This Week entries as the second
element so the marker-baseline-rewrite seam (O-3) is unchanged. Updated the single call
site in `main.py`'s `Leaderboard` branch to unpack the tuple, run the marker rewrite as
before, then `break` the main loop when `quit_requested` is set. This makes a
window-close while the board is open actually quit the game, consistent with
`run_initials_entry` (returns `None` -> quit) and `run_game_over_screen` (returns
`"quit"` -> break). `run_leaderboard` has no direct test, so no test required updating;
the marker rewrite still runs once per board open before the quit check.

---

_Fixed: 2026-06-19T18:51:18Z_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
