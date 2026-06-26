"""Final on-screen present for Bold real play: blit the offscreen render surface to
the display with a screen-shake offset and a CRT overlay (scanlines + vignette), then
flip. Task 6 swaps in a zengl GL shader when a GL context is available; this overlay
path is the always-safe fallback.

Vignette deviation from brief: the brief's _vig used a single rounded-rect subtract
which only darkened extreme corners (~18% radius). This implementation draws concentric
border-rectangles with a quadratic alpha falloff to produce a smooth gradient that
darkens all four edges and fades cleanly to zero at ~28% depth toward the centre."""
import pygame

import theme

_vignette = None


def _vig(size):
    """Build (and cache) a soft edge-darkening vignette overlay.

    Draws concentric 1-px border rectangles from the screen edge inward, each with
    a quadratic alpha falloff, so the edges are dark and the centre is fully
    transparent. The result is a proper border vignette rather than a corner-only
    effect.
    """
    global _vignette
    if _vignette is None or _vignette.get_size() != size:
        w, h = size
        v = pygame.Surface(size, pygame.SRCALPHA)
        v.fill((0, 0, 0, 0))
        depth = max(1, int(min(w, h) * 0.28))  # gradient reaches 28% inward
        for i in range(depth):
            t = 1.0 - i / depth                  # 1.0 at edge → 0.0 at inner boundary
            alpha = int(100 * t * t)             # quadratic fade; max ~100 at outer edge
            pygame.draw.rect(v, (0, 0, 0, alpha), (i, i, w - 2 * i, h - 2 * i), 1)
        _vignette = v
    return _vignette


def present(display, render_surface, shake_offset):
    """Blit `render_surface` to `display` at `shake_offset`, overlay CRT, flip."""
    display.fill((0, 0, 0))
    display.blit(render_surface, shake_offset)
    size = display.get_size()
    display.blit(theme.scanline_overlay(size, spacing=3, alpha=40), (0, 0))
    display.blit(_vig(size), (0, 0))
    pygame.display.flip()
