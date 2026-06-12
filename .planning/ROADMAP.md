# Roadmap: Pac-Man (pacman-firebase) — Milestone 1: Solid Foundation

## Overview

This milestone makes a precious, untested codebase safe to extend. The hand-tuned ghost AI is the
spec, not a draft — it must never silently regress. The strategy is a strict three-step sequence:
first build a frame-perfect **safety net** that freezes today's behavior in golden masters, then
perform a **byte-identical refactor** of the highest-debt code *behind that net*, and only then make
the single sanctioned behavior change — the **ghost-box bounds fix** — proven isolated to the box
region, followed by hygiene cleanup. Verification runs at "maximum paranoia": golden traces +
visual montages (Claude reads frames with its own vision) + micro per-ghost tests + a Claude
playtest.

## The Cardinal Rule (sequencing — never reorder)

**Net (Phase 1) → byte-identical refactor (Phase 2) → isolated bug fix + hygiene (Phase 3).**

Never mix a "must-NOT-change-behavior" step with a "must-change-behavior" step. Mixing them is
exactly how an accidental brick becomes indistinguishable from an intended change.

- Phase 2 **depends on Phase 1's golden master** — green = mathematically unchanged.
- Phase 3 **depends on the Phase 1 net AND the Phase 2 refactor** — behavior moves only where
  intended (the box edges); everything else stays byte-identical.

## The Non-Goal (the guardrail this whole milestone is built around)

**Do NOT change ghost-AI decision behavior** — targeting (`get_targets`) and turn-preference
ordering (`move_blinky/inky/pinky/clyde`) are THE SPEC. The **only** sanctioned behavior change in
the entire milestone is **BUG-01** (unifying the two inconsistent ghost-box bounds into a single
`GHOST_BOX_BOUNDS`), and it must be **provably isolated to the box region**. Arcade-accuracy is
parked as an opt-in toggle for the future More Fun milestone — never a silent change here.

## Verification Bar: "Maximum Paranoia"

Every risky change is verified four ways:

1. **Frame-perfect trace match** — replay canonical playthroughs; assert the full per-frame state
   trace is identical (or differs only in the intended frames).

2. **Visual proof** — before/after frame **montages** Claude reads with its own vision, plus a GIF
   for the human.

3. **Micro per-decision tests** — direct assertions on `check_collisions` / `move_blinky` /
   `move_inky` / `move_pinky` / `move_clyde` so a failure points to the exact ghost + decision.

4. **Claude playtest** — Claude plays a full frame-stepped session (observe → decide → act) and
   adversarially hunts for soft-locks, wall-clips, and score overflow.

## Phases

**Phase Numbering:**

- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

- [x] **Phase 1: Test Safety Net** - Build the headless record/replay + capture harness and freeze current behavior in golden masters, micro per-ghost tests, cloud-function validator tests, and CI. (completed 2026-06-11)
- [x] **Phase 2: Safe Refactor** - Collapse the 4× ghost-AI duplication and centralize board geometry *behind the net*, with golden traces byte-identical. (completed 2026-06-12)
- [ ] **Phase 3: Box-Bug Fix + Hygiene** - Unify the ghost-box bounds (the one sanctioned, isolated behavior change) and finish dependency/repo/doc/asset cleanup.

## Phase Details

### Phase 1: Test Safety Net

**Goal**: A frame-perfect safety net exists that captures, replays, and visually verifies today's behavior — so any later change is provably caught at the exact frame and ghost.
**Depends on**: Nothing (first phase)
**Requirements**: HRN-01, HRN-02, HRN-03, HRN-04, TST-01, TST-02, TST-03, TST-04
**Success Criteria** (what must be TRUE):

  1. The game runs fully headless (SDL dummy video/audio) and is steppable one frame at a time via an extracted `tick()`, and the extracted loop reproduces a baseline trace captured from the *original* `run()` loop byte-for-byte (HRN-01 — behavior-preserving change to `game.py` only).
  2. The record/replay system captures the full per-frame state trace (each ghost x/y/dir/dead/box, Pac-Man, score, lives, powerup, dots) and replays a canonical playthrough deterministically, with the replayed trace matching the recorded one byte-for-byte (HRN-02, TST-01).
  3. Rendered frames can be captured to PNG and assembled into montages (for Claude's vision) and a GIF (for the human), and Claude can drive the game in an observe→decide→act loop to play and adversarially playtest at least one full session (HRN-03, HRN-04).
  4. Micro characterization tests assert the current per-ghost decisions (`check_collisions`, `move_blinky/inky/pinky/clyde`) and golden-master traces of current ghost + game-loop behavior — including one Claude-played session — are recorded and frozen (TST-01, TST-02).
  5. Cloud-function validator tests cover initials regex `^[A-Z]{3}$`, score type/range (incl. `MAX_SCORE`), and best-score upsert logic; CI runs the full suite headless on push and is green (TST-03, TST-04).

**Plans**: 7 plans
Plans:
**Wave 1**

- [x] 01-01-PLAN.md — Dev deps (pinned, human-verified) + headless bootstrap + first conftest.py

**Wave 2** *(blocked on Wave 1 completion)*

- [x] 01-02-PLAN.md — tick() extraction (baseline-first) + trace schema + record/replay driver
- [x] 01-05-PLAN.md — Micro per-ghost characterization tests (check_collisions, move_*)
- [x] 01-06-PLAN.md — Cloud-function validator + is_new_best upsert tests (firebase mocked)

**Wave 3** *(blocked on Wave 2 completion)*

- [x] 01-03-PLAN.md — Frame capture (PNG/montage/GIF) + Claude observe->decide->act play-loop

**Wave 4** *(blocked on Wave 3 completion)*

- [x] 01-04-PLAN.md — 8 scripted + 1 Claude-session golden traces + invariants + --bless + determinism guard

**Wave 5** *(blocked on Wave 4 completion)*

- [x] 01-07-PLAN.md — Headless GitHub Actions CI + branch protection on main

### Phase 2: Safe Refactor

**Goal**: The highest-debt code (board geometry magic numbers + the 4× ghost movement duplication) is cleaned up with mathematical proof that ghost-AI behavior is byte-for-byte unchanged.
**Depends on**: Phase 1 (requires the frozen golden master and passing net — the refactor is only safe *behind the net*)
**Requirements**: REF-01, REF-02
**Success Criteria** (what must be TRUE):

  1. Tile/board geometry is centralized and inline magic numbers are removed, and the full golden-master trace replays byte-for-byte unchanged (REF-01). The two existing (inconsistent) box-region definitions are preserved as two separate named constants here — unifying them is Phase 3, not now.
  2. The 4× ghost movement duplication is collapsed into one data-driven turn-priority table (same values, same order → same pixel of movement), and every golden-master trace stays byte-identical (REF-02).
  3. The ghost-AI refactor lands with golden traces unchanged: CI is green AND Claude eyeballs before/after montages and confirms identical ghost behavior with its own vision.

**Plans**: 2 plans

Plans:

**Wave 1**

- [x] 02-01-PLAN.md — Centralize tile/board geometry (REF-01): settings.py constants + geometry.py helpers + literal substitution; check_collisions differential oracle + deterministic frame-hash manifest. Geometry-first gate (D-11).

**Wave 2** *(blocked on Wave 1 — D-11 geometry-first gate)*

- [x] 02-02-PLAN.md — Collapse the 4× mover duplication (REF-02): per-ghost profile data + unified _move + thin wrappers; synthetic-exhaustive differential oracle, per-ghost atomic commits (blinky→inky→pinky→clyde), mutation canary, one-shot oracle deletion, D-17 CLAUDE.md doc update.

### Phase 3: Box-Bug Fix + Hygiene

**Goal**: The one sanctioned behavior change (unified ghost-box bounds) lands proven-isolated to the box region, and the repo's dependency/tracking/doc/asset hygiene is cleaned up.
**Depends on**: Phase 1 (the net catches any unintended drift) AND Phase 2 (the refactor replaced the two box-region constants with the single named constants this fix unifies)
**Requirements**: BUG-01, HYG-01, HYG-02, HYG-03, HYG-04
**Success Criteria** (what must be TRUE):

  1. The two inconsistent ghost-box boundary definitions (`game.py:get_targets` `340<x<560 and 340<y<500` vs `ghost.py:check_collisions` `350<x<550 and 360<y<480`) are unified into a single `GHOST_BOX_BOUNDS` used everywhere (BUG-01).
  2. The resulting behavior change is provably isolated to the box region: golden traces move ONLY at the box edges, those frames are re-blessed, before/after montages confirm the change visually, and the rest of every trace is verified untouched (BUG-01).
  3. Client dependencies are pinned in `requirements.txt`, `.claude/settings.local.json` is untracked (`git rm --cached`) with `.gitignore` reconciled (HYG-01, HYG-02).
  4. Doc drift is fixed — `CLAUDE.md` box-exit timing reconciled with `settings.py` (`PINKY=30`, `CLYDE=60` frames @60fps), and the dead "Change Initials" docstring removed from `menu.py` (HYG-03).
  5. Dead duplicate asset folders (`assets/ghost_images/`, `assets/player_images/`) are removed after confirming no references, and CI remains green on push (HYG-04).

**Plans**: 2 plans

Plans:

**Wave 1**

- [x] 03-01-PLAN.md — Hygiene: pin client deps (HYG-01), untrack settings.local.json + reconcile .gitignore + track CLAUDE.md (HYG-02), fix box-exit doc drift + dead docstring (HYG-03), delete dead asset folders + human .exe rebuild smoke-run (HYG-04). Four behavior-neutral atomic commits, CI green at every step (D-09).

**Wave 2** *(blocked on Wave 1 — D-09 hygiene-first/fix-last)*

- [ ] 03-02-PLAN.md — Box-bug fix (BUG-01): unify GHOST_BOX_BOUNDS onto the collision box (D-01), repoint both importers (get_targets = the only value change, check_collisions byte-identical). Differential oracle + belt-check + teeth-check then one-shot delete (D-03/D-04/D-05), Linux-CI re-bless of box-edge frames only (D-06), required Claude playtest (D-07) + human GIF gate (D-08). The single isolated trace-touching commit.

## Future Milestones

Sequenced after Foundation. Listed at a high level only — NOT broken into phases here.

- **More Competitive** — leaderboard hardening (anti-cheat / server-side score validation), weekly and/or per-level boards, a web page to view scores without launching the game, private friend groups / room codes. (COMP-01…04)
- **More Fun** — gameplay depth (levels/mazes with a difficulty curve, fruit bonuses, new modes like time attack/endless); optional **arcade-accurate ghost mode** as an opt-in toggle, never the default. (FUN-01…04)
- **Easier to Share** — browser/web build (e.g. pygbag, play from a link with no install), cross-platform builds (macOS/Linux), itch.io release. (SHR-01…03)

## Progress

**Execution Order:**
Phases execute in strict numeric order: 1 → 2 → 3. The Cardinal Rule forbids reordering.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Test Safety Net | 7/7 | Complete    | 2026-06-11 |
| 2. Safe Refactor | 2/2 | Complete    | 2026-06-12 |
| 3. Box-Bug Fix + Hygiene | 1/2 | In Progress|  |
