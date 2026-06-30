# Pac-Man (pacman-firebase)

## What This Is

A complete, playable desktop **Pac-Man clone** (Python/PyGame) with a **competitive, trustworthy online
leaderboard** backed by Google Cloud Functions + Firestore. It's built to be shared with friends
arcade-style: tamper-evident machine identity, permanent 3-letter initials, weekly + all-time boards,
a "got-passed" launch banner, a public mobile web leaderboard, fully playable offline, and
distributable as a Windows `.exe`. Three milestones are complete: **Solid Foundation** (the codebase is
safe to extend — ghost-AI behavior pinned by a CI-gated golden net, the one latent box bug fixed),
**More Competitive** (the server is now the real enforcement boundary — HMAC-verified, sanity-ceilinged,
week-bucketed — and the weekly fight surfaces both in-game and on the web), and **Feels Right** (the
game now plays fair and alive — corner-kiss catches gone, smooth cornering, and arcade juice — all
without touching a single ghost personality).

## Core Value

It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read
and outplay. **That behavior is precious and must never silently regress.**

## Current State

**Shipped v1.2 Feels Right (2026-06-30).** The game now plays fair and alive without touching a single
ghost personality. Corner-kiss catches are gone (FAIR-01: integer center-to-center collision vs
`GHOST_CATCH_DISTANCE=24`, replacing the 40×40/36×36 AABB overlap), cornering registers a few pixels
early (FAIR-03: widened pre-turn window), and the missing arcade juice — death wedge-spin (FEEL-01),
eat-ghost points popup with a brief freeze (FEEL-02), frightened-end white blink (FEEL-04), and a
"READY!" round-open beat (FEEL-05) — all rides the existing juice firewall (`Game.juice`) so the
`juice=False` path stays byte-identical and the goldens needed **no re-bless**. The three FAIR-* behavior
changes batched behind **one** deliberate Linux/Docker re-bless; `ghost.py` held byte-identical
throughout. Per the D-10 playtest the player dialed chase ghosts to 2.0 px/frame (= player speed), so
FAIR-02 ships as a tunable no-op — escape is cornering-based, not speed-based (accepted SC2 override).
**FEEL-03** (distinct eat-ghost sound) was cut/descoped — wired then reverted, sourcing a `.wav` wasn't
worth the chore. A code-review pass also fixed a pre/post-move catch-sampling skew (WR-03).

**Prior milestones:** v1.1 More Competitive (2026-06-26) made the leaderboard server-enforced (HMAC,
sanity ceiling, permanent initials, week buckets) with a tamper-evident client identity and a public
web board at `pacman-firebase.web.app`. v1.0 Solid Foundation (2026-06-12) made the codebase safe to
extend — ghost AI pinned by a CI-gated golden net, the one box bug fixed.

## Next Milestone Goals

**Planning the next milestone (likely More Fun).** No milestone is in flight — the next step is
`/gsd-new-milestone` to define fresh requirements.

**Candidate directions (sequenced):**

- **More Fun** — gameplay depth (levels/mazes with a difficulty curve, fruit bonuses, new modes like
  time attack / endless); optional **arcade-accurate ghost targeting mode** as an opt-in toggle, never
  the default.
- **Multiplayer** — asymmetric 1v4 (one Pac-Man, human-drivable ghosts, AI bot-fill for empty slots);
  built as a staircase (local couch → LAN lockstep, helped by the deterministic engine → online).
- **Easier to Share** — browser/web build (e.g. pygbag), cross-platform builds (macOS/Linux), itch.io.

## Requirements

### Validated

<!-- Existing capabilities inferred from the codebase map (.planning/codebase/). -->

- ✓ Playable Pac-Man core loop — movement, dots, power pellets, lives, win/lose — existing
- ✓ Four ghosts with distinct AI personalities (Blinky/Inky/Pinky/Clyde) + staggered box exit — existing
- ✓ Online leaderboard (top-10 best scores) via Cloud Functions + Firestore, **no client credentials** — existing
- ✓ Machine-ID identity + permanent 3-letter initials — existing
- ✓ Offline resilience — leaderboard degrades gracefully; game fully playable offline — existing
- ✓ Sound system (waka, power siren, start/death) — existing
- ✓ Windows `.exe` distribution via PyInstaller — existing
- ✓ Frame-perfect characterization-test **safety net** (9 golden traces + 15 per-ghost micro tests + determinism guard) + cloud-fn validator tests + **CI merge-gate** on push/PR — *Phase 1 (test-safety-net), 2026-06-11*
- ✓ **Behavior-preserving refactor** — centralized tile/board geometry (REF-01) + collapsed the 4× ghost-AI duplication into a data-driven `_move` + per-ghost profiles (REF-02), proven byte-identical by differential oracles + golden traces — *Phase 2 (safe-refactor), 2026-06-12*
- ✓ **Ghost-box bounds unified** (BUG-01) — collapsed the two divergent box rectangles into a single `GHOST_BOX_BOUNDS` (collision box wins); the milestone's **one sanctioned behavior change**, oracle-proven isolated to the box ring (18,496 comparisons, 0 out-of-ring) + golden masters re-blessed (all 9, frame-340-rooted) — *Phase 3 (box-bug-fix-hygiene), 2026-06-12*
- ✓ **Repo hygiene** (HYG-01..04) — pinned client deps, untracked `settings.local.json` + reconciled `.gitignore`, fixed box-exit doc drift, removed dead asset folders (human `.exe` smoke-run verified) — *Phase 3 (box-bug-fix-hygiene), 2026-06-12*
- ✓ **Anti-cheat & identity hardening** (COMP-01..03, IDENT-01..03) — server is the enforcement boundary (HMAC signature verification, score sanity ceiling, server-enforced permanent initials, week-bucketed scores) *Phase 4*; client identity relocated out of the game folder to `%LOCALAPPDATA%\PacMan\` as a single obfuscated, HMAC-signed blob with fail-closed tamper detection, seamless legacy migration, and a graceful no-secret offline degrade — client submissions carry a server-verified signature, closing the signing↔verification loop end-to-end *Phase 5* — *Phases 4-5, 2026-06-19*
- ✓ **Weekly boards + got-passed banner** (BOARD-01..04, RIVAL-01) — week-bucketed scores (Monday-UTC reset) with a scope-aware `get_leaderboard` (week/all/last_week); in-game This Week / All Time toggle, last-week champion subtitle, and a launch banner naming whoever passed your score since you last looked — all degrading gracefully offline/first-launch — *Phases 4 & 6, 2026-06-19* (v1.1)
- ✓ **Public web leaderboard** (WEB-01..03) — a no-dependency ESM page on Firebase Hosting (`pacman-firebase.web.app`) mirroring the in-game This Week / All Time boards, mobile-first with arcade styling (frontend-design skill), XSS-safe, phone-verified and live — *Phase 7, 2026-06-25* (v1.1)
- ✓ **Fairness pass** (FAIR-01/02/03) — corner-kiss catches removed via integer center-to-center collision (`GHOST_CATCH_DISTANCE=24`) replacing the 40×40/36×36 AABB overlap (FAIR-01); a widened pre-turn cornering window registers queued turns ~4-6px early (FAIR-03); a per-ghost integer-rational chase-speed accumulator added (FAIR-02, shipped as a tunable no-op — player dialed chase ghosts to 2.0 px/frame, escape is cornering-based). `ghost.py` byte-identical; three FAIR changes batched behind one Linux/Docker re-bless — *Phase 8, 2026-06-29* (v1.2)
- ✓ **Arcade juice** (FEEL-01/02/04/05) — death wedge-spin animation (FEEL-01), eat-ghost points popup 200/400/800/1600 + brief freeze (FEEL-02), frightened-end white blink in the last ~2s of the power window (FEEL-04), and a "READY!" round-open beat (FEEL-05) — every effect gated behind the `Game.juice` firewall so the `juice=False` path is byte-identical and the goldens needed no re-bless — *Phase 9, 2026-06-30* (v1.2)

### Active

<!-- No milestone in flight. Next: /gsd-new-milestone to define requirements (likely More Fun). -->

**Future milestones (sequenced next):**

- [ ] **More Fun** — gameplay depth (levels/mazes, difficulty curve, fruit, modes); optional **arcade-accurate ghost mode** (opt-in toggle)
- [ ] **Multiplayer** — asymmetric 1v4 (human-drivable ghosts + AI bot-fill); staircase: local couch → LAN lockstep → online
- [ ] **Easier to Share** — browser/web build (e.g. pygbag), cross-platform, itch.io release

### Out of Scope

- Changing ghost-AI **decision behavior** during Foundation — current behavior is the spec, not a draft
- Arcade-accurate ghost targeting **as a default** — only ever an opt-in mode in the Fun milestone
- Real-time twitch-reflex AI play — deterministic step/scripted play is strictly better for testing
- **Friend groups / private join-code boards** (v1.1) — a single shared exe already *is* one friend group; revisit if circles multiply
- **Season-history archives** of past weekly boards (v1.1) — last-week's champ is enough; full history isn't worth the data model
- **Local-file encryption** beyond obfuscation + HMAC (v1.1) — client-side secrets are extractable; the server is the real enforcement boundary
- **Replay-verification** of scores / re-running inputs server-side (v1.1) — considered as the unforgeable ceiling; deferred, HMAC + sanity ceiling is the right altitude for a friends board
- **New gameplay** — levels, mazes, modes belong to the *More Fun* milestone, not Competitive
- **Scatter/chase wave system** (v1.2) — alternating ghost scatter↔chase would change ghost **decision behavior**, the precious never-touch-silently zone; parked, not in Feels Right
- **Bonus fruit + extra mazes/modes** (v1.2) — reward/content beats belong to *More Fun*, not the feel pass; kept Feels Right lean
- **Real-time multiplayer** (v1.2) — the asymmetric 1v4 staircase needs a play group to validate fun; its own future milestone, not a feel-polish pass
- **Distinct eat-ghost sound (FEEL-03)** (v1.2) — scoped, wired in 09-04, then **cut/descoped** and reverted: sourcing/licensing a `.wav` wasn't worth the chore for a friends build. Other audio polish (rising siren, extra-life jingle, fuller intro tune) was also dropped to keep Feels Right lean

## Context

- **Shipped v1.2 (Feels Right), 2026-06-30.** 2 phases · 9 plans · 20 tasks in 1 day (2026-06-29 →
  2026-06-30). Game-feel & fairness polish landed almost entirely in `game.py` / `player.py` /
  `settings.py` plus juice-gated draw code; `ghost.py` held byte-identical. The three FAIR-* behavior
  changes batched behind **one** Linux/Docker golden re-bless (constants 24/40/20/6); every FEEL effect
  rode the `Game.juice` firewall and shipped with **no re-bless**. FEEL-03 (eat-ghost sound) cut. The
  golden net (9 traces + 15 micro + frame-hash + determinism guard) remains the merge gate on `main`.
- **Shipped v1.1 (More Competitive), 2026-06-26.** 4 phases · 15 plans · 25 tasks over ~12 days
  (2026-06-14 → 2026-06-26). Added ~1,000 LOC across `web/` (no-dependency ESM + arcade CSS) and the
  two `cloud_functions/` Gen2 Cloud Run services, plus client `leaderboard_crypto.py` / `marker.py` /
  identity-storage rework. The leaderboard is now competitive and trustworthy: server-enforced
  (HMAC + sanity ceiling + permanent initials + week buckets), tamper-evident client identity, and the
  weekly board visible in-game and on a live public web page. **Known manual-only debt:** the live
  2-player got-passed E2E and the `scope=last_week` operator redeploy can't be automated in-repo
  (code paths unit-verified; see STATE.md Deferred Items).
- **Shipped v1.0 (Solid Foundation), 2026-06-12.** 3 phases · 11 plans · 84 commits over ~10 days.
  ~3,500 LOC Python (client). The codebase is now safe to extend: ghost-AI behavior is pinned by a
  CI-gated golden net (9 traces + 15 micro tests + frame-hash + determinism guard), the 4× mover
  duplication is collapsed into a data-driven `_move`, and the one latent box-bounds bug is fixed.
- **Brownfield, mapped.** 7 codebase-map docs in `.planning/codebase/`. Milestone design spec:
  `docs/superpowers/specs/2026-06-02-solid-foundation-design.md`.
- **Fully deterministic game** — no `random`, no wall-clock timing; fixed-timestep frame counters.
  This is what makes record/replay characterization testing frame-perfect.
- **The fragile heart is now netted.** `ghost.py`'s four hand-tuned movers (the riskiest code) went
  from **zero tests** to a frame-perfect, CI-merge-gating safety net — the milestone's whole point.

## Constraints

- **Tech stack**: Python 3 / PyGame client; Google Cloud Functions + Firestore backend; PyInstaller
  build. Avoid new client runtime deps without strong reason.
- **Compatibility**: Windows-first.
- **Safety**: Ghost-AI behavior preserved **byte-for-byte** through Foundation work (proven by golden traces).
- **Testing**: Headless via SDL dummy drivers; deterministic record/replay.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Tests-first safety net before any refactor | Ghost AI is fragile/hand-tuned; pin behavior so refactor is provably safe | ✓ Phase 1: 61-test net (9 goldens · 15 micro · determinism · CI-gated); behavior frozen |
| Refactor must be byte-identical; bug fix isolated & last | Never mix a must-not-change step with a must-change step | ✓ Phase 2 byte-identical; ✓ Phase 3 box-bug fix landed isolated & last (oracle-proven, goldens re-blessed) |
| Preserve ghost behavior; park arcade-accuracy as opt-in future | The hand-tuned AI is the spec | ✓ Good — behavior held byte-identical through v1.0; arcade mode parked for Fun milestone (FUN-04) |
| Foundation work on a `solid-foundation` branch | Isolate risky AI-adjacent work from `main` | — Superseded — config branching=none; Phase 1 shipped via PR #1, Phases 2–3 committed on `main` with the CI net as the gate |
| Milestone order: Foundation → Competitive → Fun → Share | Foundation makes the rest cheap and safe | ✓ Good — Competitive started 2026-06-14 (v1.1) |
| Anti-cheat altitude: HMAC signing + server-side verification + score sanity ceiling, NOT full replay-verification | Friends board; client secrets are extractable anyway — raise the bar to stop casual/`curl` cheats rather than chase the unforgeable | ✓ Good — shipped v1.1 (Phases 4-5); server rejects unsigned/forged/over-ceiling submissions, signing↔verification loop closed end-to-end |
| Permanent initials enforced **server-side** (locked on first submit), not just client-hidden | v1.0 "permanence" was bypassable by editing the local JSON; the rule belongs where the player can't reach it | ✓ Good — shipped v1.1 (Phase 4); initials locked server-side on first submission |
| Server owns week math; scores bucketed by week-id (Monday-UTC) + scope-aware `get_leaderboard` (week/all/last_week) | One backend change powers all three competitive features; server-time avoids client-clock spoofing | ✓ Good — shipped v1.1 (Phases 4 & 6); weekly composite index live, `{initials,score}`-only projection so machine_id never leaks |
| Identity stored obfuscated + HMAC-signed in `%LOCALAPPDATA%\PacMan\`, fail-closed on tamper — no local encryption beyond that | Client secrets are extractable; the server is the enforcement boundary, so stronger local crypto is theater | ✓ Good — shipped v1.1 (Phase 5); single blob, migrate-then-remove of legacy plaintext, TAMPERED sentinel blocks submit |
| Web page opens on **All Time** by default (D-08), diverging from the in-game This Week default; deploy is a manual operator step | A first-time public visitor has no weekly context; All Time is the meaningful first view. Manual deploy matches the function-redeploy pattern | ✓ Good — shipped v1.1 (Phase 7); live at `pacman-firebase.web.app` |
| v1.2 fairness changes may alter ghost **outcomes** (positions, catches) but never ghost **decision logic** (targeting/profiles) — re-bless goldens, don't rewrite personalities | The core value is the four personalities, not their pixel-exact trajectories; speed/collision are tuning + rules, not targeting. Treat like the v1.0 Phase-3 box-fix: sanctioned change, isolated, oracle-scoped, re-blessed on Linux | ✓ Good — shipped v1.2 (Phase 8); `ghost.py` byte-identical, all three FAIR-* changes batched behind one Linux/Docker re-bless (24/40/20/6) |
| Game-feel before content/multiplayer; keep Feels Right lean | Death-anim + unfair-catch were the user's actual pain; feel is 100% solo-testable (no 4 friends, no asset pile), high ROI, rides existing golden-net discipline | ✓ Good — shipped v1.2 in 1 day; FEEL-03 cut to stay lean |
| All v1.2 juice (FEEL-*) gated behind the `Game.juice` firewall (default `False`) | The golden + frame-hash replays run `juice=False`; gating every effect there keeps that path byte-identical so cosmetic work ships with no re-bless — even the eat-ghost "brief freeze" must not shift the deterministic sim | ✓ Good — shipped v1.2 (Phase 9); FEEL-01/02/04/05 all juice-gated, zero re-bless |
| FAIR-02 chase-speed ships as a tunable no-op (chase ghosts dialed to 2.0 px/frame = player speed); escape is cornering-based not speed-based | D-10 playtest: a faster-than-ghost Pac-Man felt off; with FAIR-01 (fair catches) + FAIR-03 (smooth cornering) fixed, cornering is a sufficient escape. Keep the accumulator as a tunable for later | ✓ Accepted (SC2 override) — v1.2 Phase 8 |
| FEEL-03 (distinct eat-ghost sound) cut/descoped | Sourcing/licensing a fit-for-purpose `.wav` wasn't worth the chore for a friends build; wired in 09-04 then reverted | ✓ Good — v1.2 Phase 9; reverted cleanly, no dead wiring |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-06-30 after v1.2 Feels Right milestone (fairness pass + arcade juice shipped; FEEL-03 cut; FAIR-02 a tunable no-op; ghost.py byte-identical, FEEL-* golden-safe with no re-bless)*
