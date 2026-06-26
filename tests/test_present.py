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


def test_overlay_present_survives_opengl_display(monkeypatch):
    """_overlay_present self-heals when the display surface reports the OPENGL flag.

    pygame.Surface is a C extension type so instance attributes cannot be set
    directly; we use a minimal duck-type shim that reports OPENGL from get_flags().
    _overlay_present must detect this, call pygame.display.set_mode to recreate a
    blittable 2D surface, and complete without raising.
    """
    class _GLDisplay:
        """Minimal duck-type shim that looks like an OPENGL-mode display."""
        def get_flags(self):
            return pygame.OPENGL

        def get_size(self):
            return (200, 200)

    render = pygame.Surface((200, 200))
    render.fill((9, 9, 9))
    present._overlay_present(_GLDisplay(), render, (0, 0))  # must not raise


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
