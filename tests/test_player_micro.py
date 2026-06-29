"""Micro player-cornering characterization tests (FAIR-03, D-09/D-15).

Companion to ``tests/test_ghost_micro.py`` for the PLAYER side. These pin the
pre-turn ("cornering") forgiveness window in ``Player.check_position``: the
narrow ``12 <= residue <= 18`` band that decides whether a queued perpendicular
turn is granted as Pac-Man approaches a junction.

Two cases, modelled on the ghost-micro structure:

* ``test_cornering_baseline_window`` (NO marker, green today and after) pins that
  a residue squarely inside the ORIGINAL window (15) still grants the turn - so
  the Wave 2 widening (Plan 08-03) never narrows the existing affordance.
* ``test_cornering_preturn_widened`` (``xfail(strict=True)``) asserts the NEW
  behavior: a residue of 8 - INSIDE the widened
  ``(12 - PLAYER_TURN_WINDOW_MARGIN) .. (18 + PLAYER_TURN_WINDOW_MARGIN)`` = 6..24
  band but OUTSIDE the legacy 12..18 band - also grants the turn. This is False
  under today's ``player.py`` (RED) and turns True only once Plan 08-03 widens
  the four player windows. ``ghost.py`` is NOT touched - cornering forgiveness
  is a player-only affordance (D-15).

Construction is fully headless: ``tests/conftest.py`` forces the SDL dummy
drivers before pygame imports. Every case passes a ``copy.deepcopy(board.boards)``
so a mutated board can never leak between cases (Pitfall 4).
"""
import copy

import pygame
import pytest

import board
from player import Player
from settings import PLAYER_TURN_WINDOW_MARGIN, TILE_WIDTH, TILE_HEIGHT

# Decisive 4-way junction: board column 7 is a long vertical dot-corridor and row
# 6 is a full horizontal dot-corridor, so (row 6, col 7) has open cells both above
# (row 5) and below (row 7). A player travelling RIGHT (dir 0) across it can only
# gain the up/down turns via the cornering window (player.py:76-80), which makes
# the residue band the sole gate we are characterizing here.
_JUNCTION_COL = 7   # board.boards[*][7] is open (dots) for rows 5,6,7
_JUNCTION_ROW = 6

# Travel-axis residue (centerx % TILE_WIDTH) for each case. 15 sits mid-band in the
# legacy 12..18 window; 8 is OUTSIDE 12..18 but INSIDE the margin-widened band.
_BASELINE_RESIDUE = 15
_WIDENED_RESIDUE = 8

# Document the intent in terms of the D-09 tunable: the widened residue must fall in
# the post-FAIR-03 band but not the legacy one. (Guards the test against a future
# margin change silently invalidating the chosen residue.)
assert (12 - PLAYER_TURN_WINDOW_MARGIN) <= _WIDENED_RESIDUE <= (18 + PLAYER_TURN_WINDOW_MARGIN)
assert not (12 <= _WIDENED_RESIDUE <= 18)


@pytest.fixture(scope="module")
def screen():
    """A headless SDL-dummy surface for Player construction.

    conftest.py forces SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy before pygame is
    imported, so this opens no real window. Module-scoped: one surface for all
    cases (the surface holds no per-case state - every case deep-copies the
    board separately).
    """
    pygame.display.init()
    surf = pygame.display.set_mode((900, 950))
    yield surf


def make_player(screen, x, y, direction):
    """Construct a headless Player and place it at (x, y) facing ``direction``.

    Simpler than the ghost analog: ``Player(screen)`` then set ``x``/``y``/
    ``direction``. ``check_position`` reads only ``center_x``/``center_y`` (which
    derive from ``x``/``y``) and ``direction``.
    """
    p = Player(screen)
    p.x, p.y, p.direction = x, y, direction
    return p


def _coords_for_residue(residue):
    """Player (x, y) putting center on junction (row 6, col 7) at travel residue.

    ``center_x = x + 23``, ``center_y = y + 24`` (player.py:23-29). We solve for a
    center whose ``// TILE_WIDTH`` is the junction column and whose
    ``% TILE_WIDTH`` is ``residue``, with the center row on ``_JUNCTION_ROW`` so the
    up/down corridor cells (rows 5 and 7) are the ones probed.
    """
    centerx = _JUNCTION_COL * TILE_WIDTH + residue          # col 7, chosen residue
    centery = _JUNCTION_ROW * TILE_HEIGHT + (TILE_HEIGHT // 2)  # mid-tile on row 6
    return centerx - 23, centery - 24


def test_cornering_baseline_window(screen):
    """BASELINE (green now + after): residue 15 grants the perpendicular turn.

    Travelling RIGHT across the (row 6, col 7) junction with travel-axis residue
    15 (mid the legacy 12..18 window), check_position must grant BOTH the up and
    down turns - the open corridor cells at rows 5 and 7. This pins that the
    Wave-2 widening never removes the at-junction affordance.
    """
    x, y = _coords_for_residue(_BASELINE_RESIDUE)
    p = make_player(screen, x, y, direction=0)
    assert p.center_x % TILE_WIDTH == _BASELINE_RESIDUE   # residue is what we intend
    turns = p.check_position(copy.deepcopy(board.boards))
    assert turns[2] is True   # up corridor (row 5) granted
    assert turns[3] is True   # down corridor (row 7) granted


@pytest.mark.xfail(strict=True,
                   reason="RED until FAIR-03 widens the player window - Plan 08-03, Wave 2")
def test_cornering_preturn_widened(screen):
    """WIDENED (xfail until FAIR-03): residue 8 (in 6..24, not 12..18) grants the turn.

    Same junction, but ~6px earlier so the travel-axis residue is 8 - INSIDE the
    margin-widened ``(12 - PLAYER_TURN_WINDOW_MARGIN)..(18 + PLAYER_TURN_WINDOW_MARGIN)``
    band yet OUTSIDE the legacy 12..18 band. Today player.py leaves both turns
    False here (RED); Plan 08-03 widens the four windows and this goes green.
    """
    x, y = _coords_for_residue(_WIDENED_RESIDUE)
    p = make_player(screen, x, y, direction=0)
    assert p.center_x % TILE_WIDTH == _WIDENED_RESIDUE
    turns = p.check_position(copy.deepcopy(board.boards))
    assert turns[2] is True   # up corridor granted only after the window widens
    assert turns[3] is True   # down corridor granted only after the window widens
