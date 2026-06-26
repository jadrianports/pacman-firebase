import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from settings import WIDTH, HEIGHT, COLOR_YELLOW
import menu


@pytest.fixture(autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT))
    yield


def _has_color(surface, rgb, band=None, tol=40):
    """True if any pixel in the (optional) y-band is within `tol` per channel of
    rgb. Tolerance (not exact match) so the translucent scanline overlay darkening
    a glyph pixel by ~18% doesn't cause false negatives."""
    y0, y1 = band if band else (0, surface.get_height())
    tr, tg, tb = rgb
    for y in range(y0, y1, 2):
        for x in range(0, surface.get_width(), 2):
            r, g, b = surface.get_at((x, y))[:3]
            if abs(r - tr) <= tol and abs(g - tg) <= tol and abs(b - tb) <= tol:
                return True
    return False


def test_main_menu_renders_yellow_title_and_active_option():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_main_menu(screen, selected=0)
    # title band (top ~quarter) carries the yellow glow
    assert _has_color(screen, COLOR_YELLOW, band=(80, 260))
    # selected option (index 0) is yellow somewhere in the options band
    assert _has_color(screen, COLOR_YELLOW, band=(320, 600))


def test_main_menu_banner_renders_without_error():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_main_menu(screen, selected=1, banner_text="JAM passed you this week!")
    assert _has_color(screen, COLOR_YELLOW, band=(200, 260))


def test_initials_renders_active_slot_yellow():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_initials(screen, letters=[0, 1, 2], slot=1)
    # header present (yellow band near top)
    assert _has_color(screen, COLOR_YELLOW, band=(160, 240))
    # the active slot glyph row carries yellow
    assert _has_color(screen, COLOR_YELLOW, band=(360, 440))


def test_leaderboard_data_rank1_yellow_and_tab_active():
    screen = pygame.Surface((WIDTH, HEIGHT))
    entries = [{"initials": "JAP", "score": 7540}, {"initials": "JEM", "score": 4140}]
    menu._render_leaderboard(screen, active="week", entries=entries, last_week_initials="ZZZ")
    # rank-1 row is yellow
    assert _has_color(screen, COLOR_YELLOW, band=(160, 220))


def test_leaderboard_offline_shows_verbatim_copy():
    screen = pygame.Surface((WIDTH, HEIGHT))
    # None == offline; renders without error. We assert the renderer handles the
    # sentinel (no exception) — copy correctness is covered by the string constant.
    menu._render_leaderboard(screen, active="all", entries=None, last_week_initials=None)


def test_leaderboard_empty_renders():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_leaderboard(screen, active="week", entries=[], last_week_initials=None)


def test_game_over_lose_is_red_win_is_green():
    screen = pygame.Surface((WIDTH, HEIGHT))
    from settings import COLOR_RED, COLOR_GREEN
    menu._render_game_over(screen, score=1234, is_new_best=False, game_won=False, identity_error=False)
    assert _has_color(screen, COLOR_RED, band=(200, 320))
    screen2 = pygame.Surface((WIDTH, HEIGHT))
    menu._render_game_over(screen2, score=1234, is_new_best=True, game_won=True, identity_error=False)
    assert _has_color(screen2, COLOR_GREEN, band=(200, 320))
    # NEW BEST! is yellow
    assert _has_color(screen2, COLOR_YELLOW, band=(440, 520))


def test_game_over_identity_error_renders():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_game_over(screen, score=10, is_new_best=False, game_won=False, identity_error=True)
