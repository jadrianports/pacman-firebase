# Phase 8: Fairness Pass - Context

**Gathered:** 2026-06-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the game **feel fair and escapable** by changing three mechanics — collision math, ghost
speed, and the turn-input window — so the player can round corners safely, outrun a chasing
ghost, and turn smoothly. Delivers FAIR-01, FAIR-02, FAIR-03.

**Hard guardrail (core value):** these change ghost **outcomes** (positions, who-catches-whom)
but **never** ghost **decision logic** — targeting and the per-ghost `*_PROFILE`s (`BLINKY_PROFILE`
/ `INKY_PROFILE` / `PINKY_PROFILE` / `CLYDE_PROFILE`) stay byte-identical. This is the v1.0 Phase-3
box-fix pattern: a sanctioned, isolated, oracle-scoped behavior change.

**Re-bless discipline (locked, not up for discussion):** all three FAIR-* changes batch behind a
**single** deliberate golden-net re-bless, run **only on Linux/Docker, never on Windows, never
per-change**. The re-bless happens **after** the feel is playtested and signed off (see D-10).

</domain>

<decisions>
## Implementation Decisions

### Catch tightness (FAIR-01)
- **D-01:** Replace the AABB overlap catch (`player_circle.colliderect(ghost.rect)`) with a
  **center-to-center distance** test between Pac-Man and each ghost.
- **D-02:** Tightness = **tight / arcade-faithful**, target ~**14–16px** center distance (≈ half a
  tile; `HALF_TILE`-ish). Ghost must be essentially on the player's tile to catch. This intentionally
  allows slight *visual* sprite overlap before a catch — arcade-authentic (real Pac-Man sprites are
  bigger than the collision tile). Diagonal corner-kisses must read as SAFE.
- **D-03:** Expose the catch threshold as a **named tunable constant** in `settings.py` (not a magic
  number), so the exact pixel value can be dialed in during playtest.
- **D-04:** Apply the new distance test to **all** existing catch checks symmetrically — the normal
  "ghost kills player" path AND the powerup-mode "already-eaten ghost kills player" path
  (`game.py:400-413`). Eating a frightened ghost (player catches ghost) uses the same model.

### Escape speed gap (FAIR-02)
- **D-05:** Root cause confirmed in code: Pac-Man and ghosts are **both speed 2** (equal), so a
  trailing ghost holds distance forever and escape on a straight is impossible. That equal-speed
  state is the "unbeatable" feeling — not a literal ×2 chase tier.
- **D-06:** Fix by making Pac-Man **a hair faster** than chasing ghosts — **subtle / arcade-faithful**
  (~5–10% edge; arcade reference is Pac 80% vs ghost 75%). You pull away gradually over a full
  corridor; tension is preserved, escape is real.
- **D-07:** Implement by **keeping `PLAYER_SPEED = 2` unchanged** (so the controls feel identical in
  the player's hands) and **slowing the chasing ghosts** to ~1.85. Expose the ghost speed factor as
  a tunable.
- **D-08:** **Leave the eyes-return speed (dead-ghost = 4) untouched** — those are returning eyes,
  they cannot catch the player, so they are not part of the "unbeatable" problem. Powerup-slow
  (ghost = 1) behavior unchanged in intent.

### Corner forgiveness (FAIR-03)
- **D-09:** Add a **pre-turn window** so a queued turn registers a few pixels **before** the junction
  instead of only inside the current ~7px at-junction window (`12 <= center % TILE <= 18`). Feel =
  **snappy / arcade-faithful**, target window opening ~**4–6px early** — forgives normal human timing
  and kills overshoot without feeling "auto-steered." Build on the existing input buffer
  (`direction_command` / `update_direction`), exposed as a tunable.

### Tuning loop & sequencing
- **D-10:** Workflow = **Build → playtest → re-bless.** (1) Implement all three with arcade-faithful
  defaults as named tunable constants in `settings.py`. (2) User playtests on **Windows**
  (`python main.py`) and adjusts constants until it feels right. (3) User signs off on the feel.
  (4) **Only then** run the single golden-net re-bless on Linux/Docker. Do NOT re-bless against
  unsigned-off interim numbers.

### Claude's Discretion
- Exact final pixel/factor values within the stated ranges (D-02 ~14–16px, D-07 ~1.85, D-09 ~4–6px)
  are starting points; the user dials them in during the D-10 playtest. Planner should pick clean
  arcade-faithful defaults and make them trivially editable.
- Corner-window mechanic (FAIR-03) was a "you decide" — lean snappy/arcade-faithful as above.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & requirements
- `.planning/ROADMAP.md` — Phase 8 "Fairness Pass" goal + 5 success criteria (incl. the byte-identical
  decision-logic guard and the single-re-bless criterion).
- `.planning/REQUIREMENTS.md` — FAIR-01, FAIR-02, FAIR-03 acceptance statements.
- `.planning/PROJECT.md` — Key Decisions row: "v1.2 fairness may alter ghost *outcomes* but never
  *decision logic*"; milestone framing and the hitbox/equal-speed diagnosis.
- `.planning/STATE.md` — standing v1.2 constraints (golden net = merge gate; re-bless Linux/Docker
  only; Phase 8 batches all 3 FAIR-* behind ONE re-bless).

### Golden-net / re-bless discipline
- `CLAUDE.md` — Ghost System + golden-net invariants; frame-hash net hashes pixels.
- Re-bless procedure: golden traces re-blessed **on Linux only**, via a `python:3.12` Docker
  container — never on Windows (see project memory `golden-rebless-linux-docker.md`).

No external/third-party specs — this is a self-contained gameplay-tuning phase; all requirements are
captured in the decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets / exact change sites
- **Collision (FAIR-01):** `game.py:400-413` `check_ghost_collisions(player_circle)` — currently
  `player_circle.colliderect(self.<ghost>.rect)` AABB across normal + powerup paths. Player rect =
  `40×40` centered (`player.py:32-41`, `center_x = x+23`, `center_y = y+24`). Ghost rect =
  `36×36` centered (`ghost.py:284-285, 300, 309`, `center_x = x_pos+22`). Both expose `center_x/
  center_y` already → center-distance test is a clean drop-in.
- **Speed (FAIR-02):** `settings.py:10` `PLAYER_SPEED = 2`. `game.py:333-353` `update_ghost_speeds()`
  sets `[2,2,2,2]` normal, `[1,1,1,1]` powerup, `4` per dead ghost (eyes return). This is where the
  ghost chase speed is set; the eyes-return `4` must be left alone (D-08).
- **Cornering (FAIR-03):** `player.py:44-90` `check_position()` builds `turns_allowed` using the
  `12 <= center % TILE <= 18` at-junction window; `player.py:94-101` `move()`, `109-117`
  `update_direction()` consume the `direction_command` input buffer. Ghosts share the same
  `12 <= center % TILE <= 18` window pattern (`ghost.py:343`) — pre-turn change should target the
  **player** path so ghost decision logic stays byte-identical.

### Established Patterns
- All magic dimensions/speeds live in `settings.py` (centralized) — new tunables belong there.
- Engine is **fully deterministic** (integer speeds, fixed-timestep frame counters, no `random`/
  wall-clock). This is what makes the golden net frame-perfect.

### Integration Points / risk flags for research
- **Sub-pixel ghost speed (~1.85) vs integer grid:** ghost movement and the `% TILE` turn windows
  assume integer steps. Fractional ghost speed needs careful sub-pixel accumulation or it can skip
  turn windows / drift off-grid. **Researcher must resolve** how to make ghosts slightly slower while
  keeping grid alignment and determinism intact.
- **Re-bless scope:** all three changes shift the `chase`/`ghost_eat`/`death` golden traces — expect
  the single Linux/Docker re-bless to touch most/all 9 traces + frame-hash manifests. The
  determinism guard must still pass.

</code_context>

<specifics>
## Specific Ideas

- "Arcade-faithful" is the throughline for all three dials: catch ≈ tile-based (sprites overlap
  before catch), speed ≈ Pac 80% / ghost 75% relationship, cornering ≈ classic snappy pre-turn.
- The intended player experience: *"if I wasn't basically on the same square I should live,"* *"I can
  slowly pull away if I commit to a route,"* and *"my turn lands even if I input it a touch early."*

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (Scatter/chase waves, arcade-accurate targeting mode,
content/fruit, and multiplayer remain explicitly out of scope per REQUIREMENTS.md.)

</deferred>

---

*Phase: 8-Fairness Pass*
*Context gathered: 2026-06-29*
