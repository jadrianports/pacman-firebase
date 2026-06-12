# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the game
python main.py

# Run all tests
pytest

# Run a single test file
pytest tests/test_api_service.py

# Run a single test
pytest tests/test_api_service.py::test_submit_score_new_best

# Build exe (requires pyinstaller)
python build.py  # Output: dist/pacman/pacman.exe
```

## Architecture

Pac-Man clone built with Python/PyGame, with a Cloud Functions-backed online leaderboard.

### Game Flow

`main.py` is a state machine that owns the PyGame lifecycle and routes between menu screens (`menu.py`) and gameplay (`game.py`). Game objects are created fresh for each play session — `Game(screen, timer)` accepts shared PyGame objects.

### Ghost System

- Ghost objects are recreated every frame — all ghost state (positions, directions, dead/alive) lives on the `Game` object and is passed to `Ghost` constructors
- Ghost movement is a single unified data-driven mover: `Ghost._move(profile)` consumes a per-ghost `*_PROFILE` (`BLINKY_PROFILE`/`INKY_PROFILE`/`PINKY_PROFILE`/`CLYDE_PROFILE`), each a `dict[int, DirectionRule]` keyed by direction (0-3) holding a turn-priority `blocked_ladder` (data) plus named `primary`/`forward_open` quirk hooks (control-flow). The four `move_blinky`/`move_inky`/`move_pinky`/`move_clyde` are thin wrappers that delegate to `_move` with that ghost's profile, so each ghost keeps its distinct personality while sharing one mover
- `move_clyde` doubles as fallback movement for dead/in-box ghosts

### Leaderboard

- Cloud Functions act as HTTP API proxy — no Firebase credentials in the client
- `api_service.py` talks to `submit_score` (POST) and `get_leaderboard` (GET)
- Game is fully playable offline — leaderboard features gracefully degrade
- `local_storage.py` manages machine ID (`machine_id.txt`) and player initials (`player_data.json`)
- Initials are permanent — set once on first launch, cannot be changed

### Asset/Data Paths

`paths.py` provides `resource_path()` for bundled assets and `data_path()` for user data files — handles both dev and PyInstaller exe environments.

### Key Constants

- Directions: 0=Right, 1=Left, 2=Up, 3=Down
- Board tile codes: 0=empty, 1=dot, 2=big dot, 3=vertical wall, 4=horizontal wall, 5-8=corners, 9=gate
- All constants (dimensions, speeds, positions, API URLs) in `settings.py`

### Sound System

`sound.py` manages all game audio via `SoundManager`. Uses `pygame.mixer.Sound` objects (not `pygame.mixer.music`). Dedicated channels for waka (ch 0) and powerup siren (ch 1). Start/death sounds use default channel allocation.

### Ghost Box Exit

Ghosts exit the box with staggered delays (configured in `settings.py`). Inky exits immediately, Pinky after ~2 sec, Clyde after ~4 sec. Delays reset on player death. Ghosts are frozen in place inside the box until their timer is up.
