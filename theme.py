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


def glow_text(text, font, color, glow_color=None, radius=6):
    """Render ``text`` with a soft additive glow behind the crisp glyphs.

    Returns a SRCALPHA Surface padded by ``radius`` px on every side. The glow is a
    blurred bright copy (pygame-ce ``gaussian_blur``) additively blitted under the
    sharp text. ``glow_color`` defaults to ``color``."""
    glow_color = glow_color or color
    sharp = font.render(text, True, color)
    w, h = sharp.get_width() + 2 * radius, sharp.get_height() + 2 * radius

    out = pygame.Surface((w, h), pygame.SRCALPHA)
    blur_src = pygame.Surface((w, h), pygame.SRCALPHA)
    tinted = font.render(text, True, glow_color)
    blur_src.blit(tinted, (radius, radius))
    blurred = pygame.transform.gaussian_blur(blur_src, radius)
    out.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
    out.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)  # double for intensity
    out.blit(sharp, (radius, radius))
    return out
