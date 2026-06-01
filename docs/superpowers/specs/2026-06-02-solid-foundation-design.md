# Solid Foundation — Design Spec

**Date:** 2026-06-02
**Status:** Approved (brainstorming) → ready for planning
**Milestone:** 1 of 4 (Solid Foundation → More Competitive → More Fun → Easier to Share)

## Overview

Build a frame-perfect **safety net** around the existing Pac-Man game, then *safely* refactor
the highest-debt code and fix one latent bug — with **mathematical and visual proof** that the
hand-tuned ghost AI is byte-for-byte unchanged.

This milestone exists to make every later milestone (leaderboard hardening, new gameplay, web
distribution) cheap and safe to build. Today the riskiest code — the four ghost AIs and the game
loop — has **zero tests**, so any change is a gamble. After this milestone, behavior is locked in
amber and changes become verifiable.

## Core Value

The ghost AI was written through extensive trial and error and is considered **fragile and
precious**. The #1 priority is: **do not brick the ghost AI.** Everything below is designed around
that constraint.

## The key enabling insight: the game is 100% deterministic

Verified against the codebase:

- **No randomness anywhere** — zero uses of `random` / `randint` / `shuffle`.
- **No wall-clock timing** — zero uses of `get_ticks` / `time.time` / `datetime`. All timers are
  fixed-timestep frame counters (`FPS = 60`).
- `Game.run()` (`game.py:456`) is a clean `while running:` loop returning `{score, game_won}`.

**Consequence:** same inputs → the exact same frames, every run. This makes record/replay
characterization testing frame-perfect and reliable — the foundation of the whole approach.

## Non-Goals (explicit guardrails)

- ❌ **Do NOT change ghost AI decision-making** — targeting (`get_targets`) and turn-preference
  ordering (the `move_*` methods). Current decision behavior is THE SPEC; we are not "correcting,"
  "improving," or making it arcade-accurate. **The single sanctioned exception is the ghost-box
  bounds bug fix (Phase D)** — an explicitly requested, isolated change, verified to affect only the
  box region and nothing else.
- ❌ **Not arcade-accuracy.** The real arcade ghosts use specific targeting math (Blinky → Pac-Man's
  tile, Pinky → 4 tiles ahead, Inky → Blinky-vector trick, Clyde → flees when close). **Ours do not
  work like that and we are not touching how ours work.** ("Arcade-accurate ghost mode" is parked as
  an optional, opt-in feature for the More Fun milestone — a visible toggle, never a silent change.)
- ❌ **No leaderboard / security work** (forgeable scores, App Check, rate limiting) — that belongs
  to the More Competitive milestone.
- ❌ **No new gameplay** (levels, modes, fruit) — More Fun milestone.
- ❌ **No web/cross-platform build** — Easier to Share milestone.

## The Cardinal Rule (sequencing)

Build the net → refactor → fix the bug, in that order, and **never mix a "must-NOT-change-behavior"
step with a "must-change-behavior" step.** Mixing them is exactly how you lose the ability to tell
an accidental brick from an intended change.

- **Refactor steps** (Phase C): golden traces must stay **byte-identical**. Green = mathematically
  unchanged.
- **Bug-fix step** (Phase D): behavior changes **only where intended** (the box region). Re-bless
  only those frames; confirm nothing else moved.

## Verification Strategy — "Maximum Paranoia"

Every risky change is verified four ways:

1. **Frame-perfect trace match** — replay the canonical playthroughs; assert the full per-frame state
   trace is identical (or differs only in the intended frames).
2. **Visual proof** — auto-generate before/after frame **montages** (a grid of stills) that *Claude
   reads with its own vision*, plus a **GIF** for the human to watch.
3. **Micro per-decision tests** — direct assertions on `check_collisions` / `move_blinky` /
   `move_inky` / `move_pinky` / `move_clyde` so a failure points to the exact ghost + exact decision.
4. **Claude playtest** — Claude *plays* a full session (observe → decide → act loop, frame-stepped)
   and adversarially hunts for bugs (soft-locks, wall-clips, score overflow).

## Architecture: the test harness

- **Headless mode.** Run pygame with `SDL_VIDEODRIVER=dummy` and `SDL_AUDIODRIVER=dummy` — no
  window, no sound, runs in CI on any machine. The existing `Ghost.__init__` draw side-effect
  becomes harmless (it blits to an in-memory dummy surface). Preferred: **no change to `ghost.py`**.
- **Steppable loop.** Extract a `tick()` (one frame of update) from `Game.run()`'s while-body. This
  is a **behavior-preserving change to `game.py` only — it does not touch `ghost.py` AI logic.**
- **Trace format.** Per frame, record a structured snapshot:
  `{frame, pacman:{x,y,dir}, ghosts:[{name,x,y,dir,dead,box}], score, lives, powerup,
  dots_remaining, game_over, game_won}` serialized as JSON/JSONL. Comparison is exact.
- **Frame capture.** Save the rendered surface to PNG per frame; assemble montages (for Claude) and
  a GIF (for the human).
- **Play-loop.** A driver that, each turn: steps N frames → reads state + screenshot → Claude picks
  a direction → injects the simulated key (`pygame.event.post`) → repeats. Used to generate
  realistic golden playthroughs and to bug-hunt.

## Build Sequence

### Phase A — Harness (touches AI logic: NO)
1. **Capture a baseline trace from the *existing* `run()` loop** via temporary, logic-free
   instrumentation (a per-frame state dump). This is the reference for proving the next step is safe.
2. Extract a steppable `tick()` from `Game.run()`; prove it **reproduces the baseline trace exactly**
   (resolves the chicken-and-egg: the harness's correctness is validated against the un-refactored loop).
3. Add headless mode + frame/montage/GIF capture + the Claude play-loop driver.

### Phase B — Golden master (touches AI logic: NO, reads only)
4. Record canonical playthroughs as frozen golden traces:
   - A few **scripted** scenarios (deterministic input sequences exercising box exits, power-pellet
     chases, ghost-eating, death, win).
   - One **Claude-played** realistic session.
5. **Micro characterization tests** — assert current turn decisions for representative states per ghost.
6. **Cloud-function validator tests** — initials regex `^[A-Z]{3}$`, score type/range (incl.
   `MAX_SCORE`), best-score upsert logic. (Pure, high value; write against current working-tree code —
   note `cloud_functions/*/main.py` have uncommitted modifications.)
7. **CI** — GitHub Actions runs `pytest` headless on push. (Confirm GitHub remote during planning.)

### Phase C — Safe refactor (touches AI logic: YES — *behind the passing net*)
8. **Centralize geometry / kill magic numbers (D2).** Derive tile size once; name board geometry;
   replace inline literals (`num1 = (HEIGHT-50)//32`, `num2 = WIDTH//30`, pixel literals).
   **Preserve the two existing (inconsistent) box-region definitions as two separate named constants**
   so behavior stays byte-identical — unifying them is Phase D, not here. Traces must stay byte-identical.
9. **Data-driven ghost turn-priority table (D1).** Read the exact turn-preference ordering out of each
   `move_*` method and express it as data; collapse the four ~120-line ladders into one parameterized
   mover. **Same values, same order → same pixel of movement.** Traces must stay byte-identical;
   Claude also eyeballs before/after montages.
10. *(Optional, if low-risk behind the net)* Unify the two parallel collision implementations
    (`Player.check_position` / `Ghost.check_collisions`, D4).

### Phase D — Ghost-box bug fix (touches AI logic: YES — isolated & LAST)
11. **Unify the inconsistent ghost-box bounds (D3).** Two definitions disagree today:
    - `game.py:get_targets` → `340 < x < 560 and 340 < y < 500`
    - `ghost.py:check_collisions` → `350 < x_pos < 550 and 360 < y_pos < 480`

    Replace the two named constants from Phase C with a **single unified `GHOST_BOX_BOUNDS`** and use
    it everywhere. This is an **intentional** behavior change → golden traces move **only at the box
    edges**. Re-bless those frames, verify with before/after montages, and confirm the rest of every
    trace is untouched.

### Phase E — Hygiene (touches AI logic: NO)
12. **Pin client dependencies** (`pygame`, etc.) in `requirements.txt` (P2).
13. **Stop tracking `.claude/settings.local.json`** (`git rm --cached`) and reconcile `.gitignore` (S3).
14. **Fix doc drift:** `CLAUDE.md` box-exit timing ("~2s / ~4s") vs `settings.py`
    (`PINKY=30`, `CLYDE=60` frames @60fps = 0.5s / 1s) (DOC1); remove the dead "Change Initials"
    docstring reference in `menu.py` (DOC2).
15. **Delete dead duplicate asset folders** `assets/ghost_images/`, `assets/player_images/` after
    confirming no references (D6).

## Success Criteria

- [ ] Headless harness runs in CI; canonical playthroughs replay deterministically.
- [ ] Golden-master traces captured for **current** behavior (incl. one Claude-played session).
- [ ] Micro per-ghost tests + cloud-function validator tests pass.
- [ ] Geometry centralized and ghost-AI refactor landed with **byte-identical** traces (proof: green
      CI + visual montages).
- [ ] Ghost-box bug fixed with the behavior change **provably isolated** to the box region.
- [ ] CI green on push; client deps pinned; `settings.local.json` untracked; docs reconciled; dead
      assets removed.
- [ ] Claude has played ≥1 full session and confirmed ghost behavior with its own vision.

## Risks & Mitigations

- **Extracting `tick()` subtly alters frame ordering.** → Capture the baseline trace from the
  existing loop *first* (Phase A.1), then assert the extracted loop reproduces it exactly.
- **`Ghost.__init__` rendering side-effect (C1) blocks headless construction.** → `SDL_VIDEODRIVER=dummy`
  makes `draw()` harmless with **no change to `ghost.py`**. Only decouple if a concrete need appears
  in planning (prefer not touching AI files).
- **Refactor silently changes behavior.** → That's the entire point of building the net first; the
  trace catches it at the exact frame + ghost, and Claude stops.
- **Confusing the box-fix's intended change with an accidental one.** → Strict sequencing (refactor
  before fix; fix isolated and last).

## Out of Scope / Parked for Later

- **Arcade-accurate ghost mode** — optional opt-in toggle, More Fun milestone.
- **Leaderboard security** (forgeable scores S1, App Check, rate limiting) — More Competitive.
- **New gameplay** (levels, modes, fruit) — More Fun.
- **Web / cross-platform build** — Easier to Share.

## Open Questions for Planning

1. Is there a GitHub remote for CI (GitHub Actions), or should CI target a different runner?
2. Granularity: is "Solid Foundation" one GSD phase, or split (e.g. Harness+Net / Refactor / Bug-fix
   + Hygiene)?
3. How many scripted scenarios constitute "canonical" coverage (box exit, power chase, eat, death, win)?
