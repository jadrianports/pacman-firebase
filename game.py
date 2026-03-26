import copy
import pygame
from board import boards
from ghost import Ghost
from player import Player
from paths import resource_path
from settings import (
    WIDTH, HEIGHT, FPS, PI,
    BLINKY_START_X, BLINKY_START_Y, BLINKY_START_DIR,
    INKY_START_X, INKY_START_Y, INKY_START_DIR,
    PINKY_START_X, PINKY_START_Y, PINKY_START_DIR,
    CLYDE_START_X, CLYDE_START_Y, CLYDE_START_DIR,
)


class Game:
    def __init__(self, screen, timer):
        self.screen = screen
        self.timer = timer
        self.font = pygame.font.Font(resource_path('freesansbold.ttf'), 20)
        self.level = copy.deepcopy(boards)
        self.color = 'blue'

        # Load ghost images
        self.blinky_img = pygame.transform.scale(pygame.image.load(resource_path('assets/ghosts/red.png')), (45, 45))
        self.pinky_img = pygame.transform.scale(pygame.image.load(resource_path('assets/ghosts/pink.png')), (45, 45))
        self.inky_img = pygame.transform.scale(pygame.image.load(resource_path('assets/ghosts/blue.png')), (45, 45))
        self.clyde_img = pygame.transform.scale(pygame.image.load(resource_path('assets/ghosts/orange.png')), (45, 45))
        self.spooked_img = pygame.transform.scale(pygame.image.load(resource_path('assets/ghosts/powerup.png')), (45, 45))
        self.dead_img = pygame.transform.scale(pygame.image.load(resource_path('assets/ghosts/dead.png')), (45, 45))

        # Player
        self.player = Player(self.screen)

        # Ghost state
        self.blinky_x = BLINKY_START_X
        self.blinky_y = BLINKY_START_Y
        self.blinky_direction = BLINKY_START_DIR
        self.inky_x = INKY_START_X
        self.inky_y = INKY_START_Y
        self.inky_direction = INKY_START_DIR
        self.pinky_x = PINKY_START_X
        self.pinky_y = PINKY_START_Y
        self.pinky_direction = PINKY_START_DIR
        self.clyde_x = CLYDE_START_X
        self.clyde_y = CLYDE_START_Y
        self.clyde_direction = CLYDE_START_DIR
        self.blinky_dead = False
        self.inky_dead = False
        self.clyde_dead = False
        self.pinky_dead = False
        self.blinky_box = False
        self.inky_box = False
        self.clyde_box = False
        self.pinky_box = False

        # Game state
        self.counter = 0
        self.flicker = False
        self.score = 0
        self.powerup = False
        self.power_counter = 0
        self.eaten_ghost = [False, False, False, False]
        self.targets = [(self.player.x, self.player.y)] * 4
        self.moving = False
        self.ghost_speeds = [2, 2, 2, 2]
        self.startup_counter = 0
        self.lives = 3
        self.game_over = False
        self.game_won = False
        self.return_to_menu = False

        # Ghost objects (created each frame)
        self.blinky = None
        self.inky = None
        self.pinky = None
        self.clyde = None

    def reset_ghost_positions(self):
        self.blinky_x = BLINKY_START_X
        self.blinky_y = BLINKY_START_Y
        self.blinky_direction = BLINKY_START_DIR
        self.inky_x = INKY_START_X
        self.inky_y = INKY_START_Y
        self.inky_direction = INKY_START_DIR
        self.pinky_x = PINKY_START_X
        self.pinky_y = PINKY_START_Y
        self.pinky_direction = PINKY_START_DIR
        self.clyde_x = CLYDE_START_X
        self.clyde_y = CLYDE_START_Y
        self.clyde_direction = CLYDE_START_DIR
        self.eaten_ghost = [False, False, False, False]
        self.blinky_dead = False
        self.inky_dead = False
        self.clyde_dead = False
        self.pinky_dead = False

    def reset_after_death(self):
        self.startup_counter = 0
        self.powerup = False
        self.power_counter = 0
        self.player.reset()
        self.reset_ghost_positions()

    def draw_board(self):
        num1 = ((HEIGHT - 50) // 32)
        num2 = (WIDTH // 30)
        for i in range(len(self.level)):
            for j in range(len(self.level[i])):
                if self.level[i][j] == 1:
                    pygame.draw.circle(self.screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
                if self.level[i][j] == 2 and not self.flicker:
                    pygame.draw.circle(self.screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10)
                if self.level[i][j] == 3:
                    pygame.draw.line(self.screen, self.color, (j * num2 + (0.5 * num2), i * num1),
                                     (j * num2 + (0.5 * num2), i * num1 + num1), 3)
                if self.level[i][j] == 4:
                    pygame.draw.line(self.screen, self.color, (j * num2, i * num1 + (0.5 * num1)),
                                     (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
                if self.level[i][j] == 5:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * num2 - (num2 * 0.4)) - 2, (i * num1 + (0.5 * num1)), num2, num1],
                                    0, PI / 2, 3)
                if self.level[i][j] == 6:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1], PI / 2, PI, 3)
                if self.level[i][j] == 7:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1], PI,
                                    3 * PI / 2, 3)
                if self.level[i][j] == 8:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * num2 - (num2 * 0.4)) - 2, (i * num1 - (0.4 * num1)), num2, num1],
                                    3 * PI / 2, 2 * PI, 3)
                if self.level[i][j] == 9:
                    pygame.draw.line(self.screen, 'white', (j * num2, i * num1 + (0.5 * num1)),
                                     (j * num2 + num2, i * num1 + (0.5 * num1)), 3)

    def draw_misc(self):
        score_text = self.font.render(f'Score: {self.score}', True, 'white')
        self.screen.blit(score_text, (10, 920))
        if self.powerup:
            pygame.draw.circle(self.screen, 'blue', (140, 930), 15)
        for i in range(self.lives):
            self.screen.blit(pygame.transform.scale(self.player.images[0], (30, 30)), (650 + i * 40, 915))
        if self.game_over:
            pygame.draw.rect(self.screen, 'white', [50, 200, 800, 300], 0, 10)
            pygame.draw.rect(self.screen, 'dark gray', [70, 220, 760, 260], 0, 10)
            gameover_text = self.font.render('Game over! Press SPACE to continue', True, 'red')
            self.screen.blit(gameover_text, (100, 300))
        if self.game_won:
            pygame.draw.rect(self.screen, 'white', [50, 200, 800, 300], 0, 10)
            pygame.draw.rect(self.screen, 'dark gray', [70, 220, 760, 260], 0, 10)
            gameover_text = self.font.render('Victory! Press SPACE to continue', True, 'green')
            self.screen.blit(gameover_text, (100, 300))

    def check_collisions(self):
        num1 = (HEIGHT - 50) // 32
        num2 = WIDTH // 30
        if 0 < self.player.x < 870:
            if self.level[self.player.center_y // num1][self.player.center_x // num2] == 1:
                self.level[self.player.center_y // num1][self.player.center_x // num2] = 0
                self.score += 10
            if self.level[self.player.center_y // num1][self.player.center_x // num2] == 2:
                self.level[self.player.center_y // num1][self.player.center_x // num2] = 0
                self.score += 50
                self.powerup = True
                self.power_counter = 0
                self.eaten_ghost = [False, False, False, False]

    def get_targets(self):
        if self.player.x < 450:
            runaway_x = 900
        else:
            runaway_x = 0
        if self.player.y < 450:
            runaway_y = 900
        else:
            runaway_y = 0
        return_target = (380, 400)
        if self.powerup:
            if not self.blinky.dead and not self.eaten_ghost[0]:
                blink_target = (runaway_x, runaway_y)
            elif not self.blinky.dead and self.eaten_ghost[0]:
                if 340 < self.blinky_x < 560 and 340 < self.blinky_y < 500:
                    blink_target = (400, 100)
                else:
                    blink_target = (self.player.x, self.player.y)
            else:
                blink_target = return_target
            if not self.inky.dead and not self.eaten_ghost[1]:
                ink_target = (runaway_x, self.player.y)
            elif not self.inky.dead and self.eaten_ghost[1]:
                if 340 < self.inky_x < 560 and 340 < self.inky_y < 500:
                    ink_target = (400, 100)
                else:
                    ink_target = (self.player.x, self.player.y)
            else:
                ink_target = return_target
            if not self.pinky.dead:
                pink_target = (self.player.x, runaway_y)
            elif not self.pinky.dead and self.eaten_ghost[2]:
                if 340 < self.pinky_x < 560 and 340 < self.pinky_y < 500:
                    pink_target = (400, 100)
                else:
                    pink_target = (self.player.x, self.player.y)
            else:
                pink_target = return_target
            if not self.clyde.dead and not self.eaten_ghost[3]:
                clyd_target = (450, 450)
            elif not self.clyde.dead and self.eaten_ghost[3]:
                if 340 < self.clyde_x < 560 and 340 < self.clyde_y < 500:
                    clyd_target = (400, 100)
                else:
                    clyd_target = (self.player.x, self.player.y)
            else:
                clyd_target = return_target
        else:
            if not self.blinky.dead:
                if 340 < self.blinky_x < 560 and 340 < self.blinky_y < 500:
                    blink_target = (400, 100)
                else:
                    blink_target = (self.player.x, self.player.y)
            else:
                blink_target = return_target
            if not self.inky.dead:
                if 340 < self.inky_x < 560 and 340 < self.inky_y < 500:
                    ink_target = (400, 100)
                else:
                    ink_target = (self.player.x, self.player.y)
            else:
                ink_target = return_target
            if not self.pinky.dead:
                if 340 < self.pinky_x < 560 and 340 < self.pinky_y < 500:
                    pink_target = (400, 100)
                else:
                    pink_target = (self.player.x, self.player.y)
            else:
                pink_target = return_target
            if not self.clyde.dead:
                if 340 < self.clyde_x < 560 and 340 < self.clyde_y < 500:
                    clyd_target = (400, 100)
                else:
                    clyd_target = (self.player.x, self.player.y)
            else:
                clyd_target = return_target
        return [blink_target, ink_target, pink_target, clyd_target]

    def update_ghost_speeds(self):
        if self.powerup:
            self.ghost_speeds = [1, 1, 1, 1]
        else:
            self.ghost_speeds = [2, 2, 2, 2]
        if self.eaten_ghost[0]:
            self.ghost_speeds[0] = 2
        if self.eaten_ghost[1]:
            self.ghost_speeds[1] = 2
        if self.eaten_ghost[2]:
            self.ghost_speeds[2] = 2
        if self.eaten_ghost[3]:
            self.ghost_speeds[3] = 2
        if self.blinky_dead:
            self.ghost_speeds[0] = 4
        if self.inky_dead:
            self.ghost_speeds[1] = 4
        if self.pinky_dead:
            self.ghost_speeds[2] = 4
        if self.clyde_dead:
            self.ghost_speeds[3] = 4

    def create_ghosts(self):
        self.blinky = Ghost(self.blinky_x, self.blinky_y, self.targets[0], self.ghost_speeds[0], self.blinky_img,
                            self.blinky_direction, self.blinky_dead, self.blinky_box, 0,
                            self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level)
        self.inky = Ghost(self.inky_x, self.inky_y, self.targets[1], self.ghost_speeds[1], self.inky_img,
                          self.inky_direction, self.inky_dead, self.inky_box, 1,
                          self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level)
        self.pinky = Ghost(self.pinky_x, self.pinky_y, self.targets[2], self.ghost_speeds[2], self.pinky_img,
                           self.pinky_direction, self.pinky_dead, self.pinky_box, 2,
                           self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level)
        self.clyde = Ghost(self.clyde_x, self.clyde_y, self.targets[3], self.ghost_speeds[3], self.clyde_img,
                           self.clyde_direction, self.clyde_dead, self.clyde_box, 3,
                           self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level)

    def move_ghosts(self):
        if not self.blinky_dead and not self.blinky.in_box:
            self.blinky_x, self.blinky_y, self.blinky_direction = self.blinky.move_blinky()
        else:
            self.blinky_x, self.blinky_y, self.blinky_direction = self.blinky.move_clyde()
        if not self.pinky_dead and not self.pinky.in_box:
            self.pinky_x, self.pinky_y, self.pinky_direction = self.pinky.move_pinky()
        else:
            self.pinky_x, self.pinky_y, self.pinky_direction = self.pinky.move_clyde()
        if not self.inky_dead and not self.inky.in_box:
            self.inky_x, self.inky_y, self.inky_direction = self.inky.move_inky()
        else:
            self.inky_x, self.inky_y, self.inky_direction = self.inky.move_clyde()
        self.clyde_x, self.clyde_y, self.clyde_direction = self.clyde.move_clyde()

    def check_ghost_collisions(self, player_circle):
        # Normal ghost kills player
        if not self.powerup:
            if (player_circle.colliderect(self.blinky.rect) and not self.blinky.dead) or \
                    (player_circle.colliderect(self.inky.rect) and not self.inky.dead) or \
                    (player_circle.colliderect(self.pinky.rect) and not self.pinky.dead) or \
                    (player_circle.colliderect(self.clyde.rect) and not self.clyde.dead):
                if self.lives > 0:
                    self.lives -= 1
                    self.reset_after_death()
                else:
                    self.game_over = True
                    self.moving = False
                    self.startup_counter = 0

        # Already-eaten ghost kills player during powerup
        if self.powerup and player_circle.colliderect(self.blinky.rect) and self.eaten_ghost[0] and not self.blinky.dead:
            if self.lives > 0:
                self.lives -= 1
                self.reset_after_death()
            else:
                self.game_over = True
                self.moving = False
                self.startup_counter = 0
        if self.powerup and player_circle.colliderect(self.inky.rect) and self.eaten_ghost[1] and not self.inky.dead:
            if self.lives > 0:
                self.lives -= 1
                self.reset_after_death()
            else:
                self.game_over = True
                self.moving = False
                self.startup_counter = 0
        if self.powerup and player_circle.colliderect(self.pinky.rect) and self.eaten_ghost[2] and not self.pinky.dead:
            if self.lives > 0:
                self.lives -= 1
                self.reset_after_death()
            else:
                self.game_over = True
                self.moving = False
                self.startup_counter = 0
        if self.powerup and player_circle.colliderect(self.clyde.rect) and self.eaten_ghost[3] and not self.clyde.dead:
            if self.lives > 0:
                self.lives -= 1
                self.reset_after_death()
            else:
                self.game_over = True
                self.moving = False
                self.startup_counter = 0

        # Player eats ghost during powerup
        if self.powerup and player_circle.colliderect(self.blinky.rect) and not self.blinky.dead and not self.eaten_ghost[0]:
            self.blinky_dead = True
            self.eaten_ghost[0] = True
            self.score += (2 ** self.eaten_ghost.count(True)) * 100
        if self.powerup and player_circle.colliderect(self.inky.rect) and not self.inky.dead and not self.eaten_ghost[1]:
            self.inky_dead = True
            self.eaten_ghost[1] = True
            self.score += (2 ** self.eaten_ghost.count(True)) * 100
        if self.powerup and player_circle.colliderect(self.pinky.rect) and not self.pinky.dead and not self.eaten_ghost[2]:
            self.pinky_dead = True
            self.eaten_ghost[2] = True
            self.score += (2 ** self.eaten_ghost.count(True)) * 100
        if self.powerup and player_circle.colliderect(self.clyde.rect) and not self.clyde.dead and not self.eaten_ghost[3]:
            self.clyde_dead = True
            self.eaten_ghost[3] = True
            self.score += (2 ** self.eaten_ghost.count(True)) * 100

    def check_ghost_in_box(self):
        if self.blinky.in_box and self.blinky_dead:
            self.blinky_dead = False
        if self.inky.in_box and self.inky_dead:
            self.inky_dead = False
        if self.pinky.in_box and self.pinky_dead:
            self.pinky_dead = False
        if self.clyde.in_box and self.clyde_dead:
            self.clyde_dead = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    self.player.direction_command = 0
                if event.key == pygame.K_LEFT:
                    self.player.direction_command = 1
                if event.key == pygame.K_UP:
                    self.player.direction_command = 2
                if event.key == pygame.K_DOWN:
                    self.player.direction_command = 3
                if event.key == pygame.K_SPACE and (self.game_over or self.game_won):
                    self.return_to_menu = True

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_RIGHT and self.player.direction_command == 0:
                    self.player.direction_command = self.player.direction
                if event.key == pygame.K_LEFT and self.player.direction_command == 1:
                    self.player.direction_command = self.player.direction
                if event.key == pygame.K_UP and self.player.direction_command == 2:
                    self.player.direction_command = self.player.direction
                if event.key == pygame.K_DOWN and self.player.direction_command == 3:
                    self.player.direction_command = self.player.direction
        return True

    def check_win(self):
        self.game_won = True
        for i in range(len(self.level)):
            if 1 in self.level[i] or 2 in self.level[i]:
                self.game_won = False
                break

    def run(self):
        running = True
        while running:
            if self.return_to_menu:
                return {"score": self.score, "game_won": self.game_won}
            self.timer.tick(FPS)

            # Animation counter
            if self.counter < 19:
                self.counter += 1
                if self.counter > 3:
                    self.flicker = False
            else:
                self.counter = 0
                self.flicker = True

            # Powerup timer
            if self.powerup and self.power_counter < 600:
                self.power_counter += 1
            elif self.powerup and self.power_counter >= 600:
                self.power_counter = 0
                self.powerup = False
                self.eaten_ghost = [False, False, False, False]

            # Startup delay
            if self.startup_counter < 180 and not self.game_over and not self.game_won:
                self.moving = False
                self.startup_counter += 1
            else:
                self.moving = True

            # Draw
            self.screen.fill('black')
            self.draw_board()
            self.update_ghost_speeds()
            self.check_win()

            player_circle = self.player.draw(self.counter)
            self.create_ghosts()
            self.draw_misc()
            self.targets = self.get_targets()

            self.player.check_position(self.level)
            if self.moving:
                self.player.move()
                self.move_ghosts()
            self.check_collisions()
            self.check_ghost_collisions(player_circle)

            # Input
            running = self.handle_events()
            self.player.update_direction()
            self.player.wrap_around()
            self.check_ghost_in_box()

            pygame.display.flip()

        return None
