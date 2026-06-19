---
phase: 06-in-game-weekly-boards-got-passed-banner
reviewed: 2026-06-20T00:00:00Z
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
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 6: Code Review Report

**Reviewed:** 2026-06-20T00:00:00Z
**Depth:** standard
**Files Reviewed:** 9
**Status:** issues_found

## Summary

Reviewed the Phase 6 in-game weekly boards & got-passed banner changes: the
`scope=last_week` read branch on `get_leaderboard` (Cloud Function), the
`scope`/`timeout` params on `ApiService.get_leaderboard`, the unsigned best-effort
marker IO module (`marker.py`), and the `menu.py`/`main.py` wiring for the in-board
toggle and launch banner.

The Cloud Function scope branch, `api_service` changes, and `marker.py` IO module are
clean, well-tested, and faithful to their stated contracts (no scope is forwarded to
Firestore as a forged value; marker IO never raises; week math matches the server).

The one serious problem is in `main.py`: the launch banner compute is documented as
"all best-effort — never break startup," but the actual consumption block has no
`try/except` and trusts both the marker's `tracked_best` type and the server response
shape. A malformed marker or leaderboard payload crashes the game at startup — the
exact failure the design says cannot happen. Several rivalry-computation correctness
smells and quality issues follow.

## Critical Issues

### CR-01: Launch banner compute is not exception-guarded — a malformed marker or leaderboard response crashes startup

**File:** `main.py:101-109`
**Issue:** The docstring at lines 92-97 states the banner compute is "all best-effort
— never break startup (SC-4)," and `marker.read_marker()` is carefully written to never
raise. But the block that *consumes* the marker and the network response has no guard:

```python
if _marker is not None and _marker.get("tracked_best") is not None:
    tracked_best = _marker["tracked_best"]
    initials_above = set(_marker.get("initials_above", []))
    this_week = api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)
    if this_week:
        above_now = {e["initials"] for e in this_week if e["score"] > tracked_best}
        new_passers = sorted(above_now - initials_above)
        banner_text = _format_banner(new_passers)
```

Two concrete crash vectors, both reachable without any code change elsewhere:

1. **Untyped `tracked_best` from a hand-edited / partially-corrupt marker.**
   `read_marker()` only validates `week_id` — it does NOT validate the type of
   `tracked_best`. A marker `{"week_id": "<this Monday>", "tracked_best": "1000"}`
   passes `read_marker`, then `e["score"] > tracked_best` raises
   `TypeError: '>' not supported between instances of 'int' and 'str'`. The design
   doc claims "a missing, corrupt, or wrong-week marker is HARMLESS" — this one is not.

2. **Malformed leaderboard entry.** `e["initials"]` / `e["score"]` assume every entry
   is a dict with both keys. If the server (or a future schema drift) returns an entry
   missing `score`, `KeyError` propagates out of `main()` and the game never reaches the
   menu loop.

Because this runs before `run_main_menu`, the failure is a hard startup crash, not a
degraded banner.

**Fix:** Wrap the entire compute in the best-effort guard the docstring promises:

```python
try:
    if _marker is not None and _marker.get("tracked_best") is not None:
        tracked_best = _marker["tracked_best"]
        initials_above = set(_marker.get("initials_above", []))
        this_week = api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)
        if this_week:
            above_now = {
                e["initials"] for e in this_week
                if isinstance(e.get("score"), (int, float))
                and isinstance(tracked_best, (int, float))
                and e["score"] > tracked_best
            }
            new_passers = sorted(above_now - initials_above)
            banner_text = _format_banner(new_passers)
except Exception:
    banner_text = None  # best-effort: never break startup (SC-4)
```

Optionally also type-check `tracked_best` inside `read_marker()` so other consumers
(the submit-path `max(tracked_best or 0, score)` at line 151) are equally protected.

## Warnings

### WR-01: Submit-path re-baseline updates `tracked_best` but leaves `initials_above` stale, corrupting the next launch's passer set

**File:** `main.py:149-152`
**Issue:** After a successful submit, `tracked_best` is raised to the new score, and the
marker is rewritten — but `initials_above` is persisted unchanged:

```python
if response is not None:
    week_id = marker.client_current_week_id()
    tracked_best = max(tracked_best or 0, score)
    marker.write_marker(week_id, tracked_best, initials_above)
```

`initials_above` was computed against the *old* `tracked_best`. After raising the bar,
that set no longer means "initials currently above me." On the next launch,
`new_passers = above_now - initials_above` subtracts a set that is keyed to a different
threshold. Net effect: rivals who are genuinely above your new (higher) best but happened
to be above your old best too are silently suppressed, while rivals no longer above you
linger in the baseline. The banner becomes unreliable specifically after the player
improves — the most common case. Note `initials_above` is correctly recomputed only on
board-open (lines 163-169), so a player who never opens the board accumulates this drift.

**Fix:** Either recompute `initials_above` against the new `tracked_best` from the
`response`/known entries on the submit path, or — simpler and consistent with the
board-open seam being the single source of truth — clear `initials_above` to an empty set
when `tracked_best` increases, so the next launch re-baselines cleanly:

```python
if response is not None:
    new_best = max(tracked_best or 0, score)
    if new_best > (tracked_best or 0):
        initials_above = set()  # threshold moved; old baseline is meaningless
    tracked_best = new_best
    marker.write_marker(marker.client_current_week_id(), tracked_best, initials_above)
```

### WR-02: Board-open re-baseline skips empty and offline boards, leaving a stale `initials_above`

**File:** `main.py:163-169`
**Issue:** The marker is rewritten only when `this_week_entries` is truthy:

```python
if this_week_entries and tracked_best is not None:
    initials_above = {e["initials"] for e in this_week_entries if e["score"] > tracked_best}
    marker.write_marker(...)
```

An empty board (`[]`) and an offline board (`None`) are both falsy, so opening the board
in those states does NOT reset the baseline. If everyone above you has rolled off (board
now empty), the correct `initials_above` is the empty set, but the stale non-empty set
persists and will suppress legitimate future passers. The comment at 158-160 claims board
open is "the ONLY place initials_above is reset," but it actually skips the reset in two
of the three return states.

**Fix:** Treat an explicit empty list as a valid re-baseline (reset to empty set); only
skip on the offline/`None` case where there is genuinely no fresh truth:

```python
if this_week_entries is not None and tracked_best is not None:
    initials_above = {
        e["initials"] for e in this_week_entries if e["score"] > tracked_best
    }
    marker.write_marker(marker.client_current_week_id(), tracked_best, initials_above)
```

(`this_week_entries is not None` distinguishes `[]` from offline `None`.)

### WR-03: `e["score"] > tracked_best` and entry-key access unguarded inside `run_leaderboard` render loop

**File:** `menu.py:227-232`
**Issue:** The board render loop dereferences `entry["initials"]` and `entry["score"]`
with no key/type guard. `run_leaderboard` is reached from the menu loop, not startup, so a
malformed entry here raises out of the menu loop and crashes the whole program (the outer
`while True` in `main()` has no guard either). This is the same class of trust-the-payload
issue as CR-01 but in a different entrypoint; downgraded to WARNING because it requires a
malformed server response rather than a local file the user can corrupt.
**Fix:** Defensively read fields, e.g. `entry.get("initials", "???")` and
`entry.get("score", 0)`, or validate/normalize entries once at fetch time in
`ApiService.get_leaderboard` before they reach the renderer.

### WR-04: Banner/rivalry keyed on non-unique initials collapses distinct rivals

**File:** `main.py:107-108`, `menu.py:164-166`
**Issue:** `initials_above` and `above_now` are `set[str]` of initials, but initials are
explicitly non-unique (3-letter codes, many machines can share "AAA"). Two different
players who both pass you under the same initials register as one; a genuine new passer
"AAA" is masked if any prior "AAA" was already in the baseline (`above_now - initials_above`
removes it). The banner can both under-count and mis-attribute. The server only ships
`{initials, score}` (D-10), so there is no stable identity to key on — this is a design
constraint, not a coding slip, but it should be acknowledged because the "who passed you"
feature can silently mislead. **Fix:** Document the limitation explicitly at the compute
site, or key the comparison on `(initials, score)` tuples so at least distinct scores under
the same initials are treated as distinct rivals (still imperfect on ties, but closer).

### WR-05: Three sequential blocking fetches at default 10s timeout on board open

**File:** `menu.py:170-171`, `254`
**Issue:** `run_leaderboard` issues `get_leaderboard(scope="week")` and
`get_leaderboard(scope="last_week")` back-to-back on open (each defaulting to the 10s
timeout), plus a third `scope="all"` fetch on first toggle. When offline, the board-open
path blocks for up to 20 seconds (week + last_week) on the main thread with only a single
"Loading..." frame, and the window is unresponsive to QUIT during that window. This is a
robustness/UX defect, not raw perf: the user cannot close the window or back out while the
two serial timeouts elapse. **Fix:** Pass a short timeout to the non-critical `last_week`
subtitle fetch (it is cosmetic — mirror `BANNER_FETCH_TIMEOUT_SECONDS`), and consider
fetching `last_week` lazily/only-if-week-succeeded so an offline open fails fast once
rather than twice.

## Info

### IN-01: Banner-block comment over-promises a guarantee the code does not provide

**File:** `main.py:92-97`
**Issue:** The comment asserts the banner compute is "all best-effort — never break
startup (SC-4)," which is currently false (see CR-01). Even after CR-01 is fixed, keep the
comment and code in sync. **Fix:** Once the `try/except` is added, the comment becomes
accurate; until then it is misleading documentation.

### IN-02: `_marker` underscore-prefixed local name is non-idiomatic

**File:** `main.py:101-104`
**Issue:** `_marker` uses a leading underscore for an ordinary local variable (the
underscore convention signals "private/unused"), and it shadows the intent of the imported
`marker` module by near-name collision, which is easy to misread. **Fix:** Rename to
`saved_marker` or `last_view` for clarity.

### IN-03: `last_week_initials` assumes entry shape without guarding the cosmetic path

**File:** `menu.py:172`
**Issue:** `last_week[0]["initials"]` indexes and key-accesses a network response for a
purely cosmetic subtitle. `last_week` truthiness guards emptiness/None, but a malformed
first entry (missing `initials`) raises during board open. Lower severity than WR-03
because it is a single field on the open path. **Fix:** `last_week[0].get("initials")` and
fall back to hiding the subtitle when absent.

---

_Reviewed: 2026-06-20T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
