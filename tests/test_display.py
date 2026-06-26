import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
import pytest
import display


@pytest.fixture(autouse=True)
def _pg():
    pygame.init(); pygame.display.set_mode((900, 950), pygame.SCALED); yield


def test_process_event_handles_f11(monkeypatch):
    called = {"n": 0}
    monkeypatch.setattr(display, "toggle", lambda: called.__setitem__("n", called["n"] + 1))
    assert display.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11)) is True
    assert called["n"] == 1
    # a non-F11 key is ignored
    assert display.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)) is False
    assert called["n"] == 1


def test_is_fullscreen_reads_flag():
    # windowed SCALED display -> not fullscreen
    assert display.is_fullscreen() is False
