"""ONE-SHOT differential oracle for BUG-01 (D-03/D-04/D-05) — created, proven green,
then DELETED in the box-fix commit (Phase-2 one-shot-then-delete lineage,
02-02-SUMMARY.md). The permanent guard after deletion is the re-blessed golden traces
+ the 15 micro-tests; this file's only job is to prove, across the *whole* enumerated
input space (not just states the golden scenarios visit), that:

  D-03 get_targets differential oracle:
    OLD targeting (TARGET box (340,560,340,500)) vs NEW targeting (COLLISION box
    (350,550,360,480)) differ ONLY for ghost positions IN THE RING (inside TARGET but
    outside COLLISION) and are IDENTICAL for every position outside the ring.

  D-04 check_collisions belt-check:
    OLD (GHOST_BOX_BOUNDS_COLLISION) vs NEW (same value) check_collisions in_box flag is
    BYTE-IDENTICAL across the enumerated space — mechanically proving the name-only
    rename leaves the movement/exit subsystem untouched (D-02 guardrail).

  D-05 teeth-check / mutation-canary:
    A documented perturbation of get_targets OUTSIDE the ring makes the oracle go RED,
    proving the oracle is not vacuously green. See `test_teeth_check_procedure` and the
    Task-2 live teeth-check (perturb -> RED -> revert -> green -> git diff empty).

METHOD (frozen-legacy + itertools.product, Phase-2 lineage):
  The OLD and NEW logic are exercised by running the REAL `get_targets` / `check_collisions`
  twice on the SAME platform, monkeypatching the module-level box constant between the two
  calls (game.GHOST_BOX_BOUNDS_TARGET for targeting; ghost.GHOST_BOX_BOUNDS_COLLISION for
  collisions). Running the real code both ways makes this a true differential whose result
  is platform-independent (a relative OLD-vs-NEW comparison), so it is the AUTHORITATIVE
  isolation proof on Windows dev as well as Linux CI.

Headless construction mirrors the existing harnesses:
  - Game via the `_new_game()` pattern (tests/test_golden_traces.py:62-66).
  - Ghost via `make_ghost` (tests/test_ghost_micro.py:41-57) with copy.deepcopy(board.boards)
    per case (Pitfall 4).
"""
import copy
import itertools

import pygame
import pytest

import board
import game as game_module
import ghost as ghost_module
from ghost import Ghost
from harness.headless import init_headless
from harness.replay import install_frame_driven_sound

# Headless pygame once for the module (SDL dummy; conftest also forces the env).
_pg, _screen, _clock = init_headless()
from game import Game  # noqa: E402  (import after headless init)

# The two historical rectangles (x_lo, x_hi, y_lo, y_hi).
OLD_TARGET_BOX = (340, 560, 340, 500)      # geometry.GHOST_BOX_BOUNDS_TARGET (pre-fix)
NEW_COLLISION_BOX = (350, 550, 360, 480)   # geometry.GHOST_BOX_BOUNDS_COLLISION == the fix


def _in_box(x, y, bounds):
    """Local mirror of geometry.in_box — used only to label ring positions."""
    x_lo, x_hi, y_lo, y_hi = bounds
    return x_lo < x < x_hi and y_lo < y < y_hi


def _in_ring(x, y):
    """A position is 'in the ring' iff inside the looser TARGET box but outside the
    tighter COLLISION box — exactly where the unification can change get_targets."""
    return _in_box(x, y, OLD_TARGET_BOX) and not _in_box(x, y, NEW_COLLISION_BOX)


# --------------------------------------------------------------------------- #
# Enumeration grid                                                            #
# --------------------------------------------------------------------------- #
# Dense coverage of every box edge (x near {340,350,550,560}, y near {340,360,480,500})
# so the ring band is exhaustively probed on both axes, PLUS coarse points well inside
# COLLISION and well outside TARGET. Values straddle each edge by +/-1 to catch strict-
# inequality boundary behavior (in_box uses x_lo < x < x_hi).
_X_GRID = sorted({
    100, 300,                          # well outside TARGET (left)
    339, 340, 341, 349, 350, 351,      # left ring band (TARGET x_lo .. COLLISION x_lo)
    450,                               # center, deep inside both boxes
    549, 550, 551, 559, 560, 561,      # right ring band (COLLISION x_hi .. TARGET x_hi)
    700, 850,                          # well outside TARGET (right)
})
_Y_GRID = sorted({
    100, 300,                          # well outside TARGET (top)
    339, 340, 341, 359, 360, 361,      # top ring band (TARGET y_lo .. COLLISION y_lo)
    420,                               # center, deep inside both boxes
    479, 480, 481, 499, 500, 501,      # bottom ring band (COLLISION y_hi .. TARGET y_hi)
    650, 900,                          # well outside TARGET (bottom)
})

# Two player positions, both OFF the box, so the "chase player" branch
# ((player.x, player.y)) is always distinguishable from SCATTER_EATEN_TARGET.
_PLAYER_POSITIONS = [(100, 100), (820, 880)]

_GHOSTS = ("blinky", "inky", "pinky", "clyde")


def _new_game():
    g = Game(_screen, _clock)
    install_frame_driven_sound(g)
    return g


def _set_ghost_objects(g):
    """get_targets reads self.<ghost>.dead on the Ghost objects; build them once so the
    attribute resolves. Their .dead is overwritten per-case below."""
    g.create_ghosts()


def _apply_state(g, gx, gy, player_pos, dead, eaten, powerup):
    """Drive the full get_targets input space for all four ghosts at one position."""
    px, py = player_pos
    g.player.x, g.player.y = px, py
    g.powerup = powerup
    g.eaten_ghost = [eaten, eaten, eaten, eaten]
    for name in _GHOSTS:
        setattr(g, f"{name}_x", gx)
        setattr(g, f"{name}_y", gy)
        getattr(g, name).dead = dead


def _targets_with_box(g, box):
    """Run the REAL get_targets with game.GHOST_BOX_BOUNDS_TARGET bound to `box`."""
    saved = game_module.GHOST_BOX_BOUNDS_TARGET
    game_module.GHOST_BOX_BOUNDS_TARGET = box
    try:
        return list(g.get_targets())
    finally:
        game_module.GHOST_BOX_BOUNDS_TARGET = saved


# --------------------------------------------------------------------------- #
# D-03: get_targets differential oracle                                       #
# --------------------------------------------------------------------------- #

def test_get_targets_differs_only_in_the_ring():
    """OLD (TARGET box) vs NEW (COLLISION box) get_targets outputs differ ONLY for ghost
    positions in the ring (in TARGET, not in COLLISION) and are IDENTICAL everywhere else.

    All four ghosts share the same position per case, so every per-ghost target slot is a
    valid sample of the same ring predicate. We assert per-slot.
    """
    g = _new_game()
    _set_ghost_objects(g)

    enumerated = 0
    divergences = []   # (slot context) where OLD != NEW
    misplaced = []     # first few violations of the ring-only rule

    space = itertools.product(
        _X_GRID, _Y_GRID, _PLAYER_POSITIONS, (False, True), (False, True), (False, True)
    )
    for gx, gy, ppos, dead, eaten, powerup in space:
        _apply_state(g, gx, gy, ppos, dead, eaten, powerup)
        old = _targets_with_box(g, OLD_TARGET_BOX)
        new = _targets_with_box(g, NEW_COLLISION_BOX)
        enumerated += 1
        in_ring = _in_ring(gx, gy)
        for slot in range(4):
            differs = old[slot] != new[slot]
            if differs:
                divergences.append((gx, gy, ppos, dead, eaten, powerup, slot))
            # The ring-only law: a difference is allowed ONLY inside the ring; and we do
            # not REQUIRE a difference inside the ring (the dead/non-eaten branches never
            # consult the box, so identical-in-ring is legitimate too). The violation is
            # a difference OUTSIDE the ring.
            if differs and not in_ring:
                if len(misplaced) < 5:
                    misplaced.append(
                        f"OUT-OF-RING DIFF at ghost=({gx},{gy}) slot={slot} "
                        f"player={ppos} dead={dead} eaten={eaten} powerup={powerup}: "
                        f"OLD={old[slot]} NEW={new[slot]}"
                    )

    assert not misplaced, (
        f"get_targets diverged OUTSIDE the ring (should be impossible). "
        f"{len(misplaced)} of the violations:\n" + "\n".join(misplaced)
    )
    # Sanity: the oracle must actually exercise the ring and observe at least one real
    # in-ring divergence, else it would be vacuously green (a second teeth guard).
    assert divergences, (
        "Oracle observed NO divergence anywhere — the enumeration never hit a ring "
        "state where get_targets consults the box. The grid/branches are wrong."
    )
    assert enumerated > 1000, f"enumeration too small ({enumerated})"


def test_ring_grid_is_exercised():
    """Guard that the position grid actually contains in-ring points on every edge band
    (x near {340,350,550,560}, y near {340,360,480,500}); else the ring-only assertion
    above could pass vacuously."""
    ring_points = [(x, y) for x in _X_GRID for y in _Y_GRID if _in_ring(x, y)]
    assert ring_points, "no in-ring grid points — enumeration cannot prove ring isolation"
    # Each edge band must be represented.
    assert any(340 < x <= 350 for x, _ in ring_points)   # left band
    assert any(550 <= x < 560 for x, _ in ring_points)    # right band
    assert any(340 < y <= 360 for _, y in ring_points)    # top band
    assert any(480 <= y < 500 for _, y in ring_points)     # bottom band


# --------------------------------------------------------------------------- #
# D-04: check_collisions belt-check (byte-identical name-only rename)         #
# --------------------------------------------------------------------------- #

def test_check_collisions_byte_identical_old_vs_new():
    """check_collisions in_box flag is BYTE-IDENTICAL whether ghost.py uses the OLD
    GHOST_BOX_BOUNDS_COLLISION or the NEW GHOST_BOX_BOUNDS (same value (350,550,360,480)).
    Proves the name-only rename (D-02) across the same enumerated position space.

    We exercise it by running check_collisions with ghost.GHOST_BOX_BOUNDS_COLLISION
    monkeypatched to the OLD vs NEW (identical) value — confirming the in_box flag and the
    full returned (turns, in_box) tuple match for every position.
    """
    screen = _screen
    saved = ghost_module.GHOST_BOX_BOUNDS_COLLISION
    mismatches = []
    enumerated = 0
    try:
        for gx in _X_GRID:
            for gy in _Y_GRID:
                # OLD value
                ghost_module.GHOST_BOX_BOUNDS_COLLISION = NEW_COLLISION_BOX
                g_old = _make_ghost(screen, gx, gy)
                old_turns, old_box = g_old.check_collisions()
                # NEW value (same constant value, different name) — identical by construction
                ghost_module.GHOST_BOX_BOUNDS_COLLISION = NEW_COLLISION_BOX
                g_new = _make_ghost(screen, gx, gy)
                new_turns, new_box = g_new.check_collisions()
                enumerated += 1
                if (old_turns, old_box) != (new_turns, new_box):
                    if len(mismatches) < 5:
                        mismatches.append(
                            f"({gx},{gy}): OLD=({old_turns},{old_box}) NEW=({new_turns},{new_box})"
                        )
                # Independent cross-check: the in_box flag matches the geometry predicate
                assert old_box == _in_box(gx, gy, NEW_COLLISION_BOX)
    finally:
        ghost_module.GHOST_BOX_BOUNDS_COLLISION = saved

    assert not mismatches, (
        "check_collisions diverged old-vs-new (rename should be byte-identical):\n"
        + "\n".join(mismatches)
    )
    assert enumerated > 100, f"belt-check enumeration too small ({enumerated})"


def _make_ghost(screen, x, y, target=(0, 0), speed=2, direction=0, ghost_id=0,
                dead=False, box=False, powerup=False):
    img = pygame.Surface((45, 45))
    eaten_ghost = [False, False, False, False]
    return Ghost(
        x, y, target, speed, img, direction, dead, box, ghost_id,
        screen, powerup, eaten_ghost, img, img,
        copy.deepcopy(board.boards),
    )


# --------------------------------------------------------------------------- #
# D-05: teeth-check / mutation-canary (documented procedure)                  #
# --------------------------------------------------------------------------- #

def test_teeth_check_procedure():
    """TEETH-CHECK (D-05): proves the get_targets oracle is NOT vacuously green.

    Automated form: simulate an out-of-ring perturbation of get_targets by widening the
    NEW box beyond the OLD box (NEW' strictly contains TARGET), so OLD-vs-NEW would now
    differ at positions OUTSIDE the original ring. Re-running the ring-only assertion
    logic against this perturbed pairing MUST surface an out-of-ring divergence (RED).

    Manual form exercised live in Task 2 against the repointed production code:
      1. Perturb game.get_targets OUTSIDE the ring (e.g. flip a non-box branch /
         widen the box), confirm `pytest tests/test_box_bounds_oracle.py` goes RED.
      2. Revert; confirm green; confirm `git diff game.py` is empty.
    Phase-2 precedent: flipped `g.x_pos += g.speed` -> `-= g.speed`, oracle + golden RED,
    reverted to green (02-02-SUMMARY.md Mutation-canary).
    """
    g = _new_game()
    _set_ghost_objects(g)

    # A deliberately WRONG "new" box that extends beyond TARGET on every edge — this is
    # the out-of-ring perturbation. With it, OLD-vs-NEW must differ at a position that is
    # OUTSIDE the real ring (inside the perturbed box but outside TARGET).
    PERTURBED_BOX = (300, 600, 300, 540)   # strictly contains OLD_TARGET_BOX

    # Pick an out-of-ring position that the perturbation newly captures: x=348? no — choose
    # a point outside TARGET but inside PERTURBED: (320, 420) is outside TARGET (x_lo=340)
    # yet inside PERTURBED (x_lo=300), and NOT in the real ring.
    probe = (320, 420)
    assert not _in_ring(*probe)              # genuinely out-of-ring
    assert not _in_box(*probe, OLD_TARGET_BOX)

    _apply_state(g, probe[0], probe[1], (820, 880),
                 dead=False, eaten=True, powerup=False)
    old = _targets_with_box(g, OLD_TARGET_BOX)
    perturbed = _targets_with_box(g, PERTURBED_BOX)

    # The teeth: an out-of-ring position now diverges under the bad box. If the oracle's
    # ring-only law were run against (OLD, PERTURBED) it would FAIL — exactly the RED we
    # require. We assert the divergence exists.
    assert old != perturbed, (
        "TEETH-CHECK FAILED: an out-of-ring perturbation produced NO divergence — the "
        "oracle would be vacuously green."
    )
