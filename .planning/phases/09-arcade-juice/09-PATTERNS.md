# Phase 9: Arcade Juice - Pattern Map

**Mapped:** 2026-06-30
**Files analyzed:** 8 (4 modified source, 1 new asset, 3 new tests)
**Analogs found:** 8 / 8 (all in-codebase; RESEARCH analogs verified against live code)

This phase **modifies existing files** and adds tests — it creates no new source modules. Every
change site already exists; the planner copies the in-file neighbor pattern. All analogs below were
re-read in the live tree and the file:line citations are confirmed current (not just RESEARCH echoes).

## File Classification

| New/Modified Symbol | File | Role | Data Flow | Closest Analog | Match Quality |
|---------------------|------|------|-----------|----------------|---------------|
| `SoundManager.play_eat_ghost()` + `eat_ghost_sound` + `_eat_channel` | `sound.py` | service (audio) | event-driven | `play_powerup`/`play_death` + `_load_sound` (`sound.py:36-66`) | exact |
| `_draw_death()` + `death_anim_frame` state + dying-branch | `game.py` | controller (render) | request-response (per-frame) | `player.draw()` call site + eat_freeze juice branch (`game.py:586-604`) | exact (role + flow) |
| `play_eat_ghost()` trigger | `game.py` `check_ghost_collisions` | controller (event) | event-driven | existing `stop_waka()`/`pause_powerup()` in same eat branch (`game.py:474-475`) | exact |
| `blink_white` compute + ctor kwargs + `spooked_white_img` | `game.py` `create_ghosts`/`__init__` | controller (render) | request-response (per-frame) | `create_ghosts` four-ghost ctor block (`game.py:381-393`) | exact |
| `blink_white` / `spooked_white_img` params + blit | `ghost.py` | component (sprite) | request-response | spooked branch in `Ghost.draw` (`ghost.py:305-306`) + ctor (`ghost.py:280-298`) | exact |
| `DEATH_ANIM_FRAMES`, `FRIGHT_FLASH_START`, `FRIGHT_FLASH_INTERVAL` | `settings.py` | config | — | Phase-8 tunables block (`settings.py:111-119`) | exact |
| eat-ghost `.wav` | `assets/audio/` | asset | file-I/O | `death.wav`/`powerup.wav` (loaded via `_load_sound`) | exact |
| `test_death_anim.py` | `tests/` | test | request-response | `test_juice_firewall.py` headless-Game pattern (`:1-42`) | exact |
| `test_eat_ghost_sound.py` | `tests/` | test | event-driven | `test_juice_firewall.py` `_new_game` + spy | role-match |
| `test_fright_flash.py` | `tests/` | test | request-response (pixel) | `test_ghost_micro.py` `make_ghost` positional ctor (`:41-57`) + `test_juice.py` `get_at` pixel asserts | exact |

## Pattern Assignments

### `sound.py` — `play_eat_ghost()` (service, event-driven)

**Analog:** `SoundManager.play_powerup`/`play_death`/`_load_sound` — same file, `sound.py:10-66`.

**Loader + channel pattern** (`sound.py:10-18`) — add the new load beside the others, and a dedicated
channel beside `_waka_channel` (ch 0) / `_powerup_channel` (ch 1). Use **Channel(2)** (D-10):
```python
self.start_sound = self._load_sound('start.wav', volume=0.4)
self.waka_sound = self._load_sound('wakawaka.wav', volume=0.5)
self.powerup_sound = self._load_sound('powerup.wav', volume=0.4)
self.death_sound = self._load_sound('death.wav', volume=0.5)

self._waka_channel = pygame.mixer.Channel(0)
self._powerup_channel = pygame.mixer.Channel(1)
```

**Play-method pattern** (`sound.py:43-45`, the `play_powerup` shape — None-guard + channel.play):
```python
def play_powerup(self):
    if self.powerup_sound:
        self._powerup_channel.play(self.powerup_sound, loops=-1)
```
New method mirrors it as a **one-shot** (no `loops=-1`), on `self._eat_channel` (Channel(2)).
`_load_sound` already None-guards a missing file, so the offline/degraded path is free.

---

### `game.py` — death wedge (controller, per-frame render)

**Analog:** the player-draw call site + the eat_freeze `if self.juice:` overlay branch, `game.py:586-604`.

**Draw-site branch pattern** (`game.py:586-587`) — the wedge replaces `player.draw()` **only** when
`self.dying and self.juice`; `juice=False` keeps the exact existing call (D-05):
```python
if not self.eat_freeze:
    player_circle = self.player.draw(self.counter)
```
> Pitfall 4 (verified safe): `player_circle` is referenced **only** inside the
> `if not self.dying and not self.eat_freeze and not self.starting:` collision guard (`game.py:616-618`),
> which never runs while `dying` — so the wedge branch may legally not bind it.

**Juice-gated overlay pattern to copy** (`game.py:591-604`) — the eat_freeze block is the existing
template for "juice draws X, else draw the plain thing": draw primitives directly to `self.screen`.

**State-field pattern** (`game.py:87-89` init, `:140-150` reset, `:419-424` start_dying) — add
`self.death_anim_frame` beside `self.dying`/`self.dying_delay`. Set 0 in `__init__`, `start_dying`,
and `reset_after_death`; increment **only inside `if self.dying and self.juice:`** so the
`juice=False` sim is untouched and it never enters captured state.
```python
# start_dying (game.py:419-424) — the existing reset-on-death-start template:
def start_dying(self):
    self.dying = True
    self.dying_delay = 0
    self.moving = False
    self.sound.stop_all()
    self.sound.play_death()
```

**Wedge geometry:** `math` is already imported at `settings.py:1` and in `game.py`; use
`pygame.draw.polygon` only (RESEARCH Pattern 1 has the copy-ready `_draw_death`). No `draw.pie`
(does not exist), no `gaussian_blur` (CI vanilla-pygame lacks it).

---

### `game.py` — eat-ghost sound trigger (controller, event)

**Analog:** the existing two audio calls in the same eat branch, `game.py:474-475`.
```python
self.eat_freeze_pos = (gx, gy)
self.sound.stop_waka()
self.sound.pause_powerup()
break
```
Insert `self.sound.play_eat_ghost()` right after `pause_powerup()` — **ungated** (D-02). Not behind
`self.juice`; audio never touches the hashed pixel path (SDL dummy driver headless).

---

### `game.py` — `blink_white` compute + Ghost kwargs (controller, per-frame)

**Analog:** `create_ghosts` four-ghost construction block, `game.py:381-393` (verified — all four
`Ghost(...)` calls end positionally with `..., self.spooked_img, self.dead_img, self.level)`).
```python
self.blinky = Ghost(self.blinky_x, self.blinky_y, self.targets[0], self.ghost_speeds[0], self.blinky_img,
                    self.blinky_direction, self.blinky_dead, self.blinky_box, 0,
                    self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level)
```
Append **keyword** args after `self.level`: `blink_white=blink_white, spooked_white_img=self.spooked_white_img`
to all four. Compute `blink_white` once before the four calls (RESEARCH Pattern 3 — juice + powerup +
`power_counter > FRIGHT_FLASH_START` + interval parity).

**Pre-tinted image, built once** — analog is the existing `spooked_img` load at `game.py:39`:
```python
self.spooked_img = pygame.transform.scale(pygame.image.load(resource_path('assets/ghosts/powerup.png')), (45, 45))
```
Build `self.spooked_white_img = self.spooked_img.copy()` then `.fill(..., special_flags=pygame.BLEND_RGB_ADD)`
in `__init__` right after line 39. `BLEND_RGB_ADD` exists in both pygame editions (Pitfall 5).

> `power_counter` is paused during `eat_freeze` (`game.py:548`), so the blink pauses with the freeze
> for free. Under `juice=False`, `blink_white` is always `False` → byte-identical render (D-08).

---

### `ghost.py` — keyword-default params + spooked-branch blit (component)

**Analog:** ctor signature `ghost.py:280-281` and the spooked branch `ghost.py:305-306` (both verified).

**Ctor signature** (`ghost.py:280-281`) — append the two params **with defaults, after `level`**
(CRITICAL: positional params would break `test_ghost_micro.make_ghost` and every `create_ghosts` call):
```python
def __init__(self, x_coord, y_coord, target, speed, img, direct, dead, box, id,
             screen, powerup, eaten_ghost, spooked_img, dead_img, level):
```
→ add `, blink_white=False, spooked_white_img=None` at the end; store `self.blink_white = blink_white`
and `self.spooked_white_img = spooked_white_img` (mirror the `self.spooked_img = spooked_img` line at `ghost.py:296`).

**Spooked blit** (`ghost.py:305-306`) — pick the white surface when `blink_white`:
```python
elif self.powerup and not self.dead and not self.eaten_ghost[self.id]:
    self.screen.blit(self.spooked_img, (self.x_pos, self.y_pos))
```
→ `img = self.spooked_white_img if self.blink_white else self.spooked_img` then blit `img`.

---

### `settings.py` — new tunables (config)

**Analog:** the Phase-8 fairness tunables block, `settings.py:111-119` (pure-int, no new import, with a
rationale comment per dial — keeps `test_determinism_guard` green):
```python
GHOST_CATCH_DISTANCE = 24          # FAIR-01 center-to-center catch radius (px); D-10 dial...
GHOST_CHASE_SPEED_NUM = 40         # FAIR-02 chase-step numerator; D-10 dial...
PLAYER_TURN_WINDOW_MARGIN = 6      # FAIR-03 pre-turn widening each edge (px)...
```
Add `DEATH_ANIM_FRAMES`, `FRIGHT_FLASH_START` (= 480), `FRIGHT_FLASH_INTERVAL` (= 8) as **pure ints**
with the same one-line-rationale style, tagged FEEL-01 / FEEL-04 / D-04 / D-06.

---

### `tests/` — new test files

**`test_death_anim.py` / `test_eat_ghost_sound.py` analog:** `test_juice_firewall.py:1-42` — the
headless-Game harness: SDL-dummy env, `init_headless()`, `Game(surface, clock)` on its own
off-screen `pygame.Surface`, `install_frame_driven_sound(g)` to deterministically shim
`is_death_playing` (RESEARCH "Don't Hand-Roll": `harness.replay`):
```python
from harness.headless import init_headless
pygame, _screen, _clock = init_headless()
from game import Game
from harness.replay import install_frame_driven_sound

def _new_game():
    surface = pygame.Surface(_screen.get_size())
    g = Game(surface, _clock)
    install_frame_driven_sound(g)
    return g
```
- `test_death_anim.py`: set `g.juice = True`, force `dying`, run a tick — assert no raise
  (`player_circle` safe) and that `juice=False` dying renders identically (reuse the
  `_frame_hash` two-run equality at `test_juice_firewall.py:15-16,34-42`).
- `test_eat_ghost_sound.py`: spy/monkeypatch `g.sound.play_eat_ghost`, drive the eat branch, assert
  called; plus a headless no-raise call of `play_eat_ghost()` directly.

**`test_fright_flash.py` analog (pixel + positional ctor):** `test_ghost_micro.py:41-57`
(`make_ghost` constructs a `Ghost` headless, positionally) for the white-vs-spooked blit, plus
`test_juice.py:17-21` `surf.get_at((x,y))[:3]` pixel assertions:
```python
return Ghost(x, y, target, speed, img, direction, dead, box, ghost_id,
             screen, powerup, eaten_ghost, img, img, copy.deepcopy(board.boards))
```
Construct two ghosts (distinct `spooked_img` vs `spooked_white_img`), assert differing
`screen.get_at(...)` pixels when `blink_white=True`; and assert `create_ghosts` yields
`blink_white=False` whenever `juice=False`.

## Shared Patterns

### Juice firewall gating
**Source:** `game.py:593-604` (eat_freeze `if self.juice: ... else: ...`), `game.py:626`.
**Apply to:** death wedge (`_draw_death` call) and `blink_white` compute. Every new **visual** is an
`if self.juice:` branch overlaying the unchanged `juice=False` path. Every new frame counter is
juice-gated. Audio (`play_eat_ghost`) is exempt (D-02).
```python
if self.juice:
    # juice-only effect
else:
    # existing plain render — unchanged, keeps goldens green
```

### Centralized tunables (no inline magic numbers)
**Source:** `settings.py:111-119`. **Apply to:** every new numeric dial (frame budgets, thresholds,
cadence). Pure ints, no new import, rationale comment — determinism-guard safe.

### Headless audio None-guard
**Source:** `sound.py:19-25` (`_load_sound` returns `None` if file missing) and the `if self.x_sound:`
guard in every play method. **Apply to:** `play_eat_ghost` — degrade silently when the `.wav` or mixer
is absent (matches the "fully playable offline" constraint).

### Ghost is dumb / rebuilt each frame
**Source:** `game.py:381-393` + `ghost.py:280-300`. **Apply to:** FEEL-04 — never store blink state on
the ghost across frames; compute in `Game`, pass through the constructor as a precomputed bool.

## No Analog Found

None. Every change site and test pattern has a direct in-codebase neighbor. The only genuinely-new
artifact is the eat-ghost `.wav` content file (sourced/licensed at playtest per D-09/D-10) — not a
code pattern. Verify `build.py`/PyInstaller spec globs `assets/audio/*` so it ships (RESEARCH A4).

## Metadata

**Analog search scope:** `sound.py`, `settings.py`, `game.py` (init/create_ghosts/check_ghost_collisions/tick render block), `ghost.py` (ctor + draw), `player.py` (draw), `tests/test_juice_firewall.py`, `tests/test_juice.py`, `tests/test_ghost_micro.py`, `assets/audio/`.
**Files scanned:** 9 source/test + 1 asset dir.
**All RESEARCH-cited analogs (sound.py:9-66, ghost.py:305-306, game.py:586, create_ghosts game.py:381-393, settings.py tunables) re-verified against live code — line numbers current.**
**Pattern extraction date:** 2026-06-30
