---
type: codebase-map
focus: quality
doc: CONVENTIONS
generated: 2026-06-01
last_mapped_commit: 5e8d4b1773c03b4d3953200a764d658a431911de
---

# Coding Conventions

Conventions are **observed from the code**, not enforced by tooling — there is no linter, formatter, or style config (no `.flake8`, `ruff.toml`, `.pylintrc`, `pyproject.toml`, or pre-commit). Style is broadly PEP 8-ish and internally consistent.

## Formatting & Style

- **Indentation:** 4 spaces, no tabs.
- **Line length:** mostly moderate, but several long lines in `game.py`/`ghost.py` (image loads, multi-condition collision checks) exceed ~100 cols — no enforced limit.
- **Quotes:** mixed. Client modules lean on double quotes (`"black"`, `"Play"`); some single quotes appear for pygame color/asset strings (`'white'`, `'assets/ghosts/red.png'`). Not standardized.
- **Blank lines:** two blank lines between top-level defs/classes (PEP 8), one between methods.
- **f-strings** for interpolation (`f'Score: {self.score}'`, `f"{rank} {initials} {dots} {score}"`).

## Naming

| Kind | Convention | Examples |
|------|-----------|----------|
| Modules | `snake_case.py` | `api_service.py`, `local_storage.py` |
| Classes | `PascalCase` | `Game`, `Ghost`, `Player`, `ApiService`, `SoundManager` |
| Functions/methods | `snake_case` | `run_main_menu`, `check_collisions`, `update_direction` |
| Variables/attrs | `snake_case` | `direction_command`, `power_counter`, `eat_freeze_timer` |
| Constants | `UPPER_SNAKE_CASE` (in `settings.py`) | `PLAYER_SPEED`, `BLINKY_START_X`, `MAX_SCORE` |
| Private helpers | `_leading_underscore` | `_update_score`, `_ghost_can_exit_box`, `_tile`, `_load_sound` |

**Direction encoding** is a project-wide convention: `0=Right, 1=Left, 2=Up, 3=Down` — used everywhere as the index basis for `turns[]`, `turns_allowed[]`, and `direction`/`direction_command`. The order `r, l, u, d` is repeated in comments above movement code.

**Board tile codes** (documented at the top of `board.py`): `0=empty, 1=dot, 2=big dot, 3=vertical wall, 4=horizontal wall, 5–8=corners, 9=gate`. Walkability test is the idiom `tile < 3` (empty/dot/big-dot are walkable).

## Imports

Ordering follows stdlib → third-party → local, e.g. `game.py`:
```python
import copy
import pygame
from board import boards
from ghost import Ghost
from settings import (WIDTH, HEIGHT, FPS, PI, ...)
```
- Local imports use **top-level module names** (`from settings import ...`, `from paths import resource_path`) — consistent with the flat root layout.
- Multi-name imports from `settings` use parenthesized multi-line form.

## Module / Class Patterns

- **Screens are functions, gameplay entities are classes.** `menu.py` exposes plain functions (`run_*`) that each own a blocking loop and return a result. `Game`, `Player`, `Ghost`, `ApiService`, `SoundManager` are classes.
- **State-on-the-orchestrator.** `Game` holds all gameplay state as flat attributes; `Ghost` objects are transient and recreated per frame from that state (see `ARCHITECTURE.md`). Prefer following this existing pattern when extending gameplay rather than introducing long-lived entity objects.
- **Dependency injection by argument.** Shared `screen`/`timer`/`api` are passed into screen functions and `Game(...)`; `ApiService(submit_url, leaderboard_url)` takes its URLs explicitly. Paths in `local_storage` default to module constants but accept an override arg (used by tests).
- **Computed properties** for derived geometry: `Player.center_x/center_y`, `Ghost.center_x/center_y` (offset from top-left). Note the offsets differ slightly between Player (`+23/+24`) and Ghost (`+22/+22`).
- **`@property` and `@firestore.transactional` decorators** are used; no custom decorators.

## Error Handling

Two distinct, deliberate strategies:

1. **Client network calls — swallow and degrade.** `api_service.py` wraps every call in `try/except Exception` and returns `None`. Callers interpret `None` as "offline" and show fallback UI (`run_leaderboard` renders "Could not connect…"; `main.py` treats a `None` submit response as "not a new best"). `local_storage.get_initials` catches `(json.JSONDecodeError, KeyError)` and returns `None`.
   ```python
   except Exception:
       return None
   ```
2. **Backend — validate then guarded execute.** Cloud functions validate inputs explicitly (regex for initials, type/range for score) and return structured `{"success": false, "error": ...}` with `400`; unexpected failures are caught, `print()`-logged, and returned as `500` with a generic message (no internal details leaked to the client).

There is **no use of `logging`** — diagnostics are `print()` in cloud functions and nothing in the client. No custom exception classes.

## Comments & Docs

- **Docstrings:** present on `menu.py` screen functions and `paths.py` helpers (one-line, describe return values). `game.py`/`ghost.py`/`player.py` methods are largely undocumented.
- **Inline comments** explain intent for tricky logic (ghost personality descriptions, "Check all 4 adjacent tiles so waka persists through turns", board tile legend). Movement methods are annotated with the `# r, l, u, d` direction key.
- No type hints anywhere (client or backend).

## Magic Numbers (a known stylistic exception)

While `settings.py` centralizes top-level constants, the tile/collision math embeds many literals inline and repeatedly:
```python
num1 = (HEIGHT - 50) // 32      # tile height, recomputed in game/ghost/player
num2 = WIDTH // 30              # tile width
num3 = 15                       # look-ahead offset
```
plus hardcoded pixel bounds (e.g. box-region tests `340 < x < 560`, wrap edges `900`, `-30`, `-47`). This is consistent across the gameplay code but is the main readability/maintenance debt (see `CONCERNS.md`). When extending, prefer lifting such literals into `settings.py` or shared helpers.
