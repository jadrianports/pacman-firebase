"""Micro per-ghost characterization tests (TST-02, D-13/D-14).

These tests LOCK IN the current per-ghost decision behavior so that when Phase 2
collapses the 4x movement duplication, any drift points at the exact ghost +
situation. They are CHARACTERIZATION tests: every expected value below is the
literal the UNMODIFIED ``ghost.py`` produces today (captured by running the
method), pinned as the spec. They assert what the code DOES, not what an
arcade-accurate Pac-Man "should" do.

Construction is fully headless (D-14): the SDL dummy drivers are set by
``tests/conftest.py`` before pygame imports, so ``Ghost.__init__`` (which calls
``check_collisions()`` and ``draw()``) runs against an in-memory surface with no
window. ``ghost.py`` is NOT modified.

Pitfall 4: every case passes a ``copy.deepcopy(board.boards)`` as ``level`` so a
mutated board (dots eaten / tiles changed) can never leak between cases.
"""
import copy

import pygame
import pytest

import board
from ghost import Ghost


@pytest.fixture(scope="module")
def screen():
    """A headless SDL-dummy surface for Ghost construction (D-14).

    conftest.py forces SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy before pygame is
    imported, so this opens no real window. Module-scoped: one surface for all
    cases (the surface holds no per-ghost state — every case deep-copies the
    board separately).
    """
    pygame.display.init()
    surf = pygame.display.set_mode((900, 950))
    yield surf


def make_ghost(screen, x, y, target, speed, direction, ghost_id,
               dead=False, box=False, powerup=False):
    """Construct a Ghost headless from the full ghost.py:6-7 __init__ signature.

    Dummy ``pygame.Surface((45, 45))`` objects stand in for the three images
    (img / spooked_img / dead_img) — harmless to blit headless. ``level`` is a
    ``copy.deepcopy(board.boards)`` so the shared module list is NEVER passed by
    reference (Pitfall 4). Returns the constructed Ghost; ``__init__`` has
    already run check_collisions() and draw() by the time it returns.
    """
    img = pygame.Surface((45, 45))
    eaten_ghost = [False, False, False, False]
    return Ghost(
        x, y, target, speed, img, direction, dead, box, ghost_id,
        screen, powerup, eaten_ghost, img, img,
        copy.deepcopy(board.boards),
    )


# --------------------------------------------------------------------------- #
# check_collisions characterization (Task 1)                                  #
#                                                                             #
# check_collisions returns (turns, in_box). turns is [R, L, U, D] booleans;   #
# in_box is the 350<x<550 & 360<y<480 box-region flag. Each assertion pins    #
# the EXACT tuple the current ghost.py produces at a decisive tile.           #
# --------------------------------------------------------------------------- #

def test_check_collisions_returns_turns_and_box_flag(screen):
    """make_ghost constructs headless and check_collisions yields (turns, box).

    Smoke + shape pin: turns is a 4-element bool list, in_box a bool.
    """
    g = make_ghost(screen, 384, 50, target=(384, 50), speed=2, direction=0, ghost_id=0)
    turns, in_box = g.check_collisions()
    assert turns == [False, True, True, True]  # right blocked at this intersection
    assert in_box is False


def test_check_collisions_decisive_intersection(screen):
    """Decisive multi-way intersection at (384, 50) dir 0.

    Right is walled; left/up/down are open. This is the exact turn-availability
    the move_* tests below rely on, pinned as literals.
    """
    g = make_ghost(screen, 384, 50, target=(384, 50), speed=2, direction=0, ghost_id=0)
    assert g.turns == [False, True, True, True]
    assert g.in_box is False


def test_check_collisions_box_edge_inside_sets_box_flag(screen):
    """Box-edge archetype: inside the 350<x<550 & 360<y<480 region -> in_box True.

    At (450, 420) the ghost is inside the box region, so check_collisions sets
    in_box True (ghost.py:111-112). turns are all open here.
    """
    g = make_ghost(screen, 450, 420, target=(450, 420), speed=2, direction=2, ghost_id=1)
    assert g.turns == [True, True, True, True]
    assert g.in_box is True


def test_check_collisions_box_edge_outside_clears_box_flag(screen):
    """Box-edge archetype, other side: just left of the box region -> in_box False.

    At (340, 420) x is not > 350, so the box test fails and in_box is False —
    pinning the exact boundary behavior. Right is walled here.
    """
    g = make_ghost(screen, 340, 420, target=(340, 420), speed=2, direction=0, ghost_id=1)
    assert g.turns == [True, False, True, True]
    assert g.in_box is False


def test_check_collisions_tunnel_mouth_left_edge(screen):
    """Tunnel-mouth archetype: at the far-left column the else-branch forces L+R open.

    When ``0 < center_x // 30 < 29`` is False (center_x = 0+22 = 22, 22//30 = 0),
    check_collisions takes the else branch and unconditionally opens left+right
    (ghost.py:108-110), leaving up/down False. This is the wrap-corridor mouth.
    """
    g = make_ghost(screen, 0, 460, target=(900, 460), speed=2, direction=0, ghost_id=0)
    assert g.turns == [True, True, False, False]
    assert g.in_box is False
