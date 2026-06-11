# Phase 1: Test Safety Net - Pattern Map

**Mapped:** 2026-06-11
**Files analyzed:** 17 (16 created, 1 modified)
**Analogs found:** 14 / 17 (3 greenfield — no in-repo analog, use RESEARCH.md patterns)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `game.py` (`tick()` extraction) | game-logic (MODIFIED) | event-driven / request-response | `game.py` `Game.run()` (lines 456-555) — same file | exact (self-split) |
| `harness/headless.py` | utility (harness) | config / setup | RESEARCH §Pattern 2 (no in-repo analog) | none — research |
| `harness/trace.py` | utility (harness) | transform (state→dict) | `game.py` `get_targets()` (226) + Ghost attrs | role/data-match |
| `harness/replay.py` | driver (harness) | event-driven replay | `game.py` `Game.run()` loop (458-552) | role-match (loop shape) |
| `harness/capture.py` | utility (harness) | file-I/O (PNG/GIF) | RESEARCH §Pattern 5 (no in-repo analog) | none — research |
| `harness/play_loop.py` | driver (harness) | event-driven (observe→act) | `harness/replay.py` (sibling) + §Pattern 6 | role-match |
| `harness/__init__.py` | config | n/a | empty package init | trivial |
| `tests/conftest.py` | config / fixture | setup (import patch) | `tests/test_api_service.py` fixtures + §Pattern 8 | role-match |
| `tests/test_golden_traces.py` | test | characterization | `tests/test_api_service.py` (style) | role-match |
| `tests/test_ghost_micro.py` | test | unit (state→assert) | `tests/test_local_storage.py` (fixture style) | role-match |
| `tests/test_determinism_guard.py` | test | static / batch (grep source) | `tests/test_local_storage.py` (plain pytest) | partial |
| `tests/test_submit_score.py` | test | request-response (mock I/O) | `tests/test_api_service.py` | exact |
| `tests/test_get_leaderboard.py` | test | request-response (mock I/O) | `tests/test_api_service.py` | exact |
| `tests/golden/manifest.json` | config (data registry) | CRUD (iterated by CI) | no analog (Claude's discretion) | none — research |
| `tests/golden/<scenario>/input.jsonl` | fixture (data) | event stream (sparse) | RESEARCH §Pattern 4 schema | none — research |
| `requirements-dev.txt` | config | n/a | `requirements.txt` (flat, root) | exact (shape) |
| `.github/workflows/ci.yml` | config (CI) | n/a | RESEARCH §Pattern 9 (no `.github/` today) | none — research |

## Pattern Assignments

### `game.py` — `tick()` extraction (game-logic, MODIFIED — behavior-preserving)

**Analog:** `game.py` `Game.run()` itself — lines 456-555 (read in full).

**The exact split (verified):** everything between `self.timer.tick(FPS)` (line 462, EXCLUSIVE) and `pygame.display.flip()` (line 552, INCLUSIVE) — i.e. **lines 464-552 verbatim** — becomes `tick()`. Leave the `while`/`return_to_menu`/`timer.tick(FPS)` scaffolding in `run()`.

**Loop body to move (lines 546-552, the tail that must stay in order):**
```python
            # Input
            running = self.handle_events()       # line 547 — propagate as tick() return
            self.player.update_direction()
            self.player.wrap_around()
            self.check_ghost_in_box()
            pygame.display.flip()                # line 552 — last line in tick()
```

**Order-dependent guard to preserve EXACTLY (lines 519-520, 539-544) — do NOT hoist `player_circle`:**
```python
            if not self.eat_freeze:
                player_circle = self.player.draw(self.counter)   # defined only when not eat_freeze
            ...
            if not self.dying and not self.eat_freeze and not self.starting:
                self.check_collisions()
                self.check_ghost_collisions(player_circle)        # referenced only when defined
```

**Target shape (from RESEARCH §Pattern 1):** `run()` keeps `timer.tick(FPS)` ONLY (D-17); `tick()` never calls it; `tick()` returns `running` (False on `pygame.QUIT`, mirroring `handle_events`). Validate via baseline-trace-first (instrument unmodified `run()` after line 552, capture, extract, assert byte-identical, remove instrumentation).

---

### `harness/trace.py` (utility, transform)

**Analog:** `game.py` `get_targets()` (line 226) + flat Ghost attrs on `Game`.

**Source of every trace field (verified):** `self.targets = self.get_targets()` is set each frame at **game.py:531**; ghost `*_x/*_y/*_direction/*_dead/*_box` are flat attributes on the `Game` object; `dots_remaining` derives from `g.level` (tile codes 1=dot, 2=big dot). `capture_state(g)` is a pure READER — no new game logic. Full schema in RESEARCH §Pattern 3 (D-03/D-04). `g._frame` is set by the driver, not `game.py`.

---

### `harness/replay.py` (driver, event-driven)

**Analog:** the `Game.run()` loop shape (game.py:458-552) — the replay driver is the same per-frame loop with `timer.tick(FPS)` removed, event injection added before `game.tick()`, and `capture_state` after.

**Key conventions to mirror:**
- Inject via `pygame.event.post(pygame.event.Event(KEYDOWN, key=...))` — the real input path consumed by `handle_events()` (`pygame.event.get()` at game.py:420; key reads at game.py:424-431).
- Terminal: break on `game.game_over or game.game_won` (D-19); `else`-clause on the `for range(frame_cap)` raises on soft-lock. Full driver in RESEARCH §Pattern 4.

---

### `tests/conftest.py` (config / fixture)

**Analog:** `tests/test_api_service.py` lines 7-18 (the house mock-the-I/O fixture style) + RESEARCH §Pattern 8.

**House fixture style to extend (test_api_service.py:7-18):**
```python
@pytest.fixture
def service():
    return ApiService("https://fake-submit.run.app", "https://fake-leaderboard.run.app")

def _mock_response(data, status=200):
    mock = MagicMock()
    mock.status = status
    mock.read.return_value = json.dumps(data).encode()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return mock
```

**conftest adds (D-15, first config file in repo):** `sys.path.insert(0, repo_root)`; set `SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy` before any pygame import; firebase pre-import patch fixtures (`patch("firebase_admin.initialize_app")`, `patch("firebase_admin._apps", new=[])`, `patch("firebase_admin.firestore.client")`) that `importlib.import_module` the working-tree cloud-fn module with firebase mocked; `pytest_addoption` for `--bless` (RESEARCH §Pattern 8 + "Don't Hand-Roll").

---

### `tests/test_submit_score.py` & `tests/test_get_leaderboard.py` (test, request-response)

**Analog:** `tests/test_api_service.py` (exact style match — patch the I/O seam, assert the return tuple).

**Validators under test (READ — `cloud_functions/submit_score/main.py`):**
```python
if not machine_id:                              # → 400 "Missing machine_id"  (main.py:47-48)
    return ({"success": False, "error": "Missing machine_id"}, 400, headers)
if not re.match(r"^[A-Z]{3}$", initials):       # → 400 "Invalid initials"    (main.py:49-50)
    return ({"success": False, "error": "Invalid initials"}, 400, headers)
if not isinstance(score, int) or score < 0 or score > MAX_SCORE:  # 400 "Invalid score" (51-52)
    return ({"success": False, "error": "Invalid score"}, 400, headers)
```

**Return-tuple shape to assert (main.py:58):** `({"success": True, "is_new_best": is_new_best}, 200, headers)` — mirror `test_api_service.py`'s "call the function, assert the dict" style on the FIRST tuple element.

**`is_new_best` upsert under mock (main.py:14-25):** `@firestore.transactional` decorates `_update_score`; it calls `doc_ref.get(transaction=...)`, checks `doc.exists` and `doc.to_dict().get("score", 0)`. Mock the `db.collection().document().get()` chain (`.exists`, `.to_dict.return_value`). SPIKE flagged (RESEARCH A2 / Pitfall 2): may need `patch(...main.firestore.transactional, lambda f: f)`.

**`get_leaderboard` entry shape (READ — get_leaderboard/main.py:30-33):** `{"initials": data["initials"], "score": data["score"]}` from a mocked `query.stream()`; returns `({"entries": entries}, 200, headers)`.

**D-16:** import the **working-tree** `cloud_functions/*/main.py` (uncommitted mods are what ships).

---

### `tests/test_ghost_micro.py` (test, unit)

**Analog:** `tests/test_local_storage.py` (plain-pytest + fixture style) + RESEARCH §Pattern 7.

**Fixture style to mirror (test_local_storage.py:7-11):**
```python
@pytest.fixture
def temp_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path
```

**Ghost construction signature (READ — ghost.py:6-7, do NOT modify ghost.py):**
```python
Ghost(x_coord, y_coord, target, speed, img, direct, dead, box, id,
      screen, powerup, eaten_ghost, spooked_img, dead_img, level)
```
`__init__` immediately calls `check_collisions()` (pure tile math, ghost.py:43) and `draw()` (blit — harmless under SDL dummy, D-14). Pass dummy `pygame.Surface((45,45))` for images and a `copy.deepcopy(board.boards)` for `level` (Pitfall 4).

**Targets to assert (READ-ONLY):** `move_blinky` (ghost.py:256), `move_inky` (362), `move_pinky` (484), `move_clyde` (117), `check_collisions` (43). Assert the EXACT `(x, y, dir)` each `move_*` returns at hand-curated decisive board states (D-13).

---

### `tests/test_determinism_guard.py` (test, static)

**Analog:** `tests/test_local_storage.py` plain-pytest shape (closest — no I/O mock needed).

**Pattern:** read `game.py`/`ghost.py`/`player.py` source as text, assert none of `random`/`randint`/`shuffle`/`time.time`/`get_ticks`/`datetime` appear (D-12). Self-contained static check — no harness, no pygame.

---

### `requirements-dev.txt` (config)

**Analog:** `requirements.txt` (root, READ) — flat, one package per line:
```
pygame
pyinstaller
```
**Mirror that flat shape, but PINNED (D-20).** Pins from RESEARCH §Standard Stack — `firebase-admin==6.*` and `functions-framework==3.*` MUST match `cloud_functions/*/requirements.txt` (NOT latest 7.x/3.10.x):
```
pytest==8.4.2
pygame==2.6.1
Pillow==11.0.0
firebase-admin==6.5.0
functions-framework==3.8.1
```
(exact patch versions chosen at plan time; majors are the hard constraint).

---

### Files with no in-repo analog — use RESEARCH.md verbatim

| File | Use |
|------|-----|
| `harness/headless.py` | RESEARCH §Pattern 2 (`SDL_*=dummy` before `import pygame`, then `display.init()/font.init()/mixer.init()/set_mode()`) |
| `harness/capture.py` | RESEARCH §Pattern 5 (`pygame.image.save`, blit montage, Pillow GIF) |
| `harness/play_loop.py` | RESEARCH §Pattern 6 (observe→decide→act; sibling of `replay.py`) |
| `tests/golden/manifest.json` + `input.jsonl` | RESEARCH §Pattern 4 schema + §Structure (Claude's discretion on layout) |
| `.github/workflows/ci.yml` | RESEARCH §Pattern 9 (`ubuntu-latest`, py3.12, `SDL_*=dummy`, push any branch + PRs to main) |

## Shared Patterns

### Mock-the-I/O test style (the HOUSE STYLE)
**Source:** `tests/test_api_service.py` lines 1-18
**Apply to:** `tests/test_submit_score.py`, `tests/test_get_leaderboard.py`, `tests/conftest.py`
```python
import json
from unittest.mock import patch, MagicMock
import pytest
# patch the external boundary (urlopen → firebase_admin), build a MagicMock with
# __enter__/__exit__ + .return_value, call the function, assert the returned dict/tuple.
```
New cloud-fn tests patch `firebase-admin` (in conftest, pre-import) where api_service tests patch `api_service.urlopen`.

### `tmp_path`/`monkeypatch` fixture style
**Source:** `tests/test_local_storage.py` lines 7-11
**Apply to:** `tests/test_ghost_micro.py` (and any test needing isolated state)

### Headless construction (no source change)
**Source:** RESEARCH §Pattern 2 + D-14
**Apply to:** all harness modules and `tests/test_ghost_micro.py` — set `SDL_*=dummy` BEFORE `import pygame` (also in conftest and CI `env:`, belt-and-braces per Pitfall 3).

### Behavior-preserving "thin reader" principle
**Source:** RESEARCH "Key insight" + game.py:531 (`get_targets`), ghost.py:6-26 (flat attrs)
**Apply to:** `harness/trace.py`, `harness/replay.py` — read existing `Game`/`Ghost` state; never add game logic; never touch `ghost.py`.

### Shared mutable board — deep-copy
**Source:** game.py:23 (`copy.deepcopy(boards)`) / Pitfall 4
**Apply to:** `tests/test_ghost_micro.py` and every scenario — deep-copy `board.boards` to avoid dot leakage.

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `harness/headless.py` | utility | config | No headless-init code exists yet; use §Pattern 2 |
| `harness/capture.py` | utility | file-I/O | No PNG/GIF code exists; Pillow is the one new dep; use §Pattern 5 |
| `.github/workflows/ci.yml` | config | n/a | No `.github/` directory today (first CI); use §Pattern 9 |

## Metadata

**Analog search scope:** `tests/`, `cloud_functions/*/`, `game.py`, `ghost.py`, repo root (`requirements.txt`).
**Files read for excerpts:** `tests/test_api_service.py`, `tests/test_local_storage.py`, `cloud_functions/submit_score/main.py`, `cloud_functions/get_leaderboard/main.py`, `game.py` (run loop 456-555), `ghost.py` (init + check_collisions, move_* signatures), `requirements.txt`.
**Pattern extraction date:** 2026-06-11
