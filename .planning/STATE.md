---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: "03-02 COMPLETE (BUG-01) — human GIF gate APPROVED; Phase 3 code-complete but NOT yet CI-green: DEFERRED Linux re-bless of ALL 9 golden traces required pre-merge (never on Windows)"
last_updated: "2026-06-12T14:30:00.000Z"
last_activity: 2026-06-12 -- Phase 03 Plan 02 (BUG-01) FINALIZED; human before/after GIF gate APPROVED; SUMMARY + tracking written; oracle proof (18,496 cmp / 1,728 in-ring / 0 out-of-ring) stands as authoritative isolation; golden re-bless of all 9 traces deferred to Linux CI
progress:
  total_phases: 3
  completed_phases: 2
  total_plans: 11
  completed_plans: 11
  percent: 80
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-02)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Phase 03 — box-bug-fix-hygiene

## Current Position

Phase: 03 (box-bug-fix-hygiene) — CODE-COMPLETE (re-bless pending)
Plan: 2 of 2 (Wave 2 — COMPLETE; human GIF gate APPROVED)
Status: 03-02 DONE (oracle a40ce4c; fix f45a712; human GIF APPROVED). Phase 3 code-complete but NOT yet CI-green — DEFERRED Linux re-bless of ALL 9 golden traces required pre-merge.
Last activity: 2026-06-12 -- BUG-01 FINALIZED; human before/after GIF gate APPROVED (change so surgical playthroughs look essentially identical = correct); SUMMARY + tracking written; oracle proof authoritative

### 03-02 COMPLETE (Wave 2)

| Task | What | Commit |
|------|------|--------|
| 1 — differential oracle + belt-check + teeth-check (D-03/04/05) | test addition, proven green | a40ce4c |
| 2 — unify GHOST_BOX_BOUNDS + repoint both importers + oracle teeth-checked then deleted (BUG-01/D-01/02) | isolated fix (geometry+game+ghost; traces STALE pending re-bless) | f45a712 |
| 3 — Claude adversarial playtest + before/after GIF (D-07/08) | playtest CLEAN; human GIF gate APPROVED | — |

SUMMARY: `.planning/phases/03-box-bug-fix-hygiene/03-02-SUMMARY.md`.

**KEY FINDING (deviation from plan expectation):** the fix correctly diverges ONLY at the box ring, but ALL 9 golden scenarios go red (not just box_edge/box_exit) — every trace shares the SAME in-ring root: inky at (400,358), frame 340, eaten-target flip [400,100]→chase-player (y=358 is in the 2px ring band between COLLISION y_lo=360 and TARGET y_lo=340). The cascade is the deterministic replay amplifying one legitimate in-ring decision.

**DEFERRED (required pre-merge, Linux-CI only — NEVER bless on Windows):** re-bless ALL 9 golden traces via `pytest tests/test_golden_traces.py --bless` on Linux/WSL/CI; confirm every diff is rooted at the frame-340 in-ring inky flip; fold the re-blessed traces into / amend onto f45a712 so history keeps ONE trace-touching commit before the Phase-3 PR goes CI-green.

### 03-01 Complete (Wave 1 done)

All four hygiene tasks committed atomically (golden traces byte-identical after each; full suite green after Task 4; D-14 human .exe gate APPROVED):

| Task | HYG | Commit |
|------|-----|--------|
| 1 — pin client deps (pygame==2.6.1, pyinstaller==6.20.0) | HYG-01 | 3f827db |
| 2 — untrack settings.local.json + reconcile .gitignore + track CLAUDE.md | HYG-02 | 948fe4d |
| 3 — box-exit doc timing + drop dead Change Initials docstring | HYG-03 | 5e87bf0 |
| 4 — delete dead duplicate asset folders (+ human .exe smoke-run) | HYG-04 | 70df7d1 |

SUMMARY: `.planning/phases/03-box-bug-fix-hygiene/03-01-SUMMARY.md`. Next: **03-02 (Wave 2) — BUG-01 unify ghost-box bounds**, the one sanctioned behavior change, isolated to the box region.

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**

- Total plans completed: 9
- Average duration: — min
- Total execution time: 0.0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 01 | 7 | - | - |
| 02 | 2 | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 02 P02-01 | 25 | 3 tasks | 13 files |
| Phase 02 P02 | 50min | 3 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Milestone]: Cardinal Rule sequencing — net (P1) → byte-identical refactor (P2) → isolated bug fix (P3). Never reorder.
- [Milestone]: Non-Goal — do not change ghost-AI decision behavior. The ONLY sanctioned behavior change is BUG-01 (unify ghost-box bounds), provably isolated to the box region.
- [Milestone]: Verification bar = "maximum paranoia" — golden traces + visual montages (Claude vision) + micro per-ghost tests + Claude playtest.
- [Milestone]: Foundation work on a `solid-foundation` branch to isolate AI-adjacent risk from `main`.
- [Phase ?]: [02-01]: REF-01 geometry centralized (TILE_*/geometry.py) proven byte-identical by check_collisions oracle + frame-hash; two box constants kept DISTINCT for Phase 3 BUG-01
- [Phase ?]: [02-01]: frame-hash manifest is Windows-authored placeholder; CI is the assertion authority — re-bless in Linux CI (pytest --bless)
- [Phase ?]: REF-02: unified data-driven ghost mover (DirectionRule + 4 *_PROFILE + named quirk hooks + _move + thin wrappers); proven byte-identical by a synthetic-exhaustive differential oracle (138k cases, caught a dir-3 ladder bug) then deleted; mutation canary attested the net
- [Phase 3]: [03-01]: Hygiene landed as 4 atomic, independently-green commits (D-09 at commit granularity) — golden traces byte-identical after each, full suite 61 passed/9 skipped; pinned pygame==2.6.1 + pyinstaller==6.20.0 (backend untouched); doc-drift fixed by editing PROSE not settings.py constants; dead *_images folders deleted (D-13); D-14 human .exe gate APPROVED — note: real distributable is dist/pacman/pacman.exe, not build/pacman/pacman.exe
- [Phase 3]: [03-02]: BUG-01 — unified GHOST_BOX_BOUNDS onto COLLISION value (350,550,360,480) (D-01); get_targets = only value change (9 refs), check_collisions byte-identical by construction. Oracle proof AUTHORITATIVE & platform-independent: 18,496 get_targets comparisons, 1,728 divergences 100% in-ring / 0 out-of-ring; check_collisions belt-check byte-identical; teeth-checked then oracle deleted in fix commit. KEY FINDING: ALL 9 golden traces diverge (not just box_edge/box_exit per D-06) — every one rooted at the SAME in-ring inky flip frame 340 (400,358), deterministic replay amplifying one legitimate ring decision. Claude playtest clean; human before/after GIF gate APPROVED. Re-bless of all 9 traces DEFERRED to Linux CI.

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- **Phase 3 NOT yet CI-green/mergeable** — DEFERRED Linux re-bless of ALL 9 golden traces required pre-merge (`pytest tests/test_golden_traces.py --bless` on Linux/WSL/CI; NEVER on Windows — float drift would corrupt masters). Confirm each diff is rooted at the frame-340 in-ring inky flip; fold/amend onto f45a712 or commit in the same PR so history keeps one trace-touching change. The oracle proof (18,496 cmp / 1,728 in-ring / 0 out-of-ring) stands as authoritative platform-independent isolation evidence until then. Golden traces are RED on Windows BY DESIGN.
- Open question for planning: confirm a GitHub remote exists for CI (GitHub Actions) — TST-04 depends on it.
- Note: `cloud_functions/*/main.py` have uncommitted modifications; cloud-function validator tests (TST-03) should target current working-tree code.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-06-12T14:30:00.000Z
Stopped at: 03-02 FINALIZED — BUG-01 complete, human GIF APPROVED; deferred Linux re-bless of all 9 traces required pre-merge
Resume file: .planning/phases/03-box-bug-fix-hygiene/03-02-SUMMARY.md
