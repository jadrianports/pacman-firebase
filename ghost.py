import pygame
from collections import namedtuple
from settings import TILE_HEIGHT, TILE_WIDTH, HALF_TILE, BOARD_COLS
from geometry import in_box, GHOST_BOX_BOUNDS


# --------------------------------------------------------------------------- #
# Data-driven ghost mover (REF-02).                                           #
#                                                                             #
# The four movers (move_blinky/inky/pinky/clyde) were ~90% identical: a       #
# per-direction `if direction==0/1/2/3` switch, each with three branches —    #
#                                                                             #
#   1. PRIMARY     : keep pursuing along the current axis (the leading        #
#                    if/elif, varies per ghost).                              #
#   2. BLOCKED     : `elif not self.turns[d]:` — an ordered fall-through       #
#                    ladder of target-seeking then any-open moves. This is    #
#                    the TABULAR ~90% and lives as data (blocked_ladder).     #
#   3. FORWARD-OPEN: `elif self.turns[d]:` — what to do when forward is still  #
#                    open but the primary did not fire (varies per ghost).    #
#                                                                             #
# PRIMARY and FORWARD-OPEN are genuine control-flow quirks (Q-a/Q-b/Q-c), so  #
# they stay as small named hook functions, NOT data (D-01). Each hook takes   #
# the ghost `g` and returns FIRED (it took the branch / moved) or NOT_HANDLED #
# (fall through). The blocked ladder is walked by `_move` itself.             #
#                                                                             #
# Direction key: 0=Right, 1=Left, 2=Up, 3=Down.                               #
# --------------------------------------------------------------------------- #

DirectionRule = namedtuple("DirectionRule", ["primary", "blocked_ladder", "forward_open"])

FIRED = True
NOT_HANDLED = False


# --- blocked-ladder step conditions ---------------------------------------- #
# Each blocked-ladder step is (cond, want_dir). `cond` is one of the four
# target-sign predicates below, or None for the bare `turns[want_dir]` tail.
def _ty_gt(g):  # target is below  (target[1] > y_pos) -> seek DOWN
    return g.target[1] > g.y_pos


def _ty_lt(g):  # target is above  (target[1] < y_pos) -> seek UP
    return g.target[1] < g.y_pos


def _tx_gt(g):  # target is right  (target[0] > x_pos) -> seek RIGHT
    return g.target[0] > g.x_pos


def _tx_lt(g):  # target is left   (target[0] < x_pos) -> seek LEFT
    return g.target[0] < g.x_pos


# The blocked-ladder orderings, read verbatim out of the OLD movers.
# dir-0 and dir-1 ladders are IDENTICAL across all four ghosts. dir-2 AND dir-3
# each have TWO variants: blinky's any-open tail differs from the other three.
#   dir-2: blinky t3,t0,t1  vs  others t1,t3,t0  (LANDMINE)
#   dir-3: blinky t2,t0,t1  vs  others t2,t1,t0  (LANDMINE — the oracle caught
#          this; RESEARCH FOCUS-1 / assumption A4 wrongly called dir-3 uniform).
_LADDER_DIR0 = ((_ty_gt, 3), (_ty_lt, 2), (_tx_lt, 1), (None, 3), (None, 2), (None, 1))
_LADDER_DIR1 = ((_ty_gt, 3), (_ty_lt, 2), (_tx_gt, 0), (None, 3), (None, 2), (None, 0))
_LADDER_DIR2_BLINKY = ((_tx_gt, 0), (_tx_lt, 1), (_ty_gt, 3), (None, 3), (None, 0), (None, 1))
_LADDER_DIR2_OTHER = ((_tx_gt, 0), (_tx_lt, 1), (_ty_gt, 3), (None, 1), (None, 3), (None, 0))
_LADDER_DIR3_BLINKY = ((_tx_gt, 0), (_tx_lt, 1), (_ty_lt, 2), (None, 2), (None, 0), (None, 1))
_LADDER_DIR3_OTHER = ((_tx_gt, 0), (_tx_lt, 1), (_ty_lt, 2), (None, 2), (None, 1), (None, 0))


# --- movement primitives --------------------------------------------------- #
def _go(g, direction):
    """Set facing `direction` and advance one `speed` step along it."""
    g.direction = direction
    if direction == 0:
        g.x_pos += g.speed
    elif direction == 1:
        g.x_pos -= g.speed
    elif direction == 2:
        g.y_pos -= g.speed
    else:  # 3
        g.y_pos += g.speed


# --- PRIMARY hooks --------------------------------------------------------- #
# "Keep pursuing along the current axis." Return FIRED if the leading
# if/elif chain took a branch (so `_move` skips the blocked/forward-open
# branches), else NOT_HANDLED.

def primary_advance_right(g):
    """dir-0 primary (all ghosts): if target is right and right is open, step right."""
    if _tx_gt(g) and g.turns[0]:
        g.x_pos += g.speed
        return FIRED
    return NOT_HANDLED


def primary_advance_left(g):
    """dir-1 primary (blinky/clyde): if target is left and left is open, step left."""
    if _tx_lt(g) and g.turns[1]:
        g.x_pos -= g.speed
        return FIRED
    return NOT_HANDLED


def primary_turn_no_move_down_then_left(g):
    """dir-1 primary (inky, Q-b): turn to face DOWN with NO advance this frame
    if target is below and down is open; else if target is left and left is open,
    step left."""
    if _ty_gt(g) and g.turns[3]:
        g.direction = 3
        return FIRED
    elif _tx_lt(g) and g.turns[1]:
        g.x_pos -= g.speed
        return FIRED
    return NOT_HANDLED


def primary_turn_and_move_down_then_left(g):
    """dir-1 primary (pinky, Q-b): turn DOWN and advance if target is below and
    down is open; else if target is left and left is open, step left."""
    if _ty_gt(g) and g.turns[3]:
        g.direction = 3
        g.y_pos += g.speed
        return FIRED
    elif _tx_lt(g) and g.turns[1]:
        g.x_pos -= g.speed
        return FIRED
    return NOT_HANDLED


def primary_advance_up(g):
    """dir-2 primary (blinky/inky): if target is above and up is open, step up."""
    if _ty_lt(g) and g.turns[2]:
        g.direction = 2
        g.y_pos -= g.speed
        return FIRED
    return NOT_HANDLED


def primary_seek_left_then_up(g):
    """dir-2 primary (clyde/pinky): if target is left and left is open, turn left
    and step; else if target is above and up is open, step up."""
    if _tx_lt(g) and g.turns[1]:
        g.direction = 1
        g.x_pos -= g.speed
        return FIRED
    elif _ty_lt(g) and g.turns[2]:
        g.direction = 2
        g.y_pos -= g.speed
        return FIRED
    return NOT_HANDLED


def primary_advance_down(g):
    """dir-3 primary (all ghosts): if target is below and down is open, step down."""
    if _ty_gt(g) and g.turns[3]:
        g.y_pos += g.speed
        return FIRED
    return NOT_HANDLED


# --- FORWARD-OPEN hooks ---------------------------------------------------- #
# Reached when the primary did not fire AND forward (turns[d]) is still open.

def forward_straight_right(g):
    """blinky/pinky dir-0 forward-open: just continue right."""
    g.x_pos += g.speed
    return FIRED


def forward_straight_left(g):
    """blinky/pinky dir-1 forward-open: just continue left."""
    g.x_pos -= g.speed
    return FIRED


def forward_straight_up(g):
    """blinky/inky dir-2 forward-open: just continue up."""
    g.y_pos -= g.speed
    return FIRED


def forward_straight_down(g):
    """blinky/inky dir-3 forward-open: just continue down."""
    g.y_pos += g.speed
    return FIRED


def forward_seek_perp_y_right(g):
    """clyde/inky dir-0 forward-open (Q-c): `if … if … else` override — the second
    `if` can override the first within the frame; the final `else` binds ONLY to
    the second `if`. Transcribed as literal Python, NOT an elif ladder."""
    if _ty_gt(g) and g.turns[3]:
        g.direction = 3
        g.y_pos += g.speed
    if _ty_lt(g) and g.turns[2]:
        g.direction = 2
        g.y_pos -= g.speed
    else:
        g.x_pos += g.speed
    return FIRED


def forward_seek_perp_y_left(g):
    """clyde/inky dir-1 forward-open (Q-c): same `if … if … else` override shape,
    falling through to a left step."""
    if _ty_gt(g) and g.turns[3]:
        g.direction = 3
        g.y_pos += g.speed
    if _ty_lt(g) and g.turns[2]:
        g.direction = 2
        g.y_pos -= g.speed
    else:
        g.x_pos -= g.speed
    return FIRED


def forward_seek_perp_x_up(g):
    """clyde/pinky dir-2 forward-open: opportunistically turn toward target's x,
    else continue up. (elif chain in the original — not a Q-c override.)"""
    if _tx_gt(g) and g.turns[0]:
        g.direction = 0
        g.x_pos += g.speed
    elif _tx_lt(g) and g.turns[1]:
        g.direction = 1
        g.x_pos -= g.speed
    else:
        g.y_pos -= g.speed
    return FIRED


def forward_seek_perp_x_down(g):
    """clyde/pinky dir-3 forward-open: opportunistically turn toward target's x,
    else continue down. (elif chain in the original — not a Q-c override.)"""
    if _tx_gt(g) and g.turns[0]:
        g.direction = 0
        g.x_pos += g.speed
    elif _tx_lt(g) and g.turns[1]:
        g.direction = 1
        g.x_pos -= g.speed
    else:
        g.y_pos += g.speed
    return FIRED


# --- per-ghost profiles (dict[int, DirectionRule] keyed by direction 0-3) --- #

# blinky: turns whenever colliding with walls, otherwise continues straight.
BLINKY_PROFILE = {
    0: DirectionRule(primary_advance_right, _LADDER_DIR0, forward_straight_right),
    1: DirectionRule(primary_advance_left, _LADDER_DIR1, forward_straight_left),
    2: DirectionRule(primary_advance_up, _LADDER_DIR2_BLINKY, forward_straight_up),
    3: DirectionRule(primary_advance_down, _LADDER_DIR3_BLINKY, forward_straight_down),
}

# inky: turns up or down at any point to pursue, but left/right only on collision.
INKY_PROFILE = {
    0: DirectionRule(primary_advance_right, _LADDER_DIR0, forward_seek_perp_y_right),
    1: DirectionRule(primary_turn_no_move_down_then_left, _LADDER_DIR1, forward_seek_perp_y_left),
    2: DirectionRule(primary_advance_up, _LADDER_DIR2_OTHER, forward_straight_up),
    3: DirectionRule(primary_advance_down, _LADDER_DIR3_OTHER, forward_straight_down),
}

# pinky: turns left or right whenever advantageous, but only up/down on collision.
PINKY_PROFILE = {
    0: DirectionRule(primary_advance_right, _LADDER_DIR0, forward_straight_right),
    1: DirectionRule(primary_turn_and_move_down_then_left, _LADDER_DIR1, forward_straight_left),
    2: DirectionRule(primary_seek_left_then_up, _LADDER_DIR2_OTHER, forward_seek_perp_x_up),
    3: DirectionRule(primary_advance_down, _LADDER_DIR3_OTHER, forward_seek_perp_x_down),
}

# clyde: turns whenever advantageous for pursuit.
CLYDE_PROFILE = {
    0: DirectionRule(primary_advance_right, _LADDER_DIR0, forward_seek_perp_y_right),
    1: DirectionRule(primary_turn_no_move_down_then_left, _LADDER_DIR1, forward_seek_perp_y_left),
    2: DirectionRule(primary_seek_left_then_up, _LADDER_DIR2_OTHER, forward_seek_perp_x_up),
    3: DirectionRule(primary_advance_down, _LADDER_DIR3_OTHER, forward_seek_perp_x_down),
}


class Ghost:
    def __init__(self, x_coord, y_coord, target, speed, img, direct, dead, box, id,
                 screen, powerup, eaten_ghost, spooked_img, dead_img, level):
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
        self.powerup = powerup
        self.eaten_ghost = eaten_ghost
        self.spooked_img = spooked_img
        self.dead_img = dead_img
        self.level = level
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

    def _tile(self, row, col):
        row = max(0, min(len(self.level) - 1, row))
        col = max(0, min(len(self.level[0]) - 1, col))
        return self.level[row][col]

    def check_collisions(self):
        # R, L, U, D
        # Tile dims centralized in settings (TILE_HEIGHT was num1, TILE_WIDTH was num2,
        # HALF_TILE was num3). Byte-identical: (HEIGHT-50)//32==28, WIDTH//30==30, 15.
        self.turns = [False, False, False, False]
        if 0 < self.center_x // TILE_WIDTH < BOARD_COLS - 1:
            if self._tile((self.center_y - HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) == 9:
                self.turns[2] = True
            if self._tile(self.center_y // TILE_HEIGHT, (self.center_x - HALF_TILE) // TILE_WIDTH) < 3 \
                    or (self._tile(self.center_y // TILE_HEIGHT, (self.center_x - HALF_TILE) // TILE_WIDTH) == 9 and (
                    self.in_box or self.dead)):
                self.turns[1] = True
            if self._tile(self.center_y // TILE_HEIGHT, (self.center_x + HALF_TILE) // TILE_WIDTH) < 3 \
                    or (self._tile(self.center_y // TILE_HEIGHT, (self.center_x + HALF_TILE) // TILE_WIDTH) == 9 and (
                    self.in_box or self.dead)):
                self.turns[0] = True
            if self._tile((self.center_y + HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) < 3 \
                    or (self._tile((self.center_y + HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) == 9 and (
                    self.in_box or self.dead)):
                self.turns[3] = True
            if self._tile((self.center_y - HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) < 3 \
                    or (self._tile((self.center_y - HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) == 9 and (
                    self.in_box or self.dead)):
                self.turns[2] = True

            if self.direction == 2 or self.direction == 3:
                if 12 <= self.center_x % TILE_WIDTH <= 18:
                    if self._tile((self.center_y + HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) < 3 \
                            or (self._tile((self.center_y + HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if self._tile((self.center_y - HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) < 3 \
                            or (self._tile((self.center_y - HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % TILE_HEIGHT <= 18:
                    if self._tile(self.center_y // TILE_HEIGHT, (self.center_x - HALF_TILE) // TILE_WIDTH) < 3 \
                            or (self._tile(self.center_y // TILE_HEIGHT, (self.center_x - HALF_TILE) // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if self._tile(self.center_y // TILE_HEIGHT, (self.center_x + HALF_TILE) // TILE_WIDTH) < 3 \
                            or (self._tile(self.center_y // TILE_HEIGHT, (self.center_x + HALF_TILE) // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True

            if self.direction == 0 or self.direction == 1:
                if 12 <= self.center_x % TILE_WIDTH <= 18:
                    if self._tile((self.center_y + HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) < 3 \
                            or (self._tile((self.center_y + HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[3] = True
                    if self._tile((self.center_y - HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) < 3 \
                            or (self._tile((self.center_y - HALF_TILE) // TILE_HEIGHT, self.center_x // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[2] = True
                if 12 <= self.center_y % TILE_HEIGHT <= 18:
                    if self._tile(self.center_y // TILE_HEIGHT, (self.center_x - HALF_TILE) // TILE_WIDTH) < 3 \
                            or (self._tile(self.center_y // TILE_HEIGHT, (self.center_x - HALF_TILE) // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[1] = True
                    if self._tile(self.center_y // TILE_HEIGHT, (self.center_x + HALF_TILE) // TILE_WIDTH) < 3 \
                            or (self._tile(self.center_y // TILE_HEIGHT, (self.center_x + HALF_TILE) // TILE_WIDTH) == 9 and (
                            self.in_box or self.dead)):
                        self.turns[0] = True
        else:
            self.turns[0] = True
            self.turns[1] = True
        if in_box(self.x_pos, self.y_pos, GHOST_BOX_BOUNDS):
            self.in_box = True
        else:
            self.in_box = False
        return self.turns, self.in_box

    def _move(self, profile):
        # r, l, u, d
        # Unified data-driven mover (REF-02). Consumes a per-ghost profile
        # (dict[int, DirectionRule] keyed by direction). For the current
        # direction: try the PRIMARY hook; if it did not fire, either walk the
        # BLOCKED ladder (forward closed) or run the FORWARD-OPEN hook (forward
        # open). Then apply the shared trailing wrap clamp once and return the
        # canonical (x_pos, y_pos, direction) tuple.
        rule = profile[self.direction]
        if rule.primary(self) != FIRED:
            if not self.turns[self.direction]:
                for cond, want_dir in rule.blocked_ladder:
                    if cond is None:
                        if self.turns[want_dir]:
                            _go(self, want_dir)
                            break
                    elif cond(self) and self.turns[want_dir]:
                        _go(self, want_dir)
                        break
            elif self.turns[self.direction]:
                rule.forward_open(self)
        if self.x_pos < -30:
            self.x_pos = 900
        elif self.x_pos > 900:
            self.x_pos = -30
        return self.x_pos, self.y_pos, self.direction

    def move_blinky(self):
        return self._move(BLINKY_PROFILE)

    def move_inky(self):
        return self._move(INKY_PROFILE)

    def move_pinky(self):
        return self._move(PINKY_PROFILE)

    def move_clyde(self):
        return self._move(CLYDE_PROFILE)
