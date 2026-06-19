# Pac-Man (pacman-firebase)

## What This Is

A complete, playable desktop **Pac-Man clone** (Python/PyGame) with an online high-score
**leaderboard** backed by Google Cloud Functions + Firestore. It's built to be shared with friends
arcade-style: machine-ID identity, permanent 3-letter initials, fully playable offline, and
distributable as a Windows `.exe`. The **Solid-Foundation milestone is complete** — the codebase is now
**safe to extend**, with ghost-AI behavior pinned by a CI-gated golden net and the one latent box bug fixed.

## Core Value

It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read
and outplay. **That behavior is precious and must never silently regress.**

## Current Milestone: v1.1 More Competitive

**Goal:** Make the leaderboard something friends actually compete on — trustworthy enough that scores
can't be casually forged, and alive enough that people keep fighting over it.

**Target features:**
- **Anti-cheat & identity hardening** — relocate `machine_id`/initials out of the game folder + store
  obfuscated (not plaintext); HMAC-stamp them so the client detects tampering and the server verifies
  the *same* signature (rejects raw `curl` forgeries); server-enforced **permanent initials** (rename
  impossible, locked on first submit); tightened server-side score validation (**sanity ceiling**)
- **Weekly boards** — "This Week" (Monday-UTC reset) + "All Time" toggle; shows last week's champ
- **Web leaderboard page** — Firebase Hosting, public link, mobile-first, mirrors the in-game boards
- **"You got passed" launch banner** — names whoever beat *your* score since you last looked

**Key context:** All three competitive features ride on **one backend change** — week-bucketed scores
+ a scope-aware `get_leaderboard`. Build order falls out: harden functions → in-game weekly UI +
got-passed → web page. Replay-verification (re-run inputs server-side) was considered as the
unforgeable ceiling but deferred — HMAC + sanity ceiling is the right altitude for a friends board.
`cloud_functions/*/main.py` may have uncommitted working-tree changes (flagged at v1.0 close) —
reconcile first.

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

### Active

<!-- Milestone v1.1 (More Competitive) — started 2026-06-14. Detailed REQ-IDs in REQUIREMENTS.md. -->

Building toward **v1.1 More Competitive**:

- [x] Anti-cheat & identity hardening — relocated/obfuscated identity files, HMAC tamper-detection + server-side signature verification, server-enforced permanent initials, score sanity ceiling — *delivered Phases 4-5 (2026-06-19)*
- [ ] Weekly boards (This Week + All Time, Monday-UTC reset, last-week's champ)
- [ ] Web leaderboard page (Firebase Hosting, public, mobile-first)
- [ ] "You got passed" launch banner

**Future milestones (sequenced after Competitive):**

- [ ] **More Fun** — gameplay depth (levels/mazes, difficulty curve, fruit, modes); optional **arcade-accurate ghost mode** (opt-in toggle)
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

## Context

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
| Anti-cheat altitude: HMAC signing + server-side verification + score sanity ceiling, NOT full replay-verification | Friends board; client secrets are extractable anyway — raise the bar to stop casual/`curl` cheats rather than chase the unforgeable | — Pending (v1.1) |
| Permanent initials enforced **server-side** (locked on first submit), not just client-hidden | v1.0 "permanence" was bypassable by editing the local JSON; the rule belongs where the player can't reach it | — Pending (v1.1) |

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
*Last updated: 2026-06-19 after Phase 5 (Client Identity Hardening) completion — anti-cheat & identity hardening delivered end-to-end across Phases 4-5*
