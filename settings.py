import math

WIDTH = 900
HEIGHT = 950
FPS = 60
PLAYER_SPEED = 2
PI = math.pi

# Tile geometry (was inline num1/num2/num3 recomputed in game/ghost/player).
# Derived once from named board dims (D-12) so the mysterious 32/30/50 are documented.
# Byte-identical to the old literals: (950-50)//32 == 28, 900//30 == 30.
BOARD_ROWS = 32
BOARD_COLS = 30
HUD_HEIGHT = 50
TILE_HEIGHT = (HEIGHT - HUD_HEIGHT) // BOARD_ROWS   # 28  (was num1 — tile HEIGHT, indexes rows)
TILE_WIDTH = WIDTH // BOARD_COLS                    # 30  (was num2 — tile WIDTH, indexes cols)
HALF_TILE = 15                                      # look-ahead offset (was num3)

# Wrap edges — kept DELIBERATELY DISTINCT (D-13). Ghost and player wrap thresholds
# differ; naming the look-alikes separately guards against accidental future unification.
GHOST_WRAP_LEFT = -30        # ghost.py move_* tail: if x_pos < -30 ...
GHOST_WRAP_RIGHT = 900       # ... elif x_pos > 900: x_pos = -30
PLAYER_WRAP_RIGHT_EDGE = 900  # player.py wrap_around: if x > 900 ...
PLAYER_WRAP_RIGHT_TO = -47    # ... x = -47
PLAYER_WRAP_LEFT_EDGE = -50   # elif x < -50 ...
PLAYER_WRAP_LEFT_TO = 897     # ... x = 897

# Scatter / fixed targets (D-13) — kept as SEPARATE named constants.
SCATTER_RETURN_TARGET = (380, 400)   # eyes-return target toward the box gate
SCATTER_EATEN_TARGET = (400, 100)    # eaten-ghost in-box scatter target
SCATTER_CLYDE_TARGET = (450, 450)    # clyde's non-powerup scatter corner

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

PINKY_START_X = 400
PINKY_START_Y = 438
PINKY_START_DIR = 2

CLYDE_START_X = 480
CLYDE_START_Y = 438
CLYDE_START_DIR = 2

# Box exit delays (frames) - ghosts wait before exiting the box
BOX_EXIT_DELAY_INKY = 0
BOX_EXIT_DELAY_PINKY = 30
BOX_EXIT_DELAY_CLYDE = 60

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

# Per-user identity storage (Phase 5, D-01).
# IDENTITY_DIR_NAME is the exact folder name under %LOCALAPPDATA% on Windows.
# IDENTITY_FILE_NAME is the single consolidated obfuscated+signed identity blob.
# The HMAC secret is NOT stored here (D-09 — baked at build time, never a committed literal).
IDENTITY_DIR_NAME = "PacMan"
IDENTITY_FILE_NAME = "identity.dat"

# Build/dev HMAC secret filename (D-09). This is the FILENAME only — the gitignored
# hmac_secret.local holds the real value (never committed). build.py reads it at build
# time and bakes it non-literally; dev runs read it directly via main._load_hmac_secret.
HMAC_SECRET_FILE_NAME = "hmac_secret.local"
