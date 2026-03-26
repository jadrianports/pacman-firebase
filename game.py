import copy
import math
import pygame
from board import boards
from ghost import Ghost
from player import Player
from settings import (
    WIDTH, HEIGHT, FPS, PI, BOARD_COLOR,
    GHOST_SPEED_NORMAL, GHOST_SPEED_FRIGHTENED, GHOST_SPEED_DEAD,
    BLINKY_START_X, BLINKY_START_Y, BLINKY_START_DIR,
    INKY_START_X, INKY_START_Y, INKY_START_DIR,
    PINKY_START_X, PINKY_START_Y, PINKY_START_DIR,
    CLYDE_START_X, CLYDE_START_Y, CLYDE_START_DIR,
    SCATTER, CHASE, MODE_TIMES, FRIGHTENED_DURATION,
    BLINKY_SCATTER, PINKY_SCATTER, INKY_SCATTER, CLYDE_SCATTER,
    GHOST_RETURN_TARGET, CLYDE_SHY_RADIUS,
)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode([WIDTH, HEIGHT])
        self.timer = pygame.time.Clock()
        self.font = pygame.font.Font('freesansbold.ttf', 20)
        self.level = copy.deepcopy(boards)
        self.player = Player(self.screen)

        # Load ghost images
        self.blinky_img = pygame.transform.scale(pygame.image.load('assets/ghosts/red.png'), (45, 45))
        self.pinky_img = pygame.transform.scale(pygame.image.load('assets/ghosts/pink.png'), (45, 45))
        self.inky_img = pygame.transform.scale(pygame.image.load('assets/ghosts/blue.png'), (45, 45))
        self.clyde_img = pygame.transform.scale(pygame.image.load('assets/ghosts/orange.png'), (45, 45))
        self.spooked_img = pygame.transform.scale(pygame.image.load('assets/ghosts/powerup.png'), (45, 45))
        self.dead_img = pygame.transform.scale(pygame.image.load('assets/ghosts/dead.png'), (45, 45))

        # Ghost positions and directions
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

        # Game state
        self.counter = 0
        self.flicker = False
        self.score = 0
        self.powerup = False
        self.power_counter = 0
        self.eaten_ghost = [False, False, False, False]
        self.targets = [(self.player.x, self.player.y)] * 4
        self.blinky_dead = False
        self.inky_dead = False
        self.clyde_dead = False
        self.pinky_dead = False
        self.blinky_box = False
        self.inky_box = False
        self.clyde_box = False
        self.pinky_box = False
        self.moving = False
        self.ghost_speeds = [GHOST_SPEED_NORMAL] * 4
        self.startup_counter = 0
        self.lives = 3
        self.game_over = False
        self.game_won = False

        # Ghost mode system (Chase/Scatter cycling)
        self.ghost_mode = SCATTER
        self.mode_timer = 0
        self.mode_phase = 0  # index into MODE_TIMES
        self.frightened_timer = 0

        # Ghost objects (recreated each frame)
        self.blinky = None
        self.inky = None
        self.pinky = None
        self.clyde = None

    def reset_positions(self):
        self.startup_counter = 0
        self.powerup = False
        self.power_counter = 0
        self.frightened_timer = 0
        self.player.reset()
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

    def reset_mode(self):
        self.ghost_mode = SCATTER
        self.mode_timer = 0
        self.mode_phase = 0
        self.frightened_timer = 0

    def update_mode(self):
        """Update chase/scatter mode cycling and frightened timer."""
        # Handle frightened mode countdown
        if self.powerup:
            self.frightened_timer += 1
            if self.frightened_timer >= FRIGHTENED_DURATION * FPS:
                self.powerup = False
                self.frightened_timer = 0
                self.eaten_ghost = [False, False, False, False]
            return  # mode timer is paused during frightened

        # Cycle through chase/scatter phases
        if self.mode_phase < len(MODE_TIMES):
            self.mode_timer += 1
            threshold = MODE_TIMES[self.mode_phase] * FPS
            if self.mode_timer >= threshold:
                self.mode_timer = 0
                self.mode_phase += 1
                # Alternate between scatter and chase
                if self.mode_phase < len(MODE_TIMES):
                    self.ghost_mode = SCATTER if self.mode_phase % 2 == 0 else CHASE
                else:
                    self.ghost_mode = CHASE  # permanent chase after all phases
                # Ghosts reverse direction on mode switch
                self.reverse_ghost_directions()

    def reverse_ghost_directions(self):
        """Reverse all ghost directions on mode switch (authentic arcade behavior)."""
        reverse = {0: 1, 1: 0, 2: 3, 3: 2}
        self.blinky_direction = reverse[self.blinky_direction]
        self.inky_direction = reverse[self.inky_direction]
        self.pinky_direction = reverse[self.pinky_direction]
        self.clyde_direction = reverse[self.clyde_direction]

    def enter_frightened(self):
        """Enter frightened mode when a power pellet is eaten."""
        self.powerup = True
        self.frightened_timer = 0
        self.eaten_ghost = [False, False, False, False]
        # Ghosts reverse direction when entering frightened mode
        self.reverse_ghost_directions()

    def draw_board(self):
        num1 = ((HEIGHT - 50) // 32)
        num2 = (WIDTH // 30)
        color = BOARD_COLOR
        for i in range(len(self.level)):
            for j in range(len(self.level[i])):
                if self.level[i][j] == 1:
                    pygame.draw.circle(self.screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
                if self.level[i][j] == 2 and not self.flicker:
                    pygame.draw.circle(self.screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10)
                if self.level[i][j] == 3:
                    pygame.draw.line(self.screen, color, (j * num2 + (0.5 * num2), i * num1),
                                     (j * num2 + (0.5 * num2), i * num1 + num1), 3)
                if self.level[i][j] == 4:
                    pygame.draw.line(self.screen, color, (j * num2, i * num1 + (0.5 * num1)),
                                     (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
                if self.level[i][j] == 5:
                    pygame.draw.arc(self.screen, color,
                                    [(j * num2 - (num2 * 0.4)) - 2, (i * num1 + (0.5 * num1)), num2, num1],
                                    0, PI / 2, 3)
                if self.level[i][j] == 6:
                    pygame.draw.arc(self.screen, color,
                                    [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1],
                                    PI / 2, PI, 3)
                if self.level[i][j] == 7:
                    pygame.draw.arc(self.screen, color,
                                    [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1],
                                    PI, 3 * PI / 2, 3)
                if self.level[i][j] == 8:
                    pygame.draw.arc(self.screen, color,
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
            gameover_text = self.font.render('Game over! Space bar to restart!', True, 'red')
            self.screen.blit(gameover_text, (100, 300))
        if self.game_won:
            pygame.draw.rect(self.screen, 'white', [50, 200, 800, 300], 0, 10)
            pygame.draw.rect(self.screen, 'dark gray', [70, 220, 760, 260], 0, 10)
            gameover_text = self.font.render('Victory! Space bar to restart!', True, 'green')
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
                self.enter_frightened()

    def create_ghosts(self):
        self.blinky = Ghost(self.blinky_x, self.blinky_y, self.targets[0], self.ghost_speeds[0],
                            self.blinky_img, self.blinky_direction, self.blinky_dead, self.blinky_box, 0,
                            self.screen, self.level, self.powerup, self.eaten_ghost,
                            self.spooked_img, self.dead_img)
        self.inky = Ghost(self.inky_x, self.inky_y, self.targets[1], self.ghost_speeds[1],
                          self.inky_img, self.inky_direction, self.inky_dead, self.inky_box, 1,
                          self.screen, self.level, self.powerup, self.eaten_ghost,
                          self.spooked_img, self.dead_img)
        self.pinky = Ghost(self.pinky_x, self.pinky_y, self.targets[2], self.ghost_speeds[2],
                           self.pinky_img, self.pinky_direction, self.pinky_dead, self.pinky_box, 2,
                           self.screen, self.level, self.powerup, self.eaten_ghost,
                           self.spooked_img, self.dead_img)
        self.clyde = Ghost(self.clyde_x, self.clyde_y, self.targets[3], self.ghost_speeds[3],
                           self.clyde_img, self.clyde_direction, self.clyde_dead, self.clyde_box, 3,
                           self.screen, self.level, self.powerup, self.eaten_ghost,
                           self.spooked_img, self.dead_img)

    def get_target_for_ghost(self, ghost_id, ghost_x, ghost_y, ghost_dead):
        """Compute target for a single ghost based on current mode.

        Chase targets (authentic arcade):
          Blinky: Pac-Man's current position
          Pinky:  4 tiles ahead of Pac-Man (with up-direction overflow bug: 4 up + 4 left)
          Inky:   Vector from Blinky to 2 tiles ahead of Pac-Man, doubled
          Clyde:  Pac-Man if >8 tiles away, else scatter corner

        Scatter targets: each ghost's assigned corner
        Dead: ghost box center
        """
        tile_size = WIDTH // 30  # 30 pixels per tile

        # Dead ghosts always head to the ghost box
        if ghost_dead:
            return GHOST_RETURN_TARGET

        # In the box → head to exit point
        if 340 < ghost_x < 560 and 340 < ghost_y < 500:
            return (400, 100)

        # Frightened mode doesn't use targeting (random movement), but needs a fallback
        if self.powerup and not self.eaten_ghost[ghost_id]:
            return (self.player.x, self.player.y)  # not actually used for movement

        # Eaten ghost during powerup still chases
        if self.powerup and self.eaten_ghost[ghost_id]:
            return (self.player.x, self.player.y)

        # Scatter mode: head to assigned corner
        if self.ghost_mode == SCATTER:
            scatter_targets = [BLINKY_SCATTER, INKY_SCATTER, PINKY_SCATTER, CLYDE_SCATTER]
            return scatter_targets[ghost_id]

        # Chase mode: unique per-ghost targeting
        px, py = self.player.x, self.player.y

        if ghost_id == 0:  # Blinky - targets Pac-Man directly
            return (px, py)

        elif ghost_id == 1:  # Inky - vector from Blinky doubled past 2 tiles ahead of Pac-Man
            # Find the tile 2 ahead of Pac-Man
            ahead_x, ahead_y = px, py
            if self.player.direction == 0:      # right
                ahead_x += 2 * tile_size
            elif self.player.direction == 1:    # left
                ahead_x -= 2 * tile_size
            elif self.player.direction == 2:    # up
                ahead_y -= 2 * tile_size
            elif self.player.direction == 3:    # down
                ahead_y += 2 * tile_size
            # Vector from Blinky to that point, doubled
            vec_x = ahead_x - self.blinky_x
            vec_y = ahead_y - self.blinky_y
            return (self.blinky_x + vec_x * 2, self.blinky_y + vec_y * 2)

        elif ghost_id == 2:  # Pinky - 4 tiles ahead of Pac-Man (with overflow bug)
            target_x, target_y = px, py
            if self.player.direction == 0:      # right
                target_x += 4 * tile_size
            elif self.player.direction == 1:    # left
                target_x -= 4 * tile_size
            elif self.player.direction == 2:    # up (overflow bug: 4 up + 4 left)
                target_y -= 4 * tile_size
                target_x -= 4 * tile_size
            elif self.player.direction == 3:    # down
                target_y += 4 * tile_size
            return (target_x, target_y)

        elif ghost_id == 3:  # Clyde - direct chase unless within 8-tile radius
            dist = math.sqrt((ghost_x - px) ** 2 + (ghost_y - py) ** 2)
            if dist > CLYDE_SHY_RADIUS:
                return (px, py)
            else:
                return CLYDE_SCATTER

    def get_targets(self):
        return [
            self.get_target_for_ghost(0, self.blinky_x, self.blinky_y, self.blinky_dead),
            self.get_target_for_ghost(1, self.inky_x, self.inky_y, self.inky_dead),
            self.get_target_for_ghost(2, self.pinky_x, self.pinky_y, self.pinky_dead),
            self.get_target_for_ghost(3, self.clyde_x, self.clyde_y, self.clyde_dead),
        ]

    def update_ghost_speeds(self):
        if self.powerup:
            self.ghost_speeds = [GHOST_SPEED_FRIGHTENED] * 4
        else:
            self.ghost_speeds = [GHOST_SPEED_NORMAL] * 4
        if self.eaten_ghost[0]:
            self.ghost_speeds[0] = GHOST_SPEED_NORMAL
        if self.eaten_ghost[1]:
            self.ghost_speeds[1] = GHOST_SPEED_NORMAL
        if self.eaten_ghost[2]:
            self.ghost_speeds[2] = GHOST_SPEED_NORMAL
        if self.eaten_ghost[3]:
            self.ghost_speeds[3] = GHOST_SPEED_NORMAL
        if self.blinky_dead:
            self.ghost_speeds[0] = GHOST_SPEED_DEAD
        if self.inky_dead:
            self.ghost_speeds[1] = GHOST_SPEED_DEAD
        if self.pinky_dead:
            self.ghost_speeds[2] = GHOST_SPEED_DEAD
        if self.clyde_dead:
            self.ghost_speeds[3] = GHOST_SPEED_DEAD

    def move_ghosts(self):
        frightened = self.powerup
        # All ghosts use the same unified movement; personality comes from targeting
        self.blinky_x, self.blinky_y, self.blinky_direction = self.blinky.move(
            frightened=frightened and not self.eaten_ghost[0] and not self.blinky_dead)
        self.inky_x, self.inky_y, self.inky_direction = self.inky.move(
            frightened=frightened and not self.eaten_ghost[1] and not self.inky_dead)
        self.pinky_x, self.pinky_y, self.pinky_direction = self.pinky.move(
            frightened=frightened and not self.eaten_ghost[2] and not self.pinky_dead)
        self.clyde_x, self.clyde_y, self.clyde_direction = self.clyde.move(
            frightened=frightened and not self.eaten_ghost[3] and not self.clyde_dead)

    def handle_ghost_player_collision(self, ghost, ghost_id):
        """Handle collision when player touches a ghost during powerup with eaten_ghost set."""
        if self.powerup and self.player.circle.colliderect(ghost.rect) \
                and self.eaten_ghost[ghost_id] and not ghost.dead:
            if self.lives > 0:
                self.lives -= 1
                self.reset_positions()
            else:
                self.game_over = True
                self.moving = False
                self.startup_counter = 0

    def handle_ghost_eat(self, ghost, ghost_id):
        """Handle eating a ghost during powerup."""
        if self.powerup and self.player.circle.colliderect(ghost.rect) \
                and not ghost.dead and not self.eaten_ghost[ghost_id]:
            if ghost_id == 0:
                self.blinky_dead = True
            elif ghost_id == 1:
                self.inky_dead = True
            elif ghost_id == 2:
                self.pinky_dead = True
            elif ghost_id == 3:
                self.clyde_dead = True
            self.eaten_ghost[ghost_id] = True
            self.score += (2 ** self.eaten_ghost.count(True)) * 100

    def handle_player_death(self):
        """Handle player touching a ghost without powerup."""
        if not self.powerup:
            ghosts = [self.blinky, self.inky, self.pinky, self.clyde]
            for ghost in ghosts:
                if self.player.circle.colliderect(ghost.rect) and not ghost.dead:
                    if self.lives > 0:
                        self.lives -= 1
                        self.reset_positions()
                    else:
                        self.game_over = True
                        self.moving = False
                        self.startup_counter = 0
                    return

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
                    self.reset_positions()
                    self.reset_mode()
                    self.lives -= 1
                    self.score = 0
                    self.lives = 3
                    self.level = copy.deepcopy(boards)
                    self.game_over = False
                    self.game_won = False

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

    def check_ghost_in_box(self):
        if self.blinky.in_box and self.blinky_dead:
            self.blinky_dead = False
        if self.inky.in_box and self.inky_dead:
            self.inky_dead = False
        if self.pinky.in_box and self.pinky_dead:
            self.pinky_dead = False
        if self.clyde.in_box and self.clyde_dead:
            self.clyde_dead = False

    def run(self):
        running = True
        while running:
            self.timer.tick(FPS)

            # Update animation counter and flicker
            if self.counter < 19:
                self.counter += 1
                if self.counter > 3:
                    self.flicker = False
            else:
                self.counter = 0
                self.flicker = True

            # Startup delay
            if self.startup_counter < 180 and not self.game_over and not self.game_won:
                self.moving = False
                self.startup_counter += 1
            else:
                self.moving = True

            # Update ghost mode only while ghosts are moving
            if self.moving and not self.game_over and not self.game_won:
                self.update_mode()

            # Draw
            self.screen.fill('black')
            self.draw_board()
            self.update_ghost_speeds()
            self.check_win()

            self.player.circle = self.player.draw_circle()
            self.player.draw(self.counter)
            self.create_ghosts()
            self.draw_misc()
            self.targets = self.get_targets()

            # Update
            self.player.check_position(self.level)
            if self.moving:
                self.player.move()
                self.move_ghosts()
            self.check_collisions()

            # Ghost-player interactions
            self.handle_player_death()
            self.handle_ghost_player_collision(self.blinky, 0)
            self.handle_ghost_player_collision(self.inky, 1)
            self.handle_ghost_player_collision(self.pinky, 2)
            self.handle_ghost_player_collision(self.clyde, 3)
            self.handle_ghost_eat(self.blinky, 0)
            self.handle_ghost_eat(self.inky, 1)
            self.handle_ghost_eat(self.pinky, 2)
            self.handle_ghost_eat(self.clyde, 3)

            # Input and direction
            running = self.handle_events()
            self.player.update_direction()
            self.player.handle_wrap()
            self.check_ghost_in_box()

            pygame.display.flip()

        pygame.quit()
