## ghost.PY
import pygame
from settings import *

class Ghost:
    def __init__(self, ghost_type):
        """
        ghost_type: string ID ('blinky','pinky','inky','clyde')
        """

        self.ghost_type = ghost_type
        self.target = (0, 0)
        # default starting positions (you can edit these later)
        start_positions = {
            "blinky": (56, 58),
            "inky":   (440, 388),
            "pinky":  (440, 438),
            "clyde":  (440, 438)
        }

        self.x, self.y = start_positions[ghost_type]

        # core state
        self.direction = 0
        self.speed = GHOST_SPEED
        self.dead = False
        self.in_box = False
        # self.turns, self.in_box = self.check_collisions()
        self.id = ["blinky", "pinky", "inky", "clyde"].index(ghost_type)

        # load sprites
        self.load_images()

        # rect for collision
        self.rect = pygame.Rect(self.get_center()[0] - 18,
                                self.get_center()[1] - 18,
                                36, 36)

    # -------------------------------------------------------------
    # IMAGE LOADING
    # -------------------------------------------------------------

    def load_images(self):
        """Loads ghost sprites from folder based on ghost type."""

        color_map = {
            "blinky": "red",
            "pinky": "pink",
            "inky": "blue",
            "clyde": "orange"
        }

        color = color_map[self.ghost_type]

        # normal colored ghost
        normal_img = pygame.image.load(f"assets/ghosts/{color}.png")

        # load & scale all needed frames
        self.img_normal = pygame.transform.scale(normal_img, (45, 45))
        self.img_spooked = pygame.transform.scale(
            pygame.image.load("assets/ghosts/powerup.png"), (45, 45)
        )
        self.img_dead = pygame.transform.scale(
            pygame.image.load("assets/ghosts/dead.png"), (45, 45)
        )


    # -------------------------------------------------------------
    # HELPER FUNCTIONS
    # -------------------------------------------------------------

    def get_center(self):
        return self.x + 22, self.y + 22


    # -------------------------------------------------------------
    # DRAWING
    # -------------------------------------------------------------

    def draw(self, screen, powerup_active, eaten_list):
        """Draw ghost depending on current state + powerup state."""

        if self.dead:
            img = self.img_dead

        else:
            if powerup_active:
                if eaten_list[self.id]:
                    img = self.img_normal    # recovering ghost → normal color
                else:
                    img = self.img_spooked   # vulnerable
            else:
                img = self.img_normal

        # draw sprite
        screen.blit(img, (self.x, self.y))

        # update rect for collisions
        cx, cy = self.get_center()
        self.rect.x = cx - 18
        self.rect.y = cy - 18


    # -------------------------------------------------------------
    # COLLISIONS
    # -------------------------------------------------------------
    def check_collisions(self, level):
        # update center first
        center_x, center_y = self.get_center()

        # R, L, U, D
        self.turns = [False, False, False, False]

        if 0 < center_x // 30 < 29:
            if level[(center_y - FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] == 9:
                self.turns[2] = True
            if level[center_y // TILE_HEIGHT][(center_x - FUDGE_FACTOR) // TILE_WIDTH] < 3 \
                    or (level[center_y // TILE_HEIGHT][(center_x - FUDGE_FACTOR) // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True
            if level[center_y // TILE_HEIGHT][(center_x + FUDGE_FACTOR) // TILE_WIDTH] < 3 \
                    or (level[center_y // TILE_HEIGHT][(center_x + FUDGE_FACTOR) // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True
            if level[(center_y + FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] < 3 \
                    or (level[(center_y + FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True
            if level[(center_y - FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] < 3 \
                    or (level[(center_y - FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            # additional logic based on direction
            if self.direction == 2 or self.direction == 3:
                if 12 <= center_x % TILE_WIDTH <= 18:
                    if level[(center_y + FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] < 3 \
                            or (level[(center_y + FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(center_y - FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] < 3 \
                            or (level[(center_y - FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= center_y % TILE_HEIGHT <= 18:
                    if level[center_y // TILE_HEIGHT][(center_x - TILE_WIDTH) // TILE_WIDTH] < 3 \
                            or (level[center_y // TILE_HEIGHT][(center_x - TILE_WIDTH) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[center_y // TILE_HEIGHT][(center_x + TILE_WIDTH) // TILE_WIDTH] < 3 \
                            or (level[center_y // TILE_HEIGHT][(center_x + TILE_WIDTH) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            if self.direction == 0 or self.direction == 1:
                if 12 <= center_x % TILE_WIDTH <= 18:
                    if level[(center_y + FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] < 3 \
                            or (level[(center_y + FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if level[(center_y - FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] < 3 \
                            or (level[(center_y - FUDGE_FACTOR) // TILE_HEIGHT][center_x // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= center_y % TILE_HEIGHT <= 18:
                    if level[center_y // TILE_HEIGHT][(center_x - FUDGE_FACTOR) // TILE_WIDTH] < 3 \
                            or (level[center_y // TILE_HEIGHT][(center_x - FUDGE_FACTOR) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if level[center_y // TILE_HEIGHT][(center_x + FUDGE_FACTOR) // TILE_WIDTH] < 3 \
                            or (level[center_y // TILE_HEIGHT][(center_x + FUDGE_FACTOR) // TILE_WIDTH] == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True
        else:
            self.turns[0] = True
            self.turns[1] = True

        # box check
        self.in_box = 350 < self.x < 550 and 370 < self.y < 480

        return self.turns, self.in_box

    def move_clyde(self):
        tx, ty = self.target

        # shorthand
        x, y, d = self.x, self.y, self.direction
        t = self.turns
        s = self.speed

        if d == 0:  # RIGHT
            if tx > x and t[0]:
                x += s
            elif not t[0]:
                if ty > y and t[3]:
                    d= 3
                    y += s
                elif ty < y and t[2]:
                    d=  2
                    y -= s
                elif tx < x and t[1]:
                    d = 1
                    x -= s
                elif t[3]:
                    d = 3
                    y += s
                elif t[2]:
                    d = 2
                    y -= s
                elif t[1]:
                    d = 1
                    x -= s
            elif t[0]:
                if ty >y and t[3]:
                    d = 3
                    y += s
                if ty < y and t[2]:
                    d = 2
                    y -= s
                else:
                    x += s

        elif d == 1:  # LEFT
            if ty > y and t[3]:
                d = 3
            elif tx < x and t[1]:
                x -= s
            elif not t[1]:
                if ty > y and t[3]:
                    d = 3
                    y += s
                elif ty < y and t[2]:
                    d = 2
                    y -= s
                elif tx > x and t[0]:
                    d = 0
                    x += s
                elif t[3]:
                    d = 3
                    y += s
                elif t[2]:
                    d = 2
                    y -= s
                elif t[0]:
                    d = 0
                    x += s
            elif t[1]:
                if ty > y and t[3]:
                    d = 3
                    y += s
                if ty < y and t[2]:
                    d = 2
                    y -= s
                else:
                    x -= s

        elif d == 2:  # UP
            if tx < x and t[1]:
                d = 1
                x -= s
            elif ty < y and t[2]:
                d = 2
                y -= s
            elif not t[2]:
                if tx > x and t[0]:
                    d = 0
                    x += s
                elif tx < x and t[1]:
                    d= 1
                    x -= s
                elif ty > y and t[3]:
                    d = 3
                    y += s
                elif t[1]:
                    d = 1
                    x -= s
                elif t[3]:
                    d = 3
                    y += s
                elif t[0]:
                    d = 0
                    x += s
            elif t[2]:
                if tx > x and t[0]:
                    d = 0
                    x += s
                elif tx < x and t[1]:
                    d = 1
                    x -= s
                else:
                    y -= s

        elif d == 3:  # DOWN
            if ty > y and t[3]:
                y += s
            elif not t[3]:
                if tx > x and t[0]:
                    d = 0
                    x += s
                elif tx < x and t[1]:
                    d = 1
                    x -= s
                elif ty < y and t[2]:
                    d = 2
                    y -= s
            elif t[3]:
                if tx > x and t[0]:
                    d = 0
                    x += s
                elif tx < x and t[1]:
                    d = 1
                    x -= s
                else:
                    y += s

        # tunnel wrap
        if x < -30:
            x = 900
        elif x > 900:
            x = -30

        self.x, self.y, self.direction = x, y, d
        return self.x, self.y, self.direction

    def update_target(self, blinky, inky, pinky, clyde, player_x, player_y, powerup, eaten_ghost):
        blink_x, blink_y = blinky.x, blinky.y
        ink_x, ink_y = inky.x, inky.y
        pink_x, pink_y = pinky.x, pinky.y
        clyd_x, clyd_y = clyde.x, clyde.y

        runaway_x = 900 if player_x < 450 else 0
        runaway_y = 900 if player_y < 450 else 0
        return_target = (380, 400)

        targets = []
        for g_id, g_x, g_y, dead in zip(range(4),
                                        [blink_x, ink_x, pink_x, clyd_x],
                                        [blink_y, ink_y, pink_y, clyd_y],
                                        [blinky.dead, inky.dead, pinky.dead, clyde.dead]):
            if powerup:
                if not dead and not eaten_ghost[g_id]:
                    tgt = (runaway_x, runaway_y) if g_id == 0 else \
                        (runaway_x, player_y) if g_id == 1 else \
                            (player_x, runaway_y) if g_id == 2 else \
                                (450, 450)
                elif not dead and eaten_ghost[g_id]:
                    tgt = (400, 100) if 340 < g_x < 560 and 340 < g_y < 500 else (player_x, player_y)
                else:
                    tgt = return_target
            else:
                if not dead:
                    tgt = (400, 100) if 340 < g_x < 560 and 340 < g_y < 500 else (player_x, player_y)
                else:
                    tgt = return_target
            targets.append(tgt)

        self.target = targets[self.id]

        # ---------------- CLYDE MOVEMENT ----------------

    def reset(self, x ,y ,direction):
        self.x = x
        self.y = y
        self.direction = direction
        self.dead = False
        self.in_box = True
