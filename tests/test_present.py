import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
import present
import display


@pytest.fixture(autouse=True)
def _pygame():
    pygame.init()
    display.init()
    yield


def test_present_does_not_raise():
    """present() with a valid render surface and zero shake must not raise."""
    render = pygame.Surface((900, 950))
    render.fill((10, 20, 30))
    present.present(render, (0, 0))   # must not raise


def test_vignette_does_not_crash():
    """_vig() builds and caches a vignette without raising."""
    v = present._vig((900, 950))
    assert v is not None
    assert v.get_size() == (900, 950)
    # Second call returns the same cached object.
    v2 = present._vig((900, 950))
    assert v2 is v


def test_present_with_shake_offset_does_not_raise():
    """present() with a nonzero shake offset composites without error."""
    render = pygame.Surface((900, 950))
    render.fill((5, 6, 7))
    present.present(render, (3, -2))   # must not raise
