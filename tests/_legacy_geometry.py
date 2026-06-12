"""Frozen PRE-REF-01 copy of Ghost.check_collisions (D-07 differential oracle, one-shot).

This is a verbatim, self-contained copy of ``Ghost.check_collisions`` as it stood
BEFORE Plan 02-01 centralized the tile geometry — it inlines the original
``num1 = (HEIGHT - 50) // 32``, ``num2 = WIDTH // 30``, ``num3 = 15`` literals and
the literal box test ``350 < x_pos < 550 and 360 < y_pos < 480``.

It deliberately does NOT import ``ghost.py`` so it can never drift with the
refactored production code: it is the frozen "OLD" side of the differential oracle
in ``tests/test_check_collisions_oracle.py``. It operates on a passed ghost-like
object ``g`` and returns ``(turns, in_box)`` — the same tuple the production
``check_collisions`` returns.

LIFECYCLE (D-06/D-07): this frozen copy + the oracle that consumes it are a one-shot
gate. Plan 02-02 (the mover refactor) DELETES both after its own proofs are green.
Do NOT delete them in this plan.
"""
from settings import WIDTH, HEIGHT


def _legacy_tile(g, row, col):
    """Verbatim copy of the PRE-REF-01 ``Ghost._tile`` bounds-clamped lookup."""
    row = max(0, min(len(g.level) - 1, row))
    col = max(0, min(len(g.level[0]) - 1, col))
    return g.level[row][col]


def legacy_check_collisions(g):
    """Verbatim PRE-REF-01 ``Ghost.check_collisions`` body, operating on ghost-like ``g``.

    Reads ``g.center_x``/``g.center_y``/``g.level``/``g.direction``/``g.in_box``/
    ``g.dead``/``g.x_pos``/``g.y_pos`` and returns ``(turns, in_box)`` exactly as the
    original method did. The inline ``num1/num2/num3`` and the literal box test are
    intentionally NOT centralized here — this is the frozen OLD oracle.
    """
    # R, L, U, D
    num1 = ((HEIGHT - 50) // 32)
    num2 = (WIDTH // 30)
    num3 = 15
    turns = [False, False, False, False]
    if 0 < g.center_x // 30 < 29:
        if _legacy_tile(g, (g.center_y - num3) // num1, g.center_x // num2) == 9:
            turns[2] = True
        if _legacy_tile(g, g.center_y // num1, (g.center_x - num3) // num2) < 3 \
                or (_legacy_tile(g, g.center_y // num1, (g.center_x - num3) // num2) == 9 and (
                g.in_box or g.dead)):
            turns[1] = True
        if _legacy_tile(g, g.center_y // num1, (g.center_x + num3) // num2) < 3 \
                or (_legacy_tile(g, g.center_y // num1, (g.center_x + num3) // num2) == 9 and (
                g.in_box or g.dead)):
            turns[0] = True
        if _legacy_tile(g, (g.center_y + num3) // num1, g.center_x // num2) < 3 \
                or (_legacy_tile(g, (g.center_y + num3) // num1, g.center_x // num2) == 9 and (
                g.in_box or g.dead)):
            turns[3] = True
        if _legacy_tile(g, (g.center_y - num3) // num1, g.center_x // num2) < 3 \
                or (_legacy_tile(g, (g.center_y - num3) // num1, g.center_x // num2) == 9 and (
                g.in_box or g.dead)):
            turns[2] = True

        if g.direction == 2 or g.direction == 3:
            if 12 <= g.center_x % num2 <= 18:
                if _legacy_tile(g, (g.center_y + num3) // num1, g.center_x // num2) < 3 \
                        or (_legacy_tile(g, (g.center_y + num3) // num1, g.center_x // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[3] = True
                if _legacy_tile(g, (g.center_y - num3) // num1, g.center_x // num2) < 3 \
                        or (_legacy_tile(g, (g.center_y - num3) // num1, g.center_x // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[2] = True
            if 12 <= g.center_y % num1 <= 18:
                if _legacy_tile(g, g.center_y // num1, (g.center_x - num3) // num2) < 3 \
                        or (_legacy_tile(g, g.center_y // num1, (g.center_x - num3) // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[1] = True
                if _legacy_tile(g, g.center_y // num1, (g.center_x + num3) // num2) < 3 \
                        or (_legacy_tile(g, g.center_y // num1, (g.center_x + num3) // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[0] = True

        if g.direction == 0 or g.direction == 1:
            if 12 <= g.center_x % num2 <= 18:
                if _legacy_tile(g, (g.center_y + num3) // num1, g.center_x // num2) < 3 \
                        or (_legacy_tile(g, (g.center_y + num3) // num1, g.center_x // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[3] = True
                if _legacy_tile(g, (g.center_y - num3) // num1, g.center_x // num2) < 3 \
                        or (_legacy_tile(g, (g.center_y - num3) // num1, g.center_x // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[2] = True
            if 12 <= g.center_y % num1 <= 18:
                if _legacy_tile(g, g.center_y // num1, (g.center_x - num3) // num2) < 3 \
                        or (_legacy_tile(g, g.center_y // num1, (g.center_x - num3) // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[1] = True
                if _legacy_tile(g, g.center_y // num1, (g.center_x + num3) // num2) < 3 \
                        or (_legacy_tile(g, g.center_y // num1, (g.center_x + num3) // num2) == 9 and (
                        g.in_box or g.dead)):
                    turns[0] = True
    else:
        turns[0] = True
        turns[1] = True
    if 350 < g.x_pos < 550 and 360 < g.y_pos < 480:
        in_box = True
    else:
        in_box = False
    return turns, in_box
