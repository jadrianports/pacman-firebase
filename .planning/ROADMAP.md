# Roadmap: Pac-Man (pacman-firebase)

## Milestones

- ✅ **v1.0 Solid Foundation** — Phases 1-3 (shipped 2026-06-12)
- ✅ **v1.1 More Competitive** — Phases 4-7 (shipped 2026-06-26)
- 🚧 **v1.2 Feels Right** — Phases 8-9 (in progress)
- 📋 **More Fun** — gameplay depth (planned)
- 📋 **Multiplayer** — asymmetric 1v4 (planned)
- 📋 **Easier to Share** — web/cross-platform build (planned)

## Phases

<details>
<summary>✅ v1.0 Solid Foundation (Phases 1-3) — SHIPPED 2026-06-12</summary>

Made a precious, untested codebase safe to extend via the Cardinal Rule sequence: build a
frame-perfect safety net → byte-identical refactor behind the net → one isolated, sanctioned
behavior change (the ghost-box bounds fix) + hygiene. Full detail archived in
[`milestones/v1.0-ROADMAP.md`](milestones/v1.0-ROADMAP.md).

- [x] Phase 1: Test Safety Net (7/7 plans) — completed 2026-06-11
- [x] Phase 2: Safe Refactor (2/2 plans) — completed 2026-06-12
- [x] Phase 3: Box-Bug Fix + Hygiene (2/2 plans) — completed 2026-06-12

</details>

<details>
<summary>✅ v1.1 More Competitive (Phases 4-7) — SHIPPED 2026-06-26</summary>

Made the leaderboard trustworthy and alive: the Cloud Functions became the real enforcement
boundary (HMAC verification, sanity ceiling, server-locked permanent initials, week-bucketed
scores), the client signs submissions and stores a tamper-evident identity, and the weekly
competition surfaces both in-game (This Week / All Time, last-week champion, got-passed banner)
and on a public mobile-first web page. Full detail archived in
[`milestones/v1.1-ROADMAP.md`](milestones/v1.1-ROADMAP.md).

- [x] Phase 4: Server Hardening & Weekly Data Model (4/4 plans) — completed 2026-06-19
- [x] Phase 5: Client Identity Hardening (3/3 plans) — completed 2026-06-19
- [x] Phase 6: In-Game Weekly Boards & Got-Passed Banner (4/4 plans) — completed 2026-06-19
- [x] Phase 7: Web Leaderboard Page (4/4 plans) — completed 2026-06-25

</details>

### 🚧 v1.2 Feels Right (In Progress)

**Milestone Goal:** Make the game feel fair and alive — fix the unfair corner-kiss catches, let the
player actually escape, and add the arcade juice that's missing. No new content, no multiplayer:
pure game feel. Fairness changes alter ghost *outcomes* (positions, who-catches-whom) but **never**
ghost *decision logic* (targeting/profiles stay byte-identical) — the precious core value is held.

**Sequencing rationale:** Two phases, derived from two distinct risk classes. Phase 8 batches all
three behavior changes (the FAIR-* items, pinned by the CI golden net) so a **single** deliberate
re-bless on Linux/Docker covers all of them — the established v1.0 Phase-3 box-fix pattern (isolated,
oracle-scoped, sanctioned change, re-bless once, never per-change, never on Windows). Phase 9 is
purely cosmetic and rides the **existing juice firewall** (`Game.juice`, default `False`; golden +
frame-hash replays run `juice=False` and stay byte-identical), so the FEEL-* items ship with **no
re-bless** — provided every effect (including the eat-ghost freeze) is gated behind that firewall.

#### Phase 8: Fairness Pass

**Goal**: The player can actually escape — corner-kiss catches are gone, Pac-Man outpaces the ghosts, and corners turn smoothly — all without changing a single ghost personality.
**Depends on**: Phase 7 (golden net + frame-hash manifests already the merge gate on `main`)
**Requirements**: FAIR-01, FAIR-02, FAIR-03
**Success Criteria** (what must be TRUE):

  1. A ghost passing diagonally past a corner no longer catches the player — a catch registers only when the two are genuinely adjacent, using center-to-center distance instead of the old 40×40/36×36 bounding-box overlap (`player_circle.colliderect(ghost.rect)`). (FAIR-01)
  2. On a straightaway the player visibly pulls away from a chasing ghost, and even at the high speed tier the ghosts never become an unbeatable ×2 — escape is always possible (Pac-Man a hair faster than ghosts; the ramp-to-4 tier retuned). (FAIR-02)
  3. Inputting a turn a few pixels before a junction rounds the corner smoothly instead of overshooting it (a pre-turn cornering window on the existing input buffer). (FAIR-03)
  4. Ghost **decision logic is byte-identical** — targeting and the per-ghost `*_PROFILE`s are unchanged; only outcomes (positions / who-catches-whom) move. (core-value guard)
  5. The golden net (9 traces + 15 micro tests + frame-hash + determinism guard) is green on CI again after **one** deliberate re-bless on Linux/Docker that covers all three fairness changes together — never re-blessed on Windows, never per-change.**Plans**: 4 plans

**Wave 1**

- [x] 08-01-PLAN.md - Tunables + failing test net (settings constants; player/fairness micro tests)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 08-02-PLAN.md - FAIR-01 center-distance catch + FAIR-02 escape-speed accumulator (game.py)
- [x] 08-03-PLAN.md - FAIR-03 pre-turn cornering window (player.py)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 08-04-PLAN.md - Playtest sign-off + terminal verify + single Linux/Docker re-bless

#### Phase 9: Arcade Juice

**Goal**: The game feels alive — death plays out, eating a ghost rewards you with a points popup + a distinct sound, frightened ghosts warn you they're about to turn, and every round opens on a "READY!" beat.
**Depends on**: Phase 8
**Requirements**: FEEL-01, FEEL-02, FEEL-03, FEEL-04, FEEL-05
**Success Criteria** (what must be TRUE):

  1. On death, Pac-Man plays a disintegrate/wedge animation in sync with `death.wav` before the round resets. (FEEL-01)
  2. Eating a frightened ghost floats the points earned (200/400/800/1600) at the eat location with a brief freeze, then play resumes, and a distinct eat-ghost sound plays on the bite. (FEEL-02, FEEL-03)
  3. Frightened ghosts blink white as the power-pellet timer is about to expire, signalling when it is no longer safe to chase. (FEEL-04)
  4. Each round opens on a "READY!" beat (text + brief pause) before Pac-Man and the ghosts start moving. (FEEL-05)
  5. All FEEL effects ride the existing juice firewall (`Game.juice`): the `juice=False` path stays byte-identical, so the golden state traces **and** the pixel frame-hash net stay green with **no re-bless**. In particular the eat-ghost "brief freeze" (FEEL-02) must not alter the deterministic sim under `juice=False` (a timing shift would break the `ghost_eat`/`death` goldens). (golden-safe guard)

**Plans**: TBD

### 📋 More Fun (Planned)

Gameplay depth (levels/mazes with a difficulty curve, fruit bonuses, new modes like time attack/endless);
optional **arcade-accurate ghost mode** as an opt-in toggle, never the default. (FUN-01…04) — NOT broken
into phases yet.

### 📋 Multiplayer (Planned)

Asymmetric 1v4 (one Pac-Man, human-drivable ghosts, AI bot-fill for empty slots); built as a staircase:
local couch → LAN lockstep (leveraging the deterministic engine) → online. (MP-xx) — NOT broken into
phases yet.

### 📋 Easier to Share (Planned)

Browser/web build (e.g. pygbag, play from a link with no install), cross-platform builds (macOS/Linux),
itch.io release. (SHR-01…03) — NOT broken into phases yet.

## Progress

**Execution Order:**
Phases executed in numeric order: 1 → 2 → 3 (v1.0), 4 → 5 → 6 → 7 (v1.1), 8 → 9 (v1.2)

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Test Safety Net | v1.0 | 7/7 | Complete | 2026-06-11 |
| 2. Safe Refactor | v1.0 | 2/2 | Complete | 2026-06-12 |
| 3. Box-Bug Fix + Hygiene | v1.0 | 2/2 | Complete | 2026-06-12 |
| 4. Server Hardening & Weekly Data Model | v1.1 | 4/4 | Complete | 2026-06-19 |
| 5. Client Identity Hardening | v1.1 | 3/3 | Complete | 2026-06-19 |
| 6. In-Game Weekly Boards & Got-Passed Banner | v1.1 | 4/4 | Complete | 2026-06-19 |
| 7. Web Leaderboard Page | v1.1 | 4/4 | Complete | 2026-06-25 |
| 8. Fairness Pass | v1.2 | 4/4 | Complete    | 2026-06-29 |
| 9. Arcade Juice | v1.2 | 0/TBD | Not started | - |
</content>
</invoke>
