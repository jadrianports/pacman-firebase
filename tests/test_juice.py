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
