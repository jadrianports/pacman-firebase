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
_scanline_cache = {}


def pixel_font(size):
    """Return a cached Press Start 2P Font at ``size`` px (loaded once per size)."""
    if size not in _font_cache:
        _font_cache[size] = pygame.font.Font(resource_path(PIXEL_FONT), size)
    return _font_cache[size]


def glow_text(text, font, color, glow_color=None, radius=6, intensity=0.5):
    """Render ``text`` with a soft additive glow behind the crisp glyphs.

    Returns a SRCALPHA Surface padded by ``radius`` px on every side. The glow is a
    blurred, dimmed copy (pygame-ce ``gaussian_blur``) additively blitted ONCE under
    the sharp text. ``glow_color`` defaults to ``color``. ``intensity`` (0..1) scales
    the glow brightness so bright colors (yellow) don't bloom into a blown-out blob —
    lower is subtler; the crisp glyph on top stays full-brightness regardless."""
    glow_color = glow_color or color
    sharp = font.render(text, True, color)
    w, h = sharp.get_width() + 2 * radius, sharp.get_height() + 2 * radius

    out = pygame.Surface((w, h), pygame.SRCALPHA)
    blur_src = pygame.Surface((w, h), pygame.SRCALPHA)
    # Dim the glow source before blurring so the additive halo stays soft.
    dimmed = tuple(int(c * intensity) for c in glow_color[:3])
    tinted = font.render(text, True, dimmed)
    blur_src.blit(tinted, (radius, radius))
    blurred = pygame.transform.gaussian_blur(blur_src, radius)
    out.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)  # single, dimmed pass
    out.blit(sharp, (radius, radius))
    return out


def scanline_overlay(size, spacing=4, alpha=70):
    """Return a cached SRCALPHA overlay: a dark horizontal line every ``spacing`` px.

    Blit over the whole screen each frame for a subtle CRT scanline. ``alpha`` is the
    per-line darkness (0-255). Cached by (size, spacing, alpha)."""
    key = (size, spacing, alpha)
    if key not in _scanline_cache:
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        line = (0, 0, 0, alpha)
        for y in range(0, h, spacing):
            pygame.draw.line(surf, line, (0, y), (w, y))
        _scanline_cache[key] = surf
    return _scanline_cache[key]
