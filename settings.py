import math

WIDTH = 900
HEIGHT = 950
FPS = 60
PLAYER_SPEED = 2
PI = math.pi

# Initial player position
PLAYER_START_X = 450
PLAYER_START_Y = 663
PLAYER_START_DIR = 0

# Initial ghost positions and directions
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

# Menu colors
COLOR_YELLOW = (255, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GRAY = (128, 128, 128)
COLOR_RED = (255, 0, 0)
COLOR_GREEN = (0, 255, 0)

# Font sizes
FONT_TITLE = 64
FONT_MENU = 36
FONT_SMALL = 24

# Menu options
MENU_OPTIONS = ["Play", "Leaderboard", "Quit"]

# API - Cloud Run function URLs
API_SUBMIT_SCORE_URL = "https://pacman-991339031546.asia-southeast1.run.app"
API_LEADERBOARD_URL = "https://get-leaderboard-991339031546.asia-southeast1.run.app"
