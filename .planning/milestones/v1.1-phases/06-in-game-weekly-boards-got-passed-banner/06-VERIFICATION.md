---
phase: 06-in-game-weekly-boards-got-passed-banner
verified: 2026-06-20T00:00:00Z
status: human_needed
score: 10/10 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Navigate to Leaderboard from the main menu. Confirm the board opens on This Week. Press LEFT or RIGHT and confirm the view switches to All Time (loading screen may flash). Press again to return to This Week. The active tab label should be yellow; inactive and separators gray."
    expected: "Board opens on 'This Week'. LEFT/RIGHT toggles to 'All Time' with a loading flash on first access. Active tab label is COLOR_YELLOW; inactive + '<', '|', '>' separators are COLOR_GRAY."
    why_human: "PyGame rendering cannot be automated headlessly without a display — tab coloring, lazy fetch timing, and visual toggle require a live game window."
  - test: "On a week where previous-week data exists in Firestore AND the Cloud Function has been redeployed with the scope=last_week branch: open the board, switch to This Week. Confirm 'Last week: {INITIALS}' appears below the tab indicator in gray. Switch to All Time. Confirm the subtitle disappears."
    expected: "'Last week: XXX' renders on This Week only, hidden on All Time. Hidden entirely when last week has no data."
    why_human: "Requires a live redeployed Cloud Function (the in-repo code gate is the validator tests) and real Firestore data from a previous week. The operator must trigger the manual 'get_leaderboard' Cloud Run redeploy (documented in the api-refactor spec) for live BOARD-04."
  - test: "Launch the game with a fresh marker (delete %LOCALAPPDATA%\\PacMan\\last_viewed.json). Confirm no banner appears, game reaches the main menu without error."
    expected: "No banner, no error, menu displayed normally."
    why_human: "Requires a running game instance; the cold-start code path cannot be invoked headlessly."
  - test: "With a marker present (tracked_best set, initials_above populated), launch the game offline (no network). Confirm the game reaches the menu within about 2 seconds and no banner is shown."
    expected: "Game starts within ~2s (BANNER_FETCH_TIMEOUT_SECONDS=2), no banner, no error or crash."
    why_human: "Network conditions and startup timing require a real runtime environment."
  - test: "Play a game and achieve a score. Confirm a successful submit. Open the board. Confirm the banner (if it was showing) clears. On the next launch, if someone passed your score since board open, a banner appears naming them."
    expected: "Banner clears on board open. Next launch banner is accurate (names only those who passed since last board view)."
    why_human: "Full RIVAL-01 flow requires multiple sessions, a second player submitting a higher score, and real marker persistence."
---

# Phase 6: In-Game Weekly Boards & Got-Passed Banner — Verification Report

**Phase Goal:** Surface the scoped API in-game — This Week / All Time toggle, last week's champion, and a launch banner naming whoever passed your score.
**Verified:** 2026-06-20T00:00:00Z
**Status:** human_needed
**Re-verification:** No — initial verification.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | GET get_leaderboard?scope=last_week returns the previous week's top-10 in {entries:[{initials,score}]} shape | VERIFIED | `cloud_functions/get_leaderboard/main.py` lines 50-66: `elif scope == "last_week"` branch queries `db.collection("weekly").where("week_id", "==", leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id()))...limit(10)`. Reuses shared projection loop stripping machine_id/week_id/updated_at. Two validator tests pass (test_scope_last_week_queries_weekly_with_previous_week, test_scope_last_week_projects_only_initials_and_score). |
| 2 | An unknown/garbage scope still falls back to week (never a 400) | VERIFIED | Line 39: `if scope not in ("week", "all", "last_week"): scope = "week"`. Test `test_garbage_scope_falls_back_to_week` passes. |
| 3 | The last_week branch projects only initials+score (machine_id/week_id/updated_at stripped) | VERIFIED | Shared projection loop (lines 79-84) strips all fields except initials+score for all branches. Test `test_scope_last_week_projects_only_initials_and_score` confirms. |
| 4 | get_leaderboard(scope='last_week') sends ?scope=last_week; get_leaderboard(scope='all') sends ?scope=all | VERIFIED | `api_service.py` line 33-34: `if scope: url += f"?{urlencode({'scope': scope})}"`. Tests `test_get_leaderboard_sends_scope_param` captures and asserts both. |
| 5 | get_leaderboard() with no args sends no scope param (URL == base) so the server defaults to week | VERIFIED | `scope=None` default means the `if scope:` branch is skipped; URL stays the bare base. Test `test_get_leaderboard_no_scope_omits_param` confirms `captured["url"] == service.leaderboard_url`. |
| 6 | get_leaderboard(timeout=2) threads the short timeout into urlopen; default stays 10 | VERIFIED | `urlopen(req, timeout=timeout)` in api_service.py. Test `test_get_leaderboard_passes_timeout` captures timeout kwarg and asserts 2 and 10 respectively. |
| 7 | read_marker returns None when absent/malformed/unreadable; write_marker never raises; stale week_id returns None; client_current_week_id() matches server Monday-UTC math | VERIFIED | marker.py: all three functions exist, fully best-effort. 11 marker tests pass covering: cold-start, malformed JSON, round-trip same-week, stale-week re-baseline, write failure on dump/open, week-id parity with server, signing-free AST check. |
| 8 | In the board screen, LEFT/RIGHT toggles This Week <-> All Time; opens on This Week; active tab highlighted | VERIFIED | menu.py: `_UNFETCHED` sentinel defined; `views = {"week": _UNFETCHED, "all": _UNFETCHED}; active = "week"`; K_LEFT/K_RIGHT handler flips active and lazy-fetches All Time on first toggle; tab indicator renders prefix/week_label/sep/all_label/suffix with active label COLOR_YELLOW and separators COLOR_GRAY. |
| 9 | Last-week champion subtitle 'Last week: XXX' shows under the header on This Week only, hidden when absent | VERIFIED | menu.py line 210: `if active == "week" and last_week_initials:` guards the subtitle render. `scope="last_week"` fetch is issued on open; `last_week_initials = last_week[0]["initials"] if last_week else None`. No placeholder when None. |
| 10 | On launch, new passers are computed and a banner names them; offline/cold-start/no-score → no banner, no error | VERIFIED | main.py lines 98-109: `marker.read_marker()` → None on cold start (no banner). If marker present with tracked_best: `api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)` → None if offline (no banner). `above_now - initials_above` computes new passers; `_format_banner` applies cap=3. `run_main_menu(screen, timer, banner_text=banner_text)` passes the text. Banner cleared after `run_leaderboard`. Marker rewritten on board open and on submit. |

**Score:** 10/10 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `cloud_functions/get_leaderboard/main.py` | scope=last_week read branch | VERIFIED | Lines 50-66: elif scope=="last_week" with previous_week_id call, shared query variable, shared projection loop |
| `tests/test_get_leaderboard.py` | validator tests for last_week scope | VERIFIED | Lines 175-205: two new tests, all 12 tests pass |
| `api_service.py` | get_leaderboard(scope=None, timeout=10) with urlencode | VERIFIED | Line 30-40: exact signature, urlencode({'scope': scope}), timeout=timeout threaded |
| `tests/test_api_service.py` | scope/timeout request-capture tests | VERIFIED | Lines 97-145: three new tests, all 11 tests pass |
| `settings.py` | MARKER_FILE_NAME, BANNER_FETCH_TIMEOUT_SECONDS, BANNER_NAME_CAP | VERIFIED | Lines 98-100: exact values "last_viewed.json", 2, 3 |
| `marker.py` | read_marker / write_marker / client_current_week_id | VERIFIED | All three functions exist, stdlib-only, fully best-effort, no signing, uses paths.user_data_path |
| `tests/test_marker.py` | marker IO + week-id tests | VERIFIED | 11 tests, all pass |
| `menu.py` | run_leaderboard toggle+subtitle+empty-state; run_main_menu banner_text param | VERIFIED | _UNFETCHED sentinel, K_LEFT/K_RIGHT, scope="week"/"all"/"last_week" calls, banner_text=None param renders at y=230 |
| `main.py` | launch banner compute, submit tracked-best update, board-open baseline rewrite | VERIFIED | import marker, BANNER_FETCH_TIMEOUT_SECONDS/BANNER_NAME_CAP, _format_banner, read_marker once at launch, write_marker in submit path and board-open path, banner_text cleared after run_leaderboard |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `cloud_functions/get_leaderboard/main.py` | `leaderboard_crypto.previous_week_id` | module-qualified call in last_week branch | WIRED | Line 60-62: `leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())` |
| `api_service.get_leaderboard` | `urllib.parse.urlencode` | query-string assembly when scope is truthy | WIRED | Line 2: `from urllib.parse import urlencode`; line 34: `urlencode({'scope': scope})` |
| `main.py` | `api.get_leaderboard` | short-timeout launch This Week fetch | WIRED | Line 105: `api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)` |
| `main.py` | `marker.read_marker / marker.write_marker` | launch compute + board-open baseline rewrite | WIRED | Line 101: `marker.read_marker()`; line 152: `marker.write_marker(...)` in submit path; lines 167-169: `marker.write_marker(...)` in board-open path |
| `menu.run_leaderboard` | `api_service.get_leaderboard` | per-view lazy scope fetch | WIRED | Line 170: `scope="week"`, line 171: `scope="last_week"`, line 254: `scope="all"` |
| `main.py` | `run_main_menu` | banner_text passed in | WIRED | Line 113: `run_main_menu(screen, timer, banner_text=banner_text)` |
| `main.py` | `run_leaderboard` | return-based board-open seam (O-3) | WIRED | Line 161: `this_week_entries = run_leaderboard(screen, timer, api)`; line 162: `banner_text = None`; lines 163-169: initials_above recomputed and marker rewritten |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `menu.py:run_leaderboard` | `views["week"]` | `api_service.get_leaderboard(scope="week")` line 170 | Yes — urlopen to Cloud Function endpoint | FLOWING |
| `menu.py:run_leaderboard` | `views["all"]` | `api_service.get_leaderboard(scope="all")` line 254 | Yes — lazy-fetched on toggle | FLOWING |
| `menu.py:run_leaderboard` | `last_week_initials` | `api_service.get_leaderboard(scope="last_week")` line 171 | Yes — entries[0]["initials"] when present | FLOWING |
| `menu.py:run_main_menu` | `banner_text` | Computed in `main.py` from live board data and marker | Yes — from real fetch and persisted marker | FLOWING |
| `main.py` | `banner_text` | `marker.read_marker()` + `api.get_leaderboard()` | Yes — marker is real file IO; fetch is real network call | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| settings constants accessible | `.venv/Scripts/python.exe -c "import settings; assert settings.MARKER_FILE_NAME=='last_viewed.json'; assert settings.BANNER_FETCH_TIMEOUT_SECONDS==2; assert settings.BANNER_NAME_CAP==3; print('ok')"` | ok | PASS |
| marker.py parses and exports all 3 functions | `.venv/Scripts/python.exe -c "import marker; assert callable(marker.read_marker); assert callable(marker.write_marker); assert callable(marker.client_current_week_id); print('ok')"` | ok | PASS |
| menu.py parses (ast) | `.venv/Scripts/python.exe -c "import ast; ast.parse(open('menu.py').read()); print('ok')"` | ok | PASS |
| main.py parses (ast) | `.venv/Scripts/python.exe -c "import ast; ast.parse(open('main.py').read()); print('ok')"` | ok | PASS |
| run_main_menu signature has banner_text param | `.venv/Scripts/python.exe -c "import inspect, menu; assert 'banner_text' in inspect.signature(menu.run_main_menu).parameters; print('ok')"` | ok | PASS |
| Full test suite | `.venv/Scripts/python.exe -m pytest -q` | 138 passed, 9 skipped | PASS |

### Probe Execution

No probe scripts declared or present for this phase (UI/wiring phase, not a migration/tooling phase). Step 7c: SKIPPED.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| BOARD-03 | 06-02, 06-04 | Player can toggle between This Week and All Time views in-game | SATISFIED | menu.py K_LEFT/K_RIGHT handler with lazy All Time fetch; three scoped get_leaderboard calls in run_leaderboard |
| BOARD-04 | 06-01, 06-04 | Previous week's champion shown ("Last week: BOB") | SATISFIED (code gate) | Cloud Function scope=last_week branch + tests; menu.py subtitle render on This Week only; live deploy is a human/operator action |
| RIVAL-01 | 06-03, 06-04 | On launch, banner names players who beat the player's score since last board view; no-op offline/first-launch | SATISFIED | marker.py + main.py launch compute + _format_banner; all graceful-degrade paths verified; full test suite green |

No orphaned requirements — all three IDs (BOARD-03, BOARD-04, RIVAL-01) are claimed by phase plans and evidence found in code.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| No debt markers (TBD/FIXME/XXX/TODO/HACK) found in any phase-modified file | — | — | — | — |

No unresolved debt markers. No stub return values in data-flowing paths. No hardcoded empty arrays/objects in rendering paths.

### Human Verification Required

#### 1. In-Game Tab Toggle Visual Verification (BOARD-03)

**Test:** Navigate to Leaderboard from the main menu. Confirm the board opens on This Week. Press LEFT or RIGHT and confirm the view switches to All Time (a loading screen may briefly appear on first access). Press again to return to This Week. Observe the tab indicator coloring.

**Expected:** Board opens on "This Week". LEFT/RIGHT toggles between views. The active tab label is COLOR_YELLOW (255,255,0); the inactive label and the `<`, `|`, `>` separators are COLOR_GRAY (128,128,128). "Loading..." appears on the first All Time access only. ESC or ENTER exits and the game returns to the main menu.

**Why human:** PyGame rendering cannot be driven headlessly without a display. Tab coloring, lazy-fetch timing, and the visual toggle sequence require a live game window.

#### 2. Last-Week Champion Subtitle — Live Cloud Function Redeploy (BOARD-04)

**Test:** After the operator redeploys the `get_leaderboard` Cloud Function (to pick up the `scope=last_week` branch — Google Cloud Console / Cloud Shell), open the board while connected to the network. Confirm "Last week: {INITIALS}" appears below the tab indicator in gray on the This Week view. Switch to All Time with LEFT/RIGHT. Confirm the subtitle disappears. Switch back — confirm it reappears.

**Expected:** "Last week: XXX" renders on This Week only in COLOR_GRAY. Hidden entirely on All Time. Hidden on This Week if last week has no scores.

**Why human:** The in-repo code gate is the validator tests (all pass). Live BOARD-04 behavior requires a manual Cloud Run redeploy by the operator and real Firestore data from a previous week bucket. This is a known operator action documented in the api-refactor spec, not an in-repo code gap.

#### 3. Cold-Start / Offline Launch Graceful Degrade (RIVAL-01)

**Test A (cold start):** Delete `%LOCALAPPDATA%\PacMan\last_viewed.json` if it exists. Launch the game. Confirm the main menu appears with no banner and no error/crash.

**Test B (offline):** With a valid marker on disk (tracked_best populated), launch the game with no network access. Confirm the game reaches the main menu within approximately 2 seconds (the short BANNER_FETCH_TIMEOUT_SECONDS=2 bound) and no banner appears.

**Expected:** Menu reached promptly in both cases, no error, no crash, no banner.

**Why human:** Requires a running game instance. Cold-start and offline paths are code-verified (read_marker returns None → no banner; get_leaderboard returns None → no banner) but the 2-second startup bound and the actual OS behavior require a real runtime.

#### 4. Full RIVAL-01 Got-Passed Banner End-to-End

**Test:** Play a game and achieve a score. Observe a successful submit (response.is_new_best if it's a new best). Open the board (Leaderboard from main menu) — confirm any existing banner clears on the menu after returning. Have a second player submit a higher score for the same week. Launch the game again. Confirm the banner names the new passer.

**Expected:** Banner clears when board is opened. Next launch: "{INITIALS} passed you this week!" (or multiple names with cap=3 cap). If nobody passed since the board was opened, no banner.

**Why human:** End-to-end RIVAL-01 requires multiple sessions, real score submissions from a second player, and real marker persistence across launches. The individual code paths are all unit-verified.

### Gaps Summary

No automated gaps found. All 10 must-have truths are VERIFIED, all 9 required artifacts exist and are substantive and wired, all key links are confirmed in code, all 34 targeted tests pass, the full suite (138 passed, 9 skipped) has no regressions.

The human verification items above are the remaining gate before the phase can be marked complete:
- Items 1 and 2 require a live game window and (for BOARD-04) an operator Cloud Function redeploy.
- Items 3 and 4 require real runtime conditions (network absent, multiple sessions, second player).

**Code review note (CR-01, tracked in 06-REVIEW.md, WARNING):** The launch banner compute block at `main.py:101-109` is documented as "all best-effort — never break startup" but has no surrounding `try/except`. If the marker contains a non-numeric `tracked_best` (e.g. a hand-edited string) or the leaderboard response contains a malformed entry missing the `score` key, a TypeError or KeyError propagates and crashes startup. This does not prevent goal achievement with well-formed data, and the phase tests all pass, but the "never break startup" contract is not fully enforced for malformed inputs. The fix is a single `try/except Exception: banner_text = None` wrapping lines 101-109. Remediation path is via 06-REVIEW.md, not this verification gate.

---

_Verified: 2026-06-20T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
