# gamestate.py
from settings import *
class GameState:
    def __init__(self):
        self.reset_full()

    def reset_full(self):
        """Full game restart (new game)."""
        self.lives = 3
        self.score = 0
        self.powerup = False
        self.power_counter = 0
        self.eaten_ghost = [False, False, False, False]
        self.game_over = False
        self.game_won = False
        self.startup_counter = 0
        self.moving = False

    def reset_round(self, player, ghosts):
        """
        Called when Pac-Man dies but game continues.
        Resets player and ghosts to spawn positions, clears powerup and eaten flags,
        preserves score and decremented life should be handled by caller (or use handle_player_death).
        """
        self.powerup = False
        self.power_counter = 0
        self.eaten_ghost = [False, False, False, False]
        self.startup_counter = 0
        self.moving = False

        # Reset player
        player.x = 450
        player.y = 663
        player.direction = 0
        player.direction_command = 0

        # Reset ghosts
        for ghost in ghosts:
            ghost.reset_to_spawn()

    def handle_player_death(self, player, ghosts):
        """
        Reduce life, then either reset round or mark game over.
        Returns True if game continues, False if game over.
        """
        if self.lives > 0:
            self.lives -= 1
            self.reset_round(player, ghosts)
            return True
        else:
            self.game_over = True
            self.moving = False
            self.startup_counter = 0
            return False

    def update_ghost_speeds(self, ghosts):
        """
        Apply the same speed-setting rules you had in main.py based on powerup/eaten/dead.
        Keeps behaviour centralized.
        """
        # default normal speed
        for ghost in ghosts:
            ghost.speed = GHOST_SPEED

        if self.powerup:
            for g in ghosts:
                g.speed = 1

        # if eaten, speed = 2
        for i, g in enumerate(ghosts):
            if self.eaten_ghost[i]:
                g.speed = 2

        # if dead, speed = 4
        for g in ghosts:
            if g.dead:
                g.speed = 4
