# Phase 3: Box-Bug Fix + Hygiene - Pattern Map

**Mapped:** 2026-06-12
**Files analyzed:** 11 modified files + 1 new (temporary) test artifact
**Analogs found:** 11 / 11 (10 are self-analog surgical edits; 1 new test maps to the deleted Phase-2 oracle preserved in git history + the live `make_ghost` harness)

This is a bug-fix + repo-hygiene phase. For the surgical edits the "analog" IS the file in its current state — exact lines are cited below and verified against live code (2026-06-12). The one genuinely new artifact (the `get_targets` differential oracle + `check_collisions` belt-check) maps to the Phase-2 one-shot oracle (deleted by design; reconstructed from `02-02-SUMMARY.md`) and the live `make_ghost` headless harness in `tests/test_ghost_micro.py`.

## File Classification

| File | Role | Data Flow | Change kind | Closest Analog | Match Quality |
|------|------|-----------|-------------|----------------|---------------|
| `geometry.py` | config/constants | transform | constant-collapse + docstring | itself (geometry.py:18-20) | self / exact |
| `game.py` | controller (game loop) | transform (targeting) | import repoint + 8 call-site renames | itself (game.py:18, 240-301) | self / exact — THE behavior-delta site |
| `ghost.py` | model (entity) | request-response (collision) | name-only import + 1 call-site rename | itself (ghost.py:4, 384) | self / exact — value unchanged |
| `requirements.txt` | config | n/a | unpinned → `==` pins | itself (lines 1-2) | self / exact |
| `.gitignore` | config | n/a | dedupe `/.claude`, remove `CLAUDE.md` line | itself (lines 23-26) | self / exact |
| `.claude/settings.local.json` | config (tracked) | n/a | `git rm --cached` | n/a | self |
| `CLAUDE.md` | docs | n/a | prose timing reconcile + un-ignore/track | itself ("Ghost Box Exit") + settings.py:56-58 | self / exact |
| `menu.py` | controller (UI) | event-driven | dead docstring removal | itself (menu.py:12) | self / exact |
| `assets/ghost_images/`, `assets/player_images/` | assets | file-I/O | folder deletion | n/a (byte-dupes of `assets/ghosts/`, `assets/pacman/`) | self |
| `build.py` | config (build) | file-I/O | none (reference only — `--add-data` ships folder) | itself (build.py:8) | n/a |
| **`tests/test_box_bounds_oracle.py`** (NEW, temporary) | test | transform | NEW differential oracle + belt-check | Phase-2 `tests/test_mover_oracle.py` (deleted, in git) + `make_ghost` | role+flow exact |

## Pattern Assignments

### `geometry.py` (constants, transform) — BUG-01 core

**Analog:** itself. Current state (verified geometry.py:18-20):

```python
# Two distinct box rectangles (x_lo, x_hi, y_lo, y_hi) — kept separate per D-13/D-14.
GHOST_BOX_BOUNDS_COLLISION = (350, 550, 360, 480)   # ghost.py check_collisions box test
GHOST_BOX_BOUNDS_TARGET = (340, 560, 340, 500)      # game.py get_targets eaten-ghost checks
```

**Collapse to** a single `GHOST_BOX_BOUNDS = (350, 550, 360, 480)` (the COLLISION value wins per D-01). The `in_box(x, y, bounds)` predicate at geometry.py:33-36 is UNCHANGED — it already takes `bounds` as a parameter, so only the module-level constant names change.

**Docstring must also change** (geometry.py:7-14 currently says "intentionally kept as TWO DISTINCT named constants ... Do NOT merge these" and a "D-15 landmine" line). That prose now contradicts the fix — reconcile it. Per Claude's Discretion, optionally leave a one-line comment at the unified constant noting the historical divergence to guard against a future re-split.

---

### `game.py` (controller, targeting transform) — THE behavior-delta site (D-02)

**Analog:** itself.

**Import** (game.py:18):
```python
from geometry import in_box, GHOST_BOX_BOUNDS_TARGET
```
→ repoint to `from geometry import in_box, GHOST_BOX_BOUNDS`.

**Core pattern — the 8 call sites** (game.py:240-301, inside `get_targets`). Every eaten/returning-ghost branch uses the identical idiom (verified 8 occurrences across the powerup and non-powerup branches, for blinky/inky/pinky/clyde):
```python
if in_box(self.blinky_x, self.blinky_y, GHOST_BOX_BOUNDS_TARGET):
    blink_target = SCATTER_EATEN_TARGET
else:
    blink_target = (self.player.x, self.player.y)
```
Mechanical change: replace every `GHOST_BOX_BOUNDS_TARGET` with `GHOST_BOX_BOUNDS`. This is the ONLY value change in the milestone (tighter box → an eaten ghost in the ring between the two old rectangles switches from "aim at gate" to "chase player" a touch sooner).

---

### `ghost.py` (model, collision) — name-only change, value unchanged (D-02 guardrail)

**Analog:** itself.

**Import** (ghost.py:4):
```python
from geometry import in_box, GHOST_BOX_BOUNDS_COLLISION
```
→ `from geometry import in_box, GHOST_BOX_BOUNDS`.

**Single call site** (ghost.py:384, in `check_collisions`):
```python
if in_box(self.x_pos, self.y_pos, GHOST_BOX_BOUNDS_COLLISION):
    self.in_box = True
```
→ rename to `GHOST_BOX_BOUNDS`. Value is identical `(350,550,360,480)`, so `in_box`/movement/box-exit are byte-identical by construction. The 15 micro-tests in `tests/test_ghost_micro.py` stay green untouched.

---

### `tests/test_box_bounds_oracle.py` (NEW test, transform) — HIGHEST-VALUE map

**Analogs:**
1. **Phase-2 oracle** `tests/test_mover_oracle.py` + `tests/_legacy_movers.py` — deleted (one-shot lifecycle, D-06), preserved in git history; reconstructed from `.planning/phases/02-safe-refactor/02-02-SUMMARY.md`.
2. **Live `make_ghost` harness** at `tests/test_ghost_micro.py:41-57`.

**Harness pattern — `make_ghost` builds a ghost in an arbitrary state headless** (tests/test_ghost_micro.py:41-57):
```python
def make_ghost(screen, x, y, target, speed, direction, ghost_id,
               dead=False, box=False, powerup=False):
    img = pygame.Surface((45, 45))
    eaten_ghost = [False, False, False, False]
    return Ghost(
        x, y, target, speed, img, direction, dead, box, ghost_id,
        screen, powerup, eaten_ghost, img, img,
        copy.deepcopy(board.boards),   # Pitfall 4: never pass shared board by ref
    )
```
Module-scoped headless `screen` fixture (test_ghost_micro.py:27-38) via `pygame.display.set_mode((900,950))`; `conftest.py` forces `SDL_VIDEODRIVER=dummy`. Use this same harness for both the `get_targets` and `check_collisions` enumeration. NOTE: `get_targets` is a method on `Game`, not `Ghost` — the oracle will need to construct a `Game` (or call the targeting branch with synthetic ghost x/y + eaten_ghost/dead/powerup state). Mirror the `_new_game()` helper in `tests/test_golden_traces.py:62-66` for headless `Game` construction.

**Oracle pattern — frozen-legacy + `itertools.product` exhaustive enumeration, assert old-vs-new** (Phase-2 lineage, from 02-02-SUMMARY.md §"Synthetic-exhaustive differential oracle"):
- Freeze the OLD logic (TARGET box `(340,560,340,500)`) as a local frozen copy alongside the NEW (COLLISION box `(350,550,360,480)`) — Phase 2 used `tests/_legacy_movers.py` for this.
- Enumerate with `itertools.product`. Phase-2 space (per ghost): `direction(4) × 16 turns-combos × 3×3 target-sign × in_box(2) × dead(2) × speed{1,2,4} × 5 wrap-x = 34,560`; ×4 = 138,240 cases, ~84s runtime — well inside a one-shot budget. For THIS oracle, enumerate **ghost position × board × `dead`/`eaten`/`powerup`** (D-03). The position grid MUST densely cover the ring (in TARGET, not in COLLISION): x near {340,350,550,560}, y near {340,360,480,500}.
- **Assertion (D-03):** `get_targets` old vs new differ ONLY for positions in the ring (in TARGET, not in COLLISION) and are IDENTICAL everywhere else.
- **Belt-check (D-04):** the SAME oracle asserts `check_collisions` output is byte-identical old-vs-new across all enumerated states — proving the name-only rename.

**Teeth-check pattern (D-05, mutation-canary, from 02-02-SUMMARY.md §"Mutation-canary attestation"):** before trusting green, perturb `get_targets` OUTSIDE the ring and confirm the oracle goes RED, then revert. Phase-2 precedent: flipped `g.x_pos += g.speed` → `-= g.speed`, confirmed oracle + golden both RED, reverted to green, `git diff` empty.

**Lifecycle (D-05/D-06):** prove oracle + belt-check green in ONE commit, then DELETE both. The re-blessed golden traces + 15 micro-tests are the permanent guard. Phase-2 precedent: oracle proven, then `tests/_legacy_movers.py` + `tests/test_mover_oracle.py` deleted in one commit (02-02-SUMMARY.md §"Cleanup").

**Golden re-bless pattern (D-06)** — `tests/test_golden_traces.py:188-212`, the `--bless` branch:
```python
if request.config.getoption("--bless"):
    old = read_jsonl(trace_path) if os.path.exists(trace_path) else []
    write_jsonl(replayed, trace_path)
    diff = diff_traces(old, replayed)
    print(f"\n=== BLESS DIFF [{entry['name']}] ({len(replayed)} frames) ===")
    print(diff if diff else "(no change — golden already matched)")
    return  # do NOT assert in bless mode
```
Per-frame `target` tuple is already recorded (Phase 1 D-03), so box-edge target diffs are directly visible. Re-bless ONLY the `box_edge`/`box_exit` scenarios, and **only in Linux CI** (D-08 — never bless on Windows; the frame-hash manifest is a Windows placeholder). Confirm the diff shows ONLY box-edge frames move; every other trace byte-identical.

---

### `requirements.txt` (config) — HYG-01 (D-10)

**Analog:** itself. Current (verified):
```
pygame
pyinstaller
```
→ exact `==` pins for both, sourced via `pip freeze` from the CI-green env (Claude's Discretion for the exact strings). Pin `pyinstaller` too (reproducible `.exe`). Backend `cloud_functions` pins (`3.*`/`6.*`) untouched — client-only scope.

---

### `.gitignore` (config) — HYG-02 (D-11)

**Analog:** itself. Current (verified lines 23-26):
```
/.vscode
/.claude
/.claude
CLAUDE.md
```
Dedupe the duplicate `/.claude` (keep one), and REMOVE the `CLAUDE.md` line (line 26) so the doc becomes trackable. The single `/.claude` line stays (local GSD tooling). Pair with `git rm --cached .claude/settings.local.json` (verified currently tracked).

---

### `CLAUDE.md` (docs) — HYG-03 (D-12)

**Analog:** itself + `settings.py:56-58` (the source of truth, verified):
```python
BOX_EXIT_DELAY_INKY = 0
BOX_EXIT_DELAY_PINKY = 30
BOX_EXIT_DELAY_CLYDE = 60
```
The "Ghost Box Exit" prose says "Pinky after ~2 sec, Clyde after ~4 sec". At 60 fps, 30/60 frames = ≈0.5 s / 1 s. Edit the DOC prose to ≈0.5 s / 1 s (Inky = 0 already consistent). **Do NOT change the constants** — that would be a second unsanctioned behavior change. Also un-ignore (above) and `git add` CLAUDE.md so the fix is durable.

---

### `menu.py` (controller, UI) — HYG-03 (D-12)

**Analog:** itself. Verified menu.py:12:
```python
"""Display main menu. Returns the selected option string: 'Play', 'Leaderboard', 'Change Initials', or 'Quit'."""
```
`MENU_OPTIONS = ["Play", "Leaderboard", "Quit"]` (no "Change Initials"). Remove the dead `'Change Initials'` reference from the docstring only — no code change.

---

### `assets/ghost_images/`, `assets/player_images/` (assets) — HYG-04 (D-13)

**Analog:** none needed — verified present in `assets/` (live folders are `assets/ghosts/`, `assets/pacman/`). Byte-duplicate filenames; only reference is the design spec instructing deletion. Delete both folders. `build.py:8 --add-data=assets;assets` ships the whole folder, so deletion also slims the bundle. Followed by the D-14 `.exe` rebuild + smoke-run gate (human/Windows, outside CI).

## Shared Patterns

### Headless ghost/game construction
**Source:** `tests/test_ghost_micro.py:41-57` (`make_ghost`), `tests/test_golden_traces.py:62-66` (`_new_game`), `tests/conftest.py` (SDL dummy env).
**Apply to:** the new oracle. Always `copy.deepcopy(board.boards)` per case (Pitfall 4).

### One-shot differential oracle + mutation-canary + delete
**Source:** Phase-2 (deleted; `.planning/phases/02-safe-refactor/02-02-SUMMARY.md`).
**Apply to:** the BUG-01 isolation proof (D-03/D-04/D-05). Frozen-legacy + `itertools.product`; assert old-vs-new; canary RED-then-revert; delete in the proving commit.

### Golden `--bless` re-record (Linux only)
**Source:** `tests/test_golden_traces.py:188-212`.
**Apply to:** re-blessing `box_edge`/`box_exit` frames after the box fix (D-06/D-08). Never bless on Windows.

### Atomic, independently-green commits
**Source:** Phase-2 per-ghost discipline (02-02-SUMMARY.md commit list).
**Apply to:** D-09 — four behavior-neutral hygiene commits (deps / untrack+gitignore / docs / dead assets), each CI-green, THEN the isolated final box-fix commit (the only trace-touching commit, carrying the oracle).

## No Analog Found

None requiring RESEARCH.md fallback. Every file maps to itself (surgical edit) or to the Phase-2 oracle + live `make_ghost` harness (the new test). The one nuance: `get_targets` lives on `Game` (game.py), not `Ghost`, so the oracle constructs a headless `Game` (via the `_new_game` pattern) rather than only `make_ghost` — but both harnesses already exist.

## Metadata

**Analog search scope:** `geometry.py`, `game.py`, `ghost.py`, `menu.py`, `settings.py`, `requirements.txt`, `.gitignore`, `build.py`, `assets/`, `tests/` (all), `.planning/phases/02-safe-refactor/02-02-SUMMARY.md`.
**Files scanned:** ~14.
**Pattern extraction date:** 2026-06-12.
