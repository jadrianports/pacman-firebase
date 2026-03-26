import pygame
from paths import resource_path
from settings import WIDTH, HEIGHT, PLAYER_SPEED, PLAYER_START_X, PLAYER_START_Y, PLAYER_START_DIR


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
        circle = pygame.draw.circle(self.screen, 'black', (self.center_x, self.center_y), 20, 2)
        return circle

    def check_position(self, level):
        turns = [False, False, False, False]
        num1 = (HEIGHT - 50) // 32
        num2 = (WIDTH // 30)
        num3 = 15
        centerx = self.center_x
        centery = self.center_y
        if centerx // 30 < 29:
            if self.direction == 0:
                if level[centery // num1][(centerx - num3) // num2] < 3:
                    turns[1] = True
            if self.direction == 1:
                if level[centery // num1][(centerx + num3) // num2] < 3:
                    turns[0] = True
            if self.direction == 2:
                if level[(centery + num3) // num1][centerx // num2] < 3:
                    turns[3] = True
            if self.direction == 3:
                if level[(centery - num3) // num1][centerx // num2] < 3:
                    turns[2] = True

            if self.direction == 2 or self.direction == 3:
                if 12 <= centerx % num2 <= 18:
                    if level[(centery + num3) // num1][centerx // num2] < 3:
                        turns[3] = True
                    if level[(centery - num3) // num1][centerx // num2] < 3:
                        turns[2] = True
                if 12 <= centery % num1 <= 18:
                    if level[centery // num1][(centerx - num2) // num2] < 3:
                        turns[1] = True
                    if level[centery // num1][(centerx + num2) // num2] < 3:
                        turns[0] = True
            if self.direction == 0 or self.direction == 1:
                if 12 <= centerx % num2 <= 18:
                    if level[(centery + num1) // num1][centerx // num2] < 3:
                        turns[3] = True
                    if level[(centery - num1) // num1][centerx // num2] < 3:
                        turns[2] = True
                if 12 <= centery % num1 <= 18:
                    if level[centery // num1][(centerx - num3) // num2] < 3:
                        turns[1] = True
                    if level[centery // num1][(centerx + num3) // num2] < 3:
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
        if self.x > 900:
            self.x = -47
        elif self.x < -50:
            self.x = 897

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
