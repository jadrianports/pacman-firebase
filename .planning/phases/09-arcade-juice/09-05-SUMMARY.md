---
phase: 09-arcade-juice
plan: 05
subsystem: testing
tags: [pytest, golden-traces, frame-hash, determinism, playtest]

requires:
  - phase: 09-01
    provides: failing-test net + FEEL tunables + FEEL-02/05 regression guards
  - phase: 09-02
    provides: FEEL-01 death wedge (juice-gated)
  - phase: 09-03
    provides: FEEL-04 frightened-end white blink (juice-gated)
provides:
  - SC5 sign-off — full deterministic suite green with NO --bless
  - Human playtest sign-off — death cadence (D-04) + blink readability (D-07) approved
affects: [milestone-feels-right-signoff]

tech-stack:
  added: []
  patterns: [phase-gate = full pytest green with no re-bless]

key-files:
  created:
    - .planning/phases/09-arcade-juice/09-05-SUMMARY.md
  modified: []

key-decisions:
  - "FEEL-03 (eat-ghost sound) CUT/descoped — sourcing+licensing a .wav judged not worth the chore; 09-04 audio wiring reverted (commit 1e7aa84)"
  - "Playtest sign-off accepted on death cadence + blink readability; exe-build check folded into the user's approval"

patterns-established:
  - "Golden gate: SC5 success signal = `.venv/Scripts/python.exe -m pytest -q` green with NO --bless"

requirements-completed: [FEEL-02, FEEL-05]

duration: 1min
completed: 2026-06-30
---

# Phase 9: Arcade Juice — Plan 05 (Sign-off) Summary

**SC5 golden gate green with no re-bless, FEEL-03 eat-ghost sound cut/descoped, and the death-cadence + blink-readability playtest human-approved**

## Performance

- **Duration:** ~1 min (verification + sign-off; FEEL-03 removal tracked in commit 1e7aa84)
- **Completed:** 2026-06-30
- **Tasks:** 2 (Task 1 auto; Task 2 human-verify)
- **Files modified:** 0 (verification-only plan)

## Accomplishments
- **SC5 satisfied:** deterministic gate green with NO `--bless` — golden state traces + frame-hash + juice firewall + determinism guard + `test_feel_regression` (FEEL-02 + FEEL-05) all pass.
- **Playtest signed off:** human-approved death cadence (D-04, wedge ends ~when `death.wav` ends) and blink readability (D-07, white blink reads clearly in the last ~2s).
- **FEEL-03 descoped:** eat-ghost sound removed rather than sourcing/licensing a `.wav` (see Deviations).

## Verification Evidence
- Interpreter: **Python 3.12.10** (`.venv/Scripts/python.exe`), local Windows.
- Deterministic subset: `pytest tests/test_golden_traces.py tests/test_frame_hash.py tests/test_juice_firewall.py tests/test_determinism_guard.py tests/test_feel_regression.py -q` → **26 passed, 9 skipped**.
- Full suite: `pytest -q` → **190 passed, 9 skipped**.
- **frame-hash:** the 9 skips are the pixel frame-hash tests, which skip on local Windows `.venv` and assert only on Linux CI (by design). No `--bless` was used anywhere.

## Files Created/Modified
- `.planning/phases/09-arcade-juice/09-05-SUMMARY.md` — this summary (no code/asset artifacts; verification-only plan).

## Decisions Made
- **FEEL-03 cut.** Rather than source + license a `.wav`, the eat-ghost sound feature was removed entirely. Audio is firewall-exempt, so the revert is golden-safe.
- **Playtest acceptance.** User ran `main.py` (juice=True) and approved cadence + blink. The exe-build (A4) item is covered by that approval; `build.py` was not separately re-run this session.

## Deviations from Plan

### Scope change (user-directed)
**1. FEEL-03 eat-ghost sound cut/descoped**
- **Found during:** Plan 09-05 checkpoint (the `.wav` human-action gate)
- **Issue:** The only remaining blocker was sourcing/licensing a `.wav`; user directed full removal of the feature.
- **Fix:** Reverted 09-04 wiring — `sound.py` (loader, `Channel(2)`, `play_eat_ghost()`), `game.py` (bite call); deleted `tests/test_eat_ghost_sound.py`; marked FEEL-03 **Cut** in REQUIREMENTS/ROADMAP; rewrote 09-05-PLAN to drop the `.wav` task + eat-sound dial.
- **Files modified:** sound.py, game.py, tests/test_eat_ghost_sound.py (deleted), .planning/REQUIREMENTS.md, .planning/ROADMAP.md, 09-05-PLAN.md
- **Verification:** No `.py` references to eat_ghost remain; full suite 190 passed / 9 skipped, golden-safe.
- **Committed in:** `1e7aa84` (revert(09-04): cut FEEL-03 eat-ghost sound)

---

**Total deviations:** 1 (user-directed scope change)
**Impact on plan:** FEEL-03 removed from milestone scope; all other FEEL behaviors (01/02/04/05) intact and green.

## Issues Encountered
None.

## User Setup Required
None — the `.wav` asset requirement that previously needed user setup was cut.

## Next Phase Readiness
- Phase 9 deliverables (FEEL-01, FEEL-02, FEEL-04, FEEL-05) complete and golden-safe; FEEL-03 cut.
- Milestone v1.2 "Feels Right" sign-off ready.

---
*Phase: 09-arcade-juice*
*Completed: 2026-06-30*
