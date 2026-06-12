"""Shared tile-geometry helpers + the two distinct ghost-box bounds (REF-01, D-14/D-16).

Centralizes the trivially-atomic geometry idioms that game/ghost/player all repeated:
the tile-coordinate lookup, the project-wide ``< 3`` walkability test, and the box-region
predicate that collapses ~9 inline ``x_lo < x < x_hi and y_lo < y < y_hi`` checks.

The two box rectangles are intentionally kept as TWO DISTINCT named constants — the
collision box and the targeting box genuinely differ on both axes (the latent BUG-01
inconsistency). Phase 3 / BUG-01 unifies them by pointing both at one constant; doing so
here is OUT OF SCOPE. Do NOT merge these.

D-15 landmine: share ONLY ``tile_at`` / ``is_walkable`` / ``in_box``. The alignment-band
and guard logic of ``Ghost.check_collisions`` and ``Player.check_position`` are structurally
divergent and must NOT be factored into a shared function.
"""
from settings import TILE_HEIGHT, TILE_WIDTH

# Two distinct box rectangles (x_lo, x_hi, y_lo, y_hi) — kept separate per D-13/D-14.
GHOST_BOX_BOUNDS_COLLISION = (350, 550, 360, 480)   # ghost.py check_collisions box test
GHOST_BOX_BOUNDS_TARGET = (340, 560, 340, 500)      # game.py get_targets eaten-ghost checks


def tile_at(center_x, center_y, level):
    """Row/col tile lookup using the centralized tile dims (was level[cy//num1][cx//num2])."""
    return level[center_y // TILE_HEIGHT][center_x // TILE_WIDTH]


def is_walkable(tile_code):
    """The project-wide ``< 3`` walkability idiom (0=empty, 1=dot, 2=big dot are walkable)."""
    return tile_code < 3


def in_box(x, y, bounds):
    """Box-region predicate; bounds=(x_lo, x_hi, y_lo, y_hi). Collapses ~9 inline checks."""
    x_lo, x_hi, y_lo, y_hi = bounds
    return x_lo < x < x_hi and y_lo < y < y_hi
