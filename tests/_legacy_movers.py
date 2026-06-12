"""Frozen verbatim copies of the PRE-REF-02 ghost movers (one-shot oracle, D-06).

These are byte-for-byte transcriptions of ``ghost.py``'s ``move_blinky`` /
``move_inky`` / ``move_pinky`` / ``move_clyde`` as they existed BEFORE the
data-driven ``_move`` refactor, rewritten as standalone functions operating on a
passed ghost-like object ``g`` (each reads/writes ``g.x_pos`` / ``g.y_pos`` /
``g.direction`` / ``g.target`` / ``g.turns`` / ``g.speed`` exactly as the
methods did). They do NOT import ghost.py — they are the frozen "OLD" side of
the differential oracle in ``tests/test_mover_oracle.py``.

DELETED in Task 3 once all four ghosts prove byte-identical (D-06 one-shot
lifecycle). The proof is preserved in git history; the permanent guards are the
9 golden traces + 15 micro tests + the frame-hash manifest.

Direction key: 0=Right, 1=Left, 2=Up, 3=Down (CLAUDE.md).
"""


def legacy_move_clyde(g):
    # r, l, u, d
    # clyde is going to turn whenever advantageous for pursuit
    if g.direction == 0:
        if g.target[0] > g.x_pos and g.turns[0]:
            g.x_pos += g.speed
        elif not g.turns[0]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
        elif g.turns[0]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            if g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            else:
                g.x_pos += g.speed
    elif g.direction == 1:
        if g.target[1] > g.y_pos and g.turns[3]:
            g.direction = 3
        elif g.target[0] < g.x_pos and g.turns[1]:
            g.x_pos -= g.speed
        elif not g.turns[1]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[1]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            if g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            else:
                g.x_pos -= g.speed
    elif g.direction == 2:
        if g.target[0] < g.x_pos and g.turns[1]:
            g.direction = 1
            g.x_pos -= g.speed
        elif g.target[1] < g.y_pos and g.turns[2]:
            g.direction = 2
            g.y_pos -= g.speed
        elif not g.turns[2]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[2]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            else:
                g.y_pos -= g.speed
    elif g.direction == 3:
        if g.target[1] > g.y_pos and g.turns[3]:
            g.y_pos += g.speed
        elif not g.turns[3]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[3]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            else:
                g.y_pos += g.speed
    if g.x_pos < -30:
        g.x_pos = 900
    elif g.x_pos > 900:
        g.x_pos = -30
    return g.x_pos, g.y_pos, g.direction


def legacy_move_blinky(g):
    # r, l, u, d
    # blinky is going to turn whenever colliding with walls, otherwise continue straight
    if g.direction == 0:
        if g.target[0] > g.x_pos and g.turns[0]:
            g.x_pos += g.speed
        elif not g.turns[0]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
        elif g.turns[0]:
            g.x_pos += g.speed
    elif g.direction == 1:
        if g.target[0] < g.x_pos and g.turns[1]:
            g.x_pos -= g.speed
        elif not g.turns[1]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[1]:
            g.x_pos -= g.speed
    elif g.direction == 2:
        if g.target[1] < g.y_pos and g.turns[2]:
            g.direction = 2
            g.y_pos -= g.speed
        elif not g.turns[2]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
        elif g.turns[2]:
            g.y_pos -= g.speed
    elif g.direction == 3:
        if g.target[1] > g.y_pos and g.turns[3]:
            g.y_pos += g.speed
        elif not g.turns[3]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
        elif g.turns[3]:
            g.y_pos += g.speed
    if g.x_pos < -30:
        g.x_pos = 900
    elif g.x_pos > 900:
        g.x_pos = -30
    return g.x_pos, g.y_pos, g.direction


def legacy_move_inky(g):
    # r, l, u, d
    # inky turns up or down at any point to pursue, but left and right only on collision
    if g.direction == 0:
        if g.target[0] > g.x_pos and g.turns[0]:
            g.x_pos += g.speed
        elif not g.turns[0]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
        elif g.turns[0]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            if g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            else:
                g.x_pos += g.speed
    elif g.direction == 1:
        if g.target[1] > g.y_pos and g.turns[3]:
            g.direction = 3
        elif g.target[0] < g.x_pos and g.turns[1]:
            g.x_pos -= g.speed
        elif not g.turns[1]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[1]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            if g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            else:
                g.x_pos -= g.speed
    elif g.direction == 2:
        if g.target[1] < g.y_pos and g.turns[2]:
            g.direction = 2
            g.y_pos -= g.speed
        elif not g.turns[2]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[2]:
            g.y_pos -= g.speed
    elif g.direction == 3:
        if g.target[1] > g.y_pos and g.turns[3]:
            g.y_pos += g.speed
        elif not g.turns[3]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[3]:
            g.y_pos += g.speed
    if g.x_pos < -30:
        g.x_pos = 900
    elif g.x_pos > 900:
        g.x_pos = -30
    return g.x_pos, g.y_pos, g.direction


def legacy_move_pinky(g):
    # r, l, u, d
    # pinky is going to turn left or right whenever advantageous, but only up or down on collision
    if g.direction == 0:
        if g.target[0] > g.x_pos and g.turns[0]:
            g.x_pos += g.speed
        elif not g.turns[0]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
        elif g.turns[0]:
            g.x_pos += g.speed
    elif g.direction == 1:
        if g.target[1] > g.y_pos and g.turns[3]:
            g.direction = 3
            g.y_pos += g.speed
        elif g.target[0] < g.x_pos and g.turns[1]:
            g.x_pos -= g.speed
        elif not g.turns[1]:
            if g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[1]:
            g.x_pos -= g.speed
    elif g.direction == 2:
        if g.target[0] < g.x_pos and g.turns[1]:
            g.direction = 1
            g.x_pos -= g.speed
        elif g.target[1] < g.y_pos and g.turns[2]:
            g.direction = 2
            g.y_pos -= g.speed
        elif not g.turns[2]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] > g.y_pos and g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[3]:
                g.direction = 3
                g.y_pos += g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[2]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            else:
                g.y_pos -= g.speed
    elif g.direction == 3:
        if g.target[1] > g.y_pos and g.turns[3]:
            g.y_pos += g.speed
        elif not g.turns[3]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.target[1] < g.y_pos and g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[2]:
                g.direction = 2
                g.y_pos -= g.speed
            elif g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            elif g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
        elif g.turns[3]:
            if g.target[0] > g.x_pos and g.turns[0]:
                g.direction = 0
                g.x_pos += g.speed
            elif g.target[0] < g.x_pos and g.turns[1]:
                g.direction = 1
                g.x_pos -= g.speed
            else:
                g.y_pos += g.speed
    if g.x_pos < -30:
        g.x_pos = 900
    elif g.x_pos > 900:
        g.x_pos = -30
    return g.x_pos, g.y_pos, g.direction
