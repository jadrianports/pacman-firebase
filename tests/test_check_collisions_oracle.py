"""Differential oracle for Ghost.check_collisions geometry centralization (D-07).

Proves the Plan 02-01 REF-01 substitution (inline num1/num2/num3 + the literal box
test -> centralized TILE_HEIGHT/TILE_WIDTH/HALF_TILE + in_box(GHOST_BOX_BOUNDS_COLLISION))
is BEHAVIOR-PRESERVING: for every enumerated (board-position x direction x in_box x dead)
case, the frozen PRE-REF-01 ``legacy_check_collisions`` (tests/_legacy_geometry.py) and the
NEW production ``Ghost.check_collisions`` return EXACTLY the same ``(turns, in_box)``.

This is the logic half of the "maximum paranoia" proof (the frame-hash test is the pixel
half). It locks turn-legality and the in_box flag — the in_box flag is what Phase 3 / BUG-01
later edits, so freezing it now keeps that change provably isolated.

Enumeration is PROGRAMMATIC (itertools.product), NOT @pytest.mark.parametrize: ~46k
arithmetic cases would bloat pytest collection. A single test loops and accumulates the
first few divergences for a readable failure message.

LIFECYCLE (D-06/D-07): this oracle + the frozen tests/_legacy_geometry.py are a one-shot
gate. Plan 02-02 DELETES both after its mover proofs are green. Do NOT delete here.
"""
import copy
import itertools

import pygame
import pytest

import board
from ghost import Ghost
from settings import BOARD_ROWS, BOARD_COLS, TILE_HEIGHT, TILE_WIDTH, HALF_TILE
from tests._legacy_geometry import legacy_check_collisions


@pytest.fixture(scope="module")
def screen():
    """Headless SDL-dummy surface (conftest forces SDL_*=dummy)."""
    pygame.display.init()
    surf = pygame.display.set_mode((900, 950))
    yield surf


def _make_ghost(screen, x, y, direction, ghost_id, dead, box):
    """Construct a Ghost headless (mirrors test_ghost_micro.make_ghost; Pitfall 4 deep-copy)."""
    img = pygame.Surface((45, 45))
    eaten_ghost = [False, False, False, False]
    return Ghost(
        x, y, (x, y), 2, img, direction, dead, box, ghost_id,
        screen, False, eaten_ghost, img, img,
        copy.deepcopy(board.boards),
    )


class _Probe:
    """A lightweight ghost-like snapshot the frozen legacy oracle reads from.

    legacy_check_collisions only reads center_x/center_y/level/direction/in_box/dead/
    x_pos/y_pos — never calls methods or mutates production state. We feed it a copy so
    the NEW Ghost.check_collisions (which mutates self.in_box/self.turns) cannot perturb
    the legacy input.
    """

    def __init__(self, g, in_box, dead):
        self.center_x = g.center_x
        self.center_y = g.center_y
        self.x_pos = g.x_pos
        self.y_pos = g.y_pos
        self.direction = g.direction
        self.in_box = in_box
        self.dead = dead
        self.level = copy.deepcopy(g.level)


# Position offsets within a tile that exercise the precedence-sensitive alignment bands
# (the `12 <= center % num <= 18` branches). Cover: tile origin (0), a sub-band position
# (7), the band edges (12 and 18), and the exact mid-band / HALF_TILE look-ahead (15).
_X_OFFSETS = (0, 7, 12, HALF_TILE, 18)
_Y_OFFSETS = (0, 7, 12, HALF_TILE, 18)


def test_check_collisions_old_equals_new_exhaustive(screen):
    """OLD legacy_check_collisions == NEW Ghost.check_collisions for the enumerated space.

    Crosses board tile positions (origin + half-tile + alignment-band offsets) x
    direction(0-3) x in_box(False,True) x dead(False,True). Asserts the (turns, in_box)
    tuples are EXACTLY equal (exact-bool/int compare, mirroring the micro-test style).
    """
    failures = []
    count = 0
    # center_x = x_pos + 22, center_y = y_pos + 22. Pick x_pos so the center lands at the
    # chosen tile column/row plus the intra-tile offset, covering the alignment bands.
    for row, col, xo, yo, direction, box, dead in itertools.product(
        range(BOARD_ROWS), range(BOARD_COLS), _X_OFFSETS, _Y_OFFSETS,
        range(4), (False, True), (False, True),
    ):
        # Place the ghost CENTER at (col*TILE_WIDTH + xo, row*TILE_HEIGHT + yo); x_pos is
        # center - 22 (the __init__ offset), so __init__ recomputes the same center.
        x_pos = col * TILE_WIDTH + xo - 22
        y_pos = row * TILE_HEIGHT + yo - 22

        g = _make_ghost(screen, x_pos, y_pos, direction, ghost_id=0, dead=dead, box=box)
        # Pin the enumerated flags the turn-logic reads, on BOTH sides identically.
        g.in_box = box
        g.dead = dead
        probe = _Probe(g, in_box=box, dead=dead)

        old = legacy_check_collisions(probe)
        new = g.check_collisions()

        count += 1
        if old != new:
            failures.append(
                (row, col, xo, yo, direction, box, dead, old, new)
            )
            if len(failures) >= 5:
                break

    assert not failures, (
        f"check_collisions diverged in {len(failures)} case(s) (first few shown); "
        f"checked {count} cases:\n"
        + "\n".join(
            f"  (row={r}, col={c}, xo={xo}, yo={yo}, dir={d}, in_box={b}, dead={dd}): "
            f"OLD={old} NEW={new}"
            for (r, c, xo, yo, d, b, dd, old, new) in failures
        )
    )
    # Sanity: the enumeration actually ran the full crossed space.
    assert count == BOARD_ROWS * BOARD_COLS * len(_X_OFFSETS) * len(_Y_OFFSETS) * 4 * 2 * 2
