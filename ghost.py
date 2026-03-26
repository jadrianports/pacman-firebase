import math
import random
import pygame
from settings import WIDTH, HEIGHT


# Direction constants: 0=Right, 1=Left, 2=Up, 3=Down
REVERSE = {0: 1, 1: 0, 2: 3, 3: 2}
# Tie-breaking priority (lower = higher priority): Up > Left > Down > Right
DIRECTION_PRIORITY = {2: 0, 1: 1, 3: 2, 0: 3}
# Movement deltas per direction: (dx, dy)
DIRECTION_DELTA = {0: (1, 0), 1: (-1, 0), 2: (0, -1), 3: (0, 1)}


class Ghost:
    def __init__(self, x_coord, y_coord, target, speed, img, direct, dead, box, id,
                 screen, level, powerup, eaten_ghost, spooked_img, dead_img):
        self.x_pos = x_coord
        self.y_pos = y_coord
        self.center_x = self.x_pos + 22
        self.center_y = self.y_pos + 22
        self.target = target
        self.speed = speed
        self.img = img
        self.direction = direct
        self.dead = dead
        self.in_box = box
        self.id = id
        self.screen = screen
        self.level = level
        self.powerup = powerup
        self.eaten_ghost = eaten_ghost
        self.spooked_img = spooked_img
        self.dead_img = dead_img
        self.turns, self.in_box = self.check_collisions()
        self.rect = self.draw()

    def draw(self):
        if (not self.powerup and not self.dead) or (self.eaten_ghost[self.id] and self.powerup and not self.dead):
            self.screen.blit(self.img, (self.x_pos, self.y_pos))
        elif self.powerup and not self.dead and not self.eaten_ghost[self.id]:
            self.screen.blit(self.spooked_img, (self.x_pos, self.y_pos))
        else:
            self.screen.blit(self.dead_img, (self.x_pos, self.y_pos))
        ghost_rect = pygame.rect.Rect((self.center_x - 18, self.center_y - 18), (36, 36))
        return ghost_rect

    def check_collisions(self):
        # R, L, U, D
        num1 = ((HEIGHT - 50) // 32)
        num2 = (WIDTH // 30)
        num3 = 15
        self.turns = [False, False, False, False]
        if 0 < self.center_x // 30 < 29:
            if self.level[(self.center_y - num3) // num1][self.center_x // num2] == 9:
                self.turns[2] = True
            if self.level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                    or (self.level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True
            if self.level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                    or (self.level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True
            if self.level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                    or (self.level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True
            if self.level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                    or (self.level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            if self.direction == 2 or self.direction == 3:
                if 12 <= self.center_x % num2 <= 18:
                    if self.level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (self.level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if self.level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (self.level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % num1 <= 18:
                    if self.level[self.center_y // num1][(self.center_x - num2) // num2] < 3 \
                            or (self.level[self.center_y // num1][(self.center_x - num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if self.level[self.center_y // num1][(self.center_x + num2) // num2] < 3 \
                            or (self.level[self.center_y // num1][(self.center_x + num2) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            if self.direction == 0 or self.direction == 1:
                if 12 <= self.center_x % num2 <= 18:
                    if self.level[(self.center_y + num3) // num1][self.center_x // num2] < 3 \
                            or (self.level[(self.center_y + num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if self.level[(self.center_y - num3) // num1][self.center_x // num2] < 3 \
                            or (self.level[(self.center_y - num3) // num1][self.center_x // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % num1 <= 18:
                    if self.level[self.center_y // num1][(self.center_x - num3) // num2] < 3 \
                            or (self.level[self.center_y // num1][(self.center_x - num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if self.level[self.center_y // num1][(self.center_x + num3) // num2] < 3 \
                            or (self.level[self.center_y // num1][(self.center_x + num3) // num2] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True
        else:
            self.turns[0] = True
            self.turns[1] = True
        if 350 < self.x_pos < 550 and 370 < self.y_pos < 480:
            self.in_box = True
        else:
            self.in_box = False
        return self.turns, self.in_box

    def move(self, frightened=False):
        """Unified movement: continue straight until blocked, then pick best direction.
        Ghosts only change direction when their current path is blocked by a wall.
        On wall collision: pick direction minimizing distance to target (or random if frightened).
        Tie-breaking: Up > Left > Down > Right (authentic arcade priority).
        """
        reverse_dir = REVERSE[self.direction]

        # Gather valid directions, excluding reverse
        available = [d for d in range(4) if self.turns[d] and d != reverse_dir]

        # If completely stuck, allow reverse as last resort
        if not available:
            if self.turns[reverse_dir]:
                available = [reverse_dir]
            else:
                return self.x_pos, self.y_pos, self.direction

        # If current direction is still valid, continue straight (no reconsideration)
        if self.direction in available:
            chosen = self.direction
        elif len(available) == 1:
            # Only one option, take it
            chosen = available[0]
        elif frightened:
            # Blocked and frightened: pick random direction
            chosen = random.choice(available)
        else:
            # Blocked: pick direction that minimizes distance to target
            best_dist = float('inf')
            chosen = available[0]
            for d in available:
                dx, dy = DIRECTION_DELTA[d]
                nx = self.x_pos + dx * self.speed
                ny = self.y_pos + dy * self.speed
                dist = math.sqrt((nx - self.target[0]) ** 2 + (ny - self.target[1]) ** 2)
                if dist < best_dist or (dist == best_dist and DIRECTION_PRIORITY[d] < DIRECTION_PRIORITY[chosen]):
                    best_dist = dist
                    chosen = d

        # Apply movement
        self.direction = chosen
        dx, dy = DIRECTION_DELTA[chosen]
        self.x_pos += dx * self.speed
        self.y_pos += dy * self.speed

        # Screen wrapping
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30

        return self.x_pos, self.y_pos, self.direction
