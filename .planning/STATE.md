---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Feels Right
status: executing
stopped_at: Phase 9 context gathered
last_updated: "2026-06-29T23:14:46.604Z"
last_activity: 2026-06-29 -- Phase 09 execution started
progress:
  total_phases: 2
  completed_phases: 1
  total_plans: 9
  completed_plans: 5
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-29)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Phase 09 — arcade-juice

## Current Position

Phase: 09 (arcade-juice) — EXECUTING
Plan: 2 of 5
Status: Ready to execute
Last activity: 2026-06-29 -- Phase 09 execution started

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**By Phase (shipped):**

| Phase | Milestone | Plans | Completed |
|-------|-----------|-------|-----------|
| 1-3 | v1.0 | 11 | 2026-06-12 |
| 4-7 | v1.1 | 15 | 2026-06-25 |
| 8 Fairness Pass | v1.2 | TBD | - |
| 9 Arcade Juice | v1.2 | TBD | - |
| Phase 08 P01 | 12min | 3 tasks | 3 files |
| Phase 08 P02 | 6min | 2 tasks | 2 files |
| Phase 08 P03 | 4min | 1 tasks | 2 files |
| Phase 08 P04 | 26min | 3 tasks | 17 files |
| Phase 09 P01 | 6min | 3 tasks | 5 files |

## Accumulated Context

### Decisions

Full decision log in PROJECT.md (Key Decisions). Standing constraints governing v1.2:

- **Ghost decision logic is the spec — never change it silently.** v1.2 fairness may move ghost
  *outcomes* (positions, who-catches-whom) but the targeting / per-ghost `*_PROFILE`s stay
  byte-identical. Treat like the v1.0 Phase-3 box-fix: sanctioned, isolated, oracle-scoped.

- **Golden net is the merge gate on `main`** (9 traces + 15 micro tests + frame-hash + determinism
  guard). Re-bless **only on Linux/Docker, never Windows.** Phase 8 batches all 3 FAIR-* behavior
  changes behind **one** re-bless (never per-change).

- **Frame-hash net hashes PIXELS** (`sha256(tobytes(surface,'RGB'))`). Phase 9's juice rides the
  **existing juice firewall** (`Game.juice`, default `False`; golden/frame-hash replays run
  `juice=False`) → FEEL-* ship with **no re-bless** if every effect is gated behind the firewall.

- [Phase ?]: FAIR-01/02 implemented entirely in game.py; ghost.py left byte-identical (oracle-scoped)
- [Phase ?]: Golden-trace re-bless deferred to a Linux/Docker pass after D-10; 10 baseline traces intentionally diverge
- [Phase ?]: Phase 8 closed with one Linux/Docker golden-net re-bless (pygame 2.6.1) covering FAIR-01/02/03 under dialed constants 24/40/20/6; ghost.py byte-identical; death/ghost_eat terminals re-verified (no input re-authoring)
- [Phase ?]: 09-01: Phase-9 FEEL test net + pure-int settings dials stood up golden-safe (no re-bless); RED feature tests target 09-02/03/04 symbols, GREEN guards pin FEEL-02/05

### Pending Todos

None.

### Blockers/Concerns

- **[Phase 9 risk] eat-ghost "brief freeze" (FEEL-02) must not alter the deterministic sim under
  `juice=False`** — a timing shift would break the `ghost_eat`/`death` golden traces. Keep the freeze
  (and the death animation, FEEL-01) gated behind the juice firewall. `eat_freeze*` state scaffolding
  already exists in game.py (lines 82-85) — wire it juice-gated.

- **OPERATOR (carried from v1.1) — flip `REQUIRE_SIGNATURE` to `true` on the `pacman` Cloud Run
  service** once signed clients have propagated (D-02); keep the HMAC secret backed up. Unrelated to
  v1.2 code but still open.

- [Out-of-scope, pre-existing] pygame vs pygame-ce gaussian_blur conflict: requirements.txt pins pygame-ce==2.5.7 (has gaussian_blur) but requirements-dev.txt pins pygame==2.6.1 (lacks it, installed last) -> 12 UI/juice/theme render tests fail in CI env (theme.py:45). Not a fairness regression; reconcile the pygame pin. See 08 deferred-items.md.

## Deferred Items

Carried forward (unchanged at v1.2 start):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| uat | Phase 06 — Test 4: live 2-player got-passed E2E (needs a 2nd live player; code paths unit-verified) | partial | v1.1 close (2026-06-27) |
| verification | Phase 06 — 2-player E2E + BOARD-04 live `scope=last_week` redeploy (inherently manual) | human_needed | v1.1 close (2026-06-27) |
| verification | Phase 02 — D-19 before/after GIF gate (human visual seal on the refactor) | human_needed | v1.0 close (2026-06-12) |

## Session Continuity

Last session: 2026-06-29T23:14:46.596Z
Stopped at: Phase 9 context gathered
Resume file: .planning/phases/09-arcade-juice/09-CONTEXT.md

## Operator Next Steps

- Plan the first v1.2 phase: `/gsd-plan-phase 8`

</content>
