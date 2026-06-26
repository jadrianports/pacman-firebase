"""Window + fullscreen management. Uses pygame.SCALED so the near-square game scales to
any window/fullscreen size with aspect-preserving letterboxing. F11 toggles fullscreen
from the menus. The real GL CRT is windowed-only (Play checks is_fullscreen() and uses the
overlay CRT in fullscreen, since OPENGL doesn't combine with SCALED)."""
import pygame
from settings import WIDTH, HEIGHT


def init():
    """Create/recreate the 2-D SCALED display, preserving the current fullscreen flag."""
    flags = pygame.SCALED
    surf = pygame.display.get_surface()
    if surf is not None and (surf.get_flags() & pygame.FULLSCREEN):
        flags |= pygame.FULLSCREEN
    return pygame.display.set_mode((WIDTH, HEIGHT), flags)


def is_fullscreen():
    surf = pygame.display.get_surface()
    return bool(surf and (surf.get_flags() & pygame.FULLSCREEN))


def toggle():
    """Flip fullscreen; SCALED handles the letterbox scaling. No-op safe on dummy driver."""
    try:
        pygame.display.toggle_fullscreen()
    except Exception:
        pass


def process_event(event):
    """Call from a menu event loop. F11 toggles fullscreen. Returns True if it handled
    the event (so the caller can skip its own handling for that key)."""
    if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
        toggle()
        return True
    return False
