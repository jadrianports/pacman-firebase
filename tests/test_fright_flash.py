"""FEEL-04 fright-flash (blink-white) tests (RED until 09-03).

Targets the EXACT API 09-03 will build:
  * ``Ghost(..., blink_white=..., spooked_white_img=...)`` keyword params, with the
    spooked-branch blit choosing ``spooked_white_img`` when ``blink_white`` is True.
  * ``Game.create_ghosts`` computing ``blink_white`` — and forcing it False whenever
    ``juice`` is False (firewall: juice=False frames must never blink).

The Ghost ctor is exercised through the positional ``make_ghost`` shape from
``tests/test_ghost_micro.py:41-57`` PLUS the two new keyword args (NEVER positional).
Assertions use only dual-edition-safe primitives (Surface.fill + screen.get_at) — no
gaussian_blur (Pitfall 5). RED now: Ghost rejects ``blink_white`` (TypeError) and the
blink-off attribute does not exist (AttributeError).
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import copy

from harness.headless import init_headless
pygame, _screen, _clock = init_headless()

import board
from ghost import Ghost
from game import Game
from harness.replay import install_frame_driven_sound
from settings import FRIGHT_FLASH_START


def _new_game():
    surface = pygame.Surface(_screen.get_size())
    g = Game(surface, _clock)
    install_frame_driven_sound(g)
    return g


def _spooked_ghost(surface, blink_white, spooked_img, spooked_white_img):
    """Build a spooked Ghost (powerup=True, not dead, not eaten) on its own surface.

    Mirrors make_ghost (test_ghost_micro.py) positionally, then adds the two new
    keyword args. __init__ runs check_collisions()+draw(), so the spooked sprite is
    already blitted to ``surface`` by the time this returns."""
    img = pygame.Surface((45, 45))
    dead_img = pygame.Surface((45, 45))
    eaten_ghost = [False, False, False, False]
    return Ghost(
        384, 50, (384, 50), 2, img, 0, False, False, 0,
        surface, True, eaten_ghost, spooked_img, dead_img,
        copy.deepcopy(board.boards),
        blink_white=blink_white, spooked_white_img=spooked_white_img,
    )


def test_blink_white_blits_distinct_pixel():
    """A blink_white=True spooked ghost blits a different pixel than a steady
    spooked ghost. RED now: Ghost has no blink_white/spooked_white_img kwargs."""
    blue = pygame.Surface((45, 45)); blue.fill((0, 0, 255))
    white = pygame.Surface((45, 45)); white.fill((255, 255, 255))

    surf_steady = pygame.Surface(_screen.get_size())
    surf_blink = pygame.Surface(_screen.get_size())

    _spooked_ghost(surf_steady, blink_white=False, spooked_img=blue, spooked_white_img=white)
    _spooked_ghost(surf_blink, blink_white=True, spooked_img=blue, spooked_white_img=white)

    sample = (384 + 5, 50 + 5)
    assert surf_steady.get_at(sample) != surf_blink.get_at(sample)


def test_blink_off_under_juice_false():
    """create_ghosts forces blink_white=False on every ghost when juice=False, even
    deep inside the blink window — the firewall keeps juice=False frames steady.
    RED now: Ghost exposes no ``blink_white`` attribute (create_ghosts never sets it)."""
    g = _new_game()
    assert g.juice is False
    g.powerup = True
    g.power_counter = FRIGHT_FLASH_START + 50  # inside the blink window
    g.create_ghosts()
    assert g.blinky.blink_white is False
    assert g.inky.blink_white is False
    assert g.pinky.blink_white is False
    assert g.clyde.blink_white is False
