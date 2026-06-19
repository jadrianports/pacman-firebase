---
phase: 06-in-game-weekly-boards-got-passed-banner
reviewed: 2026-06-19T18:41:52Z
depth: standard
files_reviewed: 9
files_reviewed_list:
  - api_service.py
  - cloud_functions/get_leaderboard/main.py
  - main.py
  - marker.py
  - menu.py
  - settings.py
  - tests/test_api_service.py
  - tests/test_get_leaderboard.py
  - tests/test_marker.py
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-06-19T18:41:52Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed the Phase 6 work: the `scope=last_week` read branch in the get_leaderboard
Cloud Function, the scope/timeout-aware client fetch in `api_service.py`, the unsigned
best-effort marker IO module (`marker.py`), and the menu/main UI wiring for the This
Week/All Time board toggle plus the got-passed launch banner.

The security posture is sound for this scope: the scope param is parsed tolerantly and
clamped to a fixed allowlist before touching Firestore (no injection surface), week IDs
are computed server-side only (no forged-week request possible), and only
`initials`+`score` are projected outward. The marker's deliberately-unsigned design is
correct for a cosmetic banner and is well-guarded by tests. The all-best-effort
degradation in `main.py` keeps the game playable offline.

The defects found are correctness/robustness issues, not security holes. The most
significant is a window-close (QUIT) event being swallowed in `run_leaderboard`, which
breaks the expected "close the window to quit" behavior while the board is open.

## Warnings

### WR-01: Window-close (QUIT) is swallowed while the leaderboard is open

**File:** `menu.py:243-245`
**Issue:** `run_leaderboard` handles `pygame.QUIT` by returning `views["week"]` — the
exact same value it returns for ESC/ENTER ("go back"). There is no out-of-band signal
for a quit. Back in `main.py`, the `Leaderboard` branch (lines 161-169) has no way to
distinguish "user pressed back" from "user closed the window," so it falls through to
the top of the `while True` loop and re-displays the main menu. The window-close request
is silently dropped; the user must trigger close again from the menu. This is
inconsistent with every sibling screen: `run_initials_entry` returns `None` on QUIT and
`main.py` quits (lines 87-89); `run_game_over_screen` returns `"quit"` on QUIT and
`main.py` breaks (lines 154-155). Only `run_leaderboard` cannot propagate a quit.
**Fix:** Give the leaderboard a distinct quit signal and honor it in the caller. For
example, return a 2-tuple `(quit_requested, week_entries)`:
```python
# menu.py — run_leaderboard
if event.type == pygame.QUIT:
    return True, (views["week"] if views["week"] is not _UNFETCHED else None)
...
if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
    return False, (views["week"] if views["week"] is not _UNFETCHED else None)
```
```python
# main.py — Leaderboard branch
quit_requested, this_week_entries = run_leaderboard(screen, timer, api)
banner_text = None
if this_week_entries and tracked_best is not None:
    initials_above = {e["initials"] for e in this_week_entries if e["score"] > tracked_best}
    marker.write_marker(marker.client_current_week_id(), tracked_best, initials_above)
if quit_requested:
    break
```

### WR-02: Leaderboard rows raise KeyError if a Firestore doc lacks `initials`/`score`

**File:** `cloud_functions/get_leaderboard/main.py:84`
**Issue:** `entries.append({"initials": data["initials"], "score": data["score"]})` uses
direct subscripting. A leaderboard/weekly document written without one of these fields
(partial write, schema drift, a manually-seeded doc) raises `KeyError` mid-iteration.
The surrounding `try/except` (line 86) catches it and turns the entire response into a
500 with an empty entries list — one malformed document blackholes the whole board for
every reader, even though every other document is valid. The client then renders "Could
not connect to leaderboard." (offline state) for what is actually a server-side data
issue.
**Fix:** Skip malformed documents instead of failing the whole query:
```python
for d in docs:
    data = d.to_dict()
    initials = data.get("initials")
    score = data.get("score")
    if initials is None or score is None:
        continue  # skip partial/legacy docs rather than 500 the whole board
    entries.append({"initials": initials, "score": score})
```

### WR-03: Negative dot-fill width when rank/initials/score exceed the 30-char budget

**File:** `menu.py:231`
**Issue:** `dots = "." * (30 - len(rank) - len(initials) - len(score))`. The score is
server-supplied and unbounded; for a high enough score (or longer initials than the
expected 3) the subtraction goes negative. `"." * -n` yields `""` so this does not crash,
but the row silently loses its alignment dots and the layout breaks with no warning. The
magic number `30` is also undocumented. Relying on "negative repeat count is empty
string" is fragile — a future refactor that, e.g., slices `dots[:-1]` or asserts a
minimum width would break.
**Fix:** Clamp explicitly and name the constant:
```python
LEADERBOARD_LINE_WIDTH = 30  # in settings.py
...
fill = max(0, LEADERBOARD_LINE_WIDTH - len(rank) - len(initials) - len(score))
dots = "." * fill
```

### WR-04: `submit_score` timeout is hardcoded while `get_leaderboard` made it configurable

**File:** `api_service.py:25` (vs `api_service.py:30,36`)
**Issue:** Phase 6 introduced a `timeout` parameter on `get_leaderboard` (default 10,
overridable to `BANNER_FETCH_TIMEOUT_SECONDS=2` for the launch banner) so a slow network
does not stall startup. `submit_score` still hardcodes `urlopen(req, timeout=10)`. The
asymmetry is a latent robustness gap: the submit call runs synchronously on the
game-over path (`main.py:139`) and a stalled connection blocks the UI for up to 10s with
no way for callers to tune it. Not a bug today, but the two network methods should share
one configurable timeout convention.
**Fix:** Add a `timeout=10` parameter to `submit_score` mirroring `get_leaderboard`, and
thread it into `urlopen(req, timeout=timeout)`.

## Info

### IN-01: Dead defensive branch — `views["week"]` is never `_UNFETCHED` at return

**File:** `menu.py:245,248`
**Issue:** Both return sites guard `views["week"] if views["week"] is not _UNFETCHED else
None`, but `views["week"]` is unconditionally assigned a real fetch result on line 170
before the event loop is ever entered, so it can never be `_UNFETCHED` at any return. The
`else None` arm is unreachable.
**Fix:** Simplify to `return views["week"]` (and fold into the WR-01 tuple change), or add
a comment if the guard is intentionally retained for defensiveness.

### IN-02: `_marker` underscore-prefixed local reads as a throwaway but is used

**File:** `main.py:101-104`
**Issue:** `_marker = marker.read_marker()` is then read on the next three lines. The
leading underscore conventionally signals "unused/throwaway," which is misleading here
since the value drives the whole banner-compute block. Minor naming clarity issue.
**Fix:** Rename to `marker_data` (or `last_viewed`) to avoid the unused-throwaway
connotation.

### IN-03: Server-time vs client-time week skew can produce a transient wrong banner

**File:** `marker.py:29-40` + `main.py:105-109`
**Issue:** The banner compares the marker's client-computed `week_id`
(`client_current_week_id`) against scores fetched from the server's `current_week_id`
weekly bucket. The two Monday-UTC computations are intentionally mirrored and tested for
parity (`test_client_current_week_id_matches_server`), but they read the clock at
slightly different instants on two machines. Within the ~seconds around a Monday-00:00-UTC
rollover, a client whose clock has not crossed midnight can still hold last week's marker
while the server already serves the new week — yielding a momentary spurious/empty banner.
This is cosmetic and self-corrects on the next launch (consistent with the documented
"wrong banner is harmless" contract), so it is informational only.
**Fix:** No action required for v1. If ever tightened, gate the banner on the server
echoing its own week_id rather than trusting client week math.

### IN-04: Broad `except Exception` swallows all errors uniformly in client network calls

**File:** `api_service.py:27,39`; `marker.py:63,80`
**Issue:** Every network/IO path catches bare `Exception` and returns `None`/passes. For
`marker.py` this is the explicit, documented best-effort contract and is correct. For
`api_service.py` it conflates genuinely-offline conditions with programming errors (e.g.
a malformed URL, a `json` bug, an unexpected response shape) — all surface to the user as
the same "Could not connect" state with no log, making field diagnosis hard.
**Fix:** Acceptable for graceful-degrade, but consider narrowing to
`(urllib.error.URLError, TimeoutError, json.JSONDecodeError)` or logging the exception
before swallowing so non-network failures are distinguishable in dev.

---

_Reviewed: 2026-06-19T18:41:52Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
