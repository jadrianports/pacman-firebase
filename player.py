import pygame
from paths import resource_path
from settings import (
    PLAYER_SPEED, PLAYER_START_X, PLAYER_START_Y, PLAYER_START_DIR,
    TILE_HEIGHT, TILE_WIDTH, HALF_TILE, BOARD_COLS,
    PLAYER_WRAP_RIGHT_EDGE, PLAYER_WRAP_RIGHT_TO, PLAYER_WRAP_LEFT_EDGE, PLAYER_WRAP_LEFT_TO,
    PLAYER_TURN_WINDOW_MARGIN,
)


class Player:
    def __init__(self, screen):
        self.screen = screen
        self.x = PLAYER_START_X
        self.y = PLAYER_START_Y
        self.direction = PLAYER_START_DIR
        self.direction_command = PLAYER_START_DIR
        self.speed = PLAYER_SPEED
        self.turns_allowed = [False, False, False, False]
        self.images = []
        for i in range(1, 5):
            self.images.append(pygame.transform.scale(pygame.image.load(resource_path(f'assets/pacman/{i}.png')), (45, 45)))

    @property
    def center_x(self):
        return self.x + 23

    @property
    def center_y(self):
        return self.y + 24

    def draw(self, counter):
        # 0-RIGHT, 1-LEFT, 2-UP, 3-DOWN
        if self.direction == 0:
            self.screen.blit(self.images[counter // 5], (self.x, self.y))
        elif self.direction == 1:
            self.screen.blit(pygame.transform.flip(self.images[counter // 5], True, False), (self.x, self.y))
        elif self.direction == 2:
            self.screen.blit(pygame.transform.rotate(self.images[counter // 5], 90), (self.x, self.y))
        elif self.direction == 3:
            self.screen.blit(pygame.transform.rotate(self.images[counter // 5], 270), (self.x, self.y))
        return pygame.Rect(self.center_x - 20, self.center_y - 20, 40, 40)

    def check_position(self, level):
        turns = [False, False, False, False]
        # Tile dims centralized (TILE_HEIGHT was num1, TILE_WIDTH was num2, HALF_TILE
        # was num3). Byte-identical substitution — D-15: do NOT merge with
        # Ghost.check_collisions, the band offsets/guards are deliberately divergent.
        centerx = self.center_x
        centery = self.center_y
        if centerx // TILE_WIDTH < BOARD_COLS - 1:
            if self.direction == 0:
                if level[centery // TILE_HEIGHT][(centerx - HALF_TILE) // TILE_WIDTH] < 3:
                    turns[1] = True
            if self.direction == 1:
                if level[centery // TILE_HEIGHT][(centerx + HALF_TILE) // TILE_WIDTH] < 3:
                    turns[0] = True
            if self.direction == 2:
                if level[(centery + HALF_TILE) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[3] = True
            if self.direction == 3:
                if level[(centery - HALF_TILE) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[2] = True

            if self.direction == 2 or self.direction == 3:
                if (12 - PLAYER_TURN_WINDOW_MARGIN) <= centerx % TILE_WIDTH <= (18 + PLAYER_TURN_WINDOW_MARGIN):
                    if level[(centery + HALF_TILE) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[3] = True
                    if level[(centery - HALF_TILE) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[2] = True
                if (12 - PLAYER_TURN_WINDOW_MARGIN) <= centery % TILE_HEIGHT <= (18 + PLAYER_TURN_WINDOW_MARGIN):
                    if level[centery // TILE_HEIGHT][(centerx - TILE_WIDTH) // TILE_WIDTH] < 3:
                        turns[1] = True
                    if level[centery // TILE_HEIGHT][(centerx + TILE_WIDTH) // TILE_WIDTH] < 3:
                        turns[0] = True
            if self.direction == 0 or self.direction == 1:
                if (12 - PLAYER_TURN_WINDOW_MARGIN) <= centerx % TILE_WIDTH <= (18 + PLAYER_TURN_WINDOW_MARGIN):
                    if level[(centery + TILE_HEIGHT) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[3] = True
                    if level[(centery - TILE_HEIGHT) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                        turns[2] = True
                if (12 - PLAYER_TURN_WINDOW_MARGIN) <= centery % TILE_HEIGHT <= (18 + PLAYER_TURN_WINDOW_MARGIN):
                    if level[centery // TILE_HEIGHT][(centerx - HALF_TILE) // TILE_WIDTH] < 3:
                        turns[1] = True
                    if level[centery // TILE_HEIGHT][(centerx + HALF_TILE) // TILE_WIDTH] < 3:
                        turns[0] = True
        else:
            turns[0] = True
            turns[1] = True

        self.turns_allowed = turns
        return turns

    def move(self):
        if self.direction == 0 and self.turns_allowed[0]:
            self.x += self.speed
        elif self.direction == 1 and self.turns_allowed[1]:
            self.x -= self.speed
        if self.direction == 2 and self.turns_allowed[2]:
            self.y -= self.speed
        elif self.direction == 3 and self.turns_allowed[3]:
            self.y += self.speed

    def wrap_around(self):
        if self.x > PLAYER_WRAP_RIGHT_EDGE:
            self.x = PLAYER_WRAP_RIGHT_TO
        elif self.x < PLAYER_WRAP_LEFT_EDGE:
            self.x = PLAYER_WRAP_LEFT_TO

    def update_direction(self):
        if self.direction_command == 0 and self.turns_allowed[0]:
            self.direction = 0
        if self.direction_command == 1 and self.turns_allowed[1]:
            self.direction = 1
        if self.direction_command == 2 and self.turns_allowed[2]:
            self.direction = 2
        if self.direction_command == 3 and self.turns_allowed[3]:
            self.direction = 3

    def reset(self):
        self.x = PLAYER_START_X
        self.y = PLAYER_START_Y
        self.direction = PLAYER_START_DIR
        self.direction_command = PLAYER_START_DIR
