# Phase 9: Arcade Juice - Context

**Gathered:** 2026-06-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Add cosmetic game-feel polish — a Pac-Man **death animation**, a distinct **eat-ghost sound**, a
**frightened-end warning flash**, and (already shipped) the eat-ghost popup and "READY!" intro.
Delivers FEEL-01..FEEL-05.

**Hard guardrail (golden-safe, locked — ROADMAP SC5 + standing v1.2 constraint):** every **visual**
effect rides the existing `Game.juice` firewall (default `False`). The `juice=False` path keeps
today's plain rendering, so the golden **state** traces AND the pixel **frame-hash** net stay green
with **NO re-bless**. Audio (the eat-ghost sound) is exempt — sound never touches the hashed paths
(headless uses an SDL dummy audio driver; frame-hash hashes pixels only).

**Scope reality check (verified in code during discussion):** this phase is **narrower** than the
roadmap implies. The `Game.juice` firewall, `juice.py` (glow/particles/shake/bloom), and `theme.py`
(pixel font) all already shipped via the earlier "Bold" UI redesign (commits `6ad8091`, `d817e34`,
etc., on `main`). **FEEL-02** (eat popup + 45-frame freeze) and **FEEL-05** ("READY!" beat) are
**already implemented** in `game.py` and accepted as-is. The real work is FEEL-01, FEEL-03, FEEL-04.

</domain>

<decisions>
## Implementation Decisions

### Firewall gating (locked, not discussed — flows from ROADMAP SC5)
- **D-01:** All three new **visual** effects (death animation, frightened flash; the eat popup is
  already done) render **only when `juice=True`**. The `juice=False` path is unchanged. This is what
  keeps the golden state traces + frame-hash net green with no re-bless.
- **D-02:** The eat-ghost **sound** (FEEL-03) is **not** firewall-gated — it plays in normal play like
  the other SFX (waka/death/powerup). Audio doesn't affect determinism or pixel hashes.

### Death animation (FEEL-01)
- **D-03:** Style = **classic arcade wedge spin** — Pac-Man's mouth opens wider as the wedge rotates,
  shrinking to a point, then vanishes. Drawn **programmatically** with pygame arcs (only 4 chomp
  sprites exist — `assets/pacman/1-4.png` — there are no death frames). Matches the phase-8
  "arcade-faithful" throughline.
- **D-04:** Timing = **fill the `death.wav` window** — the animation plays across the existing `dying`
  phase (which already blocks until `death.wav` finishes via `sound.is_death_playing()`), then the
  current +60-frame pause and reset. Sound and visuals end together.
- **D-05:** Replaces the normal `player.draw()` only while `dying and juice` — under `juice=False`,
  `dying` renders exactly as today (player sprite held), so the `death` golden/frame-hash terminal is
  untouched.

### Frightened-end flash (FEEL-04)
- **D-06:** Trigger = **last ~2 seconds (~120 frames) of the power window** — arcade-faithful. The
  power window is 600 frames (`power_counter`), so blink when `power_counter > ~480`. Expose the
  threshold as a **named tunable** in `settings.py` (phase-8 FAIR-* pattern) so it can be dialed.
- **D-07:** Look = **Claude's discretion** — planner picks the cleanest approach (likely a white tint
  of the existing `spooked_img`, alternating spooked-blue ↔ white every few frames). No hard
  requirement for a new white sprite asset if a tint works.
- **D-08:** Only renders under `juice=True` (per D-01). Under `juice=False`, `Ghost.draw()` blits the
  steady `spooked_img` exactly as today.

### Eat-ghost sound (FEEL-03)
- **D-09:** Source = **find a CC0 / freely-licensed retro "eat-ghost" `.wav`** and add it to
  `assets/audio/`. Fits the existing `SoundManager` `.wav`-loader pattern. **Runtime tone-synthesis
  was rejected** — `numpy`/`pygame.sndarray` are not installed and adding them violates the "avoid new
  client runtime deps without strong reason" constraint.
- **D-10:** Wire a new `SoundManager.play_eat_ghost()` and fire it on the bite (in
  `check_ghost_collisions`, where `eat_freeze` is already set, `game.py:464-476`). User verifies
  licensing + feel during playtest.

### Claude's Discretion
- FEEL-04 blink look/cadence (D-07) and the exact white/tint mechanism.
- FEEL-03 sound mix vs the powerup siren (D-10): the bite already pauses the siren for the freeze and
  unpauses after — planner picks the cleanest channel/timing so the bite is audible.
- Exact death-wedge geometry/arc math and frame cadence within the `death.wav` window (D-04).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope & golden-safety contract
- `.planning/ROADMAP.md` — Phase 9 "Arcade Juice" goal + 5 success criteria. **SC5 is the binding
  contract:** all FEEL effects ride the `Game.juice` firewall; `juice=False` stays byte-identical
  (state traces + pixel frame-hash) with no re-bless; the eat-freeze must not alter the deterministic
  sim under `juice=False`.
- `.planning/REQUIREMENTS.md` — FEEL-01..FEEL-05 acceptance statements.
- `.planning/PROJECT.md` — milestone framing ("juice that's missing", pure game-feel); Key Decisions
  row "Game-feel before content/multiplayer".
- `.planning/STATE.md` — standing v1.2 constraints; the explicit **Phase 9 risk** note: the eat-ghost
  "brief freeze" (FEEL-02) must not shift the deterministic sim under `juice=False`, and `eat_freeze*`
  scaffolding already exists in `game.py`.

### Golden-net / frame-hash discipline
- `CLAUDE.md` — Sound System (`SoundManager`, dedicated channels) + the note that the frame-hash net
  hashes PIXELS (`sha256(tobytes(surface,'RGB'))`); juice rides the firewall.
- Re-bless procedure (only relevant if a regression forces it): Linux/Docker only, never Windows
  (project memory `golden-rebless-linux-docker.md`). **Expectation for this phase: no re-bless at all.**

No external/third-party specs — this is a self-contained game-feel phase. The eat-ghost `.wav` will be
a newly-sourced CC0 asset (license to be recorded at add time).

</code_context>

<code_context>
## Existing Code Insights

### Reusable Assets / exact change sites
- **Juice firewall + toolkit (already shipped):** `Game.juice` (`game.py:116`, default `False`);
  `juice.py` — `glow_circle`, `Particles`, `Shake`, `bloom` (seeded `_rand`, no wall-clock);
  `theme.py` — pixel font. `main.py` sets `juice=True` for real play; tests run `juice=False`.
  Firewall is covered by `tests/test_juice_firewall.py` (+ `test_juice.py`, `test_theme.py`).
- **FEEL-01 death (NOT built):** `Game.start_dying()` (`game.py:419-424`) just sets `dying`, stops
  movement, plays `death.wav`. The `dying` phase loop is `game.py:566-578` (waits on
  `sound.is_death_playing()` then +60 frames). Player is drawn normally at `game.py:587` via
  `player.draw(counter)` (`player.py:32-42`) — only 4 chomp frames, no death frames. New wedge-spin
  draw must branch on `dying and self.juice`.
- **FEEL-03 sound (NOT built):** `SoundManager` (`sound.py`) loads `.wav` from `assets/audio/`
  (currently start/wakawaka/powerup/death only). Add the new `.wav` + a `play_eat_ghost()` method;
  fire it in `check_ghost_collisions` at the eat branch (`game.py:464-476`), beside the existing
  `stop_waka()`/`pause_powerup()`.
- **FEEL-04 frightened flash (NOT built):** `Ghost.draw()` (`ghost.py:302-309`) blits `spooked_img`
  whenever `powerup and not dead and not eaten`. The power timer is `Game.power_counter` (0→600,
  `game.py:548-552`). Flash needs the near-expiry blink gated behind `juice` — and the ghost only
  knows `powerup`, so the blink phase/`power_counter` (or a derived "ending" flag) must be threaded
  into the `Ghost` constructor (`ghost.py:280-300`, created fresh each frame in
  `Game.create_ghosts()` `game.py:381-393`).
- **Already-done (accepted as-is):** FEEL-02 eat popup + 45-frame freeze
  (`eat_freeze*` state `game.py:89-92`; set `464-476`; tick `541-545`; render `591-604`). FEEL-05
  "READY!" beat (`draw_ready()` `game.py:198-202`, shown during the `starting` pause).

### Established Patterns
- All tunables live in `settings.py` (centralized) — the FEEL-04 blink threshold belongs there
  (mirrors the phase-8 `GHOST_CATCH_DISTANCE` / `PLAYER_TURN_WINDOW_MARGIN` tunables).
- Engine is fully deterministic (integer steps, fixed-timestep counters, no `random`/wall-clock).
  Juice keeps its own seeded `_rand` strictly outside the hashed paths.
- `Ghost` objects are recreated every frame from `Game` state — any new per-ghost render input
  (e.g. "power ending") must be passed through the constructor, not stored on the ghost.

### Integration Points / risk flags for research
- **Eat-freeze golden-safety (carry-over risk from STATE.md):** the `eat_freeze` pause currently runs
  **unconditionally** (not behind `juice`) — it gates `moving`, so it shifts the deterministic sim.
  Researcher/planner MUST confirm the `ghost_eat`/`death` golden traces + frame-hash manifests already
  account for the freeze (Phase 8 re-verified the `ghost_eat`/`death` terminals). If FEEL-01/03/04 add
  any new sim-affecting state, it must be `juice`-gated to honor SC5. (Audio is exempt.)
- **pygame vs pygame-ce pin conflict (pre-existing, out of scope but relevant):** `juice.py` uses
  `pygame.transform.gaussian_blur` (pygame-ce only). `requirements.txt` pins pygame-ce==2.5.7 but
  `requirements-dev.txt` pins pygame==2.6.1 (lacks it, installed last) → 12 UI/juice/theme render
  tests fail in the CI env (`theme.py:45`). Not a phase-9 regression; flagged in `08` deferred-items.
  New juice render tests should be mindful of which pygame is active.

</code_context>

<specifics>
## Specific Ideas

- "Arcade-faithful" remains the throughline (carried from Phase 8): the **death** is the iconic
  spinning-wedge collapse; the **frightened flash** is the classic last-~2-seconds white blink; the
  **eat sound** is a distinct retro bite blip.
- Intended player experience: death "plays out" instead of just freezing; eating a ghost *rewards*
  (popup + freeze already there, now + a distinct bite sound); and frightened ghosts *warn* you when
  it's no longer safe to chase.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. The already-shipped FEEL-02 (eat popup/freeze) and
FEEL-05 ("READY!") were reviewed and **accepted as-is** (no tweaks requested). Content/fruit, extra
mazes, scatter/chase waves, and multiplayer remain explicitly out of scope per REQUIREMENTS.md /
PROJECT.md.

</deferred>

---

*Phase: 9-Arcade Juice*
*Context gathered: 2026-06-30*
