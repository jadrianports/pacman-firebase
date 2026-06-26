---
phase: 06
slug: in-game-weekly-boards-got-passed-banner
status: validated-partial
nyquist_compliant: false
wave_0_complete: true
created: 2026-06-20
---

# Phase 06 — Validation Strategy

> Per-phase validation contract, reconstructed from artifacts (State B — no prior
> VALIDATION.md; reconstructed from 4 PLAN/SUMMARY pairs, 06-VERIFICATION.md, and
> the live test suite). One automatable gap was found and filled; the remaining
> uncovered behaviors are inherently manual (headless PyGame render, live Cloud
> Function redeploy, two-player end-to-end) and are recorded as Manual-Only.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (pygame 2.6.1, Python 3.12.10, `.venv`) |
| **Config file** | `tests/conftest.py` (no pytest.ini/pyproject — conftest puts repo root on `sys.path`, forces `SDL_VIDEODRIVER`/`SDL_AUDIODRIVER=dummy` before pygame import, and firebase-mocks the cloud-function modules) |
| **Quick run command** | `.venv/Scripts/python.exe -m pytest tests/test_banner_format.py tests/test_marker.py tests/test_api_service.py tests/test_get_leaderboard.py -x` |
| **Full suite command** | `.venv/Scripts/python.exe -m pytest` |
| **Estimated runtime** | ~83 seconds full suite (~0.1s for the phase-06 unit files) |

---

## Sampling Rate

- **After every task commit:** Run the per-file quick command for the touched module.
- **After every plan wave:** Run the full suite (`.venv/Scripts/python.exe -m pytest`).
- **Before `/gsd-verify-work`:** Full suite must be green (last run: **146 passed, 9 skipped**).
- **Max feedback latency:** ~83 seconds.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | BOARD-04 | T-06-01 / T-06-02 / T-06-03 | `scope=last_week` is allow-list-gated (unknown→week, never 400); server-time-only week; projection strips machine_id/week_id/updated_at | unit | `.venv/Scripts/python.exe -m pytest tests/test_get_leaderboard.py -x` | ✅ | ✅ green |
| 06-02-01 | 02 | 1 | BOARD-03, BOARD-04 | T-06-05 / T-06-06 / T-06-07 | query built with `urlencode` (no injection); fetch+parse → None on failure; explicit `timeout` always passed | unit | `.venv/Scripts/python.exe -m pytest tests/test_api_service.py -x` | ✅ | ✅ green |
| 06-03-01 | 03 | 1 | RIVAL-01 | — | settings constants present with decided values; no new COLOR_*/FONT_* | unit (import assert) | `.venv/Scripts/python.exe -c "import settings; assert settings.MARKER_FILE_NAME=='last_viewed.json' and settings.BANNER_FETCH_TIMEOUT_SECONDS==2 and settings.BANNER_NAME_CAP==3"` | ✅ | ✅ green |
| 06-03-02 | 03 | 1 | RIVAL-01 | T-06-08 / T-06-09 / T-06-10 / T-06-11 | marker is unsigned plain JSON (no signing path); read/write never raise; stale-week → None re-baseline | unit | `.venv/Scripts/python.exe -m pytest tests/test_marker.py -x` | ✅ | ✅ green |
| 06-04-01 | 04 | 2 | BOARD-03, BOARD-04 | T-06-14 | `run_leaderboard` toggle / last-week subtitle / per-view empty+offline render | manual (PyGame) + AST gate | `.venv/Scripts/python.exe -c "import ast; ast.parse(open('menu.py').read())"` | ✅ (parse gate) | ⚠️ manual — see Manual-Only #1, #2 |
| 06-04-02 | 04 | 2 | RIVAL-01 | T-06-14 | `run_main_menu` banner_text render (yellow, y=230) | manual (PyGame) + signature gate | `.venv/Scripts/python.exe -c "import menu, inspect; assert 'banner_text' in inspect.signature(menu.run_main_menu).parameters"` | ✅ (sig gate) | ⚠️ manual — see Manual-Only #1 |
| 06-04-03a | 04 | 2 | RIVAL-01 | T-06-12 / T-06-13 / T-06-16 | `main._format_banner` cap=3 copy logic (empty→None, ≤cap list, >cap "+K more") | unit | `.venv/Scripts/python.exe -m pytest tests/test_banner_format.py -x` | ✅ **NEW** | ✅ green (8 tests) |
| 06-04-03b | 04 | 2 | RIVAL-01 | T-06-13 / T-06-15 / T-06-16 | launch passer set-difference (`above_now - initials_above`), submit tracked-best update, board-open baseline rewrite — inline in `main()` | manual (impl-inline) | `.venv/Scripts/python.exe -m pytest` (suite green; path not isolatable) | ❌ (not isolatable) | ⚠️ manual — see Manual-Only #3 |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky/manual*

---

## Wave 0 Requirements

Existing infrastructure covers all automatable phase requirements. No Wave 0 framework
install or scaffolding was needed — the new gap test (`tests/test_banner_format.py`)
rides the existing pytest + `conftest.py` harness.

- [x] `tests/test_banner_format.py` — RIVAL-01 banner copy/cap logic (NEW, this audit)
- [x] `tests/conftest.py` — shared fixtures (pre-existing; SDL dummy + sys.path + firebase mocks)

---

## Manual-Only Verifications

| # | Behavior | Requirement | Why Manual | Test Instructions |
|---|----------|-------------|------------|-------------------|
| 1 | Board screen This Week / All Time toggle, active-tab coloring, lazy All-Time fetch | BOARD-03 | PyGame rendering cannot be driven headlessly (no display); tab color, lazy-fetch timing, and the visual toggle need a live window | Open Leaderboard → confirm opens on This Week; LEFT/RIGHT toggles to All Time (loading flash first time); active label COLOR_YELLOW, inactive + `<`/`\|`/`>` separators COLOR_GRAY; ESC/ENTER exits. (UAT Test 1 — **PASS**) |
| 2 | "Last week: {INITIALS}" champion subtitle | BOARD-04 | In-repo gate is the validator tests; live behavior needs the operator's manual `get_leaderboard` Cloud Run redeploy (api-refactor spec) + real previous-week Firestore data | After redeploy, on This Week confirm gray "Last week: XXX" below the tab indicator; hidden on All Time; hidden entirely when last week has no data. (UAT Test 2 — **PASS**) |
| 3 | Full RIVAL-01 got-passed banner end-to-end (launch passer compute → banner → board-open re-baseline) | RIVAL-01 | The set-difference compute is inline in `main()` (not an importable seam — isolating it would require an impl refactor, out of scope for the auditor); end-to-end needs multiple sessions + a 2nd player passing your tracked best | Achieve a score & submit → have a 2nd player beat it → relaunch → banner names them; open board → banner clears and marker re-baselines so they are not re-reported. (UAT Test 4 — **BLOCKED**: needs a live 2nd player) |
| 4 | Cold-start / offline launch graceful degrade (~2s, no banner, no crash) | RIVAL-01 | The cold-start/offline code paths are unit-verified (`read_marker`→None, `get_leaderboard`→None), but the ~2s `BANNER_FETCH_TIMEOUT_SECONDS` bound and real OS/network behavior need a runtime | Delete `%LOCALAPPDATA%\PacMan\last_viewed.json` → launch → menu, no banner, no error. Then with a valid marker, launch offline → menu within ~2s, no banner. (UAT Test 3 — **PASS**) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify, an AST/signature gate, or a documented Manual-Only entry
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (every wave has a green pytest file)
- [x] Wave 0 covers all MISSING references (the one MISSING gap — `_format_banner` — is now `tests/test_banner_format.py`, green)
- [x] No watch-mode flags
- [x] Feedback latency < 83s
- [ ] `nyquist_compliant: true` — **not set.** All *automatable* requirements have automated verification; three behaviors (Manual-Only #1–#3) are inherently manual (headless PyGame render, live Cloud redeploy, two-player end-to-end) and cannot be automated in-repo. Phase is **validated-partial**.

**Approval:** approved 2026-06-20 (automatable coverage complete; manual items tracked in 06-HUMAN-UAT.md)

---

## Validation Audit 2026-06-20

| Metric | Count |
|--------|-------|
| Requirements audited | 3 (BOARD-03, BOARD-04, RIVAL-01) |
| Automatable gaps found | 1 (RIVAL-01 — `main._format_banner` untested) |
| Gaps resolved | 1 (`tests/test_banner_format.py`, 8 tests, green) |
| Escalated to manual-only | 3 (PyGame render · live Cloud redeploy · two-player end-to-end) |
| Full suite after fix | 146 passed, 9 skipped |
