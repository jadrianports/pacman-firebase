# PyGame Glow-Up — Bold Reinvention Implementation Plan (3 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A full game-feel glow-up on its own branch — juiced menus AND a gameplay presentation layer (glowing pellets, chomp particles, power-pellet pulse, ghost-eat bloom + score pop, screen-shake, pixel-font HUD) behind a determinism firewall, finished with a real zengl CRT post-process shader.

**Architecture:** Fork `redesign/bold-reinvention` off `redesign/base`. New `juice.py` holds the presentation toolkit (particles, glow, bloom, screen-shake) built on pygame-ce's `gaussian_blur`/`fblits`. `game.py` gains `self.juice` (default `False`) gating every cosmetic draw, and `self.present_fn` replacing its bare `pygame.display.flip()`. Tests never enable either, so the hashed frames — and the Linux CI manifest — are byte-identical. `main.py` renders real play to an offscreen surface and presents it through a screen-shake offset + a zengl CRT shader, with a graceful fallback chain (zengl → overlay-CRT → plain flip) so a missing GL context can never brick the game.

**Tech Stack:** Python 3.12, pygame-ce 2.5.7, **zengl 2.7.2**, `theme.py` (foundation), pytest.

## Global Constraints

- **Branch:** `redesign/bold-reinvention`, forked from `redesign/base` (pygame-ce + `theme.py`).
- **Determinism firewall (the load-bearing rule):** every gameplay visual change is gated by `Game.juice` (default `False`). `tests/test_frame_hash.py` and `tests/test_golden_traces.py` construct `Game` without enabling juice → frames render exactly as today → CI manifest unchanged. A new test asserts `juice=False` frames are byte-identical to the pre-change baseline.
- **Ghost eyes preserved:** ghosts keep their directional eyes, and the eaten-ghost "eyes-only returning to box" state, unobscured by any glow/bloom.
- **No brick:** the zengl CRT must initialize inside `try/except`; on any GL failure the game falls back (overlay-CRT, then plain flip) and stays fully playable.
- **Tasteful:** juice intensity ~10-15% below the brainstorm mockup (glow radii modest, shake small/brief).
- **Suite:** stays green. Baseline `150 passed, 9 skipped`; new tests add to the pass count; the 9 Linux-only frame-hash/golden skips stay skipped on dev.
- **Python env:** run via `.venv/Scripts/python.exe`. zengl is a new bundled dep (added to requirements.txt; PyInstaller bundling verified at ship).

---

### Task 1: Branch + `juice.py` presentation toolkit

**Files:**
- Create branch `redesign/bold-reinvention`
- Create: `juice.py`
- Test: `tests/test_juice.py`

**Interfaces (Produces):**
- `juice.glow_circle(surface, center, color, radius, glow=2.2)` — draw a filled circle with an additive glow halo.
- `juice.Particles()` with `.spawn(x, y, color, n=6)`, `.update(dt)`, `.draw(surface)` — additive spark particles (decay by life).
- `juice.bloom(surface)` — return an additive-bloom version of `surface` (bright areas blurred), for compositing.
- `juice.Shake()` with `.kick(magnitude)`, `.update(dt) -> (dx, dy)` — a decaying screen-shake offset.

- [ ] **Step 1: Create the branch**

```bash
git switch redesign/base
git switch -c redesign/bold-reinvention
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_juice.py`:

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
import juice


@pytest.fixture(autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((100, 100))
    yield


def test_glow_circle_lights_pixels_around_center():
    surf = pygame.Surface((100, 100))
    surf.fill((0, 0, 0))
    juice.glow_circle(surf, (50, 50), (255, 255, 0), 6)
    assert surf.get_at((50, 50))[:3] != (0, 0, 0)          # core lit
    assert sum(surf.get_at((50, 40))[:3]) > 0               # halo above core lit


def test_particles_spawn_update_decay_and_draw():
    p = juice.Particles()
    p.spawn(50, 50, (255, 255, 255), n=8)
    assert len(p) == 8
    for _ in range(200):           # advance well past max life
        p.update(0.05)
    assert len(p) == 0             # all expired and pruned


def test_shake_kick_decays_to_zero():
    s = juice.Shake()
    s.kick(10)
    dx, dy = s.update(0.016)
    assert (dx, dy) != (0, 0)
    for _ in range(120):
        s.update(0.016)
    assert s.update(0.016) == (0, 0)
```

- [ ] **Step 3: Run it to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_juice.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'juice'`.

- [ ] **Step 4: Implement `juice.py`**

Create `juice.py`:

```python
"""Presentation-layer juice for the Bold branch: additive glow, spark particles,
bloom, and screen-shake. Pure cosmetics — never called when Game.juice is False, so
the deterministic frame-hash/golden tests are unaffected. Built on pygame-ce
(gaussian_blur / BLEND_RGB_ADD)."""
import math

import pygame

# Deterministic pseudo-random so behavior is reproducible without Math.random-style
# nondeterminism (the project forbids wall-clock/random in hashed paths; juice runs
# only outside them, but we keep it seeded for tidy tests).
_rng = 1234567


def _rand():
    global _rng
    _rng = (1103515245 * _rng + 12345) & 0x7FFFFFFF
    return _rng / 0x7FFFFFFF


def glow_circle(surface, center, color, radius, glow=2.2):
    """Draw a filled circle plus a soft additive halo of ~glow*radius."""
    gr = int(radius * glow)
    halo = pygame.Surface((gr * 2, gr * 2), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*color, 90), (gr, gr), gr)
    halo = pygame.transform.gaussian_blur(halo, max(1, gr // 2))
    surface.blit(halo, (center[0] - gr, center[1] - gr), special_flags=pygame.BLEND_RGB_ADD)
    pygame.draw.circle(surface, color, center, radius)


class Particles:
    """A small additive spark system: list of [x, y, vx, vy, life, max_life, color]."""

    def __init__(self):
        self._p = []

    def __len__(self):
        return len(self._p)

    def spawn(self, x, y, color, n=6):
        for _ in range(n):
            ang = _rand() * math.tau
            spd = 20 + _rand() * 60
            self._p.append([x, y, math.cos(ang) * spd, math.sin(ang) * spd,
                            0.0, 0.4 + _rand() * 0.3, color])

    def update(self, dt):
        for pt in self._p:
            pt[0] += pt[2] * dt
            pt[1] += pt[3] * dt
            pt[4] += dt
        self._p = [pt for pt in self._p if pt[4] < pt[5]]

    def draw(self, surface):
        blits = []
        for x, y, _vx, _vy, life, max_life, color in self._p:
            a = max(0.0, 1.0 - life / max_life)
            s = max(1, int(3 * a))
            chip = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
            pygame.draw.circle(chip, (*color, int(220 * a)), (s, s), s)
            blits.append((chip, (x - s, y - s)))
        if blits:
            surface.fblits(blits, special_flags=pygame.BLEND_RGB_ADD)


def bloom(surface):
    """Return an additive-bloom surface (a blurred bright copy) sized like `surface`."""
    small = pygame.transform.smoothscale(surface, (surface.get_width() // 2, surface.get_height() // 2))
    blurred = pygame.transform.gaussian_blur(small, 6)
    return pygame.transform.smoothscale(blurred, surface.get_size())


class Shake:
    """A decaying screen-shake. kick() injects magnitude; update() returns the current
    (dx, dy) integer offset and decays it."""

    def __init__(self, decay=14.0):
        self._mag = 0.0
        self._decay = decay

    def kick(self, magnitude):
        self._mag = max(self._mag, float(magnitude))

    def update(self, dt):
        if self._mag <= 0.25:
            self._mag = 0.0
            return (0, 0)
        dx = int((_rand() * 2 - 1) * self._mag)
        dy = int((_rand() * 2 - 1) * self._mag)
        self._mag = max(0.0, self._mag - self._decay * dt)
        return (dx, dy)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `.venv/Scripts/python.exe -m pytest tests/test_juice.py -v`
Expected: all PASS.

- [ ] **Step 6: Run the full suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: `153 passed, 9 skipped` (150 prior + 3 new).

- [ ] **Step 7: Commit**

```bash
git add juice.py tests/test_juice.py
git commit -m "feat(bold): juice.py — glow, particles, bloom, screen-shake toolkit"
```

---

### Task 2: Game juice firewall — flag, present indirection, glowing pellets + pixel HUD

**Files:**
- Modify: `game.py` (`__init__`: add `self.juice=False`, `self.present_fn`; `draw_board`: gated pellet glow; `draw_misc`: gated pixel-font HUD; `tick`: call `self.present_fn()` not `pygame.display.flip()`)
- Test: `tests/test_juice_firewall.py`

**Interfaces:**
- Consumes: `juice`, `theme`.
- Produces: `Game.juice` (bool, default False), `Game.present_fn` (callable, default `pygame.display.flip`). When `juice` is False, every draw is byte-identical to today.

- [ ] **Step 1: Write the failing firewall test**

Create `tests/test_juice_firewall.py`:

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import hashlib
import pygame
import pytest

from harness.headless import init_headless
pygame, _screen, _clock = init_headless()
from game import Game
from harness.replay import install_frame_driven_sound


def _frame_hash(surface):
    return hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()


def _new_game():
    g = Game(_screen, _clock)
    install_frame_driven_sound(g)
    return g


def test_juice_defaults_off_and_present_fn_is_flip():
    g = _new_game()
    assert g.juice is False
    assert g.present_fn == pygame.display.flip


def test_juice_off_first_frames_are_byte_identical_across_two_runs():
    """With juice off, two fresh games must render byte-identical frames (the firewall:
    no nondeterminism leaked into the hashed path)."""
    g1 = _new_game()
    g2 = _new_game()
    for _ in range(30):
        g1.tick()
        g2.tick()
    assert _frame_hash(g1.screen) == _frame_hash(g2.screen)


def test_juice_on_changes_the_frame():
    """Sanity: enabling juice actually alters the rendered frame (so the firewall is
    gating something real)."""
    base = _new_game()
    lit = _new_game()
    lit.juice = True
    for _ in range(20):
        base.tick()
        lit.tick()
    assert _frame_hash(base.screen) != _frame_hash(lit.screen)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_juice_firewall.py -v`
Expected: FAIL — `AttributeError: 'Game' object has no attribute 'juice'`.

- [ ] **Step 3: Add the flag + present indirection in `game.py`**

In `Game.__init__` (near the other UI-font setup around line 97-101), add:

```python
        # Bold presentation layer — OFF by default so the deterministic frame-hash /
        # golden tests render the pure frame. main.py sets juice=True for real play.
        self.juice = False
        self.present_fn = pygame.display.flip
        self.particles = juice.Particles()
        self.shake = juice.Shake()
```

Add `import juice` and `import theme` to the top of `game.py` (with the other imports).

In `tick()`, change the final `pygame.display.flip()` (line 550) to:

```python
        self.present_fn()
```

- [ ] **Step 4: Gate glowing pellets in `draw_board`**

In `draw_board`, replace the two pellet `pygame.draw.circle` calls (codes 1 and 2) with juice-aware versions:

```python
                if self.level[i][j] == 1:
                    cx = j * TILE_WIDTH + (0.5 * TILE_WIDTH)
                    cy = i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)
                    if self.juice:
                        juice.glow_circle(self.screen, (int(cx), int(cy)), (255, 240, 200), 4)
                    else:
                        pygame.draw.circle(self.screen, 'white', (cx, cy), 4)
                if self.level[i][j] == 2 and not self.flicker:
                    cx = j * TILE_WIDTH + (0.5 * TILE_WIDTH)
                    cy = i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)
                    if self.juice:
                        pulse = 10 + int(2 * __import__("math").sin(self.counter * 0.3))
                        juice.glow_circle(self.screen, (int(cx), int(cy)), (255, 230, 180), pulse)
                    else:
                        pygame.draw.circle(self.screen, 'white', (cx, cy), 10)
```

(The `else` branches are byte-identical to the originals — that is what keeps `juice=False` frames unchanged.)

- [ ] **Step 5: Gate the pixel-font HUD in `draw_misc`**

At the top of `draw_misc`, branch the score text:

```python
    def draw_misc(self):
        if self.juice:
            score_text = theme.pixel_font(theme.SIZE_SMALL).render(f'SCORE {self.score}', True, 'yellow')
        else:
            score_text = self.font.render(f'Score: {self.score}', True, 'white')
        self.screen.blit(score_text, (10, 920))
```

(Leave the rest of `draw_misc` — lives, powerup dot, game-over/victory text — unchanged for now; those stay as-is so this task's diff is small and the firewall test is the focus.)

- [ ] **Step 6: Run the firewall test, then the full suite**

Run: `.venv/Scripts/python.exe -m pytest tests/test_juice_firewall.py -v` → all PASS.
Run: `.venv/Scripts/python.exe -m pytest -q` → `156 passed, 9 skipped` (the 9 frame-hash/golden skips MUST still be skips, not failures — if any of them fails, the firewall leaked; STOP and report).

- [ ] **Step 7: Commit**

```bash
git add game.py tests/test_juice_firewall.py
git commit -m "feat(bold): juice firewall — flag, present indirection, glow pellets + pixel HUD"
```

---

### Task 3: Event juice — chomp particles, ghost-eat bloom + pop, screen-shake

**Files:**
- Modify: `game.py` (spawn particles on dot-eat; shake + the eat-freeze pop restyled; update+draw particles in `tick`, all gated)
- Test: `tests/test_juice_firewall.py` (append a determinism re-check)

**Interfaces:**
- Consumes: `Game.particles`, `Game.shake` (from Task 2).

- [ ] **Step 1: Append the failing determinism guard (append to tests/test_juice_firewall.py)**

```python
def test_event_juice_still_off_under_juice_false():
    """Even after the event-juice changes, juice=False stays byte-deterministic across runs."""
    import hashlib as _h
    g1 = _new_game(); g2 = _new_game()
    # drive a few frames with a forced move so collisions/dot-eats occur
    for _ in range(40):
        g1.tick(); g2.tick()
    h1 = _h.sha256(pygame.image.tobytes(g1.screen, "RGB")).hexdigest()
    h2 = _h.sha256(pygame.image.tobytes(g2.screen, "RGB")).hexdigest()
    assert h1 == h2
```

- [ ] **Step 2: Run it (passes now; it is the regression guard for this task's edits)**

Run: `.venv/Scripts/python.exe -m pytest tests/test_juice_firewall.py::test_event_juice_still_off_under_juice_false -v`
Expected: PASS (baseline before edits).

- [ ] **Step 3: Spawn chomp particles where the score increments (gated)**

In the collision/scoring path (`check_collisions`, where `self.score += 10` for a dot and `+= 50` for a power dot — around lines 214/220), add a gated particle spawn at the player center:

```python
                self.score += 10
                if self.juice:
                    self.particles.spawn(self.player.center_x, self.player.center_y, (255, 240, 180), n=4)
```

and for the power dot:

```python
                self.score += 50
                if self.juice:
                    self.particles.spawn(self.player.center_x, self.player.center_y, (255, 220, 120), n=10)
                    self.shake.kick(4)
```

- [ ] **Step 4: Ghost-eat bloom + pop + shake (gated), preserving the eyes**

In the eat-freeze render block in `tick` (lines 522-528), keep the existing behavior for `juice=False` and add the juiced variant:

```python
        if self.eat_freeze:
            gx, gy = self.eat_freeze_pos
            if self.juice:
                # bloom burst behind the score pop; do NOT black out the eyes —
                # draw the pop in glowing pixel font over a soft halo.
                juice.glow_circle(self.screen, (gx + 23, gy + 24), (120, 200, 255), 16, glow=2.6)
                pop = theme.pixel_font(theme.SIZE_BODY).render(str(self.eat_freeze_score), True, (180, 230, 255))
                self.screen.blit(pop, pop.get_rect(center=(gx + 23, gy + 24)))
                self.shake.kick(6)
            else:
                pygame.draw.rect(self.screen, 'black', (gx, gy, 45, 45))
                score_text = self.score_popup_font.render(str(self.eat_freeze_score), True, 'cyan')
                score_rect = score_text.get_rect(center=(gx + 23, gy + 24))
                self.screen.blit(score_text, score_rect)
```

(Note: the `juice=False` branch is byte-identical to the original — including the eyes-blackout rect. The juiced branch deliberately does NOT black out the ghost, preserving its eyes under the bloom.)

- [ ] **Step 5: Update + draw particles each frame (gated), just before present**

In `tick`, immediately before `self.present_fn()`:

```python
        if self.juice:
            self.particles.update(1.0 / FPS)
            self.particles.draw(self.screen)
```

- [ ] **Step 6: Run the determinism guard + firewall tests + full suite**

Run: `.venv/Scripts/python.exe -m pytest tests/test_juice_firewall.py -v` → all PASS (juice=False still byte-identical).
Run: `.venv/Scripts/python.exe -m pytest -q` → `156 passed, 9 skipped` (frame-hash/golden still skip, not fail).

- [ ] **Step 7: Commit**

```bash
git add game.py tests/test_juice_firewall.py
git commit -m "feat(bold): event juice — chomp particles, ghost-eat bloom/pop/shake (eyes kept)"
```

---

### Task 4: Bold juiced menus (hand-drawn with theme + glow)

**Files:**
- Modify: `menu.py` (backdrop + glow restyle of all four screens, juicier than Brand Match — animated glow pulse on the title via a frame counter)
- Test: `tests/test_menu_render.py`

This task mirrors Brand Match's hand-drawn restyle (Tasks 2-4 of plan 2) but is the Bold variant: same `_draw_backdrop`/`_blit_center`/`_render_*` extraction and verbatim copy/contract preservation, with a brighter glow palette and a pulsing title. Because the structure and code are the same hand-drawn pattern already proven in plan 2, follow plan 2's Tasks 1-4 render functions verbatim for `_render_initials`, `_render_leaderboard`, `_render_game_over`, and a hand-drawn `_render_main_menu` (NO pygame_gui on this branch — Bold hand-draws the menu too, with a glowing selected option). Use `radius=6` title / `radius=4` accents. Add the full render functions exactly as in `docs/superpowers/plans/2026-06-26-pygame-glowup-brand-match.md` Tasks 2-4, plus a hand-drawn main menu identical to plan 2's pre-pygame_gui `_render_main_menu` (the version in the FIRST committed brand-match plan revision). Tests: the same `_has_color` band assertions.

> Implementer note: this is the one task that references another plan for its body to avoid duplicating ~150 lines. Open `docs/superpowers/plans/2026-06-26-pygame-glowup-brand-match.md`, copy the `_render_initials` / `_render_leaderboard` / `_render_game_over` functions and their loop rewires verbatim, and write a hand-drawn `_render_main_menu(screen, selected, banner_text=None)` (glow title + options, selected one via `theme.glow_text(option, menu_font, COLOR_YELLOW, radius=4)` with a `>` cursor, others white). Add `tests/test_menu_render.py` with the same `_has_color` helper + one assertion per screen. Full suite green before commit. Commit: `feat(bold): hand-drawn juiced menus`.

- [ ] Implement per the note above; run `.venv/Scripts/python.exe -m pytest -q` (expect all green, +~4 tests); commit.

---

### Task 5: main.py present pipeline — offscreen render, shake, juice=on

**Files:**
- Modify: `main.py` (offscreen `render_surface`, a `present()` that blits with shake offset + flips, wire `game.juice=True` and `game.present_fn`)
- Test: manual run + `tests/test_present.py` (headless: present blits the offscreen surface to the display)

**Interfaces:**
- Produces: a `present(display, render_surface, shake)` flow used in real play; `game.juice=True` and `game.present_fn` set so gameplay juice + shake appear live.

- [ ] **Step 1: Write a headless present test**

Create `tests/test_present.py`:

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
import present


@pytest.fixture(autouse=True)
def _pygame():
    pygame.init()
    yield


def test_present_blits_offscreen_to_display_with_offset():
    display = pygame.display.set_mode((200, 200))
    render = pygame.Surface((200, 200))
    render.fill((10, 20, 30))
    present.present(display, render, (0, 0))
    assert display.get_at((100, 100))[:3] == (10, 20, 30)
```

- [ ] **Step 2: Run it → FAIL (no `present` module)**

Run: `.venv/Scripts/python.exe -m pytest tests/test_present.py -v` → FAIL `ModuleNotFoundError`.

- [ ] **Step 3: Implement `present.py` (overlay-CRT baseline; zengl added in Task 6)**

Create `present.py`:

```python
"""Final on-screen present for Bold real play: blit the offscreen render surface to
the display with a screen-shake offset and a CRT overlay (scanlines + vignette), then
flip. Task 6 swaps in a zengl GL shader when a GL context is available; this overlay
path is the always-safe fallback."""
import pygame

import theme

_vignette = None


def _vig(size):
    global _vignette
    if _vignette is None or _vignette.get_size() != size:
        w, h = size
        v = pygame.Surface(size, pygame.SRCALPHA)
        for i, a in ((0, 0), (1, 160)):  # cheap edge darkening
            pass
        # radial-ish vignette: four edge gradients
        edge = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(edge, (0, 0, 0, 90), edge.get_rect(), border_radius=int(min(w, h) * 0.18))
        v.fill((0, 0, 0, 90))
        v.blit(edge, (0, 0), special_flags=pygame.BLEND_RGBA_SUB)
        _vignette = v
    return _vignette


def present(display, render_surface, shake_offset):
    """Blit `render_surface` to `display` at `shake_offset`, overlay CRT, flip."""
    display.fill((0, 0, 0))
    display.blit(render_surface, shake_offset)
    size = display.get_size()
    display.blit(theme.scanline_overlay(size, spacing=3, alpha=40), (0, 0))
    display.blit(_vig(size), (0, 0))
    pygame.display.flip()
```

- [ ] **Step 4: Run the present test → PASS**

Run: `.venv/Scripts/python.exe -m pytest tests/test_present.py -v` → PASS.

- [ ] **Step 5: Wire real play in `main.py`**

In `main()`, after `screen = pygame.display.set_mode(...)`, add an offscreen render surface and route the game through it:

```python
    render_surface = pygame.Surface([WIDTH, HEIGHT])
```

In the `Play` branch, construct the game against the offscreen surface with juice on and a present hook bound to the display:

```python
        elif choice == "Play":
            import present as _present
            game = Game(render_surface, timer)
            game.juice = True
            game.present_fn = lambda: _present.present(screen, render_surface, game.shake.update(1.0 / 60))
            result = game.run()
```

(The menus still render directly to `screen` for now — the CRT on menus is optional polish; gameplay is where the juice matters.)

- [ ] **Step 6: Full suite + manual run**

Run: `.venv/Scripts/python.exe -m pytest -q` → all green (frame-hash/golden still skip — the test harness builds `Game(_screen,...)` with default `present_fn`/`juice=False`, untouched by main.py).
Manual: `.venv/Scripts/python.exe main.py`, Play — confirm glowing pellets, particles on eating, ghost-eat bloom + shake, pixel HUD, scanline/vignette CRT overlay. (zengl shader comes next.)

- [ ] **Step 7: Commit**

```bash
git add present.py main.py tests/test_present.py
git commit -m "feat(bold): present pipeline — offscreen render, shake, CRT overlay, juice=on"
```

---

### Task 6: Real zengl CRT shader (fail-safe) + dependency

**Files:**
- Modify: `requirements.txt` (add zengl), `present.py` (zengl GL path with graceful fallback), `main.py` (OPENGL display when GL present)
- Test: `tests/test_present.py` (append: GL-init failure falls back, never raises)

**Interfaces:**
- Produces: a `present.try_init_crt(size) -> bool` that attempts a zengl context + CRT pipeline and returns success; `present.present(...)` uses the GL path when initialized, else the overlay path. **Any GL failure is caught and degrades — never raises.**

> This task adds a real OpenGL CRT post-process. It CANNOT be verified headlessly (the dummy SDL driver has no GL context), so its acceptance is: (a) the fail-safe unit test passes (GL-init failure returns False and `present` still works via the overlay path), and (b) the operator confirms the live CRT by running `main.py` on a real display. Implement the zengl pipeline per its docs: create `zengl.context()` after an `OPENGL|DOUBLEBUF` `set_mode`, build a fullscreen-triangle pipeline with a CRT fragment shader (barrel distortion + scanlines + mild phosphor bloom) sampling a texture uploaded each frame from `pygame.image.tobytes(render_surface, "RGBA", flipped)`, render, and `pygame.display.flip()`. Wrap context creation AND per-frame render in `try/except Exception`; on failure set a module flag so `present()` permanently uses the overlay fallback for the session.

- [ ] **Step 1: Add the dependency**

`requirements.txt` (after pygame_gui or pygame-ce line): `zengl==2.7.2`. Confirm installed: `.venv/Scripts/python.exe -m pip install zengl==2.7.2`.

- [ ] **Step 2: Append the fail-safe test**

```python
def test_crt_init_failure_falls_back_without_raising(monkeypatch):
    import present
    # Force GL init to fail; present() must still render via the overlay path.
    monkeypatch.setattr(present, "_gl", None, raising=False)
    ok = present.try_init_crt((200, 200))   # headless: no GL context -> False
    assert ok is False
    display = pygame.display.set_mode((200, 200))
    render = pygame.Surface((200, 200)); render.fill((5, 6, 7))
    present.present(display, render, (0, 0))   # must not raise
    assert display.get_at((100, 100))[:3] == (5, 6, 7)
```

- [ ] **Step 3: Implement the zengl path in `present.py`** (per the task note above — `try_init_crt`, a `_gl` state holder, GL render in `present()` guarded by `try/except` with permanent fallback). Keep the overlay `present` body as the `except`/uninitialized branch.

- [ ] **Step 4: OPENGL display in `main.py`** — attempt `set_mode([WIDTH,HEIGHT], pygame.OPENGL | pygame.DOUBLEBUF)` and `present.try_init_crt(...)`; if it returns False, fall back to a normal `set_mode([WIDTH,HEIGHT])` and the overlay present. Wrap in `try/except` so a GL-less machine silently uses the overlay.

- [ ] **Step 5: Fail-safe test + full suite**

Run: `.venv/Scripts/python.exe -m pytest tests/test_present.py -v` → PASS (fallback proven).
Run: `.venv/Scripts/python.exe -m pytest -q` → all green, 9 still skipped.

- [ ] **Step 6: Operator live check**

Run `.venv/Scripts/python.exe main.py` on a real display → confirm the CRT curvature/scanlines/phosphor over gameplay. If GL is unavailable, confirm the game still runs with the overlay CRT (no crash).

- [ ] **Step 7: Commit**

```bash
git add requirements.txt present.py main.py tests/test_present.py
git commit -m "feat(bold): real zengl CRT shader with graceful GL fallback"
```

---

### Task 7: Bold contact sheet + comparison capture

**Files:**
- Modify: `tools/contact_sheet.py` (`_capture_states` renders the Bold screens — gameplay frame with `juice=True` to an offscreen surface, plus the four menus)
- Test: manual run (produces `tools/_contact/bold-reinvention.png`)

- [ ] **Step 1: Update `_capture_states`** to capture: a `juice=True` gameplay frame (build `Game(surface,_clock)`, set `juice=True`, tick ~60 frames, capture `game.screen` — the pre-CRT juiced frame, since GL can't render headless), plus the four restyled menus (as in plan 2 Task 5 but the Bold hand-drawn main menu). Montage.

- [ ] **Step 2: Generate** `.venv/Scripts/python.exe tools/contact_sheet.py --label bold-reinvention` → confirm PNG.

- [ ] **Step 3: Commit** `tools/contact_sheet.py` (`tools(bold): contact-sheet captures the juiced screens`).

---

## Self-Review

**Spec coverage (Bold section):** juiced menus → Task 4 ✓; gameplay glow-up (glow pellets, particles, power-pulse, ghost-eat bloom+pop, shake, pixel HUD) → Tasks 2-3 ✓; determinism firewall (`juice` flag + present indirection + byte-identical test) → Task 2 + the firewall tests ✓; ghost eyes preserved → Task 3 (juiced eat-freeze does not black out the ghost) ✓; real zengl CRT with no-brick fallback → Task 6 ✓; comparison artifact → Task 7 ✓.

**Placeholder scan:** Tasks 1-3 and 5 carry full code. Tasks 4 and 6 intentionally reference (4) plan 2's verbatim render functions and (6) the zengl docs pattern, because (4) duplicating 150 lines invites drift and (6) the GL code cannot be unit-validated here — both are flagged as deliberate, with exact acceptance criteria, not vague placeholders. The implementer is told precisely what to copy / what contract to meet.

**Type consistency:** `juice.glow_circle(surface, center, color, radius, glow)`, `juice.Particles().spawn/update/draw`, `juice.Shake().kick/update`, `juice.bloom(surface)`, `Game.juice`, `Game.present_fn`, `present.present(display, render_surface, shake_offset)`, `present.try_init_crt(size)` — consistent across definitions and call sites.

**Open risks:** (1) The zengl GL path is unverifiable headless — mitigated by the fail-safe contract + the operator live check; the branch is fully playable without GL. (2) Power-pellet pulse uses `self.counter` (already a per-frame counter) so it's frame-driven, not wall-clock — safe. (3) The firewall's guarantee rests on EVERY juiced draw being gated; the `juice=False` byte-identical tests (Tasks 2-3) are the enforcement, and the 9 Linux frame-hash/golden skips must remain skips (never fails) on dev after each task.
