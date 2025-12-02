import math

# Screen settings
WIDTH = 900
HEIGHT = 950
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 0, 255) # or 'blue'
RED = (255, 0, 0)
GREEN = (0, 255, 0)
TEXT_COLOR = WHITE

# Font settings
FONT_SIZE = 20

# Game Physics
PI = math.pi
PLAYER_SPEED = 2
GHOST_SPEED = 2

# Calculations for grid size based on your original code
# (HEIGHT - 50 padding) // 32 rows
TILE_HEIGHT = (HEIGHT - 50) // 32
# WIDTH // 30 columns
TILE_WIDTH = WIDTH // 30


FUDGE_FACTOR = 15