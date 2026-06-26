import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy"); os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame, pytest, display

@pytest.fixture(autouse=True)
def _pg():
    pygame.init(); yield

def test_init_returns_logical_900x950():
    logical = display.init()
    assert logical.get_size() == (900, 950)

def test_process_event_f11_toggles(monkeypatch):
    calls = {"n": 0}
    monkeypatch.setattr(display, "toggle", lambda: calls.__setitem__("n", calls["n"]+1))
    assert display.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11)) is True
    assert calls["n"] == 1
    assert display.process_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)) is False

def test_flip_does_not_raise():
    display.init()
    frame = pygame.Surface((900, 950)); frame.fill((10,20,30))
    display.flip(frame)   # must not raise (scales + blits + flip)
