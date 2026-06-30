---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Feels Right
status: Awaiting next milestone
stopped_at: v1.2 Feels Right milestone complete + archived
last_updated: "2026-06-30T00:51:01.515Z"
last_activity: 2026-06-30 — Milestone v1.2 completed and archived
progress:
  total_phases: 2
  completed_phases: 2
  total_plans: 9
  completed_plans: 9
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-30)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Planning the next milestone (likely More Fun) — run `/gsd-new-milestone`.

## Current Position

Phase: Milestone v1.2 complete
Plan: —
Status: Awaiting next milestone
Last activity: 2026-06-30 — Milestone v1.2 completed and archived

## Performance Metrics

**By Phase (shipped):**

| Phase | Milestone | Plans | Completed |
|-------|-----------|-------|-----------|
| 1-3 | v1.0 | 11 | 2026-06-12 |
| 4-7 | v1.1 | 15 | 2026-06-25 |
| 8 Fairness Pass | v1.2 | 4 | 2026-06-29 |
| 9 Arcade Juice | v1.2 | 5 | 2026-06-30 |
| Phase 08 P01 | 12min | 3 tasks | 3 files |
| Phase 08 P02 | 6min | 2 tasks | 2 files |
| Phase 08 P03 | 4min | 1 tasks | 2 files |
| Phase 08 P04 | 26min | 3 tasks | 17 files |
| Phase 09 P01 | 6min | 3 tasks | 5 files |
| Phase 09 P02 | 4min | 2 tasks | 1 files |
| Phase 09 P03 | 5min | 2 tasks | 2 files |
| Phase 09 P04 | 2min | 2 tasks | 2 files |

## Accumulated Context

### Decisions

Full decision log in PROJECT.md (Key Decisions); v1.2 detail archived in `milestones/v1.2-ROADMAP.md`.

**Standing constraints (carry into every future milestone):**

- **Ghost decision logic is the spec — never change it silently.** Targeting / per-ghost `*_PROFILE`s
  stay byte-identical; only *outcomes* may move, and only as a sanctioned, isolated, oracle-scoped
  change. Held through v1.0 (box-fix), v1.2 (fairness) — `ghost.py` untouched.

- **Golden net is the merge gate on `main`** (9 traces + 15 micro tests + frame-hash + determinism
  guard). Re-bless **only on Linux/Docker, never Windows**, and batch behavior changes behind **one**
  re-bless (never per-change).

- **Juice firewall ships cosmetics for free.** Any visual/audio effect gated behind `Game.juice`
  (default `False`, the path goldens/frame-hash replays run) stays byte-identical → no re-bless. Proven
  by v1.2 FEEL-01/02/04/05.

### Pending Todos

None.

### Blockers/Concerns

- **OPERATOR (carried from v1.1) — flip `REQUIRE_SIGNATURE` to `true` on the `pacman` Cloud Run
  service** once signed clients have propagated (D-02); keep the HMAC secret backed up. Unrelated to
  v1.2 code but still open.

- [Out-of-scope, pre-existing] pygame vs pygame-ce gaussian_blur conflict: requirements.txt pins pygame-ce==2.5.7 (has gaussian_blur) but requirements-dev.txt pins pygame==2.6.1 (lacks it, installed last) -> 12 UI/juice/theme render tests fail in CI env (theme.py:45). Not a fairness regression; reconcile the pygame pin. See 08 deferred-items.md.

## Deferred Items

Carried forward (no new deferrals at v1.2 close; the pygame/pygame-ce pin conflict remains open under Blockers/Concerns):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| uat | Phase 06 — Test 4: live 2-player got-passed E2E (needs a 2nd live player; code paths unit-verified) | partial | v1.1 close (2026-06-27) |
| verification | Phase 06 — 2-player E2E + BOARD-04 live `scope=last_week` redeploy (inherently manual) | human_needed | v1.1 close (2026-06-27) |
| verification | Phase 02 — D-19 before/after GIF gate (human visual seal on the refactor) | human_needed | v1.0 close (2026-06-12) |

## Session Continuity

Last session: 2026-06-30 — v1.2 Feels Right milestone completed and archived
Stopped at: Milestone close (ROADMAP/REQUIREMENTS archived, PROJECT.md evolved, retrospective written, tagged)
Resume file: None

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
