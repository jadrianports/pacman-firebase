import os
from paths import resource_path

import pygame
import theme


def test_pixel_font_asset_present():
    path = resource_path("assets/fonts/PressStart2P-Regular.ttf")
    assert os.path.isfile(path), f"pixel font missing at {path}"
    assert os.path.getsize(path) > 10_000  # a real TTF, not an empty stub


def test_pixel_font_is_cached_and_sized(tmp_path):
    pygame.font.init()
    f1 = theme.pixel_font(theme.SIZE_MENU)
    f2 = theme.pixel_font(theme.SIZE_MENU)
    assert f1 is f2  # same size returns the cached instance
    assert isinstance(f1, pygame.font.Font)
    # a known glyph renders to a non-empty surface
    surf = f1.render("A", True, (255, 255, 0))
    assert surf.get_width() > 0 and surf.get_height() > 0
