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


# --------------------------------------------------------------------------- #
# Per-ghost decisive-state characterization (Task 2)                          #
#                                                                             #
# Each move_* returns (x_pos, y_pos, direction). Every expected tuple below   #
# is the literal the current ghost.py produces (captured by running it). A    #
# failure names the exact ghost + situation.                                  #
#                                                                             #
# Decisive intersection used by the chase/flee cases: (384, 50) facing right  #
# (dir 0). check_collisions there yields turns [False, True, True, True] —    #
# right is walled, so the move_* method must BRANCH on the target: a target   #
# above turns UP (dir 2), a target below turns DOWN (dir 3). The four ghost   #
# AIs happen to agree at this particular state, which is exactly what we pin: #
# any future refactor that diverges here will fail the specific ghost's test. #
#                                                                             #
# Archetypes covered across the suite (D-13):                                 #
#   * multi-way intersection : the (384, 50) chase/flee cases                 #
#   * flee-vs-chase          : same state, runaway target vs chase target     #
#   * box edge               : clyde dead/in-box fallback at (480, 438)       #
#   * tunnel mouth           : pinky/inky wrap at the x<-30 / x>900 edges      #
# --------------------------------------------------------------------------- #

# --- move_blinky --------------------------------------------------------------

def test_blinky_chases_up_at_blocked_intersection(screen):
    """INTERSECTION + CHASE: blinky dir0 at (384,50), right walled, target up-right.

    Right is blocked so blinky branches on the target; the target is above
    (y-200) so it turns UP one step.
    """
    g = make_ghost(screen, 384, 50, target=(584, -150), speed=2, direction=0, ghost_id=0)
    assert g.move_blinky() == (384, 48, 2)


def test_blinky_flees_down_when_target_is_below(screen):
    """FLEE-vs-CHASE: same blinky state, runaway target down-left -> turns DOWN.

    With a flee target below+left (e.g. a power-pellet runaway corner), blinky
    branches DOWN instead of up — the decision flips purely on the target tuple,
    which is how the game expresses flee (runaway target) vs chase (Pac-Man).
    """
    g = make_ghost(screen, 384, 50, target=(184, 250), speed=2, direction=0, ghost_id=0)
    assert g.move_blinky() == (384, 52, 3)


# --- move_inky ----------------------------------------------------------------

def test_inky_turns_up_at_blocked_intersection(screen):
    """INTERSECTION: inky dir0 at (384,50), right walled, chase target up-right.

    inky turns up/down freely to pursue; with right walled and target above it
    turns UP.
    """
    g = make_ghost(screen, 384, 50, target=(584, -150), speed=2, direction=0, ghost_id=1)
    assert g.move_inky() == (384, 48, 2)


def test_inky_flees_down_when_target_is_below(screen):
    """FLEE-vs-CHASE: inky same state, runaway target down-left -> turns DOWN."""
    g = make_ghost(screen, 384, 50, target=(184, 250), speed=2, direction=0, ghost_id=1)
    assert g.move_inky() == (384, 52, 3)


def test_inky_tunnel_mouth_wraps_to_right_edge(screen):
    """TUNNEL MOUTH: inky dir1 moving left past x<-30 wraps to x=900.

    Starting at x=-28 dir1 (speed 4), inky steps left, crosses the wrap
    threshold, and check_collisions/move wrap sets x_pos=900 (ghost.py:478-481).
    """
    g = make_ghost(screen, -28, 460, target=(-200, 460), speed=4, direction=1, ghost_id=1)
    assert g.move_inky() == (900, 460, 1)


# --- move_pinky ---------------------------------------------------------------

def test_pinky_turns_up_at_blocked_intersection(screen):
    """INTERSECTION: pinky dir0 at (384,50), right walled, chase target up-right."""
    g = make_ghost(screen, 384, 50, target=(584, -150), speed=2, direction=0, ghost_id=2)
    assert g.move_pinky() == (384, 48, 2)


def test_pinky_flees_down_when_target_is_below(screen):
    """FLEE-vs-CHASE: pinky same state, runaway target down-left -> turns DOWN."""
    g = make_ghost(screen, 384, 50, target=(184, 250), speed=2, direction=0, ghost_id=2)
    assert g.move_pinky() == (384, 52, 3)


def test_pinky_tunnel_mouth_wraps_to_left_edge(screen):
    """TUNNEL MOUTH: pinky dir0 moving right past x>900 wraps to x=-30.

    Starting at x=898 dir0 (speed 4), pinky steps right past the threshold and
    the wrap sets x_pos=-30 (ghost.py:604-607).
    """
    g = make_ghost(screen, 898, 460, target=(1200, 460), speed=4, direction=0, ghost_id=2)
    assert g.move_pinky() == (-30, 460, 0)


# --- move_clyde (also the dead/in-box fallback per CLAUDE.md) ------------------

def test_clyde_turns_up_at_blocked_intersection(screen):
    """INTERSECTION: clyde dir0 at (384,50), right walled, chase target up-right."""
    g = make_ghost(screen, 384, 50, target=(584, -150), speed=2, direction=0, ghost_id=3)
    assert g.move_clyde() == (384, 48, 2)


def test_clyde_dead_in_box_fallback_returns_to_target(screen):
    """BOX EDGE + dead fallback: clyde dead & in_box at (480,438) heading up.

    move_clyde doubles as the dead/in-box "eyes" fallback (CLAUDE.md). Dead and
    in the box at (480, 438) dir2 with a target up-left (the box gate at
    (440, 388)), clyde turns LEFT one step toward the target — the exact move
    Phase 2 must preserve when it collapses this fallback.
    """
    g = make_ghost(screen, 480, 438, target=(440, 388), speed=2, direction=2,
                   ghost_id=3, dead=True, box=True)
    assert g.move_clyde() == (478, 438, 1)
