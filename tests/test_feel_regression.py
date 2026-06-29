"""FEEL-02 + FEEL-05 characterization guards (GREEN — already shipped).

These PIN the current shipped behavior so the new juice work in 09-02/03/04 cannot
silently regress it. They are CHARACTERIZATION tests: every literal below is what the
UNMODIFIED game.py produces today. game.py is NOT modified by this plan.

  * FEEL-02 — eat-freeze popup: biting a ghost during powerup sets eat_freeze=True,
    eat_freeze_timer=45, eat_freeze_score in {200,400,800,1600}; the timer ticks down
    and clears (game.py:464-476, 541-545).
  * FEEL-05 — the "READY!" beat: the starting phase renders a yellow READY! near
    (WIDTH//2, 540) under juice=False (game.py:198-202).

Headless harness mirrors tests/test_juice_firewall.py. Dual-edition-safe primitives
only (screen.get_at) — no gaussian_blur (Pitfall 5).
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from harness.headless import init_headless
pygame, _screen, _clock = init_headless()
from game import Game
from harness.replay import install_frame_driven_sound
from settings import WIDTH


def _new_game():
    surface = pygame.Surface(_screen.get_size())
    g = Game(surface, _clock)
    install_frame_driven_sound(g)
    return g


def _put_ghost_on_player(g):
    """Place blinky so its center coincides with the player_circle center so the
    eat branch fires (ghost.center_x == x_pos+22; player_circle center == x+23/y+24)."""
    g.blinky_x = g.player.x + 1
    g.blinky_y = g.player.y + 2


# --------------------------------------------------------------------------- #
# FEEL-02 — eat-freeze popup (already shipped)                                 #
# --------------------------------------------------------------------------- #

def test_feel02_eat_freeze_set_on_bite():
    """Biting a ghost during powerup arms the 45-frame eat-freeze with a doubling
    score, then the freeze ticks down to 0 and clears (game.py:464-476, 541-545)."""
    g = _new_game()
    g.powerup = True
    _put_ghost_on_player(g)
    g.create_ghosts()
    player_circle = g.player.draw(g.counter)
    g.check_ghost_collisions(player_circle)

    assert g.eat_freeze is True
    assert g.eat_freeze_timer == 45
    assert g.eat_freeze_score in {200, 400, 800, 1600}

    # The freeze ticks down one frame at a time (game.py:541-545)...
    g.tick()
    assert g.eat_freeze_timer == 44
    # ...and clears within its 45-frame budget.
    for _ in range(60):
        if not g.eat_freeze:
            break
        g.tick()
    assert g.eat_freeze is False


# --------------------------------------------------------------------------- #
# FEEL-05 — the "READY!" beat (already shipped)                                #
# --------------------------------------------------------------------------- #

def _has_yellow_pixel(surface, cx, cy, half_w=70, y_lo=525, y_hi=556):
    """True if a yellow-ish ('READY!') pixel exists in the band around (cx, cy)."""
    for y in range(y_lo, y_hi):
        for x in range(cx - half_w, cx + half_w):
            r, g, b, _a = surface.get_at((x, y))
            if r > 200 and g > 200 and b < 90:
                return True
    return False


def test_feel05_ready_beat_renders_while_starting_juice_false():
    """A fresh juice=False game is in the starting phase and renders the yellow
    READY! beat near (WIDTH//2, 540) (game.py:198-202)."""
    g = _new_game()
    assert g.juice is False
    assert g.starting is True
    g.tick()                       # one frame: draw_ready blits READY! while starting
    assert g.starting is True      # start sound still 'playing' (frame-driven shim)
    assert _has_yellow_pixel(g.screen, WIDTH // 2, 540), \
        "READY! beat must render in yellow while starting"
