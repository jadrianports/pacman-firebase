"""Single display authority. The game renders at a fixed 900x950 logical resolution;
this module owns the real OS window (fit-to-desktop or fullscreen) and scales the
logical frame into it with aspect-preserving letterboxing. Menus and gameplay both
present through display.flip()/present()."""
import pygame
from settings import WIDTH, HEIGHT

_window = None          # real OS window surface
_fullscreen = False


def _fit_window_size():
    """Largest (w,h) <= ~90% of the desktop that keeps the 900x950 aspect ratio."""
    try:
        dw, dh = pygame.display.get_desktop_sizes()[0]
    except Exception:
        dw, dh = 1280, 720
    scale = min(1.0, (dw * 0.95) / WIDTH, (dh * 0.90) / HEIGHT)
    return max(1, round(WIDTH * scale)), max(1, round(HEIGHT * scale))


def init():
    """(Re)create the OS window at fit size (or fullscreen). Returns the LOGICAL
    900x950 surface that all rendering should target."""
    global _window
    if _fullscreen:
        _window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    else:
        _window = pygame.display.set_mode(_fit_window_size(), pygame.RESIZABLE)
    return pygame.Surface((WIDTH, HEIGHT))


def is_fullscreen():
    return _fullscreen


def _present(frame):
    """Aspect-scale the 900x950 frame into the current window, centered + letterboxed."""
    if _window is None:
        return
    ww, wh = _window.get_size()
    scale = min(ww / WIDTH, wh / HEIGHT)
    sw, sh = max(1, int(WIDTH * scale)), max(1, int(HEIGHT * scale))
    scaled = pygame.transform.smoothscale(frame, (sw, sh))
    _window.fill((0, 0, 0))
    _window.blit(scaled, ((ww - sw) // 2, (wh - sh) // 2))
    pygame.display.flip()


def flip(frame):
    """Present a fully-drawn 900x950 logical frame to the screen."""
    _present(frame)


def toggle():
    global _fullscreen, _window
    _fullscreen = not _fullscreen
    try:
        init()  # recreate window in the new mode (keeps logical surface in callers)
    except Exception:
        _fullscreen = not _fullscreen  # revert on failure


def process_event(event):
    """Call from a loop. F11 toggles fullscreen; window-resize is handled implicitly
    (the next flip() rescales to the new size). Returns True if it handled the event."""
    if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
        toggle()
        return True
    return False
