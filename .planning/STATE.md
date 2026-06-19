---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: More Competitive
status: executing
stopped_at: Phase 6 UI-SPEC approved
last_updated: "2026-06-19T17:41:12.914Z"
last_activity: 2026-06-19 -- Phase 06 execution started
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 11
  completed_plans: 7
  percent: 50
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-14)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Phase 06 — in-game-weekly-boards-got-passed-banner

## Current Position

Phase: 06 (in-game-weekly-boards-got-passed-banner) — EXECUTING
Plan: 1 of 4
Status: Executing Phase 06
Last activity: 2026-06-19 -- Phase 06 execution started

Progress (Phase 4 plans): [██████████] 4/4 (100%)

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
| Phase 04 P04 | operator-paced | 3 tasks | 1 file |

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
- [Phase 4]: Plan 04-04: the two functions are Cloud Run services (pacman=submit_score, get-leaderboard=get_leaderboard), deployed via `gcloud run deploy --source --function=<entrypoint>` from Cloud Shell — NOT GCF API objects / Console clicks (equivalent outcome; faster path recorded in DEPLOY.md)
- [Phase 4]: Plan 04-04: both services LIVE (revisions pacman-00005-7rk, get-leaderboard-00003-fzk, 100% traffic); secret leaderboard-hmac-secret referenced as LEADERBOARD_HMAC_SECRET on both; REQUIRE_SIGNATURE=false on pacman (grace, flip true after Phase 5 ships); max-instances=5 both (D-11); weekly composite index week_id ASC/score DESC Enabled (id CICAgOjXh4EK). Smoke: 401 on bogus sig, 200 {"entries":[]} weekly, 200 all-time {initials,score}

### Pending Todos

None.

### Blockers/Concerns

- **Phase 4 prerequisite — RESOLVED (2026-06-19):** `cloud_functions/` working tree was clean at
  execution start (no uncommitted main.py mods). TST-03 validators stayed green (baseline 21 passed →
  full suite 88 passed/9 skipped after plans 01-03).

- **RESOLVED (2026-06-19) — Phase 4 live deploy (04-04 Tasks 2-3):** Both Cloud Run services are now
  LIVE. Operator (via Cloud Shell) confirmed Secret Manager secret `leaderboard-hmac-secret`, granted
  `roles/secretmanager.secretAccessor` to the runtime SA, referenced it as `LEADERBOARD_HMAC_SECRET` on
  both services, set `REQUIRE_SIGNATURE=false` on `pacman`, set `--max-instances=5` on both, created the
  `weekly` composite index (`week_id ASC, score DESC`, id `CICAgOjXh4EK`, Enabled), and redeployed both
  (revisions `pacman-00005-7rk`, `get-leaderboard-00003-fzk`). Smoke checks passed (401 bogus sig; 200
  weekly `{"entries":[]}`; 200 all-time `{initials,score}`). Phase 4 plans 4/4 complete; phase
  verification runs next.

- **CARRY TO PHASE 5 — HMAC secret + grace-flag flip:** Phase 5 client build must embed the identical
  `leaderboard-hmac-secret` value (operator's safe copy). After the signed client ships and friends
  update, flip `REQUIRE_SIGNATURE` to `true` on `pacman` (D-02).

## Deferred Items

Items acknowledged and carried forward from v1.0 milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| verification | Phase 02 D-19 before/after GIF gate (human visual seal on the refactor) | human_needed | v1.0 close (2026-06-12) |
| uat | Phase 02 02-HUMAN-UAT.md — D-19 GIF scenario | pending | v1.0 close (2026-06-12) |

## Session Continuity

Last session: 2026-06-19T16:48:02.782Z
Stopped at: Phase 6 UI-SPEC approved
Resume file: .planning/phases/06-in-game-weekly-boards-got-passed-banner/06-UI-SPEC.md

## Operator Next Steps

- Phase 04 plans 4/4 complete and the hardened server is LIVE. Phase verification runs next (orchestrator).
- Keep the `leaderboard-hmac-secret` value safe — Phase 5 client build embeds the identical string.
- After Phase 5 signed client ships and friends update, flip `REQUIRE_SIGNATURE` to `true` on `pacman` (D-02).
