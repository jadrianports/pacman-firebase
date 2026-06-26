import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import hashlib
import pygame
import pytest

from harness.headless import init_headless
pygame, _screen, _clock = init_headless()
from game import Game
from harness.replay import install_frame_driven_sound


def _frame_hash(surface):
    return hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()


def _new_game():
    # Give each game its own off-screen surface so hashes from two concurrent games
    # are independent (not clobbering the shared display surface).
    surface = pygame.Surface(_screen.get_size())
    g = Game(surface, _clock)
    install_frame_driven_sound(g)
    return g


def test_juice_defaults_off_and_present_fn_is_flip():
    g = _new_game()
    assert g.juice is False
    assert g.present_fn == pygame.display.flip


def test_juice_off_first_frames_are_byte_identical_across_two_runs():
    """With juice off, two fresh games must render byte-identical frames (the firewall:
    no nondeterminism leaked into the hashed path)."""
    g1 = _new_game()
    g2 = _new_game()
    for _ in range(30):
        g1.tick()
        g2.tick()
    assert _frame_hash(g1.screen) == _frame_hash(g2.screen)


def test_juice_on_changes_the_frame():
    """Sanity: enabling juice actually alters the rendered frame (so the firewall is
    gating something real)."""
    base = _new_game()
    lit = _new_game()
    lit.juice = True
    for _ in range(20):
        base.tick()
        lit.tick()
    assert _frame_hash(base.screen) != _frame_hash(lit.screen)
