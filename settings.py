import math

WIDTH = 900
HEIGHT = 950
FPS = 60
PI = math.pi
BOARD_COLOR = 'blue'

PLAYER_SPEED = 2
GHOST_SPEED_NORMAL = 2
GHOST_SPEED_FRIGHTENED = 1
GHOST_SPEED_DEAD = 4

# Initial positions
PLAYER_START_X = 450
PLAYER_START_Y = 663

BLINKY_START_X = 56
BLINKY_START_Y = 58
BLINKY_START_DIR = 0

INKY_START_X = 440
INKY_START_Y = 388
INKY_START_DIR = 2

PINKY_START_X = 440
PINKY_START_Y = 438
PINKY_START_DIR = 2

CLYDE_START_X = 440
CLYDE_START_Y = 438
CLYDE_START_DIR = 2

# Ghost modes
SCATTER = 0
CHASE = 1

# Mode timing pattern (seconds): alternating scatter/chase phases
# After all phases complete, ghosts enter permanent chase
MODE_TIMES = [7, 20, 7, 20, 5, 20, 5]

# Frightened mode duration (seconds)
FRIGHTENED_DURATION = 6

# Scatter corner targets (pixel coordinates)
BLINKY_SCATTER = (WIDTH - 30, 0)         # upper-right
PINKY_SCATTER = (0, 0)                    # upper-left
INKY_SCATTER = (WIDTH - 30, HEIGHT - 50)  # lower-right
CLYDE_SCATTER = (0, HEIGHT - 50)          # lower-left

# Ghost box return target
GHOST_RETURN_TARGET = (380, 400)

# Clyde's shy radius (pixels) - switches to scatter target when closer than this
CLYDE_SHY_RADIUS = 8 * 30  # 8 tiles * 30 pixels per tile
