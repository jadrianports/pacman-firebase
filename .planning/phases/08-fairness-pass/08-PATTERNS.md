# Phase 8: Fairness Pass - Pattern Map

**Mapped:** 2026-06-29
**Files analyzed:** 4 modified + 1 new
**Analogs found:** 5 / 5 (all in-repo; this is an EDIT-heavy phase, so most "analogs" are the exact existing code the executor edits)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `game.py` (`check_ghost_collisions`, FAIR-01) | controller (collision arbiter) | event-driven (per-frame) | itself, `game.py:400-436` (current AABB code) | exact (in-place edit) |
| `game.py` (`update_ghost_speeds` + new accumulator, FAIR-02) | controller (speed assigner) | transform (per-frame) | itself, `game.py:333-353` | exact (in-place edit) |
| `player.py` (`check_position`, FAIR-03) | model (movement rules) | transform (per-frame) | itself, `player.py:43-91` | exact (in-place edit) |
| `settings.py` (new tunables) | config | n/a | `settings.py:10,21` (`PLAYER_SPEED`, `HALF_TILE`) | exact (append) |
| `tests/test_player_micro.py` (NEW) | test (characterization) | request-response (pure fn) | `tests/test_ghost_micro.py` | role-match (new file modeled on it) |

## Pattern Assignments

### `game.py` :: `check_ghost_collisions` (FAIR-01, controller / event-driven)

**Analog:** the current method itself, `game.py:400-436`. Replace 3 symmetric `colliderect` groups with integer squared-distance against existing center properties.

**Current code to edit** (`game.py:400-436`):
```python
def check_ghost_collisions(self, player_circle):
    # Normal ghost kills player
    if not self.powerup:
        if (player_circle.colliderect(self.blinky.rect) and not self.blinky.dead) or \
                (player_circle.colliderect(self.inky.rect) and not self.inky.dead) or \
                (player_circle.colliderect(self.pinky.rect) and not self.pinky.dead) or \
                (player_circle.colliderect(self.clyde.rect) and not self.clyde.dead):
            self.start_dying()

    # Already-eaten ghost kills player during powerup
    if self.powerup and not self.dying:
        if (player_circle.colliderect(self.blinky.rect) and self.eaten_ghost[0] and not self.blinky.dead) or \
                ...:
            self.start_dying()

    # Player eats ghost during powerup
    ...
    for ghost, dead_attr, idx, gx, gy in ghost_eat_checks:
        if self.powerup and player_circle.colliderect(ghost.rect) and not ghost.dead and not self.eaten_ghost[idx]:
            ...
```

**Center properties already exist (no new geometry needed):**
- Player: `player.py:23-29` — `center_x = x + 23`, `center_y = y + 24` (both `@property`, always live on `self.player`).
- Ghost: `ghost.py:284-285` — `center_x = x_pos + 22`, `center_y = y_pos + 22` (plain ints).

**Drop-in helper to introduce** (RESEARCH Pattern 1, integer-exact, no `math.sqrt`):
```python
def _catches(self, ghost):
    dx = self.player.center_x - ghost.center_x
    dy = self.player.center_y - ghost.center_y
    return dx * dx + dy * dy <= GHOST_CATCH_DISTANCE * GHOST_CATCH_DISTANCE
```
Replace every `player_circle.colliderect(<ghost>.rect)` with `self._catches(<ghost>)` across all three groups (D-04 symmetric). The `player_circle` param may be left in the signature (called at `game.py:578`) or dropped — prefer reading `self.player.center_*` (always live; `player_circle` is stale during `eat_freeze`).

**Error/guard pattern (unchanged):** death gated by `not self.dying`; eat loop `break`s after first eat; method only called `when not eat_freeze and not starting` (`game.py:576-578`).

---

### `game.py` :: `update_ghost_speeds` + accumulator (FAIR-02, controller / transform)

**Analog:** the current method itself, `game.py:333-353`.

**Current code to edit** (`game.py:333-353`):
```python
def update_ghost_speeds(self):
    if self.powerup:
        self.ghost_speeds = [1, 1, 1, 1]
    else:
        self.ghost_speeds = [2, 2, 2, 2]
    if self.eaten_ghost[0]:
        self.ghost_speeds[0] = 2
    ...  # eaten_ghost[1..3] -> 2
    if self.blinky_dead:
        self.ghost_speeds[0] = 4
    ...  # *_dead -> 4
```

**Change (RESEARCH Pattern 2):** for each ghost whose computed tier `== 2` (the lethal-chase tier, both default-chase and eaten-revived), replace the `2` with an integer-rational accumulator step (1 or 2). Leave tier `1` (frightened, D-08) and `4` (eyes, D-08) byte-identical.
```python
for i in range(4):
    if self.ghost_speeds[i] == 2:
        self.ghost_step_acc[i] += GHOST_CHASE_SPEED_NUM
        step = self.ghost_step_acc[i] // GHOST_CHASE_SPEED_DEN
        self.ghost_step_acc[i] -= step * GHOST_CHASE_SPEED_DEN
        self.ghost_speeds[i] = step
```

**State init analog** (`game.py:77`, where `self.ghost_speeds` lives):
```python
self.ghost_speeds = [2, 2, 2, 2]
# add adjacent:
self.ghost_step_acc = [0, 0, 0, 0]
```

**Reset analog** (`reset_after_death`, `game.py:133-141`) — append `self.ghost_step_acc = [0, 0, 0, 0]` so credit doesn't bank across lives.

**Gating analog (determinism-critical, Pitfall 4):** the accumulator must advance only on frames where ghosts move. Mirror the existing guard at `game.py:573-575`:
```python
if self.moving and not self.eat_freeze:
    self.player.move()
    self.move_ghosts()
```
Advance the accumulator inside the same gate (e.g. call `update_ghost_speeds` only under this guard, or compute the step there). `ghost.py` is **not touched** (consumes `self.ghost_speeds[i]` via `create_ghosts`, `game.py:355-367`).

---

### `player.py` :: `check_position` (FAIR-03, model / transform)

**Analog:** the current method itself, `player.py:43-91`. Widen the **four** player-only `12 <= … <= 18` windows; ghost windows (`ghost.py:343,352,363,372`) stay byte-identical (D-15).

**Current windows to edit** (`player.py:65,70,76,81`):
```python
if self.direction == 2 or self.direction == 3:
    if 12 <= centerx % TILE_WIDTH <= 18:          # line 65
        ...
    if 12 <= centery % TILE_HEIGHT <= 18:         # line 70
        ...
if self.direction == 0 or self.direction == 1:
    if 12 <= centerx % TILE_WIDTH <= 18:          # line 76
        ...
    if 12 <= centery % TILE_HEIGHT <= 18:         # line 81
        ...
```

**Recommended symmetric widening** (RESEARCH Pattern 3, all four sites):
```python
if (12 - PLAYER_TURN_WINDOW_MARGIN) <= centerx % TILE_WIDTH <= (18 + PLAYER_TURN_WINDOW_MARGIN):
```
Inner wall guard (`level[...] < 3`) is preserved on every branch — widening only enlarges the timing window, never permits an illegal turn. Do NOT factor into a shared helper with `Ghost.check_collisions` (D-15).

**Import pattern to extend** (`player.py:3-7`): add the new constant to the existing `from settings import (...)` block.
```python
from settings import (
    PLAYER_SPEED, PLAYER_START_X, ..., HALF_TILE, BOARD_COLS,
    PLAYER_WRAP_RIGHT_EDGE, ..., PLAYER_TURN_WINDOW_MARGIN,
)
```

---

### `settings.py` :: new tunables (config)

**Analog:** existing centralized constants, `settings.py:10` (`PLAYER_SPEED = 2`) and `settings.py:21` (`HALF_TILE = 15`). Append a documented FAIR block; each constant trivially editable for the D-10 playtest.
```python
# Phase 8 — Fairness Pass tunables (D-03/D-07/D-09). Dial during the D-10 playtest.
GHOST_CATCH_DISTANCE = 15          # FAIR-01 center-to-center catch radius (px); HALF_TILE-ish
GHOST_CHASE_SPEED_NUM = 37         # FAIR-02 integer-rational chase step numerator
GHOST_CHASE_SPEED_DEN = 20         # 37/20 = 1.85 px/frame avg; +1 to NUM ≈ +0.05 px/frame
PLAYER_TURN_WINDOW_MARGIN = 6      # FAIR-03 pre-turn widening each edge (px), ~4–6px early
```
Keep `PLAYER_SPEED = 2` unchanged (D-07). Pure integer math — no float, no new import, cannot trip the determinism guard.

---

### `tests/test_player_micro.py` (NEW — characterization test)

**Analog:** `tests/test_ghost_micro.py` (closest existing structure; no player-level characterization test exists today — RESEARCH Wave 0).

**Module docstring + headless construction pattern to mirror** (`test_ghost_micro.py:1-57`): explains it's a CHARACTERIZATION test (pins what the code DOES), relies on `conftest.py` setting SDL dummy drivers before pygame import, and deep-copies the board per case to prevent leakage.

**Fixture pattern** (`test_ghost_micro.py:27-38`):
```python
@pytest.fixture(scope="module")
def screen():
    pygame.display.init()
    surf = pygame.display.set_mode((900, 950))
    yield surf
```

**Constructor-helper pattern** (`test_ghost_micro.py:41-57`) — for the player, the analog is simpler (`Player(screen)` then set `x`/`y`/`direction`, call `check_position(copy.deepcopy(board.boards))`):
```python
import copy
import board
from player import Player

def make_player(screen, x, y, direction):
    p = Player(screen)
    p.x, p.y, p.direction = x, y, direction
    return p
```

**Assertion pattern to copy** (`test_ghost_micro.py:68-77`): construct at a crafted junction, call the method, assert the exact `turns` list literal. For FAIR-03: assert `check_position` yields the widened `turns_allowed` at a junction residue that is now in-window with `PLAYER_TURN_WINDOW_MARGIN` but was out-of-window before, plus a default-margin baseline. (Companion pure-Python unit tests for the FAIR-02 accumulator step sequence and the FAIR-01 catch helper are also Wave 0 gaps — no pygame needed for those.)

## Shared Patterns

### Tunables live in `settings.py`
**Source:** `settings.py:10,21` (centralized dims/speeds)
**Apply to:** all three FAIR changes — `GHOST_CATCH_DISTANCE`, `GHOST_CHASE_SPEED_NUM/DEN`, `PLAYER_TURN_WINDOW_MARGIN`. No inline magic numbers (D-03).

### Integer-only math (determinism doctrine)
**Source:** trace contract `harness/trace.py:7-8`; guard `tests/test_determinism_guard.py`
**Apply to:** FAIR-01 (squared distance, no `sqrt`) and FAIR-02 (positions stay integer; step is 1 or 2 via accumulator — never a fractional `x_pos`). No new import, no float, no `random`/wall-clock.

### Byte-identical ghost decision logic (the guard)
**Source:** `ghost.py` (entire), proven green by `tests/test_ghost_micro.py` (passes `speed=2` directly)
**Apply to:** FAIR-02 (do all speed work in `game.py`, never edit `ghost.py`) and FAIR-03 (widen player windows only, never `ghost.py:343,352,363,372`). Proof artifact: `pytest tests/test_ghost_micro.py tests/test_determinism_guard.py` must stay green with zero edits.

### Headless test construction
**Source:** `tests/test_ghost_micro.py:27-57` + `tests/conftest.py` (SDL dummy drivers, `--bless` flag)
**Apply to:** the new `tests/test_player_micro.py`.

## No Analog Found

None. Every change site is an in-place edit of existing first-party code, and the one new file (`tests/test_player_micro.py`) has a strong sibling analog in `tests/test_ghost_micro.py`.

## Re-bless note (not a code analog, but planner must sequence it)

The golden fixtures (`tests/golden/*/trace.jsonl` + `frame_hashes.txt`, 9 scenarios) encode OLD outcomes and shift under all three changes. Single `pytest --bless` on **Linux/Docker only** after D-10 sign-off (memory `golden-rebless-linux-docker.md`; Pitfall 3). Verify each terminal scenario still terminates (`death` reaches `game_over`, `ghost_eat` registers an eat under the 15px radius) before trusting the bless — recorded inputs may need re-authoring (Pitfall 2 / RESEARCH Open Q1).

## Metadata

**Analog search scope:** `game.py`, `player.py`, `ghost.py`, `settings.py`, `tests/`
**Files scanned:** 6 (4 source change sites + 2 test files for the new-test analog)
**Pattern extraction date:** 2026-06-29
</content>
</invoke>
