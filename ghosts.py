import pygame
from settings import *


class Ghost:
    def __init__(self, x, y, target, speed, img_path, direction, dead, box, ghost_id):
        self.x = x
        self.y = y
        self.center_x = self.x + 22
        self.center_y = self.y + 22
        self.target = target
        self.speed = speed
        self.img = pygame.transform.scale(pygame.image.load(img_path), (45, 45))
        self.direction = direction
        self.dead = dead
        self.in_box = box
        self.id = ghost_id  # 0:Blinky, 1:Inky, 2:Pinky, 3:Clyde
        self.turns = [False, False, False, False]
        self.rect = self.draw(pygame.display.get_surface(), False, False)

        # Load extra assets
        self.spooked_img = pygame.transform.scale(pygame.image.load(f'assets/ghosts/powerup.png'), (45, 45))
        self.dead_img = pygame.transform.scale(pygame.image.load(f'assets/ghosts/dead.png'), (45, 45))

    def update(self, level_map, powerup, eaten):
        self.center_x = self.x + 22
        self.center_y = self.y + 22
        self.check_collisions(level_map)

        if self.in_box and self.dead:
            self.dead = False

        # Decide which movement logic to use
        # If dead or in box, move generally towards center/exit
        if self.id == 0 and not self.dead and not self.in_box:  # Blinky
            self.move_chase()
        elif self.id == 1 and not self.dead and not self.in_box:  # Inky
            self.move_chase()
        elif self.id == 2 and not self.dead and not self.in_box:  # Pinky
            self.move_chase()
        else:
            self.move_chase()  # Fallback or Clyde logic

        self.rect = pygame.rect.Rect((self.center_x - 18, self.center_y - 18), (36, 36))

    def draw(self, screen, powerup, eaten_status):
        if (not powerup and not self.dead) or (eaten_status and powerup and not self.dead):
            screen.blit(self.img, (self.x, self.y))
        elif powerup and not self.dead and not eaten_status:
            screen.blit(self.spooked_img, (self.x, self.y))
        else:
            screen.blit(self.dead_img, (self.x, self.y))

        ghost_rect = pygame.rect.Rect((self.center_x - 18, self.center_y - 18), (36, 36))
        return ghost_rect

    def check_collisions(self, level):
        # R, L, U, D
        self.turns = [False, False, False, False]
        num3 = 15

        if 0 < self.center_x // TILE_WIDTH < 29:
            # Basic checks
            if level[(self.center_y - num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] == 9:
                self.turns[2] = True
            if level[self.center_y // TILE_HEIGHT][(self.center_x - num3) // TILE_WIDTH] < 3 \
                    or (level[self.center_y // TILE_HEIGHT][(self.center_x - num3) // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True
            if level[self.center_y // TILE_HEIGHT][(self.center_x + num3) // TILE_WIDTH] < 3 \
                    or (level[self.center_y // TILE_HEIGHT][(self.center_x + num3) // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True
            if level[(self.center_y + num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] < 3 \
                    or (level[(self.center_y + num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True
            if level[(self.center_y - num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] < 3 \
                    or (level[(self.center_y - num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            # Turning logic
            if self.direction in [2, 3]:
                if 12 <= self.center_x % TILE_WIDTH <= 18:
                    if level[(self.center_y + num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] < 3 \
                            or (level[(self.center_y + num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(self.center_y - num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] < 3 \
                            or (level[(self.center_y - num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % TILE_HEIGHT <= 18:
                    if level[self.center_y // TILE_HEIGHT][(self.center_x - TILE_WIDTH) // TILE_WIDTH] < 3 \
                            or (
                            level[self.center_y // TILE_HEIGHT][(self.center_x - TILE_WIDTH) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[self.center_y // TILE_HEIGHT][(self.center_x + TILE_WIDTH) // TILE_WIDTH] < 3 \
                            or (
                            level[self.center_y // TILE_HEIGHT][(self.center_x + TILE_WIDTH) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            if self.direction in [0, 1]:
                if 12 <= self.center_x % TILE_WIDTH <= 18:
                    if level[(self.center_y + num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] < 3 \
                            or (level[(self.center_y + num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(self.center_y - num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] < 3 \
                            or (level[(self.center_y - num3) // TILE_HEIGHT][self.center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % TILE_HEIGHT <= 18:
                    if level[self.center_y // TILE_HEIGHT][(self.center_x - num3) // TILE_WIDTH] < 3 \
                            or (level[self.center_y // TILE_HEIGHT][(self.center_x - num3) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[self.center_y // TILE_HEIGHT][(self.center_x + num3) // TILE_WIDTH] < 3 \
                            or (level[self.center_y // TILE_HEIGHT][(self.center_x + num3) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True
        else:
            self.turns[0] = True
            self.turns[1] = True

        if 350 < self.x < 550 and 370 < self.y < 480:
            self.in_box = True
        else:
            self.in_box = False

    def move_chase(self):
        # Universal chase/turn logic based on target
        # 0: Right, 1: Left, 2: Up, 3: Down

        move_x, move_y = 0, 0

        if self.direction == 0:  # Moving Right
            if self.target[0] > self.x and self.turns[0]:
                move_x = self.speed
            elif not self.turns[0]:
                if self.target[1] > self.y and self.turns[3]:
                    self.direction = 3
                    move_y = self.speed
                elif self.target[1] < self.y and self.turns[2]:
                    self.direction = 2
                    move_y = -self.speed
                elif self.target[0] < self.x and self.turns[1]:
                    self.direction = 1
                    move_x = -self.speed
                elif self.turns[3]:
                    self.direction = 3
                    move_y = self.speed
                elif self.turns[2]:
                    self.direction = 2
                    move_y = -self.speed
                elif self.turns[1]:
                    self.direction = 1
                    move_x = -self.speed
            elif self.turns[0]:
                move_x = self.speed

        elif self.direction == 1:  # Moving Left
            if self.target[1] > self.y and self.turns[3]:
                self.direction = 3
                move_y = self.speed
            elif self.target[0] < self.x and self.turns[1]:
                move_x = -self.speed
            elif not self.turns[1]:
                if self.target[1] > self.y and self.turns[3]:
                    self.direction = 3
                    move_y = self.speed
                elif self.target[1] < self.y and self.turns[2]:
                    self.direction = 2
                    move_y = -self.speed
                elif self.target[0] > self.x and self.turns[0]:
                    self.direction = 0
                    move_x = self.speed
                elif self.turns[3]:
                    self.direction = 3
                    move_y = self.speed
                elif self.turns[2]:
                    self.direction = 2
                    move_y = -self.speed
                elif self.turns[0]:
                    self.direction = 0
                    move_x = self.speed
            elif self.turns[1]:
                move_x = -self.speed

        elif self.direction == 2:  # Moving Up
            if self.target[0] < self.x and self.turns[1]:
                self.direction = 1
                move_x = -self.speed
            elif self.target[1] < self.y and self.turns[2]:
                move_y = -self.speed
            elif not self.turns[2]:
                if self.target[0] > self.x and self.turns[0]:
                    self.direction = 0
                    move_x = self.speed
                elif self.target[0] < self.x and self.turns[1]:
                    self.direction = 1
                    move_x = -self.speed
                elif self.target[1] > self.y and self.turns[3]:
                    self.direction = 3
                    move_y = self.speed
                elif self.turns[1]:
                    self.direction = 1
                    move_x = -self.speed
                elif self.turns[3]:
                    self.direction = 3
                    move_y = self.speed
                elif self.turns[0]:
                    self.direction = 0
                    move_x = self.speed
            elif self.turns[2]:
                move_y = -self.speed

        elif self.direction == 3:  # Moving Down
            if self.target[1] > self.y and self.turns[3]:
                move_y = self.speed
            elif not self.turns[3]:
                if self.target[0] > self.x and self.turns[0]:
                    self.direction = 0
                    move_x = self.speed
                elif self.target[0] < self.x and self.turns[1]:
                    self.direction = 1
                    move_x = -self.speed
                elif self.target[1] < self.y and self.turns[2]:
                    self.direction = 2
                    move_y = -self.speed
                elif self.turns[2]:
                    self.direction = 2
                    move_y = -self.speed
                elif self.turns[1]:
                    self.direction = 1
                    move_x = -self.speed
                elif self.turns[0]:
                    self.direction = 0
                    move_x = self.speed
            elif self.turns[3]:
                move_y = self.speed

        self.x += move_x
        self.y += move_y

        if self.x < -30:
            self.x = 900
        elif self.x > 900:
            self.x = -30