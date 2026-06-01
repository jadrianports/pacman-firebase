---
type: codebase-map
focus: arch
doc: STRUCTURE
generated: 2026-06-01
last_mapped_commit: 5e8d4b1773c03b4d3953200a764d658a431911de
---

# Project Structure

Flat, single-package layout: nearly all client modules live at the repo root (no `src/` or package directory). The backend lives under `cloud_functions/`, tests under `tests/`, and assets under `assets/`.

## Directory Layout

```
pacman-firebase/
├── main.py                  # Entry point + top-level state machine
├── game.py                  # Game class — gameplay state + frame loop (largest module)
├── ghost.py                 # Ghost class — 4 personality AIs + collision/turn logic
├── player.py                # Player class — movement, direction, animation
├── board.py                 # `boards` — static 30x33 tile grid (module-level list)
├── menu.py                  # Screen functions: main menu, initials, leaderboard, game over
├── settings.py              # All client constants (dims, speeds, positions, colors, API URLs)
├── sound.py                 # SoundManager (pygame.mixer wrapper)
├── paths.py                 # resource_path() / data_path() for dev + PyInstaller
├── api_service.py           # ApiService — urllib HTTP client for the leaderboard
├── local_storage.py         # machine_id.txt + player_data.json read/write
├── build.py                 # PyInstaller build entry (python build.py)
├── pacman.spec              # PyInstaller spec (git-ignored)
├── requirements.txt         # Client deps: pygame, pyinstaller
├── CLAUDE.md                # Repo guidance for Claude Code (git-ignored)
│
├── cloud_functions/
│   ├── submit_score/
│   │   ├── main.py          # POST endpoint — best-score upsert (Firestore txn)
│   │   └── requirements.txt # functions-framework==3.*, firebase-admin==6.*
│   └── get_leaderboard/
│       ├── main.py          # GET endpoint — top-10 read
│       └── requirements.txt # (identical to submit_score)
│
├── tests/
│   ├── __init__.py          # (empty — makes tests a package)
│   ├── test_api_service.py  # 6 tests, mocks urllib.urlopen
│   └── test_local_storage.py# 5 tests, tmp_path + monkeypatch.chdir
│
├── assets/
│   ├── audio/               # start.wav, wakawaka.wav, powerup.wav, death.wav  (USED)
│   ├── ghosts/              # red/pink/blue/orange/powerup/dead .png            (USED by game.py)
│   ├── pacman/              # 1..4 .png                                         (USED by player.py)
│   ├── ghost_images/        # red/pink/blue/orange/powerup/dead .png            (UNUSED duplicate)
│   └── player_images/       # 1..4 .png                                         (UNUSED duplicate)
│
├── docs/superpowers/        # Local design history (git-untracked)
│   ├── plans/               # 2026-03-26 leaderboard + api-refactor-exe plans
│   └── specs/               # matching design specs
│
├── freesansbold.ttf         # Bundled font (git-ignored)
├── firebase-key.json        # Service-account key (git-ignored, never committed)
├── machine_id.txt           # Local identity (git-ignored, runtime-generated)
├── player_data.json         # Local initials (git-ignored)
├── .venv/ .idea/ .vscode/   # Local env / IDE (mostly git-ignored)
└── build/ dist/             # PyInstaller output (git-ignored)
```

## Key Locations — "Where do I change X?"

| To change… | Edit… |
|------------|-------|
| Window size, FPS, speeds, start positions, box-exit delays | `settings.py` |
| Backend URLs | `settings.py` (`API_SUBMIT_SCORE_URL`, `API_LEADERBOARD_URL`) |
| The maze layout | `board.py` (`boards` 2D list; tile codes documented at top of file) |
| Top-level screen flow / what happens after a game | `main.py` |
| A menu / leaderboard / game-over screen | `menu.py` |
| Gameplay rules, scoring, collisions, win/lose, HUD | `game.py` |
| Ghost movement personality / targeting | `ghost.py` (movement) + `game.py:get_targets` (targets) |
| Pac-Man movement / animation | `player.py` |
| Sounds / channels | `sound.py` |
| Leaderboard validation, scoring rules, Firestore schema | `cloud_functions/submit_score/main.py` |
| Leaderboard query (count, ordering) | `cloud_functions/get_leaderboard/main.py` |

## Naming Conventions (observed)

- **Files / modules:** `snake_case.py` (`api_service.py`, `local_storage.py`).
- **Classes:** `PascalCase` (`Game`, `Ghost`, `Player`, `ApiService`, `SoundManager`).
- **Functions / methods / variables:** `snake_case` (`run_main_menu`, `check_collisions`, `direction_command`).
- **Constants:** `UPPER_SNAKE_CASE` in `settings.py` (`PLAYER_SPEED`, `BLINKY_START_X`, `MAX_SCORE`).
- **"Private" helpers:** leading underscore (`_update_score`, `_ghost_can_exit_box`, `_load_sound`, `_tile`).
- **Per-ghost state:** repeated `name_attr` families on `Game` — `blinky_x/inky_x/pinky_x/clyde_x`, `*_direction`, `*_dead`, `*_box`. Parallel arrays also used: `ghost_speeds[]`, `eaten_ghost[]`, `box_exit_timers[]`, `targets[]` (index order: blinky=0, inky=1, pinky=2, clyde=3).
- **Cloud functions:** directory name = function name (`submit_score/`, `get_leaderboard/`), each with a single `main.py` exporting the handler.

## Module Size / Complexity (rough)

| Module | ~Bytes | Role |
|--------|--------|------|
| `ghost.py` | ~27.6 KB | Largest — 4 near-duplicate movement methods |
| `game.py` | ~25.0 KB | Game loop + state |
| `menu.py` | ~8.6 KB | 4 screen functions |
| `player.py` | ~4.8 KB | Player movement |
| `board.py` | ~3.3 KB | Static maze data |
| `sound.py` | ~2.0 KB | Audio |
| `main.py`, `api_service.py`, `local_storage.py`, `paths.py`, `settings.py` | <2 KB each | Thin glue / config |

## Notable structural observations

- **Duplicate asset folders:** `assets/ghost_images/` and `assets/player_images/` mirror `assets/ghosts/` and `assets/pacman/` but are **not referenced by any code** (game.py uses `assets/ghosts/`, player.py uses `assets/pacman/`). Likely leftovers from a rename. See `CONCERNS.md`.
- **Flat root package:** tests import modules by top-level name (`from api_service import ApiService`), which works because pytest adds the repo root to `sys.path`. Moving modules into a package would break those imports without code changes.
- **No `__init__.py` at root** (only in `tests/`) — the client is a collection of scripts/modules, not an installable package.
