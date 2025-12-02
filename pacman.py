import pygame
from settings import *


class Pacman:
    def __init__(self):
        # position
        self.x = 450
        self.y = 663

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

    def handle_wraparound(self):
        """Teleport across left/right edges (keeps original numbers)."""
        if self.x > 900:
            self.x = -47
        elif self.x < -50:
            self.x = 897

    # optional helper to sync animation counter from main loop
    def set_animation_counter(self, counter):
        self.animation_counter = counter
