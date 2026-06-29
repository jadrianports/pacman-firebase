import copy
import math
import pygame
from board import boards
from ghost import Ghost
from player import Player
from paths import resource_path
from sound import SoundManager
import juice
import theme
from settings import (
    WIDTH, FPS, PI,
    TILE_HEIGHT, TILE_WIDTH,
    SCATTER_RETURN_TARGET, SCATTER_EATEN_TARGET, SCATTER_CLYDE_TARGET,
    BLINKY_START_X, BLINKY_START_Y, BLINKY_START_DIR,
    INKY_START_X, INKY_START_Y, INKY_START_DIR,
    PINKY_START_X, PINKY_START_Y, PINKY_START_DIR,
    CLYDE_START_X, CLYDE_START_Y, CLYDE_START_DIR,
    BOX_EXIT_DELAY_INKY, BOX_EXIT_DELAY_PINKY, BOX_EXIT_DELAY_CLYDE,
    GHOST_CATCH_DISTANCE,
    GHOST_CHASE_SPEED_NUM, GHOST_CHASE_SPEED_DEN,
    DEATH_ANIM_FRAMES,
    FRIGHT_FLASH_START, FRIGHT_FLASH_INTERVAL,
)
from geometry import in_box, GHOST_BOX_BOUNDS


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
        # FEEL-04/D-07: pre-tint a white-leaning copy of the spooked sprite once (no new
        # asset). BLEND_RGB_ADD exists in both pygame editions (Pitfall 5); add-color
        # tuned in the 09-05 playtest.
        self.spooked_white_img = self.spooked_img.copy()
        self.spooked_white_img.fill((90, 90, 120, 0), special_flags=pygame.BLEND_RGB_ADD)

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

        # Box exit timers
        self.box_exit_timers = [0, 0, 0, 0]

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
        # FAIR-02: per-ghost integer-rational chase-step accumulator. Keeps every
        # chasing ghost averaging GHOST_CHASE_SPEED_NUM/GHOST_CHASE_SPEED_DEN px/frame
        # while each per-frame step stays a strict integer in {1, 2}. At the D-10
        # dial (40/20 = 2.0) the average is exactly PLAYER_SPEED, so every step is 2.
        self.ghost_step_acc = [0, 0, 0, 0]
        self.starting = True
        self.start_sound_played = False
        self.dying = False
        self.dying_delay = 0
        # FEEL-01: juice-gated wedge-collapse cursor; advances only while dying and
        # juice (Pattern 1 / D-05). Not a captured-state field, so it can never enter
        # the golden state trace.
        self.death_anim_frame = 0
        self.eat_freeze = False
        self.eat_freeze_timer = 0
        self.eat_freeze_score = 0
        self.eat_freeze_pos = (0, 0)
        self.lives = 3
        self.game_over = False
        self.game_won = False
        self.return_to_menu = False

        # Ghost objects (created each frame)
        self.blinky = None
        self.inky = None
        self.pinky = None
        self.clyde = None

        # Sound
        self.sound = SoundManager()

        # UI fonts
        self.ready_font = pygame.font.Font(resource_path('freesansbold.ttf'), 36)
        self.gameover_font = pygame.font.Font(resource_path('freesansbold.ttf'), 36)
        self.hint_font = pygame.font.Font(resource_path('freesansbold.ttf'), 18)
        self.score_popup_font = pygame.font.Font(resource_path('freesansbold.ttf'), 16)
        self.end_screen_timer = 0

        # Bold presentation layer — OFF by default so the deterministic frame-hash /
        # golden tests render the pure frame. main.py sets juice=True for real play.
        self.juice = False
        self.present_fn = pygame.display.flip
        self.particles = juice.Particles()
        self.shake = juice.Shake()

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
        self.powerup = False
        self.power_counter = 0
        self.death_anim_frame = 0
        self.box_exit_timers = [0, 0, 0, 0]
        self.player.reset()
        self.reset_ghost_positions()
        self.starting = True
        self.start_sound_played = False
        # FAIR-02: drop banked chase-step credit so no phantom speed carries across
        # a death/respawn pause (Pitfall 4).
        self.ghost_step_acc = [0, 0, 0, 0]

    def draw_board(self):
        # Tile dims centralized (TILE_HEIGHT was num1, TILE_WIDTH was num2). The
        # cosmetic literals (radii 4/10, 0.5*/0.4* arc offsets, PI fractions, width 3)
        # stay inline — they are rendering, not geometry (D-13).
        for i in range(len(self.level)):
            for j in range(len(self.level[i])):
                if self.level[i][j] == 1:
                    cx = j * TILE_WIDTH + (0.5 * TILE_WIDTH)
                    cy = i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)
                    if self.juice:
                        juice.glow_circle(self.screen, (int(cx), int(cy)), (255, 240, 200), 4)
                    else:
                        pygame.draw.circle(self.screen, 'white', (cx, cy), 4)
                if self.level[i][j] == 2 and not self.flicker:
                    cx = j * TILE_WIDTH + (0.5 * TILE_WIDTH)
                    cy = i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)
                    if self.juice:
                        pulse = 10 + int(2 * math.sin(self.counter * 0.3))
                        juice.glow_circle(self.screen, (int(cx), int(cy)), (255, 230, 180), pulse)
                    else:
                        pygame.draw.circle(self.screen, 'white', (cx, cy), 10)
                if self.level[i][j] == 3:
                    pygame.draw.line(self.screen, self.color, (j * TILE_WIDTH + (0.5 * TILE_WIDTH), i * TILE_HEIGHT),
                                     (j * TILE_WIDTH + (0.5 * TILE_WIDTH), i * TILE_HEIGHT + TILE_HEIGHT), 3)
                if self.level[i][j] == 4:
                    pygame.draw.line(self.screen, self.color, (j * TILE_WIDTH, i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)),
                                     (j * TILE_WIDTH + TILE_WIDTH, i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)), 3)
                if self.level[i][j] == 5:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * TILE_WIDTH - (TILE_WIDTH * 0.4)) - 2, (i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)), TILE_WIDTH, TILE_HEIGHT],
                                    0, PI / 2, 3)
                if self.level[i][j] == 6:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * TILE_WIDTH + (TILE_WIDTH * 0.5)), (i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)), TILE_WIDTH, TILE_HEIGHT], PI / 2, PI, 3)
                if self.level[i][j] == 7:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * TILE_WIDTH + (TILE_WIDTH * 0.5)), (i * TILE_HEIGHT - (0.4 * TILE_HEIGHT)), TILE_WIDTH, TILE_HEIGHT], PI,
                                    3 * PI / 2, 3)
                if self.level[i][j] == 8:
                    pygame.draw.arc(self.screen, self.color,
                                    [(j * TILE_WIDTH - (TILE_WIDTH * 0.4)) - 2, (i * TILE_HEIGHT - (0.4 * TILE_HEIGHT)), TILE_WIDTH, TILE_HEIGHT],
                                    3 * PI / 2, 2 * PI, 3)
                if self.level[i][j] == 9:
                    pygame.draw.line(self.screen, 'white', (j * TILE_WIDTH, i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)),
                                     (j * TILE_WIDTH + TILE_WIDTH, i * TILE_HEIGHT + (0.5 * TILE_HEIGHT)), 3)

    def draw_ready(self):
        if self.starting and not self.game_over and not self.game_won:
            text = self.ready_font.render('READY!', True, 'yellow')
            text_rect = text.get_rect(center=(WIDTH // 2, 540))
            self.screen.blit(text, text_rect)

    def draw_misc(self):
        if self.juice:
            score_text = theme.pixel_font(theme.SIZE_SMALL).render(f'SCORE {self.score}', True, 'yellow')
        else:
            score_text = self.font.render(f'Score: {self.score}', True, 'white')
        self.screen.blit(score_text, (10, 920))
        if self.powerup:
            pygame.draw.circle(self.screen, 'blue', (140, 930), 15)
        for i in range(self.lives):
            self.screen.blit(pygame.transform.scale(self.player.images[0], (30, 30)), (650 + i * 40, 915))
        if self.game_over:
            self.end_screen_timer += 1
            text = self.gameover_font.render('GAME  OVER', True, 'red')
            text_rect = text.get_rect(center=(WIDTH // 2, 440))
            self.screen.blit(text, text_rect)
            if self.end_screen_timer > 120:
                hint = self.hint_font.render('Press SPACE', True, 'white')
                hint_rect = hint.get_rect(center=(WIDTH // 2, 480))
                self.screen.blit(hint, hint_rect)
        if self.game_won:
            self.end_screen_timer += 1
            text = self.gameover_font.render('VICTORY!', True, 'green')
            text_rect = text.get_rect(center=(WIDTH // 2, 440))
            self.screen.blit(text, text_rect)
            if self.end_screen_timer > 120:
                hint = self.hint_font.render('Press SPACE', True, 'white')
                hint_rect = hint.get_rect(center=(WIDTH // 2, 480))
                self.screen.blit(hint, hint_rect)

    def has_dot_nearby(self):
        row = self.player.center_y // TILE_HEIGHT
        col = self.player.center_x // TILE_WIDTH
        # Check all 4 adjacent tiles so waka persists through turns
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = row + dr, col + dc
            if 0 <= r < len(self.level) and 0 <= c < len(self.level[0]):
                if self.level[r][c] in (1, 2):
                    return True
        return False

    def check_collisions(self):
        if 0 < self.player.x < 870:
            if self.level[self.player.center_y // TILE_HEIGHT][self.player.center_x // TILE_WIDTH] == 1:
                self.level[self.player.center_y // TILE_HEIGHT][self.player.center_x // TILE_WIDTH] = 0
                self.score += 10
                if self.juice:
                    self.particles.spawn(self.player.center_x, self.player.center_y, (255, 240, 180), n=4)
                self.sound.play_waka()
            elif not self.has_dot_nearby():
                self.sound.stop_waka()
            if self.level[self.player.center_y // TILE_HEIGHT][self.player.center_x // TILE_WIDTH] == 2:
                self.level[self.player.center_y // TILE_HEIGHT][self.player.center_x // TILE_WIDTH] = 0
                self.score += 50
                if self.juice:
                    self.particles.spawn(self.player.center_x, self.player.center_y, (255, 220, 120), n=10)
                    self.shake.kick(4)
                self.powerup = True
                self.power_counter = 0
                self.eaten_ghost = [False, False, False, False]
                self.sound.play_powerup()

    def get_targets(self):
        if self.player.x < 450:
            runaway_x = 900
        else:
            runaway_x = 0
        if self.player.y < 450:
            runaway_y = 900
        else:
            runaway_y = 0
        return_target = SCATTER_RETURN_TARGET
        if self.powerup:
            if not self.blinky.dead and not self.eaten_ghost[0]:
                blink_target = (runaway_x, runaway_y)
            elif not self.blinky.dead and self.eaten_ghost[0]:
                if in_box(self.blinky_x, self.blinky_y, GHOST_BOX_BOUNDS):
                    blink_target = SCATTER_EATEN_TARGET
                else:
                    blink_target = (self.player.x, self.player.y)
            else:
                blink_target = return_target
            if not self.inky.dead and not self.eaten_ghost[1]:
                ink_target = (runaway_x, self.player.y)
            elif not self.inky.dead and self.eaten_ghost[1]:
                if in_box(self.inky_x, self.inky_y, GHOST_BOX_BOUNDS):
                    ink_target = SCATTER_EATEN_TARGET
                else:
                    ink_target = (self.player.x, self.player.y)
            else:
                ink_target = return_target
            if not self.pinky.dead and not self.eaten_ghost[2]:
                pink_target = (self.player.x, runaway_y)
            elif not self.pinky.dead and self.eaten_ghost[2]:
                if in_box(self.pinky_x, self.pinky_y, GHOST_BOX_BOUNDS):
                    pink_target = SCATTER_EATEN_TARGET
                else:
                    pink_target = (self.player.x, self.player.y)
            else:
                pink_target = return_target
            if not self.clyde.dead and not self.eaten_ghost[3]:
                clyd_target = SCATTER_CLYDE_TARGET
            elif not self.clyde.dead and self.eaten_ghost[3]:
                if in_box(self.clyde_x, self.clyde_y, GHOST_BOX_BOUNDS):
                    clyd_target = SCATTER_EATEN_TARGET
                else:
                    clyd_target = (self.player.x, self.player.y)
            else:
                clyd_target = return_target
        else:
            if not self.blinky.dead:
                if in_box(self.blinky_x, self.blinky_y, GHOST_BOX_BOUNDS):
                    blink_target = SCATTER_EATEN_TARGET
                else:
                    blink_target = (self.player.x, self.player.y)
            else:
                blink_target = return_target
            if not self.inky.dead:
                if in_box(self.inky_x, self.inky_y, GHOST_BOX_BOUNDS):
                    ink_target = SCATTER_EATEN_TARGET
                else:
                    ink_target = (self.player.x, self.player.y)
            else:
                ink_target = return_target
            if not self.pinky.dead:
                if in_box(self.pinky_x, self.pinky_y, GHOST_BOX_BOUNDS):
                    pink_target = SCATTER_EATEN_TARGET
                else:
                    pink_target = (self.player.x, self.player.y)
            else:
                pink_target = return_target
            if not self.clyde.dead:
                if in_box(self.clyde_x, self.clyde_y, GHOST_BOX_BOUNDS):
                    clyd_target = SCATTER_EATEN_TARGET
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

        # FAIR-02: refine ONLY the lethal-chase tier (speed == 2, which uniquely
        # marks the chaser in both the default-chase and eaten-revived-during-powerup
        # cases) into an integer-rational step averaging GHOST_CHASE_SPEED_NUM/DEN
        # (1.85) px/frame. Each step floors to {1, 2}; positions stay strict integers.
        # Advance the accumulator only on moving frames so no credit banks across
        # pauses (Pitfall 4); frightened (1) and eyes-return (4) tiers stay untouched
        # (D-08). On non-moving frames the tier is left at 2 but ghosts do not move,
        # so it is inert.
        if self.moving and not self.eat_freeze:
            for i in range(4):
                if self.ghost_speeds[i] == 2:
                    self.ghost_step_acc[i] += GHOST_CHASE_SPEED_NUM
                    step = self.ghost_step_acc[i] // GHOST_CHASE_SPEED_DEN
                    self.ghost_step_acc[i] -= step * GHOST_CHASE_SPEED_DEN
                    self.ghost_speeds[i] = step

    def create_ghosts(self):
        # FEEL-04/D-06/D-08: all juice + threshold + cadence logic lives here (the Ghost
        # is rebuilt every frame and stays dumb). The `self.juice and ...` guard keeps
        # juice=False frames byte-identical (firewall, golden-safe); cadence is purely
        # frame-counter driven (no nondeterministic timing source).
        blink_white = (self.juice and self.powerup
                       and self.power_counter > FRIGHT_FLASH_START
                       and (self.power_counter // FRIGHT_FLASH_INTERVAL) % 2 == 0)
        self.blinky = Ghost(self.blinky_x, self.blinky_y, self.targets[0], self.ghost_speeds[0], self.blinky_img,
                            self.blinky_direction, self.blinky_dead, self.blinky_box, 0,
                            self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level,
                            blink_white=blink_white, spooked_white_img=self.spooked_white_img)
        self.inky = Ghost(self.inky_x, self.inky_y, self.targets[1], self.ghost_speeds[1], self.inky_img,
                          self.inky_direction, self.inky_dead, self.inky_box, 1,
                          self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level,
                          blink_white=blink_white, spooked_white_img=self.spooked_white_img)
        self.pinky = Ghost(self.pinky_x, self.pinky_y, self.targets[2], self.ghost_speeds[2], self.pinky_img,
                           self.pinky_direction, self.pinky_dead, self.pinky_box, 2,
                           self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level,
                           blink_white=blink_white, spooked_white_img=self.spooked_white_img)
        self.clyde = Ghost(self.clyde_x, self.clyde_y, self.targets[3], self.ghost_speeds[3], self.clyde_img,
                           self.clyde_direction, self.clyde_dead, self.clyde_box, 3,
                           self.screen, self.powerup, self.eaten_ghost, self.spooked_img, self.dead_img, self.level,
                           blink_white=blink_white, spooked_white_img=self.spooked_white_img)

    def _ghost_can_exit_box(self, ghost_id):
        delays = [0, BOX_EXIT_DELAY_INKY, BOX_EXIT_DELAY_PINKY, BOX_EXIT_DELAY_CLYDE]
        return self.box_exit_timers[ghost_id] >= delays[ghost_id]

    def move_ghosts(self):
        if not self.blinky_dead and not self.blinky.in_box:
            self.blinky_x, self.blinky_y, self.blinky_direction = self.blinky.move_blinky()
        else:
            self.blinky_x, self.blinky_y, self.blinky_direction = self.blinky.move_clyde()
        if not self.inky_dead and not self.inky.in_box:
            self.inky_x, self.inky_y, self.inky_direction = self.inky.move_inky()
        elif self.inky.in_box and not self.inky_dead and not self._ghost_can_exit_box(1):
            pass
        else:
            self.inky_x, self.inky_y, self.inky_direction = self.inky.move_clyde()
        if not self.pinky_dead and not self.pinky.in_box:
            self.pinky_x, self.pinky_y, self.pinky_direction = self.pinky.move_pinky()
        elif self.pinky.in_box and not self.pinky_dead and not self._ghost_can_exit_box(2):
            pass
        else:
            self.pinky_x, self.pinky_y, self.pinky_direction = self.pinky.move_clyde()
        if self.clyde_dead or not self.clyde.in_box or self._ghost_can_exit_box(3):
            self.clyde_x, self.clyde_y, self.clyde_direction = self.clyde.move_clyde()

    def start_dying(self):
        self.dying = True
        self.dying_delay = 0
        self.death_anim_frame = 0
        self.moving = False
        self.sound.stop_all()
        self.sound.play_death()

    def _draw_death(self, anim_frame=None):
        """Classic arcade wedge collapse — juice-only (D-05, FEEL-01).

        Draws a filled circle minus a growing mouth: the mouth half-angle grows
        from 0 to pi as anim_frame/DEATH_ANIM_FRAMES goes 0->1, so the wedge closes
        to nothing then vanishes. Draw-only overlay; never dereferences player_circle
        (Pitfall 4). Frame-counter + math driven only, with no nondeterministic timing
        source, so the determinism guard stays green (Pitfall 3).
        """
        if anim_frame is None:
            anim_frame = self.death_anim_frame
        cx, cy, r = self.player.center_x, self.player.center_y, 21
        p = min(1.0, anim_frame / DEATH_ANIM_FRAMES)
        mouth = p * math.pi            # half-mouth 0 -> pi (full close)
        if mouth >= math.pi:
            return                     # fully collapsed -> nothing drawn (vanished)
        facing = {0: 0.0, 1: math.pi, 2: -math.pi / 2, 3: math.pi / 2}[self.player.direction]
        pts = [(cx, cy)]
        start, end, steps = facing + mouth, facing + (2 * math.pi - mouth), 24
        for i in range(steps + 1):
            a = start + (end - start) * i / steps
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pygame.draw.polygon(self.screen, (255, 222, 0), pts)

    def _catches(self, ghost, player_circle):
        # FAIR-01: integer center-to-center squared-distance catch (D-01/D-02/D-04).
        # Sample the player from player_circle -- the PRE-move rect actually drawn
        # this frame (game.py draws player+ghosts, THEN moves them). The ghost
        # center is likewise pre-move (set at construction, before move_ghosts), so
        # both sides match the rendered frame. (Previously read self.player.center_*
        # which is post-move -> up to PLAYER_SPEED px skew vs the drawn sprite.)
        # Collisions never run during eat_freeze (guarded in the caller), so the
        # frozen player_circle is never consulted then. No math.sqrt, no float ->
        # the determinism guard stays green. A diagonal corner-kiss reads SAFE.
        dx = player_circle.centerx - ghost.center_x
        dy = player_circle.centery - ghost.center_y
        return dx * dx + dy * dy <= GHOST_CATCH_DISTANCE * GHOST_CATCH_DISTANCE

    def check_ghost_collisions(self, player_circle):
        # Normal ghost kills player
        if not self.powerup:
            if (self._catches(self.blinky, player_circle) and not self.blinky.dead) or \
                    (self._catches(self.inky, player_circle) and not self.inky.dead) or \
                    (self._catches(self.pinky, player_circle) and not self.pinky.dead) or \
                    (self._catches(self.clyde, player_circle) and not self.clyde.dead):
                self.start_dying()

        # Already-eaten ghost kills player during powerup
        if self.powerup and not self.dying:
            if (self._catches(self.blinky, player_circle) and self.eaten_ghost[0] and not self.blinky.dead) or \
                    (self._catches(self.inky, player_circle) and self.eaten_ghost[1] and not self.inky.dead) or \
                    (self._catches(self.pinky, player_circle) and self.eaten_ghost[2] and not self.pinky.dead) or \
                    (self._catches(self.clyde, player_circle) and self.eaten_ghost[3] and not self.clyde.dead):
                self.start_dying()

        # Player eats ghost during powerup
        ghost_eat_checks = [
            (self.blinky, 'blinky_dead', 0, self.blinky_x, self.blinky_y),
            (self.inky, 'inky_dead', 1, self.inky_x, self.inky_y),
            (self.pinky, 'pinky_dead', 2, self.pinky_x, self.pinky_y),
            (self.clyde, 'clyde_dead', 3, self.clyde_x, self.clyde_y),
        ]
        for ghost, dead_attr, idx, gx, gy in ghost_eat_checks:
            if self.powerup and self._catches(ghost, player_circle) and not ghost.dead and not self.eaten_ghost[idx]:
                setattr(self, dead_attr, True)
                self.eaten_ghost[idx] = True
                points = (2 ** self.eaten_ghost.count(True)) * 100
                self.score += points
                self.eat_freeze = True
                self.eat_freeze_timer = 45
                self.eat_freeze_score = points
                self.eat_freeze_pos = (gx, gy)
                self.sound.stop_waka()
                self.sound.pause_powerup()
                self.sound.play_eat_ghost()  # FEEL-03: bite cue, ungated (D-02)
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
                if event.key == pygame.K_SPACE and (self.game_over or self.game_won) and self.end_screen_timer > 120:
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
        was_won = self.game_won
        self.game_won = True
        for i in range(len(self.level)):
            if 1 in self.level[i] or 2 in self.level[i]:
                self.game_won = False
                break
        if self.game_won and not was_won:
            self.sound.stop_all()

    def tick(self):
        """One frame of update — the verbatim body of run()'s while-loop, minus the
        FPS throttle (which stays in run() only, D-17) and the return_to_menu
        early-return. Returns False when a QUIT was received (mirrors handle_events),
        else True, so the interactive run() loop still exits on window close. This is
        the steppable seam the headless harness drives one frame at a time."""
        # Animation counter
        if self.counter < 19:
            self.counter += 1
            if self.counter > 3:
                self.flicker = False
        else:
            self.counter = 0
            self.flicker = True

        # Eat-freeze: brief pause when eating a ghost
        if self.eat_freeze:
            self.eat_freeze_timer -= 1
            if self.eat_freeze_timer <= 0:
                self.eat_freeze = False
                self.sound.unpause_powerup()

        # Powerup timer (don't tick during eat freeze)
        if self.powerup and not self.eat_freeze and self.power_counter < 600:
            self.power_counter += 1
        elif self.powerup and not self.eat_freeze and self.power_counter >= 600:
            self.power_counter = 0
            self.powerup = False
            self.eaten_ghost = [False, False, False, False]
            self.sound.stop_powerup()

        # Starting phase: play start sound, wait until it finishes
        if self.starting and not self.dying and not self.game_over and not self.game_won:
            self.moving = False
            if not self.start_sound_played:
                self.sound.play_start()
                self.start_sound_played = True
            elif not self.sound.is_start_playing():
                self.starting = False
                self.moving = True

        # Dying phase: wait for death sound + 1 sec delay
        if self.dying:
            self.moving = False
            if not self.sound.is_death_playing():
                self.dying_delay += 1
                if self.dying_delay >= 60:
                    self.dying = False
                    self.dying_delay = 0
                    if self.lives > 0:
                        self.lives -= 1
                        self.reset_after_death()
                    else:
                        self.game_over = True

        # Draw
        self.screen.fill('black')
        self.draw_board()
        self.update_ghost_speeds()
        self.check_win()

        if not self.eat_freeze:
            if self.dying and self.juice:
                # FEEL-01 (D-05): wedge-collapse overlay replaces the held player
                # sprite, but ONLY under juice. The counter increment lives strictly
                # inside this juice branch so the juice=False dying sim/render stays
                # byte-identical and the death golden/frame-hash net needs no re-bless.
                self.death_anim_frame += 1
                self._draw_death(self.death_anim_frame)
            else:
                player_circle = self.player.draw(self.counter)
        self.create_ghosts()
        self.draw_misc()
        self.draw_ready()
        if self.eat_freeze:
            gx, gy = self.eat_freeze_pos
            if self.juice:
                # bloom burst behind the score pop; do NOT black out the eyes —
                # draw the pop in glowing pixel font over a soft halo.
                juice.glow_circle(self.screen, (gx + 23, gy + 24), (120, 200, 255), 16, glow=2.6)
                pop = theme.pixel_font(theme.SIZE_BODY).render(str(self.eat_freeze_score), True, (180, 230, 255))
                self.screen.blit(pop, pop.get_rect(center=(gx + 23, gy + 24)))
                self.shake.kick(6)
            else:
                pygame.draw.rect(self.screen, 'black', (gx, gy, 45, 45))
                score_text = self.score_popup_font.render(str(self.eat_freeze_score), True, 'cyan')
                score_rect = score_text.get_rect(center=(gx + 23, gy + 24))
                self.screen.blit(score_text, score_rect)
        self.targets = self.get_targets()

        # Tick box exit timers while gameplay is active
        if self.moving and not self.eat_freeze:
            for i in range(4):
                self.box_exit_timers[i] += 1

        self.player.check_position(self.level)
        if self.moving and not self.eat_freeze:
            self.player.move()
            self.move_ghosts()
        if not self.dying and not self.eat_freeze and not self.starting:
            self.check_collisions()
            self.check_ghost_collisions(player_circle)

        # Input
        running = self.handle_events()
        self.player.update_direction()
        self.player.wrap_around()
        self.check_ghost_in_box()

        if self.juice:
            self.particles.update(1.0 / FPS)
            self.particles.draw(self.screen)

        self.present_fn()
        return running

    def run(self):
        running = True
        while running:
            if self.return_to_menu:
                self.sound.stop_all()
                return {"score": self.score, "game_won": self.game_won}
            self.timer.tick(FPS)
            running = self.tick()

        self.sound.stop_all()
        return None
