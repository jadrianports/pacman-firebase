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


_halo_cache = {}


def _halo(color, radius, glow):
    """Build (and cache) the blurred ROUND glow halo for a given color/radius/glow.

    The gaussian blur is the expensive op, so we do it ONCE per unique
    (color, radius, glow) and reuse the surface — critical because draw_board calls
    glow_circle for every dot every frame (~240×), and re-blurring each was the cause
    of a massive FPS drop. The surface is padded beyond the circle so the blur fades to
    transparent before the edge (otherwise the glow clips into a square)."""
    c3 = tuple(int(c) for c in color[:3])
    key = (c3, radius, round(glow, 2))
    halo = _halo_cache.get(key)
    if halo is None:
        gr = int(radius * glow)
        blur = max(1, gr // 2)
        half = gr + blur * 3            # headroom for the blur to fade out (no square clip)
        halo = pygame.Surface((half * 2, half * 2), pygame.SRCALPHA)
        pygame.draw.circle(halo, (*c3, 90), (half, half), gr)
        halo = pygame.transform.gaussian_blur(halo, blur)
        _halo_cache[key] = halo
    return halo


def glow_circle(surface, center, color, radius, glow=2.2):
    """Draw a filled circle plus a soft additive ROUND halo of ~glow*radius.

    The blurred halo is cached (see ``_halo``) so per-call cost is just two blits —
    cheap enough to run for every maze dot each frame."""
    halo = _halo(color, radius, glow)
    half = halo.get_width() // 2
    surface.blit(halo, (center[0] - half, center[1] - half), special_flags=pygame.BLEND_RGB_ADD)
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
            surface.fblits(blits, pygame.BLEND_RGB_ADD)


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
