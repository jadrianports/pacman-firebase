"""FEEL-01 wedge death-animation tests (RED until 09-02).

These target the EXACT symbols 09-02 will build:
  * ``Game.death_anim_frame`` — a per-death animation cursor that advances while
    ``dying and juice``.
  * ``Game._draw_death`` — the juice-gated wedge renderer; calling it headless must
    not raise (``player_circle`` is never dereferenced — RESEARCH Pitfall 4).

They use the same headless harness as ``tests/test_juice_firewall.py`` (SDL dummy
drivers, off-screen Surface per game, frame-driven sound shim) so nothing opens a
window. ``test_dying_juice_frame_ok`` fails RED now with an ``AttributeError`` on
``death_anim_frame`` — proving it targets the not-yet-built API rather than a
collection error.
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import hashlib

from harness.headless import init_headless
pygame, _screen, _clock = init_headless()
from game import Game
from harness.replay import install_frame_driven_sound


def _frame_hash(surface):
    return hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()


def _new_game():
    surface = pygame.Surface(_screen.get_size())
    g = Game(surface, _clock)
    install_frame_driven_sound(g)
    return g


def test_dying_juice_frame_ok():
    """A dying frame under juice=True advances the wedge cursor and renders without
    raising (FEEL-01b). RED now: ``death_anim_frame`` does not exist yet."""
    g = _new_game()
    g.juice = True
    g.start_dying()           # dying=True, death sound playing (frame-driven shim)
    # One frame of the juice death animation must not raise headless...
    g.tick()
    # ...and must advance the death-animation cursor 09-02 adds (AttributeError now).
    assert g.death_anim_frame > 0
    # The wedge renderer must be directly callable headless without raising
    # (player_circle never dereferenced — Pitfall 4). AttributeError now.
    g._draw_death()


def test_dying_frames_identical_under_juice_false():
    """Firewall guard: two fresh juice=False games in the dying phase render
    byte-identical frames — the FEEL-01 wedge must stay gated so juice=False
    golden replays never see it. GREEN now and after 09-02."""
    g1 = _new_game()
    g2 = _new_game()
    g1.start_dying()
    g2.start_dying()
    for _ in range(10):
        g1.tick()
        g2.tick()
    assert _frame_hash(g1.screen) == _frame_hash(g2.screen)
