"""FEEL-03 eat-ghost-sound tests (RED until 09-04).

Targets the EXACT API 09-04 will build on ``SoundManager``:
  * ``play_eat_ghost()`` — plays the bite cue on a DEDICATED channel (Channel 2),
    distinct from waka (ch 0) and powerup (ch 1); no-raise headless.
  * the eat branch in ``Game.check_ghost_collisions`` calls it once per bite.

Headless harness mirrors ``tests/test_juice_firewall.py``. A ghost is placed
directly on the player (centers coincident) so the powerup eat branch fires. RED
now: ``play_eat_ghost`` does not exist (AttributeError), and the eat branch does
not yet call it (spy never fires).
"""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from harness.headless import init_headless
pygame, _screen, _clock = init_headless()
from game import Game
from harness.replay import install_frame_driven_sound


def _new_game():
    surface = pygame.Surface(_screen.get_size())
    g = Game(surface, _clock)
    install_frame_driven_sound(g)
    return g


def _put_ghost_on_player(g):
    """Place blinky so its center coincides with the player_circle center, so
    _catches() reads True this frame. ghost.center_x == x_pos+22; player_circle
    center == player.center_x == player.x+23 (and +24 in y)."""
    g.blinky_x = g.player.x + 1
    g.blinky_y = g.player.y + 2


def test_play_eat_ghost_exists_on_dedicated_channel_no_raise():
    """play_eat_ghost() exists, runs headless without raising, and owns a dedicated
    channel separate from waka/powerup. RED now: AttributeError (method absent)."""
    g = _new_game()
    g.sound.play_eat_ghost()                 # AttributeError until 09-04 (RED)
    assert g.sound._eat_channel is not None   # dedicated Channel(2)


def test_eat_branch_calls_play_eat_ghost():
    """When the powerup eat branch fires, it calls sound.play_eat_ghost() exactly
    once. RED now: the branch does not call it yet, so the spy never fires."""
    g = _new_game()
    calls = []
    # Spy the (future) method. Assigning the attribute always works; the assertion
    # below proves 09-04 wired the call site, not that the symbol exists.
    g.sound.play_eat_ghost = lambda *a, **k: calls.append(1)

    g.powerup = True
    _put_ghost_on_player(g)
    g.create_ghosts()
    player_circle = g.player.draw(g.counter)
    g.check_ghost_collisions(player_circle)

    # Sanity: the eat branch actually fired (eat_freeze was set by the bite).
    assert g.eat_freeze is True
    assert calls, "eat branch must call sound.play_eat_ghost() on a bite"
