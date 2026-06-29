import math

# Shipped app version (PEP440). tufup compares this to the signed update metadata
# to decide whether a newer build is available. Bump on every release.
APP_VERSION = "1.0.0"

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

# Leaderboard row layout: total character budget for "rank initials dots score".
# The dot-fill is clamped to >= 0 against this width so an unbounded server score or
# longer-than-expected initials never produce a negative repeat count (WR-03).
LEADERBOARD_LINE_WIDTH = 30

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

# Phase 6 — in-game weekly boards & got-passed banner.
# MARKER_FILE_NAME (D-13): the unsigned plain-JSON last-viewed marker under
#   %LOCALAPPDATA%\PacMan\ — the deliberate INVERSE of the identity blob (no obfuscation,
#   no HMAC; a missing/corrupt/wrong-week marker is harmless and silently re-baselines).
# BANNER_FETCH_TIMEOUT_SECONDS (D-09 / UI-SPEC): the short launch-fetch timeout for the
#   got-passed banner — NOT the 10s in-board default.
# BANNER_NAME_CAP (D-06 / UI-SPEC): max passer initials shown before "+K more".
MARKER_FILE_NAME = "last_viewed.json"
BANNER_FETCH_TIMEOUT_SECONDS = 2
BANNER_NAME_CAP = 3

# Phase 8 - Fairness Pass tunables (D-03/D-07/D-09). Each is a D-10 playtest dial:
# trivially editable here, no inline magic numbers downstream. Pure integers - no
# float, no new import - so the determinism guard (tests/test_determinism_guard.py)
# stays green. PLAYER_SPEED is DELIBERATELY untouched (D-07): controls must feel
# identical in the player's hands; fairness moves ghost outcomes, not player feel.
GHOST_CATCH_DISTANCE = 24          # FAIR-01 center-to-center catch radius (px); D-10 dial. Keep < TILE_HEIGHT(28) so a one-tile-off corner-kiss stays safe; 15 felt too forgiving head-on
GHOST_CHASE_SPEED_NUM = 40         # FAIR-02 chase-step numerator; D-10 dial. 40/20 = 2.0 px/frame = same as PLAYER_SPEED (FAIR-02 reset to original chase speed)
GHOST_CHASE_SPEED_DEN = 20         # chase-step denominator; NUM/DEN = px/frame avg. -1 to NUM is ~-0.05 px/frame; dial NUM < 40 to make chasers slower than the player
PLAYER_TURN_WINDOW_MARGIN = 6      # FAIR-03 pre-turn widening each edge (px), ~4-6px early per D-09

# Phase 9 - Arcade Juice tunables (FEEL-01/FEEL-04; D-04/D-06/D-07). Each is a
# D-10 playtest dial, same style as the Phase-8 block: pure integers, no float,
# no new import, so the determinism guard (tests/test_determinism_guard.py) stays
# green. These are inert tunables — the juice features in 09-02/03/04 consume them
# only behind the juice firewall, so juice=False golden/frame-hash replays are
# unchanged (SC5, no re-bless).
DEATH_ANIM_FRAMES = 75             # FEEL-01/D-04 wedge collapse frame budget; ~1.25s at 60 FPS; provisional, dialed to death.wav length during the 09-05 playtest
FRIGHT_FLASH_START = 480           # FEEL-04/D-06 blink when power_counter > 480, i.e. the last 120 of the 600-frame power window (~2s)
FRIGHT_FLASH_INTERVAL = 8          # FEEL-04/D-07 frames per blink half-cycle
