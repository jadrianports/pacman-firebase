# Roadmap: Pac-Man (pacman-firebase)

## Milestones

- ✅ **v1.0 Solid Foundation** — Phases 1-3 (shipped 2026-06-12)
- 🚧 **v1.1 More Competitive** — Phases 4-7 (in progress)
- 📋 **More Fun** — gameplay depth (planned)
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

### 🚧 v1.1 More Competitive (In Progress)

**Milestone Goal:** Make the leaderboard something friends actually compete on — trustworthy enough
that scores can't be casually forged, and alive enough that people keep fighting over it.

**Build order rationale:** All three competitive features ride on **one backend change** — scores
bucketed by week + a scope-aware `get_leaderboard`. So the server data-model + anti-cheat work lands
first (Phase 4); the client then signs its submissions to satisfy the server's HMAC check and grows
the in-game weekly UI + got-passed banner (Phases 5-6); the web page, a pure consumer of the finished
API, comes last (Phase 7).

**Phase Numbering:**

- Integer phases (4, 5, 6, 7): Planned milestone work (continues from v1.0's Phase 3)
- Decimal phases (e.g. 4.1): Urgent insertions (marked INSERTED)

- [x] **Phase 4: Server Hardening & Weekly Data Model** — Reconcile the Cloud Functions, then make the server the enforcement boundary: HMAC verification, sanity ceiling, permanent initials, week-bucketed scores + a scope-aware leaderboard API. (completed 2026-06-19 — server live & enforcing; verified)
- [x] **Phase 5: Client Identity Hardening** — Relocate identity files out of the game folder, store them obfuscated, and HMAC-sign them so the client detects tampering and its submissions pass the server's signature check end-to-end. (completed 2026-06-19 — 3/3 plans; verified 4/4 after closing 2 no-secret graceful-degrade blockers)
- [x] **Phase 6: In-Game Weekly Boards & Got-Passed Banner** — Surface the scoped API in-game: This Week / All Time toggle, last week's champion, and a launch banner naming whoever passed your score. (completed 2026-06-19)
- [ ] **Phase 7: Web Leaderboard Page** — A public, mobile-first Firebase Hosting page that mirrors the in-game This Week / All Time boards by consuming the existing API.

## Phase Details

### Phase 4: Server Hardening & Weekly Data Model

**Goal**: The Cloud Functions become the real enforcement boundary and the single source of weekly/all-time score data that every other feature consumes.
**Depends on**: Phase 3 (v1.0 close) — must reconcile uncommitted `cloud_functions/*/main.py` working-tree changes first
**Requirements**: COMP-01, COMP-02, COMP-03, BOARD-01, BOARD-02
**Success Criteria** (what must be TRUE):

  1. A submission whose HMAC signature is missing or invalid (e.g. a raw `curl` post) is rejected and does not appear on any board.
  2. A score above the sanity ceiling is rejected as impossible and is not recorded.
  3. Once a machine has submitted initials, a later submission cannot change those initials — the original initials are retained.
  4. Submitted scores are bucketed by week (Monday 00:00 UTC reset); `get_leaderboard` returns either the current week's top scores or the all-time top scores depending on the requested scope.
  5. The v1.0 cloud-function validator tests (TST-03) still pass against the reconciled functions, and the CI golden net (ghost-AI traces + determinism guard) stays green.**Plans**: 4 plans

**Wave 1**

- [x] 04-01-PLAN.md — Baseline-green check + leaderboard_crypto helper (HMAC verify + week math, stdlib-only; identical copy in both function dirs)

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 04-02-PLAN.md — Harden submit_score: MAX_SCORE 50k, HMAC grace verify, permanent initials, week-bucket write + lazy prune in one transaction
- [x] 04-03-PLAN.md — Scope-aware get_leaderboard (week|all, default week), weekly query, machine_id-out projection preserved

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 04-04-PLAN.md — cloud_functions/DEPLOY.md + manual Console ops (Secret Manager, REQUIRE_SIGNATURE, max-instances, weekly composite index, redeploy)

**Notes:**

- **Prerequisite (surfaced risk):** `cloud_functions/*/main.py` may carry uncommitted working-tree edits flagged at v1.0 close. The first action of this phase is to reconcile/commit that state *before* modifying the functions, so TST-03 validator tests target a known baseline.
- **Shared-secret seam:** COMP-01 verifies the HMAC against a shared key that must live in *both* the Cloud Functions and the client build. This phase establishes the key and the server-side verification; the client half (producing matching signatures) lands in Phase 5. The end-to-end "valid signed submission is accepted, forged one is rejected" assertion is only fully closed once Phase 5 ships — Phase 4 proves rejection of unsigned/invalid submissions against the known key.
- Standing constraint: this is leaderboard/Cloud-Functions work only — no ghost-AI decision behavior changes. The CI golden net is a merge gate on `main`.

### Phase 5: Client Identity Hardening

**Goal**: The player's identity is stored safely outside the game folder and signed, so the client both detects local tampering and produces submissions the hardened server accepts.
**Depends on**: Phase 4 (server defines the HMAC scheme + shared key and is verifying signatures)
**Requirements**: IDENT-01, IDENT-02, IDENT-03
**Success Criteria** (what must be TRUE):

  1. Identity data (`machine_id`, initials) is stored in a per-user location outside the game/exe folder, not in a file sitting next to the exe.
  2. The stored identity files are obfuscated, not human-readable plaintext.
  3. If an identity file is altered out-of-band, the game detects the broken HMAC on load and refuses to submit that tampered identity.
  4. A normally-played score submitted by the client carries a valid HMAC signature and is accepted onto the board by the Phase 4 server (the signing↔verification loop is closed end-to-end).

**Plans**: 3 plans

**Wave 1**

- [x] 05-01-PLAN.md — Client leaderboard_crypto module: canonical_message/sign_submission (server-contract mirror) + obfuscation + domain-separated file-integrity HMAC, with the loop-closing oracle test

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 05-02-PLAN.md — Relocate + consolidate identity into a single obfuscated, HMAC-signed blob in %LOCALAPPDATA%\PacMan\ with migrate-then-remove and a fail-closed tamper sentinel

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 05-03-PLAN.md — Wire it up: signed submissions (signature field), startup load/migrate, tamper submit-gate + game-over notice, and build.py baking the gitignored secret non-literally

**Notes:**

- IDENT-03 (client signs) is the second half of the COMP-01 (server verifies) mechanism from Phase 4 — same shared secret. This phase closes the loop the previous phase opened.
- Scope guard: obfuscation + HMAC only — no local-file encryption beyond that (client secrets are extractable; the server is the enforcement boundary, already handled in Phase 4).

### Phase 6: In-Game Weekly Boards & Got-Passed Banner

**Goal**: Players see and fight over the weekly competition directly inside the game.
**Depends on**: Phase 4 (scope-aware `get_leaderboard` + week buckets); benefits from Phase 5 (signed identity for accurate "your score" tracking)
**Requirements**: BOARD-03, BOARD-04, RIVAL-01
**Success Criteria** (what must be TRUE):

  1. In-game, the player can toggle between a "This Week" board and an "All Time" board and see the corresponding scores.
  2. The board shows the previous week's champion (e.g. "Last week: BOB").
  3. On launch, if someone has beaten the player's score since they last viewed the board, a banner names that player (or players).
  4. When offline or on first launch, these features degrade gracefully — no error, no banner, the game stays fully playable.

**Plans**: 4 plans
**UI hint**: yes

**Wave 1** *(parallel — no file overlap)*

- [x] 06-01-PLAN.md — Server `scope=last_week` read branch in `get_leaderboard` + validator tests (BOARD-04; the one server touch — reuses `previous_week_id(current_week_id())`, no data-model change)
- [x] 06-02-PLAN.md — Client `api_service.get_leaderboard(scope, timeout)` param (urlencode'd query string, None/[]-on-failure contract preserved) + request-capture tests (BOARD-03/BOARD-04 plumbing, D-14)
- [x] 06-03-PLAN.md — `settings.py` marker/banner constants + new `marker.py` unsigned last-viewed marker IO (plain JSON, best-effort, Monday-UTC week stamp) + tests (RIVAL-01 foundation, D-13)

**Wave 2** *(blocked on 06-02 + 06-03)*

- [x] 06-04-PLAN.md — Board screen This Week/All Time toggle + last-week subtitle + per-view empty/offline states (`run_leaderboard`); main-menu banner line (`run_main_menu`); `main.py` launch banner compute (short-timeout fetch), submit-path tracked-best update, board-open baseline rewrite (BOARD-03/BOARD-04/RIVAL-01)

**Notes:**

- Consumer of the Phase 4 scoped API — no new server data model here.
- "Since you last looked" requires persisting a last-viewed marker locally (rides on the Phase 5 identity storage).
- Live BOARD-04 (`scope=last_week`) requires a manual `get_leaderboard` redeploy (Google Cloud Console / Cloud Shell) — the in-repo gate is the validator tests; live behavior depends on the operator deploying.

### Phase 7: Web Leaderboard Page

**Goal**: Anyone with the link can view the leaderboard from a phone without launching the game.
**Depends on**: Phase 4 (the scope-aware API it fetches from); mirrors the boards finalized in Phase 6
**Requirements**: WEB-01, WEB-02, WEB-03
**Success Criteria** (what must be TRUE):

  1. A public web page hosted on Firebase Hosting displays the leaderboard, fetching from the existing Cloud Functions API.
  2. The page is mobile-first and readable on a phone, in an arcade style matching the game.
  3. The page mirrors the in-game boards — both "This Week" and "All Time" views are available.

**Plans**: 4 plans
**UI hint**: yes

**Wave 1**

- [x] 07-01-PLAN.md — Static markup contract: `index.html` (PAC-MAN wordmark, `This Week | All Time` tabs defaulting to All Time per D-08, last-week subtitle slot, board container, Refresh, hint) + branding head (title `PAC-MAN — Leaderboard`, OG/Twitter Card, favicon + font links) + root `firebase.json` + `.firebaserc` (project `pacman-firebase`) + `web/package.json` ESM marker (WEB-01/03)

**Wave 2** *(parallel — no file overlap; both depend on 07-01's DOM contract)*

- [x] 07-02-PLAN.md — Client logic `app.js`: fetch `get_leaderboard` (`scope=all|week|last_week`), `null`=offline sentinel mirroring `api_service`, lazy per-view cache (default All Time), three render states (verbatim copy), rank-1 highlight, last-week subtitle, Refresh; `node --test` coverage + XSS-safe rendering (WEB-01/03)
- [x] 07-03-PLAN.md — Retro arcade `styles.css` via the **frontend-design** skill (UI-SPEC tokens #000000/#10102E/#FFFF00, mobile-first, 44px touch targets, dot-leaders, Press Start 2P + monospace) + Pac-Man `favicon.svg` + ~1200×630 `og-preview.png` (WEB-02/03)

**Wave 3** *(blocked on 07-02 + 07-03)*

- [ ] 07-04-PLAN.md — Local visual/behavior human-verify on a phone-width viewport + manual operator `firebase deploy --only hosting` (D-03) + live smoke on `pacman-firebase.web.app` (WEB-01/02/03)

**Notes:**

- Pure consumer of the finished API — intentionally last so it mirrors the boards exactly as shipped in Phases 4 and 6.
- No server/API change this phase: the page only CALLS the already-deployed `get_leaderboard` (CORS `*`), it does not modify `cloud_functions/`.
- The web page opens on **All Time** by default (D-08) — a deliberate divergence from the in-game This Week default; not to be "fixed".
- Visual build is a hard directive to route through the **frontend-design** skill (D-05); deploy is a manual operator step (D-03), same pattern as the Phase 4/6 function redeploys.

### 📋 More Fun (Planned)

Gameplay depth (levels/mazes with a difficulty curve, fruit bonuses, new modes like time attack/endless);
optional **arcade-accurate ghost mode** as an opt-in toggle, never the default. (FUN-01…04) — NOT broken
into phases yet.

### 📋 Easier to Share (Planned)

Browser/web build (e.g. pygbag, play from a link with no install), cross-platform builds (macOS/Linux),
itch.io release. (SHR-01…03) — NOT broken into phases yet.

## Progress

**Execution Order:**
Phases execute in numeric order: 4 → 5 → 6 → 7

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Test Safety Net | v1.0 | 7/7 | Complete | 2026-06-11 |
| 2. Safe Refactor | v1.0 | 2/2 | Complete | 2026-06-12 |
| 3. Box-Bug Fix + Hygiene | v1.0 | 2/2 | Complete | 2026-06-12 |
| 4. Server Hardening & Weekly Data Model | v1.1 | 4/4 | Complete    | 2026-06-19 |
| 5. Client Identity Hardening | v1.1 | 3/3 | Complete    | 2026-06-19 |
| 6. In-Game Weekly Boards & Got-Passed Banner | v1.1 | 4/4 | Complete   | 2026-06-19 |
| 7. Web Leaderboard Page | v1.1 | 3/4 | In Progress|  |
