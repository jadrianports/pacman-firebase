# Phase 8: Fairness Pass - Research

**Researched:** 2026-06-29
**Domain:** Deterministic 2D game-feel tuning (PyGame, integer-grid movement, golden-master regression net)
**Confidence:** HIGH (all recommendations grounded in the actual `game.py` / `ghost.py` / `player.py` / test harness; no external dependencies)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Replace the AABB overlap catch (`player_circle.colliderect(ghost.rect)`) with a **center-to-center distance** test between Pac-Man and each ghost.
- **D-02:** Tightness = **tight / arcade-faithful**, target ~**14–16px** center distance (≈ half a tile; `HALF_TILE`-ish). Ghost must be essentially on the player's tile to catch. Intentionally allows slight *visual* sprite overlap before a catch. Diagonal corner-kisses must read as SAFE.
- **D-03:** Expose the catch threshold as a **named tunable constant** in `settings.py` (not a magic number).
- **D-04:** Apply the new distance test to **all** existing catch checks symmetrically — the normal "ghost kills player" path AND the powerup-mode "already-eaten ghost kills player" path (`game.py:400-413`). Eating a frightened ghost (player catches ghost) uses the same model.
- **D-05:** Root cause: Pac-Man and ghosts are **both speed 2** (equal), so a trailing ghost holds distance forever. That equal-speed state is the "unbeatable" feeling — not a literal ×2 chase tier.
- **D-06:** Fix by making Pac-Man **a hair faster** than chasing ghosts — **subtle / arcade-faithful** (~5–10% edge; arcade reference Pac 80% vs ghost 75%).
- **D-07:** Keep `PLAYER_SPEED = 2` unchanged; **slow the chasing ghosts** to ~1.85. Expose the ghost speed factor as a tunable.
- **D-08:** **Leave eyes-return speed (dead-ghost = 4) untouched.** Powerup-slow (ghost = 1) behavior unchanged in intent.
- **D-09:** Add a **pre-turn window** so a queued turn registers a few pixels **before** the junction instead of only inside the current ~7px at-junction window (`12 <= center % TILE <= 18`). Feel = **snappy / arcade-faithful**, target window opening ~**4–6px early**. Build on the existing input buffer (`direction_command` / `update_direction`), exposed as a tunable.
- **D-10:** Workflow = **Build → playtest → re-bless.** Implement all three with arcade-faithful defaults as named tunable constants; user playtests on **Windows** (`python main.py`) and dials constants; signs off; **only then** run the single golden-net re-bless on Linux/Docker. Do NOT re-bless against unsigned-off interim numbers.

### Claude's Discretion
- Exact final pixel/factor values within the stated ranges (D-02 ~14–16px, D-07 ~1.85, D-09 ~4–6px) are starting points; the user dials them in during the D-10 playtest. Planner should pick clean arcade-faithful defaults and make them trivially editable.
- Corner-window mechanic (FAIR-03) was a "you decide" — lean snappy/arcade-faithful as above.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (Scatter/chase waves, arcade-accurate targeting mode, content/fruit, and multiplayer remain explicitly out of scope per REQUIREMENTS.md.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FAIR-01 | Catch uses center-to-center distance, not bounding-box overlap; diagonal corner-kisses no longer register | Drop-in at `game.py:400-436`; both `center_x/center_y` pairs already exist (`player.py:24-29`, `ghost.py:284-285`). Squared-distance integer test. See **Pattern 1**. |
| FAIR-02 | Pac-Man moves slightly faster than ghosts; escape always possible; never an unbeatable ×2 | **THE #1 question.** Resolved via integer-step accumulator in `game.py` (positions stay integer → grid-aligned, deterministic, trace-safe). Ghost decision logic untouched. See **Pattern 2** + **Pitfall 1**. |
| FAIR-03 | A turn input registers a few pixels early; smooth corner-cutting | Widen the **player-only** `12 <= center % TILE <= 18` windows in `player.check_position` (`player.py:64-85`). Ghost windows (`ghost.py:343+`) stay byte-identical. See **Pattern 3**. |
</phase_requirements>

## Summary

This is a self-contained, code-only game-feel phase with **no external dependencies and no new libraries**. All three FAIR-* changes are small, surgical edits to `game.py`, `player.py`, and `settings.py`, plus a single deliberate golden-master re-bless. The hard constraint shaping every recommendation is the project's determinism doctrine: the golden net (9 state traces + frame-hash manifests + a static determinism guard + ~15 ghost micro-tests) is the merge gate, and it is frame-perfect *only because* the simulation uses integer pixel math and frame-counter timers with zero randomness/wall-clock.

The single highest-risk item — FAIR-02's "~1.85 px/frame" ghost speed — is **not** safely implemented as a fractional per-frame step. The per-frame trace schema (`harness/trace.py:7-8`) records ghost `x`/`y` as **integers** and explicitly relies on "every captured value is an int or bool, so comparison is exact and platform-independent." A fractional ghost position would (a) drop floats into the trace and break platform-independent comparison, and (b) drift the ghost off the integer grid so it can miss the `12 <= center % TILE <= 18` turn windows. The correct resolution keeps ghost positions **strictly integer** and instead varies the per-frame integer *step* (1 or 2) via a hidden accumulator on the `Game` object so the long-run average is ~1.85. `ghost.py` is **not touched at all** — which makes the byte-identical-decision-logic guard trivially true and keeps the 15 ghost micro-tests green as the proof artifact.

The second meaningful risk is **not** in the code change but in the re-bless: because FAIR-01 (tighter catch) and FAIR-02 (slower ghosts) both make the player harder to kill, the one scenario with a `game_over` terminal (`death`, frame_cap 4200) may no longer reach a natural death from its recorded inputs — and `ghost_eat` may no longer register its scripted eat under the tighter catch radius. Those scenarios may need their **input** re-recorded, which is a larger lift than `pytest --bless`. This must be verified explicitly, not assumed.

**Primary recommendation:** Implement all three as named `settings.py` tunables touching only `game.py` (FAIR-01 + FAIR-02) and `player.py` (FAIR-03); keep ghost positions integer via an integer-rational step accumulator; leave `ghost.py` byte-identical; then run **one** `pytest --bless` in the Linux/Docker `python:3.12` CI env after D-10 sign-off, and verify each terminal scenario still reaches its terminal before trusting the bless.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Catch / death / eat decision (FAIR-01) | `game.py` (`check_ghost_collisions`) | `settings.py` (tunable) | Collision arbitration already lives in `Game`, reading `player`/`ghost` centers. Ghosts never decide catches. |
| Ghost chase speed (FAIR-02) | `game.py` (`update_ghost_speeds` / new accumulator) | `settings.py` (tunable) | Speed is *assigned* by `Game` per frame (`self.ghost_speeds`, `game.py:333-353`) and passed into the per-frame `Ghost`. `ghost.py` only *consumes* `self.speed`. Keep the change entirely in `Game` so `ghost.py` decision logic stays byte-identical. |
| Cornering window (FAIR-03) | `player.py` (`check_position`) | `settings.py` (tunable) | Turn-availability for the player is computed in `Player.check_position` (`player.py:43-91`), deliberately divergent from `Ghost.check_collisions` (D-15). |
| Determinism / regression net | `tests/` + `harness/` | CI (`.github/workflows/ci.yml`) | Golden traces, frame-hash, determinism guard, ghost micro-tests. The re-bless and "guard held" proofs live here. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| (none new) | — | — | This phase adds **zero** dependencies. All math is stdlib integer arithmetic already present in the sim. |

**Already in use (no version change):** `pygame` (2.6.1 per frame-hash contract, `test_frame_hash.py:21`), `pytest`, stdlib `hashlib`/`json`/`math`. `[VERIFIED: tests/test_frame_hash.py:21 names pygame 2.6.1 as the pinned CI version]`

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Integer-step accumulator (positions stay int) | Fractional ghost position (`x += 1.85`) | **Rejected** — breaks trace int-only contract (`harness/trace.py:7-8`), drifts ghost off the integer grid, risks skipping `% TILE` turn windows. See Pitfall 1. |
| Integer-rational accumulator (num/den, pure int) | Float accumulator (`acc += 1.85`) | Float accumulator is *acceptable* (positions stay int, CI is homogeneous Linux), but integer-rational keeps the "integer pixel math" doctrine literally true and adds no float to the sim hot path. Recommended. |
| Frame-cadence "skip-a-frame" stutter (move 2 or 0) | — | Viable arcade-authentic alternative, but produces a visible 1-frame freeze and synchronized stutter; the accumulator's 1px/2px steps are smoother. Listed as fallback. |

**Installation:** None. No `npm`/`pip` install for this phase. (Confirmed: no package legitimacy audit required — see below.)

## Package Legitimacy Audit

**Not applicable.** Phase 8 installs **no external packages** — it edits existing first-party modules (`game.py`, `player.py`, `settings.py`) and re-blesses committed golden fixtures. No registry, no `pip install`, no slopcheck surface. `[VERIFIED: codebase — change sites are all existing files]`

## Architecture Patterns

### System Architecture Diagram

```
                        ┌──────────────── one frame (Game.tick, game.py:485) ─────────────────┐
   keyboard ──KEYDOWN──▶ handle_events ──▶ player.direction_command (input buffer)             │
                        │                                                                       │
                        │  update_ghost_speeds() ──▶ self.ghost_speeds[i]                       │
                        │        │  (FAIR-02: integer-step accumulator rewrites the "2" tier    │
                        │        │   to a per-frame 1-or-2 step; leaves 1 and 4 untouched)       │
                        │        ▼                                                               │
                        │  create_ghosts() ──▶ Ghost(speed=ghost_speeds[i]) [recreated/frame]   │
                        │        │             └─ ghost.check_collisions() builds turns[]        │
                        │        │                (12<=center%TILE<=18 windows — UNCHANGED)       │
                        │        ▼                                                               │
                        │  player.check_position(level) ──▶ turns_allowed[]                      │
                        │        │  (FAIR-03: widen PLAYER-ONLY % TILE windows ± margin)          │
                        │        ▼                                                               │
                        │  player.move() / move_ghosts() ──▶ integer x/y advance by self.speed   │
                        │        ▼                                                               │
                        │  check_ghost_collisions(player_circle)                                 │
                        │        │  (FAIR-01: center-to-center squared-distance vs colliderect)  │
                        │        ├─ ghost-kills-player (normal)                                   │
                        │        ├─ ghost-kills-player (powerup, already-eaten)  ← D-04 symmetric │
                        │        └─ player-eats-ghost (powerup)                  ← D-04 same model │
                        │        ▼                                                               │
                        │  present_fn() ──▶ frame pixels  ──▶ (CI) frame-hash net                │
                        └────────────────────────────────────────────────────────────────────────┘
                                 capture_state() ──▶ int-only per-frame trace ──▶ (CI) golden net
```

### Component Responsibilities
| File:lines | Owns | FAIR change |
|------------|------|-------------|
| `game.py:333-353` `update_ghost_speeds` | Per-frame ghost speed tier (2 chase / 1 frightened / 4 eyes / 2 eaten-revived) | FAIR-02: rewrite the `==2` tier to accumulator step |
| `game.py:355-367` `create_ghosts` | Builds fresh `Ghost` each frame with `ghost_speeds[i]` | unchanged (consumes the new step value) |
| `game.py:400-436` `check_ghost_collisions` | Death + eat arbitration | FAIR-01: replace 3 groups of `colliderect` with center-distance |
| `player.py:43-91` `check_position` | Player `turns_allowed` incl. `% TILE` windows | FAIR-03: widen player-only windows |
| `player.py:109-117` `update_direction` | Consumes `direction_command` against `turns_allowed` | unchanged (benefits from the wider window) |
| `ghost.py` (entire) | Ghost decision logic, profiles, ladders, `% TILE` windows | **BYTE-IDENTICAL — do not touch** |
| `settings.py` | All tunables | add `GHOST_CATCH_DISTANCE`, ghost-speed tunable(s), `PLAYER_TURN_WINDOW_MARGIN` |

### Pattern 1: FAIR-01 — center-to-center squared-distance catch
**What:** Replace `player_circle.colliderect(ghost.rect)` with an integer squared-distance test between the two existing center points.
**Where:** `game.py:400-436` — three groups, all switched symmetrically (D-04):
1. normal ghost-kills-player (`game.py:403-406`)
2. powerup already-eaten ghost-kills-player (`game.py:411-414`)
3. player-eats-frightened-ghost loop (`game.py:425`)

**Grounding:**
- Player center exists: `player.center_x = x+23`, `player.center_y = y+24` (`player.py:24-29`). Always current on `self.player`.
- Ghost center exists: `ghost.center_x = x_pos+22`, `ghost.center_y = y_pos+22` (`ghost.py:284-285`).
- Both are integers → the test is integer-only → deterministic and platform-independent.

**Recommended form (planner turns into a helper, e.g. `_catches(self, ghost)`):**
```
dx = self.player.center_x - ghost.center_x
dy = self.player.center_y - ghost.center_y
caught = dx*dx + dy*dy <= GHOST_CATCH_DISTANCE * GHOST_CATCH_DISTANCE
```
Use the **squared** comparison (no `math.sqrt`) to stay integer-exact and avoid any float. `GHOST_CATCH_DISTANCE` default **15** (D-02; `HALF_TILE` is already 15 in `settings.py:21`). Tunable name e.g. `GHOST_CATCH_DISTANCE` in `settings.py` (D-03).

**Why this reads as "arcade-faithful safe":** centers one tile apart on a straight are 30px (horizontal `TILE_WIDTH`) or 28px (vertical `TILE_HEIGHT`) apart → both `> 15` → safe. A diagonal corner-kiss is `sqrt(30²+28²) ≈ 41px` → safe. Only an essentially-same-tile overlap (<15px) catches. Matches D-02 exactly.

**Bonus correctness note:** Using `self.player.center_x/center_y` instead of the passed `player_circle` rect is *safer* — during `eat_freeze` the player rect is not recomputed (`game.py:546-547`), but `check_ghost_collisions` is only called when `not eat_freeze` (`game.py:576`) and `self.player.center_*` is always live. The `player_circle` parameter may be left in the signature or dropped; prefer reading centers off `self.player`.

### Pattern 2: FAIR-02 — integer-step accumulator (THE #1 question, resolved)
**What:** Keep every ghost position a strict integer. Do not give a ghost a fractional speed. Instead, vary the per-frame **integer step** (1 or 2 px) so the long-run average for the chase tier is ~1.85 px/frame. Pac-Man stays at integer 2 (`PLAYER_SPEED` unchanged, D-07) → Pac-Man pulls away ~0.15 px/frame ≈ a corridor over a few seconds (subtle, D-06).

**Why fractional is wrong here (the trap):**
- The per-frame trace records ghost `x`/`y` as integers and depends on int-only comparison for platform independence (`harness/trace.py:7-8`). A float `x_pos` would serialize floats into `trace.jsonl` and break that contract.
- `ghost.check_collisions` reads tiles at `center // TILE` and gates turns on `12 <= center % TILE <= 18` (`ghost.py:322-380`). With integer speed-2 from even start positions the ghost reliably lands in those windows; a 1.85 step makes `center % TILE` drift non-periodically and can land the ghost off-grid, skipping a junction (the documented "drift off-grid / skip turn windows" risk).

**Why the integer-step accumulator is correct:**
- Positions stay integer → grid alignment preserved → all `% TILE` windows fire exactly as before in *kind* (only *when* shifts, which is an allowed outcome change).
- Max step is 2 and the window is 7 wide (`12,13,14,15,16,17,18`) → a 2px step can never jump over it; 1px steps land in-window *more* often, not less. **No new skip risk.**
- `ghost.py` is **not edited** — the step value is decided in `Game` *before* `create_ghosts`. The byte-identical-decision-logic guard is therefore trivially satisfied and the 15 ghost micro-tests (which pass `speed=2` directly, `tests/test_ghost_micro.py`) stay green untouched — that is the *proof* the guard held.

**Recommended implementation (all in `game.py` + `settings.py`):**
1. Add per-ghost accumulator state to `Game.__init__`: `self.ghost_step_acc = [0, 0, 0, 0]` (integer-rational) — placed near `self.ghost_speeds` (`game.py:77`).
2. In/after `update_ghost_speeds` (`game.py:333-353`), for every ghost whose computed tier speed `== 2` (this uniquely identifies the *lethal chase* tier in BOTH the default-chase case AND the eaten-revived-during-powerup case at `game.py:338-345`), replace the `2` with an accumulator step:
   ```
   acc[i] += GHOST_CHASE_SPEED_NUM            # e.g. 37
   step = acc[i] // GHOST_CHASE_SPEED_DEN     # e.g. // 20  -> 1 or 2
   acc[i] -= step * GHOST_CHASE_SPEED_DEN
   ghost_speeds[i] = step
   ```
   Leave tier `1` (frightened, D-08) and `4` (eyes, D-08) exactly as-is.
3. Tunable in `settings.py`: `GHOST_CHASE_SPEED_NUM = 37`, `GHOST_CHASE_SPEED_DEN = 20  # 37/20 = 1.85 px/frame avg`. To dial during the D-10 playtest the user edits the numerator (each +1 ≈ +0.05 px/frame). **Pure integer math — no float, no new import, cannot trip the determinism guard.**

**Tunability alternative (if a single readable number is preferred):** keep `GHOST_CHASE_SPEED = 1.85` as a float constant and accumulate with float (`acc += 1.85; step = int(acc); acc -= step`). This is still safe because positions stay integer and the only float lives in a hidden, *untraced* accumulator, and CI is a single homogeneous Linux env. The integer-rational form is recommended over this purely to honor the "integer pixel math" doctrine literally. `[ASSUMED]` that the user prefers integer-rational — confirm during planning; either is determinism-safe.

**Gating detail (important for determinism):** advance the accumulator **only on frames where ghosts actually move** — mirror the existing `self.moving and not self.eat_freeze` guard around `move_ghosts()` (`game.py:573-575`). Advancing during `starting`/`dying`/`eat_freeze`/box-wait would bank phantom credit and cause a burst of 2-steps afterward. Also reset `self.ghost_step_acc = [0,0,0,0]` in `reset_after_death` (`game.py:133-141`) to keep determinism crisp across lives (start positions are even integers, so no drift accumulates anyway).

**Frame-cadence fallback (Option A, if the accumulator is rejected):** keep integer speed 2 but skip the ghost move on ~3 of every 20 moving frames (`step pattern indexed by a frame counter`), average `2 * 17/20 = 1.7`… tune the skip count. Smoother to reason about but produces a visible synchronized 1-frame stutter; the accumulator is preferred.

### Pattern 3: FAIR-03 — widen the player-only pre-turn window
**What:** A queued perpendicular turn becomes available a few pixels earlier by widening the player's `12 <= center % TILE <= 18` bands. **Player path only** — `ghost.py`'s identical-looking windows (`ghost.py:343,352,363,372`) must stay byte-identical (the decision-logic guard, and D-15 already forbids merging the two routines).

**Where:** `player.check_position` (`player.py:43-91`). There are **four** `12 <= … <= 18` window expressions across the two direction blocks:
- moving vertical (dir 2/3): `player.py:65` (`centerx % TILE_WIDTH`) and `player.py:70` (`centery % TILE_HEIGHT`)
- moving horizontal (dir 0/1): `player.py:76` (`centerx % TILE_WIDTH`) and `player.py:81` (`centery % TILE_HEIGHT`)

**Recommended form:** introduce `PLAYER_TURN_WINDOW_MARGIN = 6` in `settings.py` (D-09, ~4–6px) and widen all four player windows to:
```
(12 - PLAYER_TURN_WINDOW_MARGIN) <= center % TILE <= (18 + PLAYER_TURN_WINDOW_MARGIN)
```
**Recommendation: symmetric widening** (both edges). Rationale: it forgives both slightly-early and slightly-late human input (FAIR-03's "register the queued direction a few pixels early" + "smooth corner-cutting"), is a one-line change per site, and the inner wall guard (`level[...] < 3`) still prevents turning into a wall — widening only enlarges the *timing* window, never permits an illegal turn. Default margin 6 → window opens at residue 6 instead of 12 (≈6px early) and closes at 24 instead of 18.

**Strictly-early alternative (if symmetric feels auto-steered during D-10):** widen only the leading edge in the travel direction (low edge when moving right/down, high edge when moving left/up). More faithful to "pre-turn only" but direction-dependent and more code. Start symmetric; let the playtest decide.

**Do NOT** factor this into a shared helper with `Ghost.check_collisions` — D-15 explicitly keeps them divergent, and sharing would change ghost decision logic.

### Anti-Patterns to Avoid
- **Fractional ghost `x_pos`/`y_pos`.** Breaks the int-only trace contract and grid alignment. (Pitfall 1.)
- **Editing `ghost.py` for FAIR-02.** Any edit there risks the byte-identical guard and breaks the proof value of the green ghost micro-tests. Do all FAIR-02 work in `game.py`.
- **Touching the ghost `% TILE` windows for FAIR-03.** Cornering forgiveness is a *player* affordance only.
- **Re-blessing per change / on Windows.** One bless, Linux/Docker, after sign-off (D-10).
- **Adding `math.sqrt` / float distance for FAIR-01.** Use squared integer comparison.
- **Tunables as inline magic numbers.** All three go in `settings.py` (D-03/D-07/D-09).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Sub-unit average speed on an integer grid | A fractional position with float `x_pos` | Integer-step accumulator (this codebase's own pattern: speed is already an int passed per frame) | Floats break the trace contract + grid alignment; the engine is built on integer steps. |
| Distance test | `math.hypot` / `sqrt` | `dx*dx + dy*dy <= R*R` | Integer-exact, no float, faster, deterministic. |
| Re-recording goldens | Hand-editing `trace.jsonl` / `frame_hashes.txt` | `pytest --bless` (registered, `tests/conftest.py:59-62`) | The harness re-records correctly and prints a diff. |
| Cross-platform frame-hash truth | Blessing pixels on Windows | Bless in the Linux pinned CI/Docker env | Font rasterization differs across SDL builds; only Linux-pinned hashes are the committed truth (`test_frame_hash.py:18-31`). |

**Key insight:** This engine already *has* the right primitive (an integer per-frame `speed` assigned by `Game`). FAIR-02 is not "make the ghost slower," it's "make the average step 1.85 while every actual step stays an integer." That reframing is the whole solution.

## Common Pitfalls

### Pitfall 1: Fractional ghost speed drifts off-grid and poisons the trace
**What goes wrong:** Setting `ghost.speed = 1.85` makes `x_pos`/`y_pos`/`center_*` fractional; `center % TILE` no longer reliably lands in `12..18`, so a ghost overshoots junctions and can pin to a corridor; and the trace serializes floats, breaking int-only platform-independent comparison.
**Why it happens:** The `% TILE` windows and the trace schema both silently assume integer positions (`ghost.py:343`, `harness/trace.py:7-8`).
**How to avoid:** Integer-step accumulator (Pattern 2). Positions never leave the integers.
**Warning signs:** `trace.jsonl` lines containing decimal points; a ghost test where a ghost stops turning at intersections; determinism test flaking.

### Pitfall 2: Re-bless is NOT purely mechanical — terminal scenarios may stop terminating
**What goes wrong:** FAIR-01 (tighter catch) + FAIR-02 (slower ghosts) make Pac-Man harder to kill. The `death` scenario (`manifest.json`, the only `terminal: "game_over"`, frame_cap 4200) replays *recorded inputs*; if those inputs relied on the old wide AABB or equal speed to make contact, the new run may **never reach `game_over`** → `assert_invariants` fails with "death did not reach game_over" (`test_golden_traces.py:171-173`). Symmetrically, `ghost_eat` (fixed_frames) may no longer register its scripted eat under the 15px radius.
**Why it happens:** Golden inputs are frozen key events; the *outcome* of those inputs is exactly what this phase changes.
**How to avoid:** Before/at re-bless, explicitly verify each terminal-dependent scenario still reaches its terminal: `death` still dies, `ghost_eat` still eats, `win` still runs its full window. If not, that scenario's `input.jsonl` must be **re-authored** (a headless re-capture, larger than `--bless`). Plan a verification task for this; do not assume `pytest --bless` alone suffices.
**Warning signs:** A `--bless` run where `death` produces a 4200-frame trace that never sets `game_over`; soft-lock backstop tripping; `ghost_eat` trace showing no `dead=True` flip.

### Pitfall 3: Frame-hash must be blessed in the Linux pinned env, never Windows
**What goes wrong:** Blessing `frame_hashes.txt` on the Windows playtest machine mints hashes that disagree with CI (font rasterization differs), turning CI red.
**Why it happens:** `freesansbold.ttf` HUD text rasterizes differently across SDL builds (`test_frame_hash.py:18-31`); only Linux-pinned hashes are authoritative.
**How to avoid:** Run the bless in `python:3.12` Docker on Linux (project memory `golden-rebless-linux-docker.md`) or directly in CI; CI is `ubuntu-latest` / Python 3.12 / `SDL_*=dummy` (`.github/workflows/ci.yml`). State traces are int-only and platform-independent, but bless them in the same Linux pass for consistency.
**Warning signs:** Local Windows bless changing `frame_hashes.txt`; CI frame-hash assertion failing on the first push after an off-platform bless.

### Pitfall 4: Accumulator advancing during pauses
**What goes wrong:** If the step accumulator advances on non-moving frames (`starting`/`dying`/`eat_freeze`/box-wait), it banks credit and emits a burst of 2-steps when motion resumes, subtly changing outcomes and making the speed feel uneven.
**How to avoid:** Advance only under the same `self.moving and not self.eat_freeze` guard that gates `move_ghosts()` (`game.py:573-575`); reset the accumulator in `reset_after_death` (`game.py:133-141`).
**Warning signs:** Ghosts lurching after the READY!/eat-freeze pause.

## Runtime State Inventory

> This is a code-and-fixtures phase, not a rename/migration. Included for completeness; the only "stored state" is the committed golden fixtures.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | **None** — game has no runtime DB for sim state. Identity/leaderboard files are unrelated to gameplay sim. | none |
| Live service config | **None** — no external service participates in the offline sim. | none |
| OS-registered state | **None.** | none |
| Secrets/env vars | **None** relevant. (HMAC secret is leaderboard-only; untouched.) | none |
| Build artifacts / committed fixtures | **9× `tests/golden/*/trace.jsonl` + 9× `tests/golden/*/frame_hashes.txt`** encode the OLD outcomes; all three FAIR-* changes shift them. | Single Linux/Docker `pytest --bless` after D-10 sign-off, commit updated fixtures. |

## Code Examples

> No external API examples apply (no libraries). The "examples" are the verified change sites, cited above:
- FAIR-01 catch sites: `game.py:403-406`, `game.py:411-414`, `game.py:425`.
- FAIR-02 speed assignment: `game.py:333-353` (`update_ghost_speeds`), consumed at `game.py:356-367` (`create_ghosts`) and `game.py:373-391` (`move_ghosts`). Movement primitive uses `g.speed` at `ghost.py:69-79`.
- FAIR-03 windows: `player.py:65,70,76,81`. Player input buffer: `direction_command` set in `handle_events` (`game.py:453-460`), consumed in `update_direction` (`player.py:109-117`).
- Ghost windows to leave untouched: `ghost.py:343,352,363,372`.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| AABB `colliderect` 40×40 vs 36×36 | center-to-center squared distance | this phase (FAIR-01) | corner-kisses become safe |
| Pac-Man and ghosts both speed 2 | Pac 2, chase ghosts ~1.85 avg via integer-step accumulator | this phase (FAIR-02) | escape becomes possible, grid + determinism preserved |
| Turn only inside `12..18` at-junction | player window widened ±margin | this phase (FAIR-03) | early/forgiving cornering, player-only |

**Deprecated/outdated:** none — nothing is removed; three mechanics are retuned behind named constants.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | User prefers the integer-rational accumulator (num/den) over a single float constant for the ghost-speed tunable | Pattern 2 | Low — both are determinism-safe; only affects how the D-10 dial is expressed. Confirm in planning. |
| A2 | The eaten-revived-during-powerup ghost (the `==2` set at `game.py:338-345`) *should* also be slowed, since it is a lethal chaser (D-04) | Pattern 2 | Low–Med — if the user wants only the default-chase tier slowed, the rule must key on context, not just `==2`. Recommend slowing all `==2`; flag for confirmation. |
| A3 | Symmetric window widening (both edges) is acceptable for FAIR-03 vs strictly-early | Pattern 3 | Low — tunable/reversible during D-10; strictly-early variant documented as fallback. |
| A4 | The `death` and `ghost_eat` scenarios may need input re-authoring (not just `--bless`) — stated as a *risk to verify*, not a certainty | Pitfall 2 | Med — must be checked empirically at bless time; the plan should include the verification task regardless. |

## Open Questions

1. **Does the `death` scenario still reach `game_over` after FAIR-01+FAIR-02?**
   - What we know: it's the only `game_over` terminal, frame_cap 4200; tighter catch + slower ghosts make death less likely.
   - What's unclear: whether its recorded inputs still force contact within the cap.
   - Recommendation: verify empirically during the bless task; if not, re-record `tests/golden/death/input.jsonl`. (Same check for `ghost_eat`.)

2. **Should the eaten-revived chaser be slowed (A2)?**
   - Recommendation: yes, slow every `==2` tier uniformly; confirm with user during planning/playtest.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (`.venv`) | run game + pytest | ✓ (per project memory `venv-is-real-python-env.md`) | 3.12/3.13 local | — |
| pytest + `--bless` flag | golden net + re-bless | ✓ | registered `tests/conftest.py:59-62` | — |
| pygame | sim + frame-hash | ✓ | 2.6.1 pinned in CI | — |
| Linux + Docker `python:3.12` | **frame-hash re-bless (mandatory env)** | ⚠ must be invoked | — | run bless directly in CI (`ubuntu-latest`, `.github/workflows/ci.yml`) |
| Windows (`python main.py`) | D-10 playtest | ✓ | — | — |

**Missing dependencies with no fallback:** none.
**Note:** the re-bless *cannot* be done on the Windows playtest machine for the frame-hash manifests (Pitfall 3). Linux/Docker or CI is required.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (CI: Python 3.12, pygame 2.6.1, `SDL_*=dummy`) |
| Config file | `tests/conftest.py` (registers `--bless`); CI `.github/workflows/ci.yml` |
| Quick run command | `.venv/Scripts/python.exe -m pytest tests/test_ghost_micro.py tests/test_determinism_guard.py -q` |
| Full suite command | `.venv/Scripts/python.exe -m pytest -q` (frame-hash asserts only in pinned CI env) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FAIR-01 | center-distance catch; corner-kiss safe; eat still works | unit + golden | new unit on `check_ghost_collisions` catch helper + `pytest -k "death or ghost_eat"` | ❌ unit (Wave 0) / ✅ golden (re-bless) |
| FAIR-02 | chase ghosts avg ~1.85, integer positions, Pac pulls away | unit + golden | new unit asserting the accumulator yields the expected integer step *sequence* + `pytest -k baseline` | ❌ unit (Wave 0) / ✅ golden (re-bless) |
| FAIR-02 guard | ghost decision logic byte-identical | characterization | `pytest tests/test_ghost_micro.py` **must stay green with zero edits** | ✅ (proof artifact) |
| FAIR-02 guard | no nondeterminism introduced | static | `pytest tests/test_determinism_guard.py` **must stay green** | ✅ |
| FAIR-03 | player turn registers ~4–6px early; ghost windows unchanged | unit + golden | new unit on `Player.check_position` window + `pytest -k baseline` | ❌ unit (Wave 0) / ✅ golden (re-bless) |

### Sampling Rate
- **Per task commit:** `pytest tests/test_ghost_micro.py tests/test_determinism_guard.py -q` (fast guard that the byte-identical + determinism invariants still hold).
- **Per wave merge:** full suite green (golden net skips frame-hash off-CI, asserts state traces).
- **Phase gate:** full suite green in the pinned CI env *after* the single re-bless; ghost micro-tests + determinism guard green **without** re-bless.

### Wave 0 Gaps
- [ ] `tests/test_player_micro.py` (or extend an existing player test) — characterization for the new cornering window: assert `Player.check_position` yields the widened `turns_allowed` at a chosen junction with `PLAYER_TURN_WINDOW_MARGIN`, and assert a default-margin baseline. **No player-level characterization test exists today** (verified — `tests/` has none), so FAIR-03 is otherwise guarded only by the golden traces.
- [ ] Unit test for the FAIR-02 accumulator: feed N frames, assert the produced integer step sequence and that the running average converges to `NUM/DEN`. Pure-Python, no pygame.
- [ ] Unit test for the FAIR-01 catch helper: corner-kiss (diagonal one-tile) → not caught; same-tile overlap → caught; using crafted `center_*` values.
- [ ] (Verification task, not a file) confirm `death` / `ghost_eat` still reach their scripted outcome post-change; re-author input if not (Pitfall 2).

## Security Domain

> `security_enforcement: true`, `security_asvs_level: 1`. This phase has effectively **no new attack surface**: it is offline single-player simulation math. No network, no persistence, no untrusted input enters here (the only input is local keyboard, already handled).

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (leaderboard/identity untouched) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | minimal | local keyboard only; `MAX_SCORE` score-range invariant already enforced in the golden net (`test_golden_traces.py:43,113-117`) |
| V6 Cryptography | no | — (HMAC leaderboard path not touched) |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Score overflow / impossible score | Tampering | existing `0 <= score <= MAX_SCORE` per-frame invariant (unchanged) |
| Nondeterminism injection (would silently void the regression net) | Tampering | static determinism guard `test_determinism_guard.py` — FAIR changes add no forbidden token (pure integer math, no new import) |

No security blockers. `security_block_on: high` — nothing in this phase reaches that bar.

## Sources

### Primary (HIGH confidence)
- Codebase (read directly this session): `game.py` (collision `400-436`, speeds `333-353`, tick `485-591`), `ghost.py` (mover `390-415`, windows `343+`, centers `284-285`, profiles `247-276`), `player.py` (`check_position 43-91`, `update_direction 109-117`, centers `24-29`), `settings.py` (`PLAYER_SPEED 10`, `HALF_TILE 21`, tile dims `19-21`).
- Test harness: `harness/trace.py:7-8,42-52` (int-only trace contract), `tests/test_golden_traces.py` (`--bless`, terminal assertions `171-179`), `tests/test_frame_hash.py:18-31` (Linux-pinned platform contract, pygame 2.6.1), `tests/test_determinism_guard.py:22-25` (forbidden tokens), `tests/test_ghost_micro.py` (speed=2 characterization, byte-identical proof), `tests/golden/manifest.json` (9 scenarios; `death` is the only `game_over`).
- `.github/workflows/ci.yml` (ubuntu-latest / Python 3.12 / SDL dummy).
- Planning docs: `08-CONTEXT.md` (D-01…D-10), `REQUIREMENTS.md` (FAIR-01/02/03), `ROADMAP.md` (Phase 8 success criteria), `STATE.md`, `CLAUDE.md` (Ghost System, golden-net invariants).
- Project memory: `golden-rebless-linux-docker.md`, `venv-is-real-python-env.md`, `plan-crlf-breaks-musthaves-parse.md`.

### Secondary (MEDIUM confidence)
- Arcade reference (Pac 80% / ghost 75% relationship) — used only to validate that "~1.85 from 2" is in the right ballpark; the exact value is a D-10 dial, so currency doesn't matter.

### Tertiary (LOW confidence)
- None relied upon.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; all change sites read and confirmed.
- Architecture (FAIR-01/02/03 approach): HIGH — grounded in actual code + the trace/determinism contracts that constrain it.
- Pitfalls: HIGH for the determinism/trace reasoning; the terminal-scenario re-authoring risk (Pitfall 2) is HIGH-importance but its *occurrence* is MEDIUM (must be verified empirically at bless).

**Research date:** 2026-06-29
**Valid until:** stable indefinitely (self-contained, no fast-moving external deps) — re-verify only if the trace schema or golden manifest changes.
