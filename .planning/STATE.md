---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: More Competitive
status: planning
last_updated: "2026-06-13T18:12:18.810Z"
last_activity: 2026-06-13
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-12)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Planning next milestone (More Competitive)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-06-13 — Milestone v1.1 started

## Performance Metrics

**By Phase:**

| Phase | Plans | Completed |
|-------|-------|-----------|
| 01 Test Safety Net | 7 | 2026-06-11 |
| 02 Safe Refactor | 2 | 2026-06-12 |
| 03 Box-Bug Fix + Hygiene | 2 | 2026-06-12 |

## Accumulated Context

### Decisions

Full decision log lives in PROJECT.md (Key Decisions) and the archived
`.planning/milestones/v1.0-ROADMAP.md`. Standing milestone-level decisions that still constrain
future work:

- Ghost-AI **decision behavior is the spec** — never change it silently. Arcade-accurate targeting is
  only ever an opt-in toggle in the future Fun milestone (FUN-04), never a default.

- Any change to ghost AI or the game loop must stay **behind the golden net** (9 traces + 15 micro
  tests + frame-hash + determinism guard) and CI-green before merge.

- Golden traces must be re-blessed on **Linux/CI only** — never on Windows (float drift corrupts
  masters).

### Pending Todos

None.

### Blockers/Concerns

Carried into the next milestone (More Competitive — leaderboard/cloud-fn work):

- `cloud_functions/*/main.py` may have uncommitted working-tree modifications — cloud-function
  validator tests (TST-03) target current working-tree code; reconcile/commit before hardening the
  leaderboard.

- COMP-01 (anti-cheat / server-side score validation) addresses the known forgeable-score gap —
  scores are currently client-trusted.

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-06-12:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| verification | Phase 02 D-19 before/after GIF gate (human visual seal on the refactor) | human_needed | v1.0 close (2026-06-12) |
| uat | Phase 02 02-HUMAN-UAT.md — D-19 GIF scenario | pending | v1.0 close (2026-06-12) |

**Acknowledgement rationale:** Phase 2's byte-identity is mathematically proven (384k + 138k oracle
cases, 9 byte-identical golden traces, frame-hash net — 16/16 automated must-haves VERIFIED). The
D-19 GIF is only the human-readable seal; Phase 3's human before/after GIF gate — which runs on top
of the refactored AI — was already APPROVED, so the refactored ghosts have effectively been eyeballed
and signed off.

## Session Continuity

Last session: 2026-06-12 — milestone v1.0 close
Stopped at: Milestone v1.0 (Solid Foundation) completed, archived, and tagged
Resume file: .planning/MILESTONES.md

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
