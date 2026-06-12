"""Headless pygame bootstrap.

`init_headless()` sets the SDL dummy video/audio drivers BEFORE importing pygame
so the game initializes with no window and no audio device — safe for tests and
for CI runners. Importing pygame before the SDL env is set would bind the real
drivers, so the ordering here is load-bearing (see RESEARCH Pitfall 3).
"""
import os


def init_headless(size=(900, 950)):
    """Initialize pygame headless and return (pygame, screen, clock).

    SDL_VIDEODRIVER / SDL_AUDIODRIVER are set to "dummy" on the lines BELOW this
    comment but ABOVE `import pygame` — this order is required.
    """
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"

    import pygame

    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()

    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    return pygame, screen, clock
