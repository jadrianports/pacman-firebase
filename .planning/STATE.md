---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: More Competitive
status: executing
stopped_at: Phase 04 plans 01-03 complete & green; 04-04 deploy deferred at human-verify checkpoint
last_updated: "2026-06-19"
last_activity: 2026-06-19 -- Phase 04 executed (plans 01-03 done); 04-04 live Console deploy deferred by operator
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 4
  completed_plans: 3
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-14)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Phase 04 — server-hardening-weekly-data-model

## Current Position

Phase: 04 (server-hardening-weekly-data-model) — EXECUTING (paused at deploy checkpoint)
Plan: 04-04 of 4 — DEPLOY.md authored; Console deploy (Tasks 2-3) deferred by operator
Status: Code complete & green (01-03 verified); live Cloud Console deploy not yet done
Last activity: 2026-06-19 -- plans 01-03 complete; 04-04 deploy deferred

Progress (plans): [███████░░░] 3/4 (75%)

## Performance Metrics

**By Phase:**

| Phase | Plans | Completed |
|-------|-------|-----------|
| 01 Test Safety Net | 7 | 2026-06-11 |
| 02 Safe Refactor | 2 | 2026-06-12 |
| 03 Box-Bug Fix + Hygiene | 2 | 2026-06-12 |
| 04 Server Hardening & Weekly Data Model | TBD | - |
| 05 Client Identity Hardening | TBD | - |
| 06 In-Game Weekly Boards & Got-Passed Banner | TBD | - |
| 07 Web Leaderboard Page | TBD | - |
| Phase 04 P01 | 12min | 2 tasks | 3 files |
| Phase 04 P02 | 10min | 2 tasks | 2 files |
| Phase 04 P03 | 8min | 1 tasks | 2 files |

## Accumulated Context

### Decisions

Full decision log lives in PROJECT.md (Key Decisions) and the archived
`.planning/milestones/v1.0-ROADMAP.md`. Standing decisions that still constrain v1.1 work:

- Ghost-AI **decision behavior is the spec** — never change it silently. This milestone is
  leaderboard/Cloud-Functions/UI work only and must NOT touch ghost-AI decision behavior.

- Any change must stay CI-green behind the golden net (9 traces + 15 micro tests + frame-hash +
  determinism guard) before merge — it's a merge gate on `main`. Golden traces re-bless on Linux/CI
  only, never Windows.

- Anti-cheat altitude: HMAC signing + server-side verification + score sanity ceiling, NOT full
  replay-verification. Permanent initials enforced server-side (locked on first submit).

- HMAC is one mechanism split across two phases: server verifies (COMP-01, Phase 4) ↔ client signs
  (IDENT-03, Phase 5), sharing one secret that lives in both the Cloud Functions and the client build.

- [Phase ?]: Plan 04-01: Locked canonical JSON kwargs (sort_keys, compact separators, ensure_ascii=False) as the Phase 5 client wire-format contract
- [Phase ?]: Plan 04-01: HMAC secret read at call time; machine_id+initials+score bound into signed payload; constant-time compare_digest
- [Phase ?]: Plan 04-02: MAX_SCORE lowered to 50_000; HMAC grace gate (invalid always 401, missing rejected only when REQUIRE_SIGNATURE on)
- [Phase ?]: Plan 04-02: permanent initials locked server-side; weekly doc {machine_id}_{week_id} only-if-higher from server time; two-weeks-back lazy prune; is_new_best stays all-time
- [Phase ?]: Plan 04-03: get_leaderboard scope-aware (?scope=week|all); default+unknown -> week; weekly path filters week_id==current_week_id(); {initials,score}-only projection on both scopes (D-10)

### Pending Todos

None.

### Blockers/Concerns

- **Phase 4 prerequisite — RESOLVED (2026-06-19):** `cloud_functions/` working tree was clean at
  execution start (no uncommitted main.py mods). TST-03 validators stayed green (baseline 21 passed →
  full suite 88 passed/9 skipped after plans 01-03).
- **OPEN — Phase 4 live deploy (04-04 Tasks 2-3, deferred by operator 2026-06-19):** The hardened
  code is committed but NOT yet live. Manual Google Cloud Console steps remain (see
  `cloud_functions/DEPLOY.md`): create Secret Manager secret `leaderboard-hmac-secret` + reference as
  `LEADERBOARD_HMAC_SECRET` on both functions, set `REQUIRE_SIGNATURE=false` grace flag, set
  max-instances 3-5, create `weekly` composite index (`week_id ASC, score DESC`), redeploy both
  functions in asia-southeast1, run smoke checks. Phase 4 stays in-progress until done.
  Resume: `/gsd-execute-phase 4` (re-enters 04-04 at the Task 2 checkpoint).

## Deferred Items

Items acknowledged and carried forward from v1.0 milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| verification | Phase 02 D-19 before/after GIF gate (human visual seal on the refactor) | human_needed | v1.0 close (2026-06-12) |
| uat | Phase 02 02-HUMAN-UAT.md — D-19 GIF scenario | pending | v1.0 close (2026-06-12) |

## Session Continuity

Last session: 2026-06-19
Stopped at: Phase 04 — plans 01-03 complete & green; 04-04 deploy deferred at human-verify checkpoint (Task 2)
Resume file: .planning/phases/04-server-hardening-weekly-data-model/04-04-PLAN.md (Tasks 2-3 = Console deploy)

## Operator Next Steps

- When ready to deploy: follow `cloud_functions/DEPLOY.md`, then `/gsd-execute-phase 4` to close 04-04
  and run phase verification (re-enters at the Task 2 human-verify checkpoint).
- Phase 4 is NOT complete until the live deploy checkpoints are approved.
