"""Shared visual primitives for the redesigned UI: the pixel font, named sizes,
and small render helpers. Imported by menu.py and game.py on the redesign branches.
Colors live in settings.py; this module reuses them rather than redefining."""
import pygame
from paths import resource_path

PIXEL_FONT = "assets/fonts/PressStart2P-Regular.ttf"

# Named pixel-font sizes (px). Press Start 2P reads best at integer sizes.
SIZE_TITLE = 48
SIZE_HEADING = 28
SIZE_MENU = 18
SIZE_BODY = 12
SIZE_SMALL = 9

_font_cache = {}


def pixel_font(size):
    """Return a cached Press Start 2P Font at ``size`` px (loaded once per size)."""
    if size not in _font_cache:
        _font_cache[size] = pygame.font.Font(resource_path(PIXEL_FONT), size)
    return _font_cache[size]
