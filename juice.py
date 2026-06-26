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
