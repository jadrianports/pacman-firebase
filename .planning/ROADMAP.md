# Roadmap: Pac-Man (pacman-firebase)

## Milestones

- ✅ **v1.0 Solid Foundation** — Phases 1-3 (shipped 2026-06-12)
- ✅ **v1.1 More Competitive** — Phases 4-7 (shipped 2026-06-26)
- ✅ **v1.2 Feels Right** — Phases 8-9 (shipped 2026-06-30)
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

<details>
<summary>✅ v1.2 Feels Right (Phases 8-9) — SHIPPED 2026-06-30</summary>

Made the game feel fair and alive without touching a single ghost personality: corner-kiss catches
are gone (integer center-to-center collision vs `GHOST_CATCH_DISTANCE`), cornering registers a few
pixels early, and the missing arcade juice (death wedge-spin, eat-ghost points popup, frightened-end
white blink, READY! beat) all rides the existing juice firewall (`Game.juice`) so it shipped with
**no golden re-bless**. The three FAIR-* behavior changes batched behind one deliberate Linux/Docker
re-bless; `ghost.py` held byte-identical throughout. FEEL-03 (eat-ghost sound) was cut/descoped.
FAIR-02 ships as a tunable no-op (player dialed chase ghosts to 2.0 px/frame per the D-10 playtest —
escape is cornering-based, not speed-based). Full detail archived in
[`milestones/v1.2-ROADMAP.md`](milestones/v1.2-ROADMAP.md).

- [x] Phase 8: Fairness Pass (4/4 plans) — completed 2026-06-29
- [x] Phase 9: Arcade Juice (5/5 plans) — completed 2026-06-30

</details>

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
| 9. Arcade Juice | v1.2 | 5/5 | Complete    | 2026-06-30 |
</content>
</invoke>
