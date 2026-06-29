---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: Feels Right
status: planning
last_updated: "2026-06-29T08:44:29.673Z"
last_activity: 2026-06-29
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-06-27)

**Core value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.
**Current focus:** Planning next milestone (More Fun) — run `/gsd-new-milestone`. v1.0 and v1.1 both shipped.

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-06-29 — Milestone v1.2 started

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
| Phase 07 P01 | 2min | 2 tasks | 5 files |
| Phase 07 P02 | 5min | 2 tasks | 2 files |
| Phase 07 P03 | 9min | 2 tasks | 5 files |

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
- [Phase ?]: Plan 07-01: index.html fixes the DOM hook contract (.wordmark, nav#tabbar > button.tab[data-scope], #subtitle[hidden], ol#board, button#refresh, #hint) so Plan 02 app.js + Plan 03 styles.css attach independently in parallel wave 2
- [Phase ?]: Plan 07-01: tab DOM order mirrors in-game 'This Week | All Time' but tab--active defaults to All Time (D-08 web divergence); Press Start 2P self-hosted via @font-face (D-16 zero-tracking, no Google Fonts/preconnect)
- [Phase ?]: Plan 07-01: single root firebase.json, hosting-only, public=web/public (T-07-02 root key never deployable); .firebaserc default=pacman-firebase enables one-command firebase deploy --only hosting (D-15)
- [Phase 7]: Plan 07-02: app.js = no-dep ESM; fetchEntries mirrors api_service null=offline sentinel; lazy per-view cache (UNFETCHED Symbol), All Time on load (D-08), This Week+last-week lazy on toggle (D-11), Refresh re-pulls active view only (D-10)
- [Phase 7]: Plan 07-02: boardMarkup returns escaped HTML string (node-testable; escapeHtml on all API data = T-07-01 XSS mitigation); rank-1 gets rank-row--first; subtitle hides when no champion (D-09)
- [Phase ?]: Web leaderboard styled via frontend-design skill (D-05): retro-arcade, yellow reserved to 4 uses, pellet dot-leaders, self-hosted Press Start 2P TTF (D-16 zero-tracking)

### Pending Todos

None.

### Blockers/Concerns

All v1.1 execution blockers resolved at milestone close. Standing operator note carried forward:

- **OPERATOR — flip `REQUIRE_SIGNATURE` to `true` on `pacman`:** the hardened server shipped in grace
  mode (`REQUIRE_SIGNATURE=false`) so pre-signing clients weren't locked out. Now that the signed client
  (Phase 5) has shipped and friends have updated, flip it to `true` on the `pacman` Cloud Run service to
  reject all unsigned submissions (D-02). The HMAC secret (`leaderboard-hmac-secret`) must stay backed up.

## Deferred Items

Items acknowledged and deferred at milestone close on 2026-06-27 (v1.1):

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| uat | Phase 06 06-HUMAN-UAT.md — Test 4: live 2-player got-passed E2E (needs a 2nd live player; code paths unit-verified) | partial | v1.1 close (2026-06-27) |
| verification | Phase 06 06-VERIFICATION.md — 2-player E2E + BOARD-04 live `scope=last_week` redeploy (inherently manual, can't be automated in-repo) | human_needed | v1.1 close (2026-06-27) |

Carried forward from v1.0 milestone close:

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| verification | Phase 02 D-19 before/after GIF gate (human visual seal on the refactor) | human_needed | v1.0 close (2026-06-12) |
| uat | Phase 02 02-HUMAN-UAT.md — D-19 GIF scenario | pending | v1.0 close (2026-06-12) |

## Session Continuity

Last session: 2026-06-25T21:59:54.285Z
Stopped at: Phase 7 UI-SPEC approved
Resume file: .planning/phases/07-web-leaderboard-page/07-UI-SPEC.md

## Operator Next Steps

- Start the next milestone with /gsd-new-milestone
