"""Shared tile-geometry helpers + the unified ghost-box bounds (REF-01; BUG-01/D-01).

Centralizes the trivially-atomic geometry idioms that game/ghost/player all repeated:
the tile-coordinate lookup, the project-wide ``< 3`` walkability test, and the box-region
predicate that collapses ~9 inline ``x_lo < x < x_hi and y_lo < y < y_hi`` checks.

The ghost box is a SINGLE rectangle ``GHOST_BOX_BOUNDS``, consumed by both
``ghost.py:check_collisions`` (the physical in_box flag — turn legality, box-exit timing,
dead-ghost revival) and ``game.py:get_targets`` (the eaten-ghost targeting check). BUG-01
unified the two formerly-divergent constants onto the tighter collision box (D-01); the
looser targeting heuristic now conforms to the physical box rather than vice versa.

D-15 landmine: share ONLY ``tile_at`` / ``is_walkable`` / ``in_box``. The alignment-band
and guard logic of ``Ghost.check_collisions`` and ``Player.check_position`` are structurally
divergent and must NOT be factored into a shared function.
"""
from settings import TILE_HEIGHT, TILE_WIDTH

# Single ghost-box rectangle (x_lo, x_hi, y_lo, y_hi), used by both ghost.py:check_collisions
# and game.py:get_targets (BUG-01/D-01). Historical divergence (do NOT re-split): this was
# once TWO constants — a looser targeting box (340,560,340,500) for get_targets vs the
# tighter collision box (350,550,360,480) for check_collisions. They were unified onto the
# tighter collision box per BUG-01/D-01 (the targeting box conforms to physics).
GHOST_BOX_BOUNDS = (350, 550, 360, 480)


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
