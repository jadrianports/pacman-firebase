## pacman.py
import pygame
from settings import *


class Pacman:
    def __init__(self):
        # position
        self.start_position = (430, 663)  # x, y
        self.x , self.y = self.start_position

        # directions: 0=right,1=left,2=up,3=down
        self.direction = 0
        self.direction_command = 0

        self.speed = PLAYER_SPEED
        self.lives = 3
        self.score = 0

        # animation frames
        self.images = []
        self.load_images()
        self.animation_counter = 0

        # allowed turns: [R, L, U, D]
        self.turns_allowed = [False, False, False, False]

        #player circle
        #self.circle = pygame.draw.circle()

    def load_images(self):
        # load your pacman frames (1..4)
        for i in range(1, 5):
            img = pygame.image.load(f'assets/pacman/{i}.png')
            scaled = pygame.transform.scale(img, (45, 45))
            self.images.append(scaled)

    def draw(self, screen):
        # ensure we don't index out-of-range if animation_counter is small/large
        idx = min(len(self.images) - 1, self.animation_counter // 5)
        img = self.images[idx]

        if self.direction == 0:
            screen.blit(img, (self.x, self.y))
        elif self.direction == 1:
            screen.blit(pygame.transform.flip(img, True, False), (self.x, self.y))
        elif self.direction == 2:
            screen.blit(pygame.transform.rotate(img, 90), (self.x, self.y))
        elif self.direction == 3:
            screen.blit(pygame.transform.rotate(img, 270), (self.x, self.y))

    def get_center(self):
        return self.x + 23, self.y + 24

    def set_turns_allowed(self, turns):
        self.turns_allowed = turns

    def update_direction(self):
        """Apply direction_command only when allowed."""
        for i in range(4):
            if self.direction_command == i and self.turns_allowed[i]:
                self.direction = i

    def move(self):
        """Move according to current direction and allowed turns."""
        if self.direction == 0 and self.turns_allowed[0]:
            self.x += self.speed
        elif self.direction == 1 and self.turns_allowed[1]:
            self.x -= self.speed

        if self.direction == 2 and self.turns_allowed[2]:
            self.y -= self.speed
        elif self.direction == 3 and self.turns_allowed[3]:
            self.y += self.speed

    def check_collisions(self, level_map, power, power_count, eaten_ghosts):
        """
        Exact O.G. Pacman logic preserved.
        Moved from main.py → Pacman class.
        Uses self.x, self.y, self.score, and self.get_center().
        """

        center_x, center_y = self.get_center()

        if 0 < self.x < 870:
            tile = level_map[center_y // TILE_HEIGHT][center_x // TILE_WIDTH]

            if tile == 1:
                level_map[center_y // TILE_HEIGHT][center_x // TILE_WIDTH] = 0
                self.score += 10

            elif tile == 2:
                level_map[center_y // TILE_HEIGHT][center_x // TILE_WIDTH] = 0
                self.score += 50
                power = True
                power_count = 0
                eaten_ghosts = [False, False, False, False]

        return self.score, power, power_count, eaten_ghosts

    def compute_turns(self, level_map):
        """
        Exact same logic as your global check_position() in main.py.
        Uses Pacman's own x, y, and direction.
        Returns: [R_allowed, L_allowed, U_allowed, D_allowed]
        """
        centerx, centery = self.get_center()
        direction = self.direction

        turns = [False, False, False, False]

        if centerx // 30 < 29:
            if direction == 0:
                if level_map[centery // TILE_HEIGHT][(centerx - FUDGE_FACTOR) // TILE_WIDTH] < 3:
                    turns[1] = True
            if direction == 1:
                if level_map[centery // TILE_HEIGHT][(centerx + FUDGE_FACTOR) // TILE_WIDTH] < 3:
                    turns[0] = True
            if direction == 2:
                if level_map[(centery + FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[3] = True
            if direction == 3:
                if level_map[(centery - FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[2] = True

            if direction in (2, 3):
                if 12 <= centerx % TILE_WIDTH <= 18:
                    if level_map[(centery + FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[3] = True
                    if level_map[(centery - FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[2] = True
                if 12 <= centery % TILE_HEIGHT <= 18:
                    if level_map[centery // TILE_HEIGHT][(centerx - TILE_WIDTH) // TILE_WIDTH] < 3:
                        turns[1] = True
                    if level_map[centery // TILE_HEIGHT][(centerx + TILE_WIDTH) // TILE_WIDTH] < 3:
                        turns[0] = True

            if direction in (0, 1):
                if 12 <= centerx % TILE_WIDTH <= 18:
                    if level_map[(centery + TILE_HEIGHT) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[3] = True
                    if level_map[(centery - TILE_HEIGHT) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[2] = True
                if 12 <= centery % TILE_HEIGHT <= 18:
                    if level_map[centery // TILE_HEIGHT][(centerx - FUDGE_FACTOR) // TILE_WIDTH] < 3:
                        turns[1] = True
                    if level_map[centery // TILE_HEIGHT][(centerx + FUDGE_FACTOR) // TILE_WIDTH] < 3:
                        turns[0] = True
        else:
            turns[0] = True
            turns[1] = True

        return turns



    def handle_wraparound(self):
        """Teleport across left/right edges (keeps original numbers)."""
        if self.x > 900:
            self.x = -47
        elif self.x < -50:
            self.x = 897

    # optional helper to sync animation counter from main loop
    def set_animation_counter(self, counter):
        self.animation_counter = counter

    def reset(self, reset_score=False):
        """Reset Pacman to starting position and optionally reset score."""
        self.x, self.y = self.start_position
        if reset_score:
            self.score = 0


