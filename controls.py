# controls.py
import pygame

class ControlManager:
    """
    Handles keyboard input for Pacman.
    Supports both Arrow Keys and WASD.
    Easily extendable to other keys later.
    """

    def __init__(self):
        # Define movement bindings: multiple keys can map to the same direction.
        self.bindings = {
            pygame.K_RIGHT: 0,
            pygame.K_d: 0,

            pygame.K_LEFT: 1,
            pygame.K_a: 1,

            pygame.K_UP: 2,
            pygame.K_w: 2,

            pygame.K_DOWN: 3,
            pygame.K_s: 3,
        }

    def handle_event(self, event, player):
        """
        Processes events and updates the player's direction_command.
        """

        # -----------------------------
        # KEY DOWN
        # -----------------------------
        if event.type == pygame.KEYDOWN:
            if event.key in self.bindings:
                player.direction_command = self.bindings[event.key]


        # -----------------------------
        # KEY UP
        # -----------------------------
        elif event.type == pygame.KEYUP:
            if event.key in self.bindings:
                released_dir = self.bindings[event.key]

                # If releasing the same direction key, fall back to current direction
                if player.direction_command == released_dir:
                    player.direction_command = player.direction

