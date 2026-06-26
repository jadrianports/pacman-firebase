"""Final on-screen present for gameplay: composite the CRT overlay (scanlines +
vignette) at logical 900x950 resolution with a screen-shake offset, then present the
composed frame to the OS window via display.flip(). No OpenGL/zengl path.

Vignette: concentric border-rectangles with quadratic alpha falloff, darkening all
four edges and fading to zero at ~28% depth toward the centre.
"""
import pygame
import theme
import display

_vignette = None
_frame = None  # reused per-frame compose buffer (avoid a 900x950 alloc every frame)


def _vig(size):
    global _vignette
    if _vignette is None or _vignette.get_size() != size:
        # soft edge-darkening vignette (concentric border rects, quadratic falloff)
        w, h = size
        v = pygame.Surface(size, pygame.SRCALPHA)
        depth = int(min(w, h) * 0.28)
        for i in range(depth):
            t = 1.0 - i / depth
            a = int(100 * t * t)
            pygame.draw.rect(v, (0, 0, 0, a), (i, i, w - 2*i, h - 2*i), 1)
        _vignette = v
    return _vignette


def present(render_surface, shake_offset):
    """Compose the CRT-overlay frame at 900x950 (shake + scanlines + vignette) and
    present it scaled-to-fit via display."""
    global _frame
    size = render_surface.get_size()
    if _frame is None or _frame.get_size() != size:
        _frame = pygame.Surface(size)
    frame = _frame
    frame.fill((0, 0, 0))
    frame.blit(render_surface, shake_offset)
    frame.blit(theme.scanline_overlay(size, spacing=3, alpha=40), (0, 0))
    frame.blit(_vig(size), (0, 0))
    display.flip(frame)
