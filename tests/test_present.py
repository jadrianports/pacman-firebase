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


def test_crt_init_failure_falls_back_without_raising(monkeypatch):
    # Force GL state to None (simulate absent/failed GL context).
    monkeypatch.setattr(present, "_gl", None, raising=False)
    ok = present.try_init_crt((200, 200))   # headless: no GL context -> False
    assert ok is False
    display = pygame.display.set_mode((200, 200))
    render = pygame.Surface((200, 200))
    render.fill((5, 6, 7))
    present.present(display, render, (0, 0))   # must not raise
    assert display.get_at((100, 100))[:3] == (5, 6, 7)
