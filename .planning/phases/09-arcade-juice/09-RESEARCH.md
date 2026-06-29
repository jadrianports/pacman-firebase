# Phase 9: Arcade Juice - Research

**Researched:** 2026-06-30
**Domain:** PyGame game-feel rendering + audio, inside a deterministic, golden-pinned engine
**Confidence:** HIGH (change sites read in code; golden/frame-hash harness read in full; pygame-ce 2.5.7 draw API verified locally + via Context7)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** All three new **visual** effects (death animation, frightened flash) render **only when `juice=True`**. The `juice=False` path is unchanged — this is what keeps the golden state traces + frame-hash net green with no re-bless.
- **D-02:** The eat-ghost **sound** (FEEL-03) is **not** firewall-gated — it plays in normal play like the other SFX. Audio doesn't affect determinism or pixel hashes.
- **D-03:** Death style = **classic arcade wedge spin**, drawn **programmatically** with pygame arcs/polygons (only 4 chomp sprites exist — `assets/pacman/1-4.png`; no death frames).
- **D-04:** Death timing = **fill the `death.wav` window** — animation plays across the existing `dying` phase (which already blocks on `sound.is_death_playing()` then +60 frames). Sound and visuals end together.
- **D-05:** Death animation replaces the normal `player.draw()` **only while `dying and juice`**. Under `juice=False`, `dying` renders exactly as today.
- **D-06:** Frightened flash trigger = **last ~2 s (~120 frames) of the 600-frame power window** (`power_counter > ~480`). Threshold is a **named tunable in `settings.py`**.
- **D-07:** Flash look = **Claude's discretion** — likely a white tint of `spooked_img`, alternating blue↔white. No new white sprite asset required if a tint works.
- **D-08:** Flash only renders under `juice=True`. Under `juice=False`, `Ghost.draw()` blits the steady `spooked_img` exactly as today.
- **D-09:** Eat-ghost sound = **find a CC0 / freely-licensed retro `.wav`** added to `assets/audio/`. **Runtime tone-synthesis was rejected** (`numpy`/`pygame.sndarray` not installed; no new client runtime deps).
- **D-10:** Wire `SoundManager.play_eat_ghost()`; fire on the bite in `check_ghost_collisions` (`game.py:464-476`). User verifies licensing + feel during playtest.

### Claude's Discretion
- FEEL-04 blink look/cadence (D-07) and the exact white/tint mechanism.
- FEEL-03 sound mix vs the powerup siren (D-10): the bite already pauses the siren for the freeze and unpauses after — planner picks the cleanest channel/timing so the bite is audible.
- Exact death-wedge geometry/arc math and frame cadence within the `death.wav` window (D-04).

### Deferred Ideas (OUT OF SCOPE)
None. FEEL-02 (eat popup + 45-frame freeze) and FEEL-05 ("READY!" beat) are **already shipped and accepted as-is** — do not retouch them. Scatter/chase waves, fruit, extra mazes, modes, multiplayer, screen-shake-on-death, level-clear flash, extra audio polish: all explicitly out of scope per REQUIREMENTS.md.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FEEL-01 | On death, Pac-Man plays a wedge/disintegrate animation synced to `death.wav` before reset | Architecture Pattern 1 (juice-gated wedge in `tick()` draw block); Code Example "Death wedge"; settings tunable `DEATH_ANIM_FRAMES` |
| FEEL-02 | Eat-ghost points popup + brief freeze | **ALREADY SHIPPED & golden-baked** — see Golden-Safety Status. No work. |
| FEEL-03 | Distinct eat-ghost sound on the bite | Architecture Pattern 2 (`SoundManager.play_eat_ghost()` on dedicated channel 2); Sourcing guidance (CC0 / self-authored bfxr) |
| FEEL-04 | Frightened ghosts blink white as power timer expires | Architecture Pattern 3 (compute `blink_white` in `create_ghosts`, thread into `Ghost` via keyword-default param, white-tint `spooked_img`); settings tunables |
| FEEL-05 | "READY!" beat before each round | **ALREADY SHIPPED & accepted** (`draw_ready()`). No work. |
</phase_requirements>

## Summary

Phase 9 is three small, surgical features bolted onto a codebase whose hardest constraint — the
juice firewall — is **already built and proven**. The `Game.juice` flag (default `False`),
`juice.py`, `theme.py`, the eat-freeze pause, the eat-popup render, and the "READY!" beat all
shipped in the Phase-8 era. FEEL-02 and FEEL-05 are done. The real work is FEEL-01 (death wedge),
FEEL-03 (eat-ghost sound), FEEL-04 (frightened-end flash).

The dominant risk is **not** the features — it is touching the `juice=False` render or sim path
and forcing a golden re-bless. I verified the regression net directly: `tests/golden/ghost_eat/`
and `tests/golden/death/` each contain a committed `trace.jsonl` **and** `frame_hashes.txt`, and
STATE.md records they were re-blessed in Phase 8 **with the unconditional `eat_freeze` pause
already in place**. So the eat-freeze is already accounted for in both the state trace and the
pixel manifest — there is **nothing to "fix"** there, and moving it behind `juice` now would
*break* the re-blessed goldens (the inverse of SC5's intent). Every new visual must add **zero**
pixel change and **zero** captured-state change under `juice=False`.

**Primary recommendation:** Implement all three visuals as `if … self.juice:` branches that
overlay the *existing* unchanged `juice=False` path; keep every new render primitive to
`pygame.draw.polygon`/`circle` + `Surface.fill(..., BLEND_RGB_ADD)` (works on both pygame-ce and
vanilla pygame); thread the FEEL-04 signal into `Ghost` via **keyword-default** constructor
params (so `tests/test_ghost_micro.py`'s positional `make_ghost()` and all existing callers keep
working); wire the eat sound on a dedicated `pygame.mixer.Channel(2)`; add no new runtime deps;
gate every new frame counter behind `juice`. The phase gate is: full `pytest` green, including
`test_juice_firewall`, `test_golden_traces`, and `test_frame_hash`, with **no `--bless`**.

## Golden-Safety Status (the #1 risk — RESOLVED, read first)

| Question | Answer | Evidence |
|----------|--------|----------|
| Does the committed `ghost_eat`/`death` **state** golden already include the unconditional `eat_freeze` pause? | **YES** | `tests/golden/ghost_eat/trace.jsonl` + `death/trace.jsonl` exist; STATE.md L70 "death/ghost_eat terminals re-verified" at Phase-8 close; `eat_freeze` is wired unconditionally in `game.py:541-545,548,586,608,613`. |
| Does the committed **frame-hash** manifest already include the `eat_freeze` non-juice popup render? | **YES** | `tests/golden/ghost_eat/frame_hashes.txt` + `death/frame_hashes.txt` exist; the `juice=False` eat-popup (black rect + cyan score text) renders at `game.py:600-604` and is hashed. |
| Should Phase 9 move `eat_freeze` behind `juice` (per the old STATE.md risk note)? | **NO — TRAP** | It is already baked into the re-blessed goldens. Gating it now would change the `juice=False` sim/pixels → force a re-bless → violate SC5. **Leave `eat_freeze` exactly as-is.** |
| Where does the frame-hash net actually assert? | Linux pinned CI only (`CI`/`GSD_FRAME_HASH_ENV`); skips on Windows dev | `tests/test_frame_hash.py:64-66,155-159`. Local Windows runs **skip** frame-hash — do not mistake a local green for proof; the CI Linux run is the authority. |
| Local interpreter vs CI interpreter | `.venv` = **pygame-ce 2.5.7**; CI frame-hash bless env = vanilla **pygame 2.6.1** | Verified `.venv/Scripts/python.exe` → `pygame-ce 2.5.7 (SDL 2.32.10)`; manifest docstring `test_frame_hash.py:18-23`. New juice tests must pass on **both** (see Pitfall 5). |

**Net effect:** if all three new visuals are strictly `juice`-gated and add no captured-state
field, the golden state traces (9 scenarios) and the frame-hash manifests stay green with **no
re-bless**. That is the entire SC5 contract and it is achievable with the branch-overlay pattern below.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Death wedge animation (FEEL-01) | `game.py` `tick()` render block | `settings.py` (frame budget) | The dying-phase lifecycle + the player draw call both live in `tick()`; the wedge is a draw-only overlay gated by `self.juice`. |
| Death-phase frame counter | `Game` state (`__init__`/`start_dying`/`reset_after_death`) | — | Needs a monotonic counter across the dying window; owned by `Game`, juice-gated. |
| Eat-ghost sound (FEEL-03) | `sound.py` `SoundManager` | `game.py` `check_ghost_collisions` (trigger) | Audio ownership is `SoundManager`'s; the bite event is detected in the existing eat branch. Not firewall-gated (D-02). |
| Eat-ghost `.wav` asset | `assets/audio/` (content) | credits/NOTICE (license record) | Content asset, not a code dependency. |
| Frightened-end blink decision (FEEL-04) | `game.py` `create_ghosts` (compute `blink_white`) | `settings.py` (threshold/cadence) | Ghosts are rebuilt each frame and are "dumb"; keep all juice/threshold logic in `Game` and pass a single precomputed bool. |
| Frightened-end blink render | `ghost.py` `Ghost.draw` spooked branch | `Game.__init__` (pre-tinted white image) | The blit decision is local to the spooked branch; the tinted surface is built once and threaded in. |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pygame-ce | 2.5.7 (local `.venv`) | Rendering, mixer, draw primitives | Already the project's engine; `requirements.txt` pins `pygame-ce==2.5.7`. [VERIFIED: `.venv/Scripts/python.exe -c "import pygame; print(pygame.ver)"` → `pygame-ce 2.5.7`] |
| pygame (vanilla) | 2.6.1 (CI / `requirements-dev.txt`) | The CI frame-hash bless interpreter | Frame-hash manifest is blessed under vanilla pygame 2.6.1 on Linux. [CITED: tests/test_frame_hash.py:18-23] |

**No new libraries.** D-09 explicitly rejects `numpy`/`pygame.sndarray`. The death wedge uses
`math` (already imported in `game.py:2`) + `pygame.draw`. The white tint uses `Surface.copy()` +
`Surface.fill(..., special_flags=pygame.BLEND_RGB_ADD)`. All are in both pygame editions.

### Verified draw primitives (pygame-ce 2.5.7, confirmed locally)
| Primitive | Available | Use |
|-----------|-----------|-----|
| `pygame.draw.polygon(surface, color, points)` | ✅ (filled) | Death wedge body (circle-minus-mouth) |
| `pygame.draw.circle(surface, color, center, r)` | ✅ | Optional rounded wedge base |
| `pygame.draw.arc(...)` | ✅ but **outline only, no fill** | NOT used for the filled wedge |
| `pygame.draw.pie` | ❌ does not exist | — |
| `Surface.fill(color, special_flags=BLEND_RGB_ADD)` | ✅ | White-tint the spooked image |

[VERIFIED: local probe — `has arc True; has polygon True; has pie False`] · [CITED: Context7
/pygame-community/pygame-ce — `gfxdraw.pie` is *unfilled*; `gfxdraw.filled_polygon` exists but
`gfxdraw` antialiasing is platform-variable, so prefer `pygame.draw.polygon` for predictability.]

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `pygame.draw.polygon` wedge | `pygame.gfxdraw.filled_polygon` / `pie` | gfxdraw gives smoother arcs but is platform-variable; irrelevant for the net (FEEL-01 is juice-only, never hashed) but adds risk in any juice render test. Stick with `draw.polygon`. |
| White-tint `spooked_img` (D-07) | New `powerup_white.png` asset | A tint is zero-asset, zero-license, cached once. Only add a PNG if the tint reads poorly in playtest. |
| Self-authored bfxr `.wav` (FEEL-03) | Downloaded CC0 `.wav` | Self-authored = zero third-party license risk and you own it; download requires recording source+license. Both fit the loader. |

**Installation:** None. (No `npm`/`pip` install. The only new artifact is one `.wav` file copied
into `assets/audio/`.)

## Package Legitimacy Audit

**No external packages are installed in this phase.** D-09 rejected `numpy`/`pygame.sndarray`;
no other dependency is introduced. slopcheck/registry verification is **N/A** — there is nothing
to audit on npm/PyPI/crates.

The single new external artifact is a **content asset** (`assets/audio/<eat-ghost>.wav`). Its
supply-chain risk is *licensing*, not code execution:
- A downloaded `.wav` cannot run a postinstall script, but **must** carry a recorded CC0/permissive
  license + source URL + author, captured in a credits/NOTICE file at add time. `[ASSUMED]` until
  the user selects and verifies the specific file during playtest (D-10).
- **Lowest-risk path:** generate the sound yourself in bfxr/jsfxr/sfxr and export `.wav` — you are
  the author, so there is no third-party license to verify. `[ASSUMED — tool suggestion, verify the
  exact tool/output at add time]`.

## Architecture Patterns

### System Architecture Diagram

```
                          ┌─────────────────────── Game.tick() (one frame) ───────────────────────┐
                          │                                                                        │
  input/events ──▶ handle_events ──▶ state update (counter, eat_freeze, power_counter, dying)      │
                          │                                                                        │
                          │   ── RENDER BLOCK ──                                                   │
                          │   screen.fill('black') ─▶ draw_board                                   │
                          │                                                                        │
                          │   if not eat_freeze:                                                   │
   FEEL-01 ───────────────┼──────▶ if dying and juice:  _draw_death(death_anim_frame)  [WEDGE]     │
                          │        else:                player.draw(counter)   ◀── juice=False path│ unchanged
                          │                                                                        │
                          │   create_ghosts ──▶ compute blink_white (juice & power_counter>thr)    │
   FEEL-04 ───────────────┼──────▶ Ghost.draw: spooked branch blits white_img if blink_white       │
                          │                              else spooked_img      ◀── juice=False path │ unchanged
                          │                                                                        │
                          │   draw_misc / draw_ready / eat_freeze popup (FEEL-02, already shipped)  │
                          │                                                                        │
                          │   if not dying/eat_freeze/starting: check_ghost_collisions ────────────┤
   FEEL-03 ───────────────┼──────────────────────────────▶ on bite: sound.play_eat_ghost() (ch 2)  │ (audio, ungated)
                          │                                                                        │
                          │   present_fn()  (pygame.display.flip)                                  │
                          └────────────────────────────────────────────────────────────────────────┘

  Golden net (juice=False replays): state trace + frame-hash must stay byte-identical → all three
  branches above are no-ops under juice=False (FEEL-03 audio is never hashed: SDL dummy + RGB pixels).
```

### Recommended change map (files, not new structure)
```
game.py       # FEEL-01 wedge branch + death_anim_frame state; FEEL-04 blink_white compute + Ghost call;
              #   FEEL-03 single call in check_ghost_collisions eat branch
ghost.py      # FEEL-04: keyword-default params (blink_white=False, spooked_white_img=None) + spooked-branch blit
sound.py      # FEEL-03: load eat-ghost wav, Channel(2), play_eat_ghost()
settings.py   # DEATH_ANIM_FRAMES, FRIGHT_FLASH_START, FRIGHT_FLASH_INTERVAL
assets/audio/ # new eat-ghost .wav (+ license note)
tests/        # test_death_anim.py, test_eat_ghost_sound.py, test_fright_flash.py
```

### Pattern 1: Death wedge as a juice-gated overlay (FEEL-01)
**What:** Replace `player.draw()` only when `dying and juice`; otherwise the existing call runs.
**When to use:** The exact draw site is `game.py:586-587`.
**Key facts:**
- During `dying`, `check_ghost_collisions` is skipped (`game.py:616`), so the `player_circle`
  returned by `player.draw()` is **not consulted** — the wedge branch can safely not produce one.
  `player_circle` is only referenced inside the `if not self.dying …` block, so it never goes
  unbound there.
- The dying window length in real play is driven by `death.wav` via `sound.is_death_playing()`
  then +60 frames (`game.py:566-578`). There is **no existing monotonic dying-frame counter**
  (`dying_delay` only counts the *post-sound* 60 frames). Add one: `self.death_anim_frame`, set to
  0 in `__init__`/`start_dying`/`reset_after_death`, incremented **gated behind `juice`** while
  `dying`. Gating keeps `juice=False` sim untouched (SC5); the counter is also not a captured-state
  field (`harness/trace.py` capture is fixed to pacman/ghosts/score/lives/powerup/dots/flags), so
  it can never enter the state golden regardless.
- Map animation progress `p = min(1.0, death_anim_frame / DEATH_ANIM_FRAMES)`; mouth half-angle
  grows `0 → 180°` so the wedge closes to nothing then vanishes. Set `DEATH_ANIM_FRAMES`
  (settings tunable) near `death.wav` length × FPS so sound + visuals end together (D-04). If the
  sound outlasts the budget, the final (vanished) frame simply holds until reset.

**Example:**
```python
# Source: pattern derived from pygame-ce draw API (Context7 /pygame-community/pygame-ce) + game.py:586
# settings.py
DEATH_ANIM_FRAMES = 75   # ~1.25 s at 60 FPS; D-04 dial — tune to death.wav length. Pure int (determinism guard safe).

# game.py  (math already imported at game.py:2)
def _draw_death(self, anim_frame):
    """Classic wedge collapse — juice-only (D-05). Filled circle minus a growing mouth."""
    cx, cy, r = self.player.center_x, self.player.center_y, 21
    p = min(1.0, anim_frame / DEATH_ANIM_FRAMES)
    mouth = p * math.pi            # half-mouth 0 -> pi (full close)
    if mouth >= math.pi:
        return                     # fully collapsed -> nothing drawn (vanished)
    facing = {0: 0.0, 1: math.pi, 2: -math.pi/2, 3: math.pi/2}[self.player.direction]
    pts = [(cx, cy)]
    start, end, steps = facing + mouth, facing + (2*math.pi - mouth), 24
    for i in range(steps + 1):
        a = start + (end - start) * i / steps
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    pygame.draw.polygon(self.screen, (255, 222, 0), pts)

# game.py  tick() draw block, replacing the player.draw branch at ~586:
if not self.eat_freeze:
    if self.dying and self.juice:
        self.death_anim_frame += 1
        self._draw_death(self.death_anim_frame)
    else:
        player_circle = self.player.draw(self.counter)
```
> Note: `get_length()` (if used to derive the budget dynamically) is **not** a determinism-guard
> forbidden token (`tests/test_determinism_guard.py:25` bans `random/randint/shuffle/time.time/get_ticks/datetime`), but the
> headless shim overrides `is_death_playing`, not `get_length` — a named `settings.py` constant is
> simpler and equally golden-safe.

### Pattern 2: Eat-ghost sound on a dedicated channel (FEEL-03)
**What:** Add the sound to `SoundManager`, play it once on its own channel when the bite lands.
**Where:** load in `SoundManager.__init__`; trigger in `check_ghost_collisions` eat branch
(`game.py:474-475`), beside the existing `self.sound.stop_waka()` / `self.sound.pause_powerup()`.
**Channel rationale (D-10 discretion):** at the bite, waka (channel 0) is stopped and powerup
(channel 1) is *paused* for the 45-frame freeze, then unpaused (`game.py:474-475`, `545`). Play the
bite on a **dedicated `pygame.mixer.Channel(2)`** so it is guaranteed audible over the paused siren
and never stolen. Default mixer has 8 channels, so channel 2 needs no `set_num_channels` call. Not
firewall-gated (D-02).

**Example:**
```python
# Source: sound.py existing pattern (sound.py:9-66)
# sound.py __init__:
self.eat_ghost_sound = self._load_sound('eat_ghost.wav', volume=0.5)   # filename TBD by asset chosen
self._eat_channel = pygame.mixer.Channel(2)

def play_eat_ghost(self):
    if self.eat_ghost_sound:
        self._eat_channel.play(self.eat_ghost_sound)   # one-shot, no loop

# game.py check_ghost_collisions, inside the eat branch (~474):
self.sound.stop_waka()
self.sound.pause_powerup()
self.sound.play_eat_ghost()     # FEEL-03 — ungated (D-02)
```

### Pattern 3: Thread the frightened-end signal into the per-frame Ghost (FEEL-04)
**What:** Compute one boolean in `Game.create_ghosts`, pass it (plus a pre-tinted white image) into
the `Ghost` constructor as **keyword-default** params; the spooked branch of `Ghost.draw` picks the
white image when the bool is set.
**Why keyword-default (CRITICAL):** `tests/test_ghost_micro.py:53-57` (`make_ghost`) constructs
`Ghost(...)` **positionally** through `level`. Adding *positional* params after `level` would break
those characterization tests and every `create_ghosts` call. Add the new params **after `level`
with defaults** (`blink_white=False, spooked_white_img=None`) so existing callers/tests are untouched.
**Why compute in `Game`:** the ghost is "dumb" and rebuilt each frame; keeping the juice gate +
threshold + cadence in `Game` means `Ghost` stays minimal and the firewall lives in one place.
**Golden-safety:** under `juice=False`, `blink_white` is always `False`, so `Ghost.draw` blits the
identical `spooked_img` — byte-identical (D-08). Confirmed against `ghost.py:305-306`.

**Example:**
```python
# settings.py
FRIGHT_FLASH_START = 480     # blink when power_counter > 480 (last 120 of 600 frames ≈ 2 s) — D-06 dial
FRIGHT_FLASH_INTERVAL = 8    # frames per blink half-cycle — D-07 cadence dial

# game.py __init__ (build the tinted image once; BLEND_RGB_ADD brightens toward white, keeps alpha):
self.spooked_white_img = self.spooked_img.copy()
self.spooked_white_img.fill((90, 90, 120, 0), special_flags=pygame.BLEND_RGB_ADD)

# game.py create_ghosts (compute once, pass to all four):
blink_white = (self.juice and self.powerup
               and self.power_counter > FRIGHT_FLASH_START
               and (self.power_counter // FRIGHT_FLASH_INTERVAL) % 2 == 0)
self.blinky = Ghost(..., self.level, blink_white=blink_white,
                    spooked_white_img=self.spooked_white_img)
# ...same kwargs for inky/pinky/clyde

# ghost.py __init__ signature: append  blink_white=False, spooked_white_img=None
# ghost.py draw(), spooked branch (ghost.py:305-306):
elif self.powerup and not self.dead and not self.eaten_ghost[self.id]:
    img = self.spooked_white_img if self.blink_white else self.spooked_img
    self.screen.blit(img, (self.x_pos, self.y_pos))
```
> `power_counter` is paused during `eat_freeze` (`game.py:548`), so the blink naturally pauses with
> the freeze — no special handling needed.

### Anti-Patterns to Avoid
- **Moving `eat_freeze` behind `juice` now.** It is already baked into the re-blessed goldens;
  gating it changes the `juice=False` sim/pixels and forces a re-bless. Leave it alone.
- **Adding positional `Ghost` params.** Breaks `test_ghost_micro.make_ghost` and every caller.
- **Reading wall-clock / `random` for animation timing.** Trips `test_determinism_guard` (and
  there is no need — use a frame counter).
- **Using `gaussian_blur`/`bloom` in a new juice test.** Vanilla pygame (CI) lacks `gaussian_blur`;
  it would fail in the CI interpreter. Keep new visuals to `draw.polygon`/`circle` + `fill+BLEND`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Headless sound timing in tests | A custom mixer fake | `harness.replay.install_frame_driven_sound` | Already shims `is_death_playing` deterministically (`harness/replay.py:45-89`). |
| Frame-hash regression check | A new pixel-diff harness | `tests/test_frame_hash.py` (run unchanged) | The manifest + bless flow already exists; just keep `juice=False` byte-identical. |
| Byte-identical-render assertion | A bespoke check | `tests/test_juice_firewall.py` pattern | It already proves two `juice=False` games render identical frames; extend with a death/power scenario. |
| White sprite | A new PNG pipeline | `Surface.copy()` + `fill(BLEND_RGB_ADD)` | One cached tint, no asset, no license. |
| Eat-sound synthesis | `numpy`/`sndarray` runtime tone gen | A pre-made `.wav` (bfxr-authored or CC0) | D-09 rejects new runtime deps; mixer loads `.wav` directly. |

**Key insight:** the entire deterministic/golden infrastructure this phase must not break is *also*
the infrastructure you reuse to *prove* you didn't break it. Don't reinvent any of it.

## Runtime State Inventory

> This is a feature phase, not a rename/migration. No stored data, live-service config, OS-registered
> state, or secrets are involved. The only persisted artifact is the new `.wav` content file.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — verified (no datastore touched; game state is in-memory, reset per session). | none |
| Live service config | None — verified (no Cloud Functions / leaderboard interaction in this phase). | none |
| OS-registered state | None — verified. | none |
| Secrets/env vars | None — verified (HMAC/identity untouched). | none |
| Build artifacts | New `assets/audio/<eat-ghost>.wav` must be bundled by PyInstaller. `build.py`/spec data-glob should already include `assets/audio/*` (it ships `death.wav` etc.) — **verify the new file is picked up** in the exe build. | confirm asset glob at build |

## Common Pitfalls

### Pitfall 1: A new captured-state field or unconditional sim change forces a re-bless
**What goes wrong:** any change that alters the `juice=False` state trace (new field captured, or a
timing/position shift) or the `juice=False` pixels turns the 9 golden traces or the frame-hash
manifest red → forces a Linux/Docker re-bless → violates SC5.
**Why it happens:** treating "add juice" as "add behavior" instead of "add a gated overlay".
**How to avoid:** every new visual is `if … self.juice:`; every new frame counter is juice-gated;
add no field to `harness/trace.py:capture_state`. Audio (FEEL-03) is exempt (never hashed).
**Warning signs:** `pytest -k baseline` or `-k frame_hash` red without `--bless`; a diff in a
`juice=False` scenario.

### Pitfall 2: Ghost constructor signature break
**What goes wrong:** adding positional params to `Ghost.__init__` breaks `make_ghost()` and the
~dozens of characterization assertions in `test_ghost_micro.py`, plus all four `create_ghosts` calls.
**How to avoid:** append `blink_white=False, spooked_white_img=None` **after** `level`, with defaults.
**Warning signs:** `TypeError: __init__() takes N positional arguments` in ghost tests.

### Pitfall 3: Determinism guard trips on animation timing
**What goes wrong:** importing `time`/`random` or calling `get_ticks()` for the wedge cadence fails
`tests/test_determinism_guard.py` (scans `game.py`/`ghost.py`/`player.py` for
`random|randint|shuffle|time.time|get_ticks|datetime`).
**How to avoid:** drive the wedge from `self.death_anim_frame` (a frame counter) and `math` only.
**Warning signs:** `determinism guard tripped in game.py: line N -> '<token>'`.

### Pitfall 4: `player_circle` unbound during dying
**What goes wrong:** the wedge branch skips `player.draw()`, so `player_circle` is not assigned that
frame; a later unconditional reference would `NameError`.
**Why it's actually safe:** `player_circle` is referenced only inside `if not self.dying and not
self.eat_freeze and not self.starting:` (`game.py:616-618`), which never runs during `dying`.
**How to avoid:** keep the wedge branch strictly inside the existing `if not self.eat_freeze:` block
and do not add references to `player_circle` outside the collision guard. Add a unit test that runs
a dying frame under `juice=True` without raising.

### Pitfall 5: Local green ≠ CI green (pygame edition + frame-hash skip)
**What goes wrong:** local `.venv` is pygame-ce 2.5.7 and **skips** the frame-hash assertion on
Windows (`test_frame_hash.py:155-159`); CI asserts under vanilla pygame 2.6.1 on Linux. A juice
render test that uses a pygame-ce-only API (`gaussian_blur`) passes locally, fails in CI.
**How to avoid:** restrict new visuals/tests to APIs present in **both** editions
(`draw.polygon`/`circle`, `Surface.fill` + `BLEND_RGB_ADD`/`BLEND_RGB_MAX`). Treat the Linux CI run
as the frame-hash authority. (Pre-existing: `requirements-dev.txt` pins vanilla pygame and 12
juice/theme tests already fail in that env over `gaussian_blur` — not a Phase-9 regression, but do
not add to that pile.)

### Pitfall 6: Eat-sound channel collision / inaudibility
**What goes wrong:** playing the bite via `Sound.play()` with default allocation can land on a busy
channel or be masked; or reusing channel 0/1 conflicts with waka/siren control.
**How to avoid:** dedicated `pygame.mixer.Channel(2)`, one-shot. Default mixer has 8 channels so no
`set_num_channels` is needed; if the build ever lowers channel count, add `set_num_channels(>=3)`.

## Code Examples

(See Patterns 1-3 above for the three verified, copy-ready snippets — death wedge, eat-sound wiring,
and the Ghost blink threading. Each is grounded in the exact current change sites: `game.py:586`,
`game.py:474-475`, `ghost.py:305-306`, `create_ghosts` `game.py:381-393`.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sprite-sheet death frames (classic arcade had dedicated frames) | Programmatic `draw.polygon` wedge | This phase (D-03) | No new art; deterministic; juice-gated. |
| Runtime tone synthesis for SFX | Pre-baked `.wav` files | Project standing constraint (D-09) | No `numpy`/`sndarray` runtime dep. |

**Deprecated/outdated:** none relevant. (Note: `pygame.draw.pie` does not exist in any edition —
do not assume it; use `draw.polygon`. The Namco eat-ghost sound is copyrighted — do not rip it.)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | A CC0/self-authored eat-ghost `.wav` can be sourced and will feel right; exact file/tool chosen at playtest (D-10) | FEEL-03 sourcing | Low — user verifies at add time; loader is agnostic to the specific file. |
| A2 | `DEATH_ANIM_FRAMES ≈ 75` (~1.25 s) matches `death.wav` length closely enough for "end together" (D-04) | Pattern 1 | Low — it's a `settings.py` dial; tune after hearing the wav. The animation holds (vanished) if sound is longer. |
| A3 | White tint via `BLEND_RGB_ADD (90,90,120,0)` reads as a clear blink (D-07) | Pattern 3 | Low — discretionary look; adjust the add-color or swap to a PNG if playtest disagrees. |
| A4 | `build.py`/PyInstaller spec already globs `assets/audio/*` so the new wav ships in the exe | Runtime State Inventory | Medium — if the spec lists files explicitly, the new wav must be added or it's silently missing in the build (game degrades: no eat sound, still playable). Verify. |
| A5 | The bite is audible on `Channel(2)` over the paused siren without a `set_num_channels` call | Pattern 2 / Pitfall 6 | Low — default mixer is 8 channels; verify in playtest. |

## Open Questions (RESOLVED)

1. **Exact `death.wav` length → `DEATH_ANIM_FRAMES`.**
   - What we know: dying blocks on `is_death_playing()` (`death.wav` length × FPS) then +60 frames.
   - What's unclear: the wav's exact duration (not measured here).
   - Recommendation: at implementation, read `int(sound.death_sound.get_length()*FPS)` once to pick
     `DEATH_ANIM_FRAMES` (or just measure the file), then hard-code the int in `settings.py`.
   - **RESOLVED:** Handled as a provisional `settings.py` dial (`DEATH_ANIM_FRAMES=75`) tuned at the
     09-05 playtest (D-04). Plan 09-02 implements the frame-counter; 09-05 Task closes the timing.
2. **Specific eat-ghost `.wav` + license record.**
   - What we know: must be CC0/permissive or self-authored; recorded at add time (D-09/D-10).
   - Recommendation: author in bfxr/jsfxr (zero license risk) OR pull a CC0 clip from
     freesound.org (License = CC0 filter) / Kenney.nl audio / OpenGameArt (CC0); commit a NOTICE
     line with source+author+license. Do NOT fabricate a URL; user selects during playtest.
   - **RESOLVED:** Deferred to the 09-05 human-action checkpoint (`autonomous: false`) — the user
     selects/verifies the file and a NOTICE line is committed at add time (D-09/D-10).
3. **PyInstaller asset bundling (A4).** Confirm the spec ships the new wav.
   - **RESOLVED:** `build.py` uses `--add-data=assets;assets` (globs the whole tree), so the new
     `.wav` ships automatically — no `build.py` edit needed. Confirmation folded into 09-05 Task 3.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pygame-ce | all rendering/audio | ✅ (`.venv`) | 2.5.7 | — |
| pygame (vanilla) | CI frame-hash bless | ✅ (CI / dev reqs) | 2.6.1 | — |
| `math`, `pygame.draw`, `pygame.mixer` | FEEL-01/03/04 | ✅ stdlib/engine | — | — |
| bfxr/jsfxr (sound authoring) | FEEL-03 (optional path) | ✗ (web tool, no install) | — | Download a CC0 `.wav` instead |
| `numpy`/`pygame.sndarray` | (rejected) | ✗ | — | N/A — runtime synth rejected (D-09) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** the eat-ghost `.wav` itself is the only new artifact —
author it (bfxr) or download a CC0 clip; either fits the existing loader.

## Validation Architecture

> `workflow.nyquist_validation: true` (config.json) — section included.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (repo-root conftest; SDL dummy drivers forced) |
| Config file | `tests/conftest.py` (no pytest.ini; registers `--bless`) |
| Quick run command | `.venv/Scripts/python.exe -m pytest tests/test_juice_firewall.py tests/test_determinism_guard.py -q` |
| Full suite command | `.venv/Scripts/python.exe -m pytest -q` |
| Golden subset | `… -m pytest tests/test_golden_traces.py tests/test_frame_hash.py -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEEL-01 | Wedge draws only under `dying and juice`; `juice=False` dying unchanged | unit + firewall | `pytest tests/test_death_anim.py -x` | ❌ Wave 0 |
| FEEL-01 | A dying frame under `juice=True` raises nothing (player_circle safe) | unit | `pytest tests/test_death_anim.py::test_dying_juice_frame_ok -x` | ❌ Wave 0 |
| FEEL-03 | `play_eat_ghost` uses Channel(2), no-raise headless; called on bite | unit | `pytest tests/test_eat_ghost_sound.py -x` | ❌ Wave 0 |
| FEEL-04 | `Ghost.draw` blits white when `blink_white`, spooked otherwise | unit (pixel) | `pytest tests/test_fright_flash.py -x` | ❌ Wave 0 |
| FEEL-04 | `create_ghosts` computes `blink_white=False` whenever `juice=False` | unit | `pytest tests/test_fright_flash.py::test_blink_off_under_juice_false -x` | ❌ Wave 0 |
| SC5 (all) | `juice=False` golden state traces byte-identical | regression | `pytest tests/test_golden_traces.py -q` | ✅ |
| SC5 (all) | `juice=False` frame-hash manifest unchanged (Linux CI authority) | regression | `pytest tests/test_frame_hash.py -q` (CI) | ✅ |
| SC5 (all) | Two `juice=False` games render byte-identical (firewall) | regression | `pytest tests/test_juice_firewall.py -q` | ✅ |
| determinism | No `random`/wall-clock in game.py/ghost.py/player.py | static | `pytest tests/test_determinism_guard.py -q` | ✅ |

### Sampling Rate
- **Per task commit:** quick run (firewall + determinism guard) — catches the two highest-risk regressions fast.
- **Per wave merge:** golden subset (`test_golden_traces` + `test_frame_hash`) + the new feature tests.
- **Phase gate:** full `pytest` green **with no `--bless`**, and the Linux CI run green (frame-hash
  asserts only there). NO re-bless is the success signal.

### Wave 0 Gaps
- [ ] `tests/test_death_anim.py` — FEEL-01: juice-gated wedge; `juice=False` dying unchanged; no-raise dying frame.
- [ ] `tests/test_eat_ghost_sound.py` — FEEL-03: `play_eat_ghost` channel + headless no-raise; spy that the eat branch calls it.
- [ ] `tests/test_fright_flash.py` — FEEL-04: white-vs-spooked blit; `blink_white` off under `juice=False`.
- [ ] `settings.py` constants: `DEATH_ANIM_FRAMES`, `FRIGHT_FLASH_START`, `FRIGHT_FLASH_INTERVAL` (and failing tests referencing them, phase-8 pattern).
- [ ] Optional: extend a firewall-style test to replay the `death`/`power_chase` scenarios under `juice=False` twice and assert identical frame hashes (belt-and-braces before CI).
- [ ] New `.wav` present in `assets/audio/` + license NOTICE (manual, playtest gate).

## Security Domain

> `security_enforcement: true`, ASVS level 1. This is a local, single-player, offline game-feel
> phase with **no** network, auth, input-trust, persistence, or crypto surface. Applicability is low;
> documented for completeness.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | — (no auth touched) |
| V3 Session Management | no | — |
| V4 Access Control | no | — |
| V5 Input Validation | no | — (no new external/user input; inputs are local keystrokes already handled) |
| V6 Cryptography | no | — (HMAC/identity untouched) |
| V14 Config / Supply-chain (asset) | yes (light) | Record CC0/permissive license + source for the new `.wav`; prefer self-authored (bfxr) to eliminate third-party provenance risk. No executable dependency added. |

### Known Threat Patterns for this stack
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Untracked-license third-party asset | Repudiation / legal | Commit a NOTICE with source+author+license at add time (D-10); or self-author the sound. |
| New runtime dependency expands attack surface | Tampering | None added (D-09 rejects numpy/sndarray); a `.wav` is inert data, not code. |

## Sources

### Primary (HIGH confidence)
- Codebase (read in full this session): `game.py`, `ghost.py`, `player.py`, `sound.py`, `settings.py`,
  `juice.py`, `tests/test_juice_firewall.py`, `tests/test_frame_hash.py`, `tests/test_golden_traces.py`,
  `tests/test_determinism_guard.py`, `tests/conftest.py`, `harness/replay.py`, `tests/test_ghost_micro.py`,
  `tests/test_juice.py`, `tests/golden/manifest.json` — exact change sites + the regression contract.
- Local probe: `.venv/Scripts/python.exe` → `pygame-ce 2.5.7 (SDL 2.32.10)`; `draw.arc` ✅, `draw.polygon` ✅, `draw.pie` ❌.
- Filesystem: `tests/golden/{ghost_eat,death}/{trace.jsonl,frame_hashes.txt}` exist; `assets/audio/` = {death,powerup,start,wakawaka}.wav.
- `.planning/` docs: CONTEXT.md (D-01..D-10), ROADMAP.md (SC1-SC5), STATE.md (Phase-9 risk + Phase-8 re-bless), REQUIREMENTS.md (FEEL-01..05), `config.json`.

### Secondary (MEDIUM confidence)
- Context7 `/pygame-community/pygame-ce` — `gfxdraw.pie` is unfilled; `gfxdraw.filled_polygon` exists;
  `Surface.fill` + BLEND special-flags compositing. Used to confirm the filled-wedge + tint approach.

### Tertiary (LOW confidence)
- CC0 sound sourcing venues (freesound.org CC0 filter, Kenney.nl, OpenGameArt, bfxr/jsfxr) — general
  ecosystem knowledge, `[ASSUMED]`; the specific file/tool is selected and license-verified by the
  user at add time (D-10).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libs; pygame edition verified locally and against CI pins.
- Architecture / change sites: HIGH — every site read in code; the firewall contract read in the test harness.
- Golden-safety: HIGH — committed `trace.jsonl` + `frame_hashes.txt` for `ghost_eat`/`death` confirmed present; Phase-8 re-bless recorded in STATE.md.
- Pitfalls: HIGH — derived from the actual tests (`test_ghost_micro` positional ctor, `test_determinism_guard` token list, frame-hash skip logic, pygame edition split).
- Sound sourcing: LOW — intentionally deferred to playtest (D-10); flagged in Assumptions.

**Research date:** 2026-06-30
**Valid until:** 2026-07-30 (stable; the only moving piece is the chosen `.wav`, resolved at implementation)
