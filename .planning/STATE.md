---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: "03-01: 4/4 tasks complete (D-14 .exe gate APPROVED) — 03-02 (BUG-01 box fix) next"
last_updated: "2026-06-12T12:30:00.000Z"
last_activity: 2026-06-12 -- Phase 03 Plan 01 COMPLETE (hygiene HYG-01..04 + human-approved .exe rebuild); Wave 2 / 03-02 next
progress:
  total_phases: 3
  completed_phases: 2
  total_plans: 11
  completed_plans: 10
  percent: 73
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-02)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Phase 03 — box-bug-fix-hygiene

## Current Position

Phase: 03 (box-bug-fix-hygiene) — EXECUTING
Plan: 2 of 2 (Wave 2 next)
Status: 03-01 COMPLETE — 4/4 tasks committed, D-14 .exe gate APPROVED; 03-02 (BUG-01) next
Last activity: 2026-06-12 -- Phase 03 Plan 01 hygiene complete: HYG-01..04 atomic commits (golden traces byte-identical after each; full suite 61 passed/9 skipped); human-verified .exe rebuild on cleaned asset tree

### 03-01 Complete (Wave 1 done)

All four hygiene tasks committed atomically (golden traces byte-identical after each; full suite green after Task 4; D-14 human .exe gate APPROVED):

| Task | HYG | Commit |
|------|-----|--------|
| 1 — pin client deps (pygame==2.6.1, pyinstaller==6.20.0) | HYG-01 | 3f827db |
| 2 — untrack settings.local.json + reconcile .gitignore + track CLAUDE.md | HYG-02 | 948fe4d |
| 3 — box-exit doc timing + drop dead Change Initials docstring | HYG-03 | 5e87bf0 |
| 4 — delete dead duplicate asset folders (+ human .exe smoke-run) | HYG-04 | 70df7d1 |

SUMMARY: `.planning/phases/03-box-bug-fix-hygiene/03-01-SUMMARY.md`. Next: **03-02 (Wave 2) — BUG-01 unify ghost-box bounds**, the one sanctioned behavior change, isolated to the box region.

Progress: [███████░░░] 73%

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

### Pending Todos

[From .planning/todos/pending/ — ideas captured during sessions]

None yet.

### Blockers/Concerns

[Issues that affect future work]

- Open question for planning: confirm a GitHub remote exists for CI (GitHub Actions) — TST-04 depends on it.
- Note: `cloud_functions/*/main.py` have uncommitted modifications; cloud-function validator tests (TST-03) should target current working-tree code.

## Deferred Items

Items acknowledged and carried forward from previous milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| *(none)* | | | |

## Session Continuity

Last session: 2026-06-12T11:14:11.315Z
Stopped at: Phase 3 context gathered
Resume file: .planning/phases/03-box-bug-fix-hygiene/03-CONTEXT.md
