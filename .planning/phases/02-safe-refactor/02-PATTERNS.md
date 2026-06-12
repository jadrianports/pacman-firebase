# Phase 2: Safe Refactor - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 11 (4 created, 6 modified, 1 doc)
**Analogs found:** 10 / 11 (1 file — `geometry.py` — is a new module type with a partial analog)

Note: `.planning/codebase/TESTING.md` is stale (pre-Phase 1; says "11 tests / 2 files / no CI / no conftest"). The real Phase 1 net (`tests/conftest.py`, `tests/test_ghost_micro.py`, `tests/test_golden_traces.py`) is the authoritative test-style analog and is mapped directly below from source reads.

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `settings.py` (modify: `TILE_*`, box/wrap/scatter constants) | config | transform (derived constants) | `settings.py:3-7` existing derived/flat consts | exact (self-analog) |
| `geometry.py` (new: `tile_at`/`is_walkable`/`in_box` + bounds) | utility | transform (pure helpers) | `ghost.py:38-41 _tile` + `settings.py` const idiom | role-match (partial) |
| `ghost.py` profile data (new: `DirectionRule`, 4 `*_PROFILE`) | model (data table) | transform | `settings.py` module-level const block; `ghost.py` `# r,l,u,d` comment idiom | role-match |
| `ghost.py` unified `_move` + 4 thin wrappers | service (game logic) | transform | `ghost.py:117-254 move_clyde` (the byte-identical signature/wrap target) | exact |
| `ghost.py:43-115 check_collisions` (modify: substitute literals) | service (game logic) | transform | itself (self-analog); `in_box` call site `ghost.py:111` | exact |
| `game.py` `get_targets`/`draw_board`/eat-dot (modify) | service (game logic) | transform | `game.py:240-299` (8 box checks), `game.py:130-137` tile math | exact (self-analog) |
| `player.py:39-87 check_position` (modify: substitute literals) | service (game logic) | transform | itself (self-analog) | exact |
| `tests/_legacy_movers.py` (new: frozen OLD movers/check_collisions) | test (one-shot oracle) | transform | `ghost.py` move_*/check_collisions verbatim copy | exact (copy source) |
| `tests/test_mover_oracle.py` + `tests/test_check_collisions_oracle.py` (new) | test (differential) | transform | `tests/test_ghost_micro.py` (`make_ghost`, headless `screen` fixture) | exact |
| `tests/test_frame_hash.py` + `tests/golden/<s>/frame_hashes.txt` (new) | test (golden) | transform | `tests/test_golden_traces.py` (`--bless` flow, tile-math mirror) | exact |
| `CLAUDE.md` Ghost System section (modify, D-17) | config (doc) | n/a | existing "Ghost System" bullets | exact (self-analog) |

---

## Pattern Assignments

### `settings.py` — derived tile constants + named position constants (D-12/D-13)

**Analog:** `settings.py` itself — the existing module already does flat + derived constants and `UPPER_SNAKE_CASE` per `CONVENTIONS.md:29`.

**Existing derived/flat constant idiom** (`settings.py:1-12`):
```python
import math

WIDTH = 900
HEIGHT = 950
FPS = 60
PLAYER_SPEED = 2
PI = math.pi

# Initial player position
PLAYER_START_X = 450
PLAYER_START_Y = 663
```
Note `settings.py` imports only `math` (no heavy deps) — adding `TILE_*` derived from `WIDTH`/`HEIGHT` keeps it pure-constants. Comment-grouped sections (`# Initial ghost positions`, `# Box exit delays`) are the house grouping idiom to mirror for the new `# Tile geometry` / `# Box regions` / `# Wrap edges` blocks.

**New constants to add** (research FOCUS-7, byte-identical: `(950-50)//32==28`, `900//30==30`):
```python
# Tile geometry (was inline num1/num2/num3 in game/ghost/player)
BOARD_ROWS = 32
BOARD_COLS = 30
HUD_HEIGHT = 50
TILE_HEIGHT = (HEIGHT - HUD_HEIGHT) // BOARD_ROWS   # 28  (was num1)
TILE_WIDTH  = WIDTH // BOARD_COLS                   # 30  (was num2)
HALF_TILE   = 15                                    # look-ahead (was num3)
```
⚠️ Naming landmine: `num1` is tile HEIGHT (rows), `num2` is tile WIDTH (cols). Do not transpose.

The two box rectangles + wrap/scatter literals: per D-16 the bounds + `in_box` predicate live in `geometry.py`; flat wrap/scatter literals may live in either — keep them as DISTINCT named constants (D-13) so Phase 3's unification is the only merge point.

---

### `geometry.py` (new utility module — D-14/D-16)

**Analog:** no existing standalone pure-helper module exists (closest single-purpose modules are `paths.py` and `local_storage.py`, which have one-line docstrings per `CONVENTIONS.md:72`). The *helper bodies* are lifted from existing code:

**`tile_at`/`is_walkable` analog** — `ghost.py:38-41`:
```python
def _tile(self, row, col):
    row = max(0, min(len(self.level) - 1, row))
    col = max(0, min(len(self.level[0]) - 1, col))
    return self.level[row][col]
```
plus the project-wide `< 3` walkability idiom (`ghost.py:52`, `player.py:48`, `CONVENTIONS.md:34`).

**`in_box` body** collapses the literal `350 < self.x_pos < 550 and 360 < self.y_pos < 480` (`ghost.py:111`) and the 8 `340 < ..._x < 560 and 340 < ..._y < 500` checks in `game.py:240-297`.

**Import idiom to follow** (`CONVENTIONS.md:38-47`, `game.py:8`): local imports by top-level name — `geometry.py` does `from settings import TILE_HEIGHT, TILE_WIDTH`. One-line docstrings on each helper (matches `paths.py`/`menu.py` style).

Recommended bodies (research FOCUS-8):
```python
def in_box(x, y, bounds):
    x_lo, x_hi, y_lo, y_hi = bounds
    return x_lo < x < x_hi and y_lo < y < y_hi
```
Bounds constants kept distinct (D-13): `GHOST_BOX_BOUNDS_COLLISION = (350,550,360,480)`, `GHOST_BOX_BOUNDS_TARGET = (340,560,340,500)`.
⚠️ D-15 landmine: share ONLY `tile_at`/`is_walkable`/`in_box`. Do NOT factor the band/guard logic — `check_collisions` and `check_position` are divergent.

---

### `ghost.py` — profile data + unified `_move` + thin wrappers (D-01/D-02/D-03)

**Analog (data placement):** module-level data block at top of `ghost.py` (after `import`, before `class Ghost`), mirroring `settings.py`'s grouped-constant style. The personality comments (`ghost.py:118-119` `# clyde is going to turn whenever advantageous for pursuit`; `ghost.py:257-258` `# blinky is going to turn whenever colliding with walls, otherwise continue straight`) become per-profile docstrings (D-03). Preserve the `# r, l, u, d` direction-key comment idiom.

**Analog (wrapper signature — must stay byte-identical, D-02):** the existing zero-arg movers all share this exact shape. `move_blinky` head (`ghost.py:256-261`):
```python
def move_blinky(self):
    # r, l, u, d
    # blinky is going to turn whenever colliding with walls, otherwise continue straight
    if self.direction == 0:
        if self.target[0] > self.x_pos and self.turns[0]:
            self.x_pos += self.speed
```
The new wrappers must preserve these names/signatures exactly so `game.py:move_ghosts` and the 15 micro tests are untouched:
```python
def move_blinky(self): return self._move(BLINKY_PROFILE)
def move_inky(self):   return self._move(INKY_PROFILE)
def move_pinky(self):  return self._move(PINKY_PROFILE)
def move_clyde(self):  return self._move(CLYDE_PROFILE)
```

**Shared trailing wrap clamp + return (fold into `_move` once)** — identical across all four, e.g. `move_clyde` tail (`ghost.py:250-254`):
```python
if self.x_pos < -30:
    self.x_pos = 900
elif self.x_pos > 900:
    self.x_pos = -30
return self.x_pos, self.y_pos, self.direction
```
⚠️ Q-b/Q-c landmines (research FOCUS-1): inky dir-1 PRIMARY sets `direction=3` with NO `y_pos +=`; pinky sets direction AND moves. The `if … if … else` override blocks (e.g. `move_clyde:142-150`) must be transcribed as literal Python in a named hook, NOT an `elif` ladder.

---

### `ghost.py:43-115 check_collisions` — geometry substitution (REF-01)

**Analog:** itself. Substitute inline `num1/num2/num3` (`ghost.py:45-47`) with `TILE_HEIGHT`/`TILE_WIDTH`/`HALF_TILE`; replace the box literal (`ghost.py:111`) with `in_box(self.x_pos, self.y_pos, GHOST_BOX_BOUNDS_COLLISION)`; replace the `self._tile(...) < 3` reads with `tile_at`/`is_walkable` where atomic.
⚠️ The guard `0 < self.center_x // 30 < 29` (`ghost.py:49`) uses literal `30` (== `TILE_WIDTH`) and `29` (== `BOARD_COLS - 1`) — substitute to those names; byte-identical (proven by the FOCUS-4 oracle). The gate-tile-9 + `in_box or self.dead` logic is ghost-only — keep in place.

---

### `game.py` get_targets / draw_board / eat-dot — geometry touch-points (D-13/D-14)

**Analog:** itself. The 8 `in_box`-replaceable box checks (`game.py:240, 249, 258, 267, 275, 282, 289, 296`), each:
```python
if 340 < self.blinky_x < 560 and 340 < self.blinky_y < 500:
    blink_target = (400, 100)
```
→ `if in_box(self.blinky_x, self.blinky_y, GHOST_BOX_BOUNDS_TARGET): ...`

Scatter/fixed targets to name (D-13): `return_target = (380, 400)` (`game.py:235`), `(400, 100)` eaten target, `(450, 450)` clyde scatter (`game.py:265`).

**`draw_board` tile math** (`game.py:130-131`) → use `TILE_HEIGHT`/`TILE_WIDTH`:
```python
num1 = ((HEIGHT - 50) // 32)
num2 = (WIDTH // 30)
```
⚠️ Leave the cosmetic literals inline (radii `4`/`10`, `0.5*` offsets at `game.py:135-137`) — they are rendering, not geometry (D-13).

---

### `player.py:39-87 check_position` — geometry substitution (REF-01)

**Analog:** itself. Substitute inline `num1/num2/num3` (`player.py:41-43`) and the guard `centerx // 30 < 29` (`player.py:46`). Note this guard differs from the ghost's (`0 < ... < 29` vs `... < 29`) and the band offsets mix `num1`/`num2`/`num3` differently (`player.py:67-80`) — D-15: substitute literals only, do NOT merge with `check_collisions`.

---

### `tests/_legacy_movers.py` (new, one-shot — D-06/D-07)

**Analog (copy source):** verbatim copies of current `ghost.py` `move_blinky/inky/pinky/clyde` (`ghost.py:117-607`) and `check_collisions` (`ghost.py:43-115`) as standalone functions operating on a constructed ghost. Captured in the same commit that introduces the unified mover; deleted once all four ghosts prove green.

---

### `tests/test_mover_oracle.py` + `tests/test_check_collisions_oracle.py` (new — D-04/D-05/D-07)

**Analog:** `tests/test_ghost_micro.py`. Reuse its exact harness:

**Headless `screen` fixture** (`test_ghost_micro.py:27-38`):
```python
@pytest.fixture(scope="module")
def screen():
    pygame.display.init()
    surf = pygame.display.set_mode((900, 950))
    yield surf
```

**`make_ghost` constructor + Pitfall-4 deep-copy** (`test_ghost_micro.py:41-57`):
```python
def make_ghost(screen, x, y, target, speed, direction, ghost_id,
               dead=False, box=False, powerup=False):
    img = pygame.Surface((45, 45))
    eaten_ghost = [False, False, False, False]
    return Ghost(x, y, target, speed, img, direction, dead, box, ghost_id,
                 screen, powerup, eaten_ghost, img, img,
                 copy.deepcopy(board.boards))
```
After construction, clobber synthetic inputs (research FOCUS-3): `g.turns = list(turns_combo); g.in_box = box`. Use programmatic `itertools.product` loops with a first-divergence accumulator (NOT `parametrize` at 138k cases). Assertion style mirrors the micro tests' exact-tuple compare: `assert old == g.move_blinky()`.

---

### `tests/test_frame_hash.py` + `tests/golden/<s>/frame_hashes.txt` (new — D-08/D-09)

**Analog:** `tests/test_golden_traces.py`. Reuse:

**`--bless` branch idiom** (`test_golden_traces.py:195-205`):
```python
if request.config.getoption("--bless"):
    old = read_jsonl(trace_path) if os.path.exists(trace_path) else []
    write_jsonl(replayed, trace_path)
    ...
    return  # do NOT assert in bless mode
```
`--bless` is registered in `tests/conftest.py:59-66`. Frame-hash bless writes `frame_hashes.txt` instead of `trace.jsonl`; otherwise asserts.

**Tile-math mirror + exact-integer compare** (`test_golden_traces.py:40-43`): the test module re-declares `NUM1 = (950-50)//32` / `NUM2 = 900//30` to mirror game math — the frame-hash test follows the same "mirror the constant, compare exactly" convention.

**Hash helper** (research FOCUS-5, Code Examples): `hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()`.
⚠️ Pinned-env-only assertion (Pitfall 4 / D-09): bless + assert frame-hash ONLY in the Linux CI env (`conftest.py:_ensure_default_font` guarantees the font); regenerate elsewhere.

---

### `CLAUDE.md` Ghost System section (D-17)

**Analog:** the existing "### Ghost System" bullets. Replace "Each ghost has its own AI method (`move_blinky`, …) with distinct personality" with a description of the unified data-driven `_move` + per-ghost `*_PROFILE` data + thin wrappers. Preserve the existing "`move_clyde` doubles as fallback" bullet (still true via the clyde profile).

---

## Shared Patterns

### Headless ghost construction (all logic oracles)
**Source:** `tests/test_ghost_micro.py:41-57` (`make_ghost`) + `:27-38` (`screen` fixture).
**Apply to:** `test_mover_oracle.py`, `test_check_collisions_oracle.py`.

### `--bless` re-record flow (all golden artifacts)
**Source:** `tests/conftest.py:59-66` (flag) + `tests/test_golden_traces.py:195-205` (read-old / write-new / return-without-assert).
**Apply to:** `test_frame_hash.py` (frame_hashes.txt manifest).

### Constant centralization idiom
**Source:** `settings.py` grouped `UPPER_SNAKE_CASE` blocks + `CONVENTIONS.md:76-84` ("lift literals into settings.py / shared helpers").
**Apply to:** `settings.py` (`TILE_*`), `geometry.py` (bounds + helpers), and every literal substitution in `game.py`/`ghost.py`/`player.py`.

### Local import-by-name idiom
**Source:** `game.py:8` (`from settings import (...)`), `CONVENTIONS.md:38-47`.
**Apply to:** `geometry.py` imports `TILE_*` from `settings`; `game/ghost/player` import helpers from `geometry`. Avoid a `player → ghost` import (D-16).

### Exact-integer equality + tile-math mirror
**Source:** `tests/test_golden_traces.py:40-43` (mirror NUM1/NUM2) + micro-test exact-tuple asserts.
**Apply to:** both differential oracles and the frame-hash test.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `geometry.py` (as a *module*) | utility | transform | No existing standalone pure-helper module; closest single-purpose modules are `paths.py`/`local_storage.py` (style analog only). Helper *bodies* are lifted from `ghost.py:38-41` + the inline box/`<3` idioms, so this is a partial-analog, not a true gap. |

---

## Metadata

**Analog search scope:** repo root (`settings.py`, `ghost.py`, `game.py`, `player.py`), `tests/`, `harness/`, `.planning/codebase/`.
**Files scanned (read):** `settings.py`, `ghost.py` (L1-160, 244-269), `game.py` (L1-15, 130-137, 228-299), `player.py` (L39-103), `tests/test_ghost_micro.py`, `tests/test_golden_traces.py`, `tests/conftest.py`, plus CONTEXT/RESEARCH/CONVENTIONS/TESTING.
**Pattern extraction date:** 2026-06-12

## PATTERN MAPPING COMPLETE
