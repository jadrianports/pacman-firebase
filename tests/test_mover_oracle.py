"""Synthetic-exhaustive differential oracle for the unified ghost mover (D-04/D-05).

Proves the new data-driven ``Ghost._move`` (via the thin ``move_blinky/inky/
pinky/clyde`` wrappers) is BYTE-IDENTICAL to the frozen pre-refactor movers
(``tests/_legacy_movers.py``) across the WHOLE decision space, per ghost:

    direction(4) × all 16 turns[] combos × target-sign-per-axis(3×3)
    × in_box(2) × dead(2) × speed{1,2,4} × 5 wrap-x representatives
    = 4 × 16 × 9 × 2 × 2 × 3 × 5 = 34,560 cases / ghost.

`check_collisions` is bypassed: each case constructs a ghost via ``make_ghost``
then CLOBBERS ``g.turns`` / ``g.in_box`` AFTER construction to control the
mover's full input space directly (RESEARCH FOCUS-3). Two independent ghosts
are built per case (one for legacy, one for the new path) so neither side's
self-mutation leaks. ``itertools.product`` loops with a first-divergence
accumulator (NOT ``pytest.mark.parametrize`` — 138k IDs would bloat collection).

One-shot: DELETED in Task 3 once all four ghosts prove green (D-06). The
permanent guards going forward are the 9 golden traces + 15 micro tests +
the frame-hash manifest.
"""
import itertools

import pytest

from tests.test_ghost_micro import make_ghost, screen  # noqa: F401  (reuse fixture + harness)
from tests import _legacy_movers


# All 16 [R, L, U, D] boolean combinations.
TURNS_COMBOS = list(itertools.product((False, True), repeat=4))
# Target sign per axis realised as an offset relative to the case position.
SIGNS = (-100, 0, 100)
# Wrap-x representatives: just past left wrap, boundary, interior, boundary, past right.
WRAP_XS = (-31, -30, 450, 900, 901)
SPEEDS = (1, 2, 4)
BASE_Y = 460

# ghost name -> (legacy fn, new-mover method name, ghost_id)
GHOSTS = {
    "blinky": (_legacy_movers.legacy_move_blinky, "move_blinky", 0),
    "inky": (_legacy_movers.legacy_move_inky, "move_inky", 1),
    "pinky": (_legacy_movers.legacy_move_pinky, "move_pinky", 2),
    "clyde": (_legacy_movers.legacy_move_clyde, "move_clyde", 3),
}


def _run_ghost(screen, name):
    legacy_fn, method_name, gid = GHOSTS[name]
    failures = []
    for d, turns, dx, dy, box, dead, spd, x in itertools.product(
        range(4), TURNS_COMBOS, SIGNS, SIGNS,
        (False, True), (False, True), SPEEDS, WRAP_XS,
    ):
        y = BASE_Y
        tx, ty = x + dx, y + dy

        # OLD side: a frozen-mover run on an independent ghost.
        old_g = make_ghost(screen, x, y, target=(tx, ty), speed=spd,
                            direction=d, ghost_id=gid, dead=dead, box=box)
        old_g.turns = list(turns)
        old_g.in_box = box
        old_g.x_pos, old_g.y_pos = x, y
        old = legacy_fn(old_g)

        # NEW side: the unified _move via the public wrapper, on its own ghost.
        new_g = make_ghost(screen, x, y, target=(tx, ty), speed=spd,
                           direction=d, ghost_id=gid, dead=dead, box=box)
        new_g.turns = list(turns)
        new_g.in_box = box
        new_g.x_pos, new_g.y_pos = x, y
        new = getattr(new_g, method_name)()

        if old != new:
            failures.append((d, turns, (dx, dy), box, dead, spd, x, old, new))
            if len(failures) >= 5:
                break
    return failures


def _format(name, failures):
    head = f"{name}: {len(failures)} divergence(s) unified != legacy. First few:\n"
    body = "\n".join(
        f"  dir={d} turns={turns} tsign={tsign} box={box} dead={dead} "
        f"speed={spd} x={x}: legacy={old} new={new}"
        for (d, turns, tsign, box, dead, spd, x, old, new) in failures
    )
    return head + body


def test_unified_mover_matches_legacy_blinky(screen):
    failures = _run_ghost(screen, "blinky")
    assert not failures, _format("blinky", failures)


def test_unified_mover_matches_legacy_inky(screen):
    failures = _run_ghost(screen, "inky")
    assert not failures, _format("inky", failures)


def test_unified_mover_matches_legacy_pinky(screen):
    failures = _run_ghost(screen, "pinky")
    assert not failures, _format("pinky", failures)


def test_unified_mover_matches_legacy_clyde(screen):
    failures = _run_ghost(screen, "clyde")
    assert not failures, _format("clyde", failures)
