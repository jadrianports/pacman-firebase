---
type: codebase-map
focus: arch
doc: ARCHITECTURE
generated: 2026-06-01
last_mapped_commit: 5e8d4b1773c03b4d3953200a764d658a431911de
---

# Architecture

A single-process PyGame application organized as a **top-level state machine** that hands control to one of several blocking "screen" loops, plus a serverless backend for the leaderboard. There is no framework or DI container — wiring is explicit through constructor arguments and module-level functions.

## High-Level Pattern

- **State machine + per-screen game loops.** `main.py` owns the PyGame lifecycle and routes between screens. Each screen (`run_main_menu`, `run_initials_entry`, `run_leaderboard`, `run_game_over_screen`, and `Game.run`) is its own `while` loop that ticks the clock, draws, processes `pygame.event.get()`, and returns a value when done.
- **Shared PyGame objects, fresh game state.** The `screen` (`pygame.display`) and `timer` (`pygame.time.Clock`) are created once in `main()` and passed into every screen. A new `Game(screen, timer)` is constructed for each play session, so all gameplay state resets naturally.
- **Frame-driven, fixed timestep.** Everything runs at `FPS = 60` via `timer.tick(FPS)`. Timers are expressed in frames (counters), not wall-clock seconds.

## Layers

```
┌─────────────────────────────────────────────────────────────┐
│ Entry / State machine            main.py                      │
│   - pygame.init, display, clock                               │
│   - first-launch initials gate                                │
│   - menu → play → submit score → game-over loop               │
├─────────────────────────────────────────────────────────────┤
│ Presentation / Screens           menu.py (functions)          │
│   run_main_menu / run_initials_entry /                        │
│   run_leaderboard / run_game_over_screen                      │
├─────────────────────────────────────────────────────────────┤
│ Game engine                      game.py  (Game)              │
│   - owns ALL gameplay state + the frame loop (Game.run)       │
│   - player.py (Player)  ghost.py (Ghost)  board.py (boards)   │
├─────────────────────────────────────────────────────────────┤
│ Services                         api_service.py (ApiService)  │
│                                  local_storage.py (id/initials)│
├─────────────────────────────────────────────────────────────┤
│ Cross-cutting / Infra            settings.py (constants)      │
│                                  paths.py (resource/data)     │
│                                  sound.py (SoundManager)       │
├─────────────────────────────────────────────────────────────┤
│ Backend (separate deploy)        cloud_functions/*            │
│   submit_score / get_leaderboard → Firestore "leaderboard"    │
└─────────────────────────────────────────────────────────────┘
```

## Entry Point & Top-Level Flow

`main.py:main()`:
1. `pygame.init()`, create `screen` + `timer`, construct `ApiService`, read `machine_id`.
2. **First-launch gate:** if `get_initials()` is `None`, run `run_initials_entry` and `save_initials`.
3. **State loop:**
   - `run_main_menu` → `"Play" | "Leaderboard" | "Quit"`.
   - `"Play"` → `Game(screen, timer).run()` → `{score, game_won}` (or `None` if the window was closed) → `api.submit_score(...)` → `run_game_over_screen(...)`.
   - `"Leaderboard"` → `run_leaderboard(screen, timer, api)`.
   - `"Quit"` or a window-close `None` → break → `pygame.quit()`.

`MENU_OPTIONS` is `["Play", "Leaderboard", "Quit"]` (`settings.py`). Note `run_main_menu`'s docstring mentions a "Change Initials" option that is not in `MENU_OPTIONS` — initials are effectively permanent.

## Game Engine Design (`game.py`)

`Game` is the heart of the system: it holds **all** mutable gameplay state as plain attributes and runs the loop in `Game.run()`. Per frame it:

1. Advances the animation `counter` (0–19) and `flicker` toggle (drives big-dot blink + pac-man frames).
2. Handles transient phases: `eat_freeze` (brief pause when eating a ghost), `powerup` timer (600 frames), `starting` (waits for the start jingle), `dying` (waits for the death sound + 60 frames, then decrements `lives` or sets `game_over`).
3. Draws board → recomputes ghost speeds → checks win → draws player/ghosts/HUD.
4. Computes ghost `targets` (`get_targets`), ticks box-exit timers, moves player + ghosts, runs collision checks.
5. Processes input (`handle_events`), updates player direction, wrap-around, box re-entry.
6. `pygame.display.flip()`.

### Key abstraction: ghosts are recreated every frame

The single most distinctive architectural decision. Ghost **state** (position, direction, dead/in-box flags, speeds) lives on the `Game` object as parallel attributes (`blinky_x`, `inky_dead`, `ghost_speeds[]`, `eaten_ghost[]`, …). Each frame, `create_ghosts()` constructs four brand-new `Ghost` objects from that state:

```python
self.blinky = Ghost(self.blinky_x, self.blinky_y, self.targets[0], self.ghost_speeds[0],
                    self.blinky_img, self.blinky_direction, self.blinky_dead, self.blinky_box,
                    0, self.screen, self.powerup, self.eaten_ghost,
                    self.spooked_img, self.dead_img, self.level)
```

`Ghost.__init__` even **draws itself** (calls `self.draw()` and `check_collisions()` as constructor side effects). `move_ghosts()` then calls the ghost's AI method and writes the new `(x, y, direction)` back onto the `Game` attributes. So a `Ghost` is effectively a transient "compute one frame of movement" object, not a long-lived entity.

### Ghost AI (`ghost.py`)

Each ghost has a personality method — `move_blinky`, `move_inky`, `move_pinky`, `move_clyde` — sharing a common direction model (`0=R, 1=L, 2=U, 3=D`) and the `turns[]` legality array from `check_collisions()`. `move_clyde` doubles as the **fallback** mover for dead or in-box ghosts. Targets are assigned in `Game.get_targets()` based on powerup state and per-ghost scatter/chase logic.

### Box exit

Ghosts spawn inside the central box and are frozen until a per-ghost frame delay elapses (`BOX_EXIT_DELAY_*` in `settings.py`, gated by `Game._ghost_can_exit_box`). Timers tick only while `moving` and not in `eat_freeze`, and reset on death.

## Data Flow: Score Submission

```
Game.run() ──{score, game_won}──▶ main.py
   main.py ──submit_score(machine_id, initials, score)──▶ ApiService (urllib POST)
        ──▶ Cloud Function submit_score ──▶ Firestore txn (best-score upsert)
        ◀── {success, is_new_best} ──
   main.py ──is_new_best──▶ run_game_over_screen()
```

## Data Flow: Leaderboard

```
run_main_menu ─"Leaderboard"▶ run_leaderboard(screen, timer, api)
   ── api.get_leaderboard() (urllib GET) ──▶ Cloud Function get_leaderboard
        ──▶ Firestore order_by(score desc).limit(10)
        ◀── {entries:[{initials, score}...]} ──
   render top-10 (or "Could not connect" if None)
```

## Cross-Cutting Concerns

- **Configuration:** centralized constants in `settings.py` (though much positional/tile math is still inline — see `CONVENTIONS.md`/`CONCERNS.md`).
- **Audio:** `SoundManager` (`sound.py`) wraps `pygame.mixer.Sound` with dedicated channels for waka (ch 0) and powerup siren (ch 1); start/death use default allocation.
- **Path resolution:** `paths.py` keeps dev and PyInstaller-frozen runs working for both bundled assets and writable user data.
- **Offline resilience:** all network access is funneled through `ApiService`, which returns `None` on any error; every caller treats `None` as "offline" and degrades gracefully.

## Backend Architecture

Two independent, stateless HTTP Cloud Functions (`functions_framework`), each initializing `firebase-admin` once (`if not firebase_admin._apps`) and sharing the Firestore `leaderboard` collection. `submit_score` uses a Firestore transaction for the best-score upsert; `get_leaderboard` is a simple ordered read. No shared code between the two functions (each is a self-contained `main.py` + `requirements.txt`).
