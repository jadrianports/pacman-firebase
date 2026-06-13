---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: More Competitive
status: executing
stopped_at: Phase 4 context gathered
last_updated: "2026-06-13T19:25:56.509Z"
last_activity: 2026-06-14 — v1.1 roadmap created (Phases 4-7)
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-14)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Phase 4 — Server Hardening & Weekly Data Model

## Current Position

Phase: 4 of 7 (Server Hardening & Weekly Data Model) — first phase of v1.1
Plan: — (roadmap created, phase not yet planned)
Status: Ready to execute
Last activity: 2026-06-14 — v1.1 roadmap created (Phases 4-7)

Progress: [░░░░░░░░░░] 0%

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

### Pending Todos

None.

### Blockers/Concerns

- **Phase 4 prerequisite:** `cloud_functions/*/main.py` may carry uncommitted working-tree
  modifications (flagged at v1.0 close). Reconcile/commit that state BEFORE modifying the functions,
  and keep the v1.0 cloud-function validator tests (TST-03) green against the reconciled baseline.

## Deferred Items

Items acknowledged and carried forward from v1.0 milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| verification | Phase 02 D-19 before/after GIF gate (human visual seal on the refactor) | human_needed | v1.0 close (2026-06-12) |
| uat | Phase 02 02-HUMAN-UAT.md — D-19 GIF scenario | pending | v1.0 close (2026-06-12) |

## Session Continuity

Last session: 2026-06-13T18:45:23.898Z
Stopped at: Phase 4 context gathered
Resume file: .planning/phases/04-server-hardening-weekly-data-model/04-CONTEXT.md

## Operator Next Steps

- Plan the first phase with `/gsd-plan-phase 4`
