"""Fast non-golden unit proofs for FAIR-01 (catch helper) and FAIR-02 (accumulator).

These are the sub-second, deterministic proof artifacts for the two ``game.py``
fairness changes, independent of the golden net (which is re-blessed only once,
on Linux, after the D-10 playtest). They assert the NEW (post-change) behavior
and are RED today, each guarded with ``@pytest.mark.xfail(strict=True)`` so the
suite stays green at wave merge. Plan 08-02 removes each marker as its target
behavior turns green.

FAIR-01 - catch helper (``Game._catches``, introduced in Plan 08-02):
  Integer squared-distance against the existing live center properties
  (``player.center_*`` / ghost ``center_*``) - no square-root, no float.
    * same-tile overlap -> caught
    * diagonal one-tile corner-kiss (~41px) -> NOT caught (corner-kiss-safe, D-02)
    * boundary: exactly GHOST_CATCH_DISTANCE apart -> caught; one past -> not

FAIR-02 - chase accumulator (added in Plan 08-02):
  Over 20 moving frames with no powerup / no dead / no eaten ghosts, the per-frame
  ``ghost_speeds[0]`` is an integer-rational step in {1, 2} whose 20-frame sum is
  exactly GHOST_CHASE_SPEED_NUM (37 -> 1.85 px/frame avg). Today (no accumulator)
  the value is always 2 and the 20-sum is 40, so the assertion is RED.

Headless construction mirrors ``tests/test_ghost_micro.py`` / the golden harness:
conftest.py forces the SDL dummy drivers before pygame imports.
"""
import types

import pygame
import pytest

from game import Game
from settings import GHOST_CATCH_DISTANCE, GHOST_CHASE_SPEED_NUM


@pytest.fixture(scope="module")
def screen():
    """A headless SDL-dummy surface for Game construction.

    conftest.py forces SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy before pygame is
    imported, so this opens no real window.
    """
    # Mirror harness/headless.py: Game.__init__ loads a font (pygame.font.Font)
    # and constructs SoundManager (pygame.mixer.Sound), so both subsystems must be
    # up. SDL_*=dummy (conftest) keeps this windowless/silent.
    pygame.display.init()
    pygame.font.init()
    pygame.mixer.init()
    surf = pygame.display.set_mode((900, 950))
    yield surf


@pytest.fixture
def game(screen):
    """A fresh headless Game; ``pygame.time.Clock()`` stands in for the timer arg.

    Function-scoped so the FAIR-02 accumulator test starts from a clean speed
    state every run.
    """
    return Game(screen, pygame.time.Clock())


def _place_player_center(game, cx, cy):
    """Move the player so its live center properties equal (cx, cy).

    ``center_x = x + 23``, ``center_y = y + 24`` (player.py:23-29).
    """
    game.player.x = cx - 23
    game.player.y = cy - 24


def _fake_ghost(cx, cy):
    """A stand-in ghost exposing only the attributes ``_catches`` reads."""
    return types.SimpleNamespace(center_x=cx, center_y=cy)


# --------------------------------------------------------------------------- #
# FAIR-01: catch helper (Game._catches) - RED until Plan 08-02 adds it.       #
# Each case is xfail(strict) so AttributeError today reads as expected-RED.    #
# --------------------------------------------------------------------------- #

def test_catch_same_tile_overlap(game):
    """Same-tile overlap (player center == ghost center) -> caught."""
    _place_player_center(game, 300, 300)
    assert game._catches(_fake_ghost(300, 300)) is True


def test_catch_corner_kiss_is_safe(game):
    """Diagonal one-tile corner-kiss (~30x28, dist ~41px) -> NOT caught (D-02)."""
    _place_player_center(game, 300, 300)
    # offset one tile diagonally: 30px x, 28px y -> sqrt(900+784) ~= 41px
    assert game._catches(_fake_ghost(330, 328)) is False


def test_catch_boundary_exactly_at_radius(game):
    """Centers exactly GHOST_CATCH_DISTANCE apart -> caught (d*d <= r*r)."""
    _place_player_center(game, 300, 300)
    assert game._catches(_fake_ghost(300 + GHOST_CATCH_DISTANCE, 300)) is True


def test_catch_boundary_one_past_radius(game):
    """One pixel past GHOST_CATCH_DISTANCE -> NOT caught."""
    _place_player_center(game, 300, 300)
    assert game._catches(_fake_ghost(300 + GHOST_CATCH_DISTANCE + 1, 300)) is False


# --------------------------------------------------------------------------- #
# FAIR-02: chase-speed accumulator - RED until Plan 08-02 adds the step.       #
# Today update_ghost_speeds yields 2 every frame (20-sum 40 != 37).           #
# --------------------------------------------------------------------------- #

@pytest.mark.xfail(strict=True, reason="RED until FAIR-02 adds the integer-rational step - Plan 08-02, Wave 2")
def test_chase_accumulator_averages_to_num_over_den_frames(game):
    """20 moving chase frames yield steps in {1,2} summing to GHOST_CHASE_SPEED_NUM.

    No powerup, no dead/eaten ghosts, ghosts moving (moving=True, eat_freeze=False)
    -> the default-chase tier. Today every frame is 2 (20-sum 40); after FAIR-02 the
    integer-rational accumulator yields a {1,2} sequence summing to 37 (1.85 avg).
    """
    game.powerup = False
    game.eaten_ghost = [False, False, False, False]
    game.blinky_dead = game.inky_dead = game.pinky_dead = game.clyde_dead = False
    game.moving = True
    game.eat_freeze = False

    steps = []
    for _ in range(20):
        game.update_ghost_speeds()
        steps.append(game.ghost_speeds[0])

    assert all(s in (1, 2) for s in steps)
    assert sum(steps) == GHOST_CHASE_SPEED_NUM
