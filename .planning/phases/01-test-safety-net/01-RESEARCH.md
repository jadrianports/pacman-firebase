# Phase 1: Test Safety Net - Research

**Researched:** 2026-06-11
**Domain:** Deterministic record/replay characterization testing for a PyGame game + headless CI + cloud-function validator tests
**Confidence:** HIGH (libraries verified via Context7 + PyPI; harness mechanics derived from reading the actual source)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions (D-01 … D-20)

- **D-01:** Canonical set = targeted short scripts + ONE long Claude-played session (both).
- **D-02:** Targeted scripts = the design spec's 5 (box-exit, power-pellet chase, ghost-eat, death, win) PLUS three extra: ghost-at-box-edge approaches (Phase 3 BUG-01), tunnel wrap-around (Phase 2 wrap math), dead-ghost return-to-box/"eyes" (`move_clyde` fallback Phase 2 collapses). = 8 scripted scenarios.
- **D-03:** Per-frame snapshot = `frame`, `pacman{x,y,dir}`, `ghosts[{name,x,y,dir,dead,box}]`, `score`, `lives`, `powerup`, `dots_remaining`, `game_over`, `game_won` PLUS each ghost's current `target` tuple.
- **D-04:** Do NOT capture internal counters (box-exit timers, powerup countdown, `eat_freeze`/`starting`/`dying`/`flicker`/`counter`).
- **D-05:** Comparison is EXACT. All trace values are integers → platform-independent, no float policy.
- **D-06:** Commit ONLY the JSONL golden traces + input sequences. All PNG/montage/GIF gitignored + regenerated on demand.
- **D-07:** Re-bless via `pytest --bless` flag that regenerates traces AND prints a human-readable diff.
- **D-08:** Linux-only (`ubuntu-latest`), pinned Python + pygame; that pinned env is the canonical bless environment.
- **D-09:** CI runs on push to any branch + PRs to `main`; green is a required check (branch protection on `main`). Remote: `github.com/jadrianports/pacman-firebase` (verified).
- **D-10:** Split capture from hunt: record ONE Claude session's per-frame inputs → deterministic CI-replayable golden. Live observe→decide→act adversarial bug-hunt stays a MANUAL phase-verification gate.
- **D-11:** Standing per-frame invariants on EVERY replay: `score ∈ [0, 500000]`; Pac-Man center never inside a wall tile; no soft-lock (position changes within N frames while `moving` and NOT in `eat_freeze`/`starting`/`dying`).
- **D-12:** Determinism guard test that HARD-FAILS CI if `random`/`randint`/`shuffle`/`time.time`/`get_ticks`/`datetime` appears in `game.py`/`ghost.py`/`player.py`.
- **D-13:** Hand-curate decisive board states per ghost (multi-way intersection, tunnel mouth, box edge, flee-vs-chase), informed by states the long golden session visits; assert exact turn each `move_*` makes.
- **D-14:** Construct `Ghost` headlessly against SDL-dummy surface (C1 side-effect harmless); NO change to `ghost.py`.
- **D-15:** Mock `firebase-admin` — patch `firebase_admin.initialize_app`/`firestore.client` in `conftest.py` BEFORE import. Test validators via the HTTP entrypoint + `is_new_best` upsert vs a mocked transaction/doc. No emulator (no Java).
- **D-16:** Tests target the CURRENT working-tree `cloud_functions/*/main.py` (uncommitted mods are what ships).
- **D-17:** `timer.tick(FPS)` stays ONLY in interactive `run()`; harness steps `tick()` in a tight uncapped loop; `tick()` must NOT read the throttle return value.
- **D-18:** Scripted input format = sparse `{frame, key}` event JSONL; recorded sessions serialize to the same format; injection via `pygame.event.post` upstream of `handle_events`.
- **D-19:** Each scenario runs to a natural terminal state (`game_won`, or `game_over` after all lives) bounded by a generous safety frame cap (doubles as soft-lock backstop).
- **D-20:** Test/harness deps in a new pinned `requirements-dev.txt`. PNG via pygame `image.save` + surface-blit montages (zero new dep); Pillow ONLY for GIF. All dev-only.

### Claude's Discretion (settled in this research — see §Discretion Decisions)
- Golden-artifact directory layout + scenario manifest/registry format.
- `conftest.py` `sys.path`/import handling + firebase-admin pre-import patch wiring.
- Scenario naming conventions + exact soft-lock frame threshold `N`.
- Exact pinned Python + pygame versions.

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope. (Refactor = Phase 2; box-bug fix + hygiene = Phase 3; arcade-accuracy + leaderboard hardening = later milestones.)
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HRN-01 | Game runs headless (SDL dummy) and is steppable via extracted `tick()` (behavior-preserving, `game.py` only) | §Pattern 1 (tick extraction recipe) + §Pattern 2 (headless init) — verified the exact `run()` loop body to split; `Clock.tick` return is discarded |
| HRN-02 | Record/replay captures full per-frame state trace, replays deterministically | §Pattern 3 (trace schema from `get_targets`/Ghost attrs) + §Pattern 4 (replay driver) |
| HRN-03 | Frames captured to PNG, assembled into montages + a GIF | §Pattern 5 (`pygame.image.save` + blit montage + Pillow GIF) |
| HRN-04 | Claude drives game in observe→decide→act loop to play + adversarially playtest | §Pattern 6 (play-loop driver) + D-10 split (recorded golden vs manual gate) |
| TST-01 | Golden-master traces of current behavior recorded + frozen | §Pattern 4 + §Golden-Master Coverage (8 scripted + 1 Claude session) |
| TST-02 | Micro per-ghost characterization tests (`check_collisions`, `move_*`) | §Pattern 7 (headless Ghost construction + decisive board states) |
| TST-03 | Cloud-function validator tests (initials regex, score type/range, best-score upsert) | §Pattern 8 (conftest pre-import firebase mock + HTTP entrypoint testing) |
| TST-04 | CI runs full suite headless on push | §Pattern 9 (GitHub Actions workflow) |
</phase_requirements>

## Summary

This is a **deterministic characterization-testing** phase. The enabling property — the game has zero
randomness and zero wall-clock timing (verified by reading `game.py`/`ghost.py`/`player.py`: all
timers are integer frame counters, all positions integer pixel math) — makes record/replay
frame-perfect. The entire safety net is built by exploiting that property and then locking it in with
a determinism guard.

The work decomposes cleanly into nine concrete patterns: (1) a behavior-preserving `tick()` extraction
from `Game.run()`'s while-body, validated against a baseline trace captured from the *unmodified*
loop; (2) headless init via `SDL_VIDEODRIVER=dummy`/`SDL_AUDIODRIVER=dummy`; (3) a trace schema
assembled from already-existing state (`get_targets()` returns the `target` tuples; Ghost x/y/dir/dead/box
live on the `Game` object); (4) a replay driver that injects sparse `{frame,key}` events via
`pygame.event.post`; (5) PNG capture via `pygame.image.save` + blit-based montages (zero new dep) with
Pillow only for the GIF; (6) a Claude play-loop; (7) headless micro per-ghost tests; (8) cloud-function
validator tests using a `conftest.py` pre-import firebase-admin patch + the Flask request entrypoint;
(9) a pinned `ubuntu-latest` GitHub Actions workflow.

**Primary recommendation:** Build in the design spec's Phase A→B order. **First** instrument the
existing `run()` to dump a baseline trace, **then** extract `tick()` and assert byte-identical
reproduction — this resolves the chicken-and-egg and is the single most important sequencing decision
in the phase. All libraries are current, well-known, and have verified Linux/py3.12 wheels.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Steppable game simulation (`tick()`) | Game logic (`game.py`) | — | `tick()` is extracted from `Game.run()`; lives with the orchestrator that owns all state |
| Headless rendering surface | PyGame / SDL (env config) | Harness setup | Driver sets `SDL_*=dummy` env *before* `import pygame`; surface is in-memory |
| Trace capture / serialization | Test harness (new `harness/` module) | Game logic (reads its state) | Harness reads `Game` attributes + `get_targets()`; does NOT add logic to game files |
| Input injection | Test harness → PyGame event queue | `Game.handle_events` (unchanged) | `pygame.event.post` feeds the real input path |
| Frame capture (PNG/montage/GIF) | Test harness (new) | PyGame `image.save` + Pillow | Pure dev-side; never enters the shipped `.exe` |
| Golden trace comparison | pytest tests | Harness (produces traces) | Tests own the assertions; harness owns generation |
| Cloud-function validation tests | pytest tests | conftest firebase mock | Validators are pure; mocked I/O at the conftest seam |
| CI orchestration | GitHub Actions (`.github/workflows/`) | pytest + pip | Runner installs pinned deps, runs headless pytest |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pytest` | 8.4.2 (pin) | Test runner, fixtures, `monkeypatch`, `--bless` flag via `pytest_addoption` | Already the project's runner (TESTING.md); `pytest_addoption` is the canonical custom-flag hook `[CITED: github.com/pytest-dev/pytest doc/en/example/simple.rst]` |
| `pygame` | 2.6.1 (pin) | Headless game execution, event injection, PNG capture | Game already targets pygame; 2.6.1 latest stable with verified `cp312 manylinux2014_x86_64` wheel `[VERIFIED: PyPI — pygame 2.6.1 cp312 linux wheel downloaded successfully]` |
| `Pillow` | 11.0.0+ (pin a specific patch) | GIF assembly ONLY (`Image.save(save_all, append_images, duration, loop)`) | The friendly PIL fork; `append_images` GIF API is stable since 3.4.0 `[CITED: github.com/python-pillow/pillow docs/handbook/tutorial.rst]` |

> **Pin choice rationale (D-08):** pygame **2.6.1** is the bless-environment pin. The version determines
> font rasterization and surface byte layout; since traces are *numeric game state* (not pixel hashes)
> the trace is pygame-version-robust, but PNG montages are not — so pin pygame to make montage
> regeneration reproducible. Pin Python to a single minor (recommend **3.12**, matches the local dev
> machine `Python 3.12.10` `[VERIFIED: local python --version]`).

### Supporting (cloud-function test deps — must match deployed pins)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `functions-framework` | `3.*` (match `cloud_functions/*/requirements.txt`) | Provides the Flask request the entrypoint expects | TST-03 — invoke `submit_score`/`get_leaderboard` entrypoints |
| `firebase-admin` | `6.*` (match deployed pin) | Module under patch; tests mock `initialize_app`/`firestore.client` | TST-03 — imported by the cloud functions; mocked before import |
| `Flask` | (transitive via functions-framework) | Build a `flask.Request` test double / `app.test_request_context()` | TST-03 — construct request objects without a server |

> **CRITICAL pin alignment:** `cloud_functions/submit_score/requirements.txt` and
> `cloud_functions/get_leaderboard/requirements.txt` both pin `functions-framework==3.*` and
> `firebase-admin==6.*` `[VERIFIED: read both files]`. `requirements-dev.txt` MUST install
> `firebase-admin==6.*` and `functions-framework==3.*` (NOT the latest 7.x/3.10.x) so the test
> environment matches what ships. Latest PyPI: firebase-admin 7.4.0, functions-framework 3.10.1
> `[VERIFIED: pip index versions]` — do not use 7.x.

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Mocking firebase-admin in conftest (D-15) | Firestore emulator | Emulator needs Java + a running process; slow, not CI-cheap, overkill for validator tests. Decision locked: mock. `[CITED: firebase-admin docs confirm emulator = separate process via FIRESTORE_EMULATOR_HOST]` |
| pygame `image.save` montages (D-20) | matplotlib / imageio grids | Adds a heavy dep for what `Surface.blit` does natively. Decision locked: blit. |
| Pillow for GIF (D-20) | pygame has no GIF writer; imageio | Pillow is the lightest standard GIF writer; one dev-only dep. Decision locked: Pillow. |

**Installation (`requirements-dev.txt`):**
```
pytest==8.4.2
pygame==2.6.1
Pillow==11.0.0
firebase-admin==6.5.0
functions-framework==3.8.1
```
> Pick exact patch versions at plan time (these are illustrative-but-valid; the `6.*`/`3.*` majors are
> the hard constraint). `requirements-dev.txt` is flat-but-pinned, matching the existing
> `requirements.txt` shape (D-20). Client `requirements.txt` stays unpinned this phase (pinning is
> HYG-01, Phase 3).

## Package Legitimacy Audit

> slopcheck could not be run — the sandbox classifier denied installing the (agent-chosen, unverified)
> `slopcheck` package. Per the graceful-degradation protocol, packages are tagged `[ASSUMED]` and the
> planner SHOULD gate the `requirements-dev.txt` install behind a `checkpoint:human-verify` task.
> **Mitigating facts:** all five packages were discovered/confirmed via Context7 (authoritative) and
> verified on PyPI; four of five are already in the project's manifests (`requirements.txt`,
> `cloud_functions/*/requirements.txt`); Pillow is the only genuinely new name and is the canonical PIL
> fork with ~100M+ weekly downloads.

| Package | Registry | Age | Source Repo | slopcheck | Disposition |
|---------|----------|-----|-------------|-----------|-------------|
| `pytest` | PyPI | 15+ yrs | github.com/pytest-dev/pytest | not-run `[ASSUMED]` | Approved (already used in repo) |
| `pygame` | PyPI | 20+ yrs | github.com/pygame/pygame | not-run `[ASSUMED]` | Approved (already in `requirements.txt`) |
| `Pillow` | PyPI | 14+ yrs | github.com/python-pillow/pillow | not-run `[ASSUMED]` | Approved (NEW dep — canonical PIL fork) |
| `firebase-admin` | PyPI | — | github.com/firebase/firebase-admin-python | not-run `[ASSUMED]` | Approved (already pinned in cloud_functions) |
| `functions-framework` | PyPI | — | github.com/GoogleCloudPlatform/functions-framework-python | not-run `[ASSUMED]` | Approved (already pinned in cloud_functions) |

**Packages removed due to [SLOP]:** none.
**Packages flagged [SUS]:** none. Planner: insert ONE `checkpoint:human-verify` before the
`pip install -r requirements-dev.txt` task to satisfy the gate (the names above are real and stable;
this is a formality given slopcheck was unavailable).

## Architecture Patterns

### System Architecture Diagram

```
                          ┌─────────────────────────────────────────────┐
   input.jsonl  ─────────▶│  REPLAY DRIVER (harness/replay.py)           │
   {frame,key} sparse     │  for frame in range(cap):                    │
                          │    inject events scheduled at this frame ───┐│
                          │      → pygame.event.post(KEYDOWN/KEYUP)      ││
                          │    game.tick()  ◀───────────────────────────┘│
                          │    snapshot = capture_state(game) ──────────┐│
                          │    (optional) pygame.image.save(screen,png) ││
                          │    if game.game_over or game.game_won: break ││
                          └──────────────────────────────────────────────┘
                                                                          │
   SDL_VIDEODRIVER=dummy ─┐                                               ▼
   SDL_AUDIODRIVER=dummy  │  (set BEFORE import pygame)            trace.jsonl (one
                          ▼                                        snapshot per frame)
                  ┌───────────────┐                                       │
                  │  Game.tick()  │  extracted from run() while-body      ▼
                  │  (game.py)    │  — NO timer.tick(FPS) here     ┌──────────────┐
                  │               │  — reads handle_events()       │ pytest assert│
                  └───────┬───────┘   (events from queue)          │ replayed ==  │
                          │                                        │ golden trace │
            create_ghosts() every frame (Ghost.__init__            │ + invariants │
            draws to dummy surface — harmless, C1)                 └──────────────┘

   ── separate test family ──────────────────────────────────────────────────────
   conftest.py: patch firebase_admin.initialize_app + firestore.client
                BEFORE importing cloud_functions.*.main
        │
        ▼
   import submit_score(main) ──▶ build flask.Request ──▶ call submit_score(req)
                                  (bad initials/score)     assert (status, body)
```

### Recommended Project Structure
```
harness/                         # NEW — dev-only simulation/capture code (not shipped in .exe)
├── __init__.py
├── headless.py                  # init_headless(): sets SDL env, pygame.init, returns (screen, clock)
├── replay.py                    # run_scenario(input_path, capture_frames=False) -> list[snapshot]
├── trace.py                     # capture_state(game) -> dict ; serialize/deserialize JSONL
├── capture.py                   # save_png, build_montage (blit), build_gif (Pillow)
└── play_loop.py                 # observe→decide→act driver (HRN-04)

tests/
├── __init__.py                  # exists
├── conftest.py                  # NEW — sys.path + firebase pre-import patch + --bless flag
├── golden/                      # committed goldens (D-06)
│   ├── manifest.json            # scenario registry CI iterates (Claude's discretion)
│   ├── box_exit/
│   │   ├── input.jsonl          # sparse {frame,key}
│   │   └── trace.jsonl          # frozen golden (committed)
│   ├── power_chase/ ...
│   └── claude_session_01/ ...
├── artifacts/                   # GITIGNORED — regenerated PNG/montage/GIF (D-06)
├── test_golden_traces.py        # TST-01: iterate manifest, replay, assert == golden + invariants
├── test_ghost_micro.py          # TST-02: headless Ghost + decisive board states
├── test_determinism_guard.py    # D-12: grep game/ghost/player for forbidden tokens
├── test_submit_score.py         # TST-03
└── test_get_leaderboard.py      # TST-03

.github/workflows/ci.yml         # NEW — TST-04
requirements-dev.txt             # NEW — D-20
```

### Pattern 1: Behavior-preserving `tick()` extraction (HRN-01, D-17)
**What:** Split the body of `Game.run()`'s `while running:` loop into a `tick()` method, leaving the
loop scaffolding (and `self.timer.tick(FPS)`) in `run()`.

**The chicken-and-egg resolution (design spec Phase A.1 — DO THIS FIRST):**
1. Temporarily instrument the EXISTING `run()`: after `pygame.display.flip()` (line 552), append a
   per-frame call that writes `capture_state(self)` to a JSONL file. This is logic-free.
2. Run a scripted scenario through the instrumented original loop → **baseline trace**.
3. Extract `tick()`. Replay the same scenario through `tick()`.
4. **Assert the `tick()` trace == baseline trace, byte-for-byte.** Only then is the extraction proven safe.
5. Remove the temporary instrumentation.

**The exact split (verified against `game.py:456-555`):** everything between `self.timer.tick(FPS)`
(line 462, EXCLUSIVE) and `pygame.display.flip()` (line 552, INCLUSIVE) becomes `tick()`. Specifically
lines 464–552: animation counter, eat-freeze, powerup timer, starting/dying phases, draw block,
`update_ghost_speeds`, `check_win`, ghost creation, targeting, box-exit timers, movement, collision
checks, `handle_events`, direction update, wrap, `check_ghost_in_box`, `display.flip()`.

```python
# game.py — AFTER extraction (illustrative — preserve exact statement order from run())
def tick(self):
    """One frame of update. Behavior-identical to the body of run()'s while-loop,
    minus the throttle (timer.tick) and the return_to_menu early-return.
    Returns False if a QUIT was received (mirrors handle_events), else True."""
    # ... lines 464-545 verbatim (counter, freeze, powerup, starting, dying, draw,
    #     speeds, win, ghosts, targets, box timers, movement, collisions) ...
    running = self.handle_events()           # was line 547
    self.player.update_direction()
    self.player.wrap_around()
    self.check_ghost_in_box()
    pygame.display.flip()
    return running

def run(self):
    running = True
    while running:
        if self.return_to_menu:
            self.sound.stop_all()
            return {"score": self.score, "game_won": self.game_won}
        self.timer.tick(FPS)                 # THROTTLE STAYS HERE ONLY (D-17)
        running = self.tick()
    self.sound.stop_all()
    return None
```

**Verified gotchas:**
- `Clock.tick(framerate)` returns the elapsed milliseconds as an int `[VERIFIED: pygame Clock.tick semantics — returns int ms]`. D-17 is trivially satisfied because `tick()` simply **never calls `self.timer.tick`** — the return value is discarded by construction. No sleep-dependence enters the harness.
- `handle_events()` returns `False` on `pygame.QUIT` (line 421) — `tick()` must propagate that so the interactive `run()` loop still exits on window close.
- `player_circle` is computed inside the `if not self.eat_freeze:` block (line 519-520) and used by `check_ghost_collisions` (line 544). During eat-freeze that branch is skipped — but `check_ghost_collisions` is also guarded by `not self.eat_freeze` (line 542), so `player_circle` is only referenced when defined. **Preserve this exact guard structure** — do not hoist `player_circle`.

### Pattern 2: Headless execution (HRN-01, D-14)
**What:** Run pygame with no window/audio so it works in CI and in tests.

```python
# harness/headless.py
import os
def init_headless(size=(900, 950)):
    os.environ["SDL_VIDEODRIVER"] = "dummy"   # MUST be set BEFORE import pygame
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    import pygame
    pygame.display.init()                      # some platforms need explicit init
    pygame.font.init()                         # Game.__init__ builds Fonts (game.py:22,95-98)
    pygame.mixer.init()                        # SoundManager uses mixer; dummy audio = no-op
    screen = pygame.display.set_mode(size)
    clock = pygame.time.Clock()
    return pygame, screen, clock
```
**Verified:** `[CITED: pygame examples/headless_no_windows_needed.py — set os.environ["SDL_VIDEODRIVER"]="dummy" BEFORE import pygame, then pygame.display.init(); set_mode()]`. The same pattern + `SDL_AUDIODRIVER=dummy` is the standard CI recipe.

**Ghost C1 side-effect is harmless headless (D-14):** `Ghost.__init__` calls `self.check_collisions()`
(pure, mutates only the Ghost) and `self.draw()` (blits to `self.screen`). Under the dummy driver the
blit targets an in-memory surface and is a no-op visually. **No change to `ghost.py`.** Construction
requires real surfaces for the ghost images — load them once via `Game.__init__` (which already loads
`assets/ghosts/*.png`) or pass small dummy `pygame.Surface((45,45))` objects in micro-tests.

### Pattern 3: Trace schema (HRN-02, D-03/D-04/D-05)
**What:** Per-frame snapshot of OBSERVABLE state + each ghost's `target`. Everything needed already
exists on the `Game` object — no new game logic.

```python
# harness/trace.py — capture_state reads ONLY existing attributes
def capture_state(g) -> dict:
    names = ["blinky", "inky", "pinky", "clyde"]
    targets = g.targets  # list set each frame by g.get_targets() (game.py:531)
    ghosts = []
    for i, n in enumerate(names):
        ghosts.append({
            "name": n,
            "x": getattr(g, f"{n}_x"),
            "y": getattr(g, f"{n}_y"),
            "dir": getattr(g, f"{n}_direction"),
            "dead": getattr(g, f"{n}_dead"),
            "box": getattr(g, f"{n}_box"),
            "target": list(targets[i]),         # D-03: record target tuple
        })
    return {
        "frame": g._frame,                       # add a frame counter to the driver, not game.py
        "pacman": {"x": g.player.x, "y": g.player.y, "dir": g.player.direction},
        "ghosts": ghosts,
        "score": g.score,
        "lives": g.lives,
        "powerup": g.powerup,
        "dots_remaining": sum(row.count(1) + row.count(2) for row in g.level),
        "game_over": g.game_over,
        "game_won": g.game_won,
    }
```
**Verified field sources:** `g.targets` is `[blink, ink, pink, clyd]` (game.py:531, returned by
`get_targets()`); ghost x/y/dir/dead/box are flat attrs on `Game` (game.py:38-57); `*_box` is
recomputed each frame inside `Ghost.check_collisions` and surfaced via `check_ghost_in_box` —
**record the `*_box` flag as the `g.*_box` attr after the frame**, matching what the diagram replays.
`dots_remaining` is derived from `g.level` (tile codes 1=dot, 2=big dot, per `board.py`).

**Comparison (D-05):** exact integer equality. `PLAYER_SPEED=2`, ghost speeds ∈ {1,2,4}, all start
coords integer `[VERIFIED: settings.py + read of move_* — x_pos += speed only]` → every value is an
exact int (or bool/derived-int) → no float rounding policy needed; traces are platform-independent.
Serialize as JSONL (one JSON object per frame per line) for line-diffable goldens.

### Pattern 4: Record / replay driver (HRN-02, TST-01, D-18/D-19)
```python
# harness/replay.py
import json
def load_events(input_path):
    by_frame = {}
    with open(input_path) as f:
        for line in f:
            if line.strip():
                ev = json.loads(line)            # {"frame": 12, "key": "RIGHT", "type": "down"}
                by_frame.setdefault(ev["frame"], []).append(ev)
    return by_frame

KEYMAP = {"RIGHT": "K_RIGHT", "LEFT": "K_LEFT", "UP": "K_UP", "DOWN": "K_DOWN", "SPACE": "K_SPACE"}

def run_scenario(game, pygame, input_path, frame_cap, capture_state, on_frame=None):
    events = load_events(input_path)
    trace = []
    for frame in range(frame_cap):              # D-19 safety cap = soft-lock backstop
        game._frame = frame
        for ev in events.get(frame, []):
            etype = pygame.KEYDOWN if ev.get("type", "down") == "down" else pygame.KEYUP
            key = getattr(pygame, KEYMAP[ev["key"]])
            pygame.event.post(pygame.event.Event(etype, key=key))  # D-18 real input path
        game.tick()                              # consumes queue via handle_events()
        snap = capture_state(game)
        trace.append(snap)
        if on_frame:
            on_frame(frame, game)                # e.g. save PNG
        if game.game_over or game.game_won:      # D-19 natural terminal
            break
    else:
        raise AssertionError(f"scenario hit frame_cap={frame_cap} without terminating (soft-lock?)")
    return trace
```
**Verified:** `pygame.event.post(Event(...))` enqueues; `handle_events()` drains via
`pygame.event.get()` (game.py:420) `[CITED: pygame event.md — post() places event on queue, get() retrieves/removes]`.
Posting `KEYDOWN` with a `key=` attribute is exactly what `handle_events` reads (`event.key ==
pygame.K_RIGHT`, etc., game.py:424-431).

**KEYUP nuance (verified):** `handle_events` resets `direction_command` to `self.player.direction` on
KEYUP of the currently-commanded key (game.py:435-443). A realistic recorded session emits both down
and up; a simple scripted scenario can emit just `down` events and rely on the held direction (no KEYUP)
— matches how the game treats a held arrow. The input format carries an optional `"type"` defaulting to
`"down"`.

**Frame cap (D-19, discretion):** A full level is large. Recommend `frame_cap = 60 * 60 * 8 = 28800`
(8 minutes @60fps) as the generous default, overridable per-scenario in the manifest. The cap doubles
as the hard soft-lock backstop (the `else` clause fails loudly instead of hanging CI).

### Pattern 5: Frame capture — PNG / montage / GIF (HRN-03, D-06/D-20)
```python
# harness/capture.py
def save_png(pygame, screen, path):
    pygame.image.save(screen, path)              # PNG inferred from extension

def build_montage(pygame, frame_surfaces, cols, cell=(180, 190), pad=4):
    rows = (len(frame_surfaces) + cols - 1) // cols
    W = cols * (cell[0] + pad) + pad
    H = rows * (cell[1] + pad) + pad
    sheet = pygame.Surface((W, H))
    sheet.fill((0, 0, 0))
    for i, surf in enumerate(frame_surfaces):
        thumb = pygame.transform.scale(surf, cell)
        r, c = divmod(i, cols)
        sheet.blit(thumb, (pad + c * (cell[0] + pad), pad + r * (cell[1] + pad)))
    return sheet                                 # then save_png(sheet, ...) — ZERO new dep

def build_gif(png_paths, out_path, duration_ms=33, loop=0):
    from PIL import Image                         # Pillow ONLY for GIF (D-20)
    frames = [Image.open(p) for p in png_paths]
    frames[0].save(out_path, save_all=True, append_images=frames[1:],
                   duration=duration_ms, loop=loop)
```
**Verified:** `pygame.image.save(surface, "x.png")` writes PNG `[CITED: pygame video.py example — pg.image.save(readsurf, "test.png")]`. Montage via `Surface.blit` of scaled thumbnails is pure pygame. GIF via `Image.save(..., save_all=True, append_images=[...], duration=, loop=)` `[CITED: pillow tutorial.rst + image-file-formats.rst — duration ms, loop=0 forever]`.

**D-06 directory policy:** PNG/montage/GIF write to `tests/artifacts/` (gitignored). Only
`golden/<scenario>/{input.jsonl, trace.jsonl}` are committed. Add `tests/artifacts/` to `.gitignore`.

### Pattern 6: Claude play-loop (HRN-04, D-10)
```python
# harness/play_loop.py — observe → decide → act
def play_turn(game, pygame, capture_state, decide_fn, png_path=None):
    if png_path:
        pygame.image.save(game.screen, png_path)     # OBSERVE (montage for Claude vision)
    state = capture_state(game)
    key = decide_fn(state, png_path)                 # DECIDE: Claude returns "RIGHT"/"LEFT"/...
    if key:
        pygame.event.post(pygame.event.Event(
            pygame.KEYDOWN, key=getattr(pygame, KEYMAP[key])))   # ACT
    game.tick()                                      # advance N frames between decisions as needed
    return capture_state(game)
```
**D-10 split (locked):**
- **Recorded golden:** drive one full session, **serialize every injected `{frame,key}` to the same
  sparse JSONL format** (Pattern 4), commit it as `golden/claude_session_01/{input.jsonl, trace.jsonl}`.
  It then replays deterministically in CI like any scripted scenario.
- **Live adversarial hunt:** the interactive observe→decide→act bug-hunt (soft-lock/wall-clip/score-
  overflow probing) stays a **MANUAL phase-verification gate** — it needs Claude in the loop and cannot
  be deterministic-green. Its pass is attested in the phase verification artifact, NOT a committed file.

### Pattern 7: Micro per-ghost characterization (TST-02, D-13/D-14)
```python
# tests/test_ghost_micro.py
def make_ghost(pygame, screen, x, y, target, speed, direction, ghost_id,
               level, dead=False, box=False, powerup=False):
    img = pygame.Surface((45, 45))               # dummy images OK headless
    eaten = [False, False, False, False]
    from ghost import Ghost
    return Ghost(x, y, target, speed, img, direction, dead, box, ghost_id,
                 screen, powerup, eaten, img, img, level)

def test_blinky_chases_right_at_intersection(headless, fresh_level):
    pygame, screen, _ = headless
    g = make_ghost(pygame, screen, x=..., y=..., target=(900, ...), speed=2,
                   direction=0, ghost_id=0, level=fresh_level)
    nx, ny, ndir = g.move_blinky()
    assert (nx, ny, ndir) == (...expected ints...)   # assert the EXACT turn
```
**D-13 board states (hand-curated, informed by the long golden session):** for each of the four
`move_*` methods, pick decisive states — a multi-way intersection, a tunnel mouth (wrap edge at
`x_pos < -30` / `> 900`, ghost.py:250-253), a box edge (the `350<x<550 & 360<y<480` boundary,
ghost.py:111), and a flee-vs-chase target (e.g. `runaway_x/y` vs Pac-Man target from `get_targets`).
Assert the exact `(x,y,dir)` returned. A failure then names the exact ghost + situation.

**Construction notes (verified):** `Ghost.__init__` (ghost.py:6-26) requires
`(x, y, target, speed, img, direct, dead, box, id, screen, powerup, eaten_ghost, spooked_img, dead_img, level)`;
it immediately calls `check_collisions()` (pure tile math against `level`) and `draw()` (blit to
`screen` — harmless headless). Pass the REAL `board.boards` (deep-copied) as `level` so tile math is
real. **Do not modify `ghost.py`.**

### Pattern 8: Cloud-function validator tests (TST-03, D-15/D-16)
```python
# tests/conftest.py  — patch firebase BEFORE the cloud function modules import
import sys, os
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))  # repo root (Claude's discretion)

@pytest.fixture
def submit_module():
    """Import cloud_functions.submit_score.main with firebase-admin mocked at import time (C2)."""
    with patch("firebase_admin.initialize_app"), \
         patch("firebase_admin._apps", new=[]), \
         patch("firebase_admin.firestore.client") as mock_client:
        # Ensure a clean import each test so the module-level db = firestore.client() re-runs mocked
        sys.modules.pop("cloud_functions.submit_score.main", None)
        import importlib
        mod = importlib.import_module("cloud_functions.submit_score.main")
        mod._mock_client = mock_client
        yield mod
```
```python
# tests/test_submit_score.py
import json
def make_request(body, method="POST"):
    from werkzeug.test import EnvironBuilder
    from flask import Request
    builder = EnvironBuilder(method=method, json=body)   # functions-framework brings Flask/werkzeug
    return Request(builder.get_environ())

def test_bad_initials_returns_400(submit_module):
    req = make_request({"machine_id": "m1", "initials": "ab", "score": 100})
    body, status, headers = submit_module.submit_score(req)
    assert status == 400 and body["error"] == "Invalid initials"

def test_score_over_max_returns_400(submit_module):
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 500001})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400 and body["error"] == "Invalid score"

def test_non_int_score_returns_400(submit_module):
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": "100"})
    _, status, _ = submit_module.submit_score(req)
    assert status == 400

def test_missing_machine_id_returns_400(submit_module):
    req = make_request({"initials": "ABC", "score": 100})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400 and body["error"] == "Missing machine_id"
```
**`is_new_best` upsert vs a mocked transaction/doc (verified against submit_score/main.py:14-58):**
The function builds `doc_ref = db.collection(...).document(machine_id)`, `transaction = db.transaction()`,
then `_update_score(transaction, doc_ref, ...)`. `_update_score` calls `doc_ref.get(transaction=...)`,
checks `doc.exists` and `doc.to_dict().get("score", 0)`. Mock the chain so `doc_ref.get(...)` returns a
MagicMock with `.exists = True/False` and `.to_dict.return_value = {"score": 4000}`:
```python
def test_is_new_best_true_when_higher(submit_module):
    db = submit_module._mock_client.return_value
    doc = db.collection.return_value.document.return_value
    snap = doc.get.return_value                       # doc_ref.get(transaction=...)
    snap.exists = True
    snap.to_dict.return_value = {"score": 4000}
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200 and body["is_new_best"] is True

def test_not_new_best_when_lower_or_equal(submit_module):
    db = submit_module._mock_client.return_value
    snap = db.collection.return_value.document.return_value.get.return_value
    snap.exists = True
    snap.to_dict.return_value = {"score": 9000}
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert body["is_new_best"] is False
```
> **Pitfall (verified):** `_update_score` is decorated `@firestore.transactional` (main.py:14). Under the
> mock, `firestore` is the real `firebase_admin.firestore` module, so `@firestore.transactional` still
> wraps the function — it may try to drive `transaction.begin/commit`. Mock the `transaction` object
> (from `db.transaction()`) so those are no-ops, OR patch `firestore.transactional` to a pass-through
> decorator in conftest. **Plan a spike** to confirm whether `@firestore.transactional` needs patching;
> the cleanest path is to patch `cloud_functions.submit_score.main.firestore.transactional` to
> `lambda f: f` so the inner logic runs directly with the mocked transaction/doc. `[CITED: firebase-admin firestore — db.transaction(), @firestore.transactional]`

**Flask request construction (verified):** functions-framework passes the entrypoint a `flask.Request`
`[CITED: functions-framework-python README — def hello(request: flask.Request)]`. Build one in-test via
`werkzeug.test.EnvironBuilder(json=...)` → `flask.Request(builder.get_environ())`, which gives a working
`request.get_json(silent=True)`, `request.method`, etc. Alternatively use
`functions_framework.create_app(target=..., source=...)` + Flask test client `[CITED: functions-framework create_app]` —
but the direct-call approach mirrors the existing house style (call the function, assert the tuple) and
is simpler. **Recommend direct-call.**

**D-16:** import the **working-tree** `cloud_functions/*/main.py` (uncommitted mods are what ships).
Also add a couple of `get_leaderboard` tests (success path returns `{"entries":[...]}` from a mocked
`query.stream()`; the entry shape is `{"initials","score"}`, main.py:30-33).

### Pattern 9: GitHub Actions CI (TST-04, D-08/D-09)
```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: ['**']            # D-09: push to any branch
  pull_request:
    branches: [main]            # D-09: PRs to main
jobs:
  test:
    runs-on: ubuntu-latest      # D-08: Linux-only, canonical bless env
    env:
      SDL_VIDEODRIVER: dummy     # headless
      SDL_AUDIODRIVER: dummy
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'    # D-08 pin (matches local 3.12.10)
      - name: Install deps
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install -r requirements-dev.txt
      - name: Run tests (headless)
        run: pytest -q
```
**Verified versions:** `actions/setup-python` current major is **v6** (v6.2.0) and `actions/checkout`
is **v6** `[CITED: github.com/actions/setup-python]`. v4/v5 still work and are widely used; **recommend
pinning to `@v5`/`@v4` or the current `@v6`/`@v6` — choose at plan time and pin the major.** Always set
`python-version` explicitly (the action recommends it). `[CITED: actions/setup-python — always set python-version explicitly]`

**D-09 required check / branch protection:** Set via GitHub repo settings → Branches → add a protection
rule on `main` requiring the `test` status check. This is a **manual one-time repo-settings step** (or
via `gh api`), not part of the YAML — the plan must include a task/checkpoint for it. The remote exists:
`https://github.com/jadrianports/pacman-firebase.git` `[VERIFIED: git remote -v]`.

### Anti-Patterns to Avoid
- **Extracting `tick()` before capturing the baseline trace.** This destroys the only reference that
  proves the extraction is safe. Baseline FIRST (Phase A.1).
- **Hashing PNG pixels for the golden comparison.** Pixels are pygame-version/font-render sensitive;
  the trace is numeric game state and is the stable golden. Pixels are for human/Claude eyes only.
- **Touching `ghost.py` to make it testable.** The C1 side-effect is harmless headless (D-14). Any
  change to `ghost.py` movement/targeting is out of scope and would invalidate the "byte-identical"
  premise of the whole milestone.
- **Reading `timer.tick(FPS)`'s return value in `tick()`.** D-17: keep `tick()` sleep-independent —
  it must not call `timer.tick` at all.
- **Installing latest firebase-admin (7.x) / functions-framework (3.10.x) for tests.** Must match the
  deployed `6.*`/`3.*` pins or tests validate code that won't ship.
- **Mutating `board.boards` directly in tests.** It's a shared module-level list; `Game` already
  `copy.deepcopy`s it (game.py:23). Tests must deep-copy too, or scenarios leak dots between runs.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Headless rendering | A custom no-op Surface shim | `SDL_VIDEODRIVER=dummy` | Native, exercises the real blit/font path; zero shim drift |
| Injecting key input | Direct mutation of `player.direction_command` | `pygame.event.post` + real `handle_events` | D-18: tests the real input path incl. KEYUP reset logic |
| PNG writing | Manual surface→bytes encode | `pygame.image.save` | One call, format from extension |
| Montage grid | A new image lib | `Surface.blit` of scaled thumbs | Zero new dep (D-20) |
| GIF assembly | Frame-encoding by hand | `PIL.Image.save(save_all, append_images)` | The one sanctioned new dep; battle-tested |
| Custom `--bless` arg parsing | `sys.argv` hacking | `pytest_addoption` + `request.config.getoption` | Canonical pytest hook `[CITED: pytest doc/en/example/simple.rst]` |
| Firestore in tests | Standing up the emulator (Java) | `unittest.mock.patch` at the conftest seam | D-15: validators are pure; emulator is heavy/slow |
| Trace diff | A bespoke differ | JSONL + line diff (and Python dict compare per frame) | Line-diffable goldens; `difflib`/`assert ==` is enough |

**Key insight:** Nearly everything this phase needs already exists in the codebase as observable state
(`get_targets()` yields the `target` tuples; ghost x/y/dir/dead/box are flat `Game` attrs; `level`
yields `dots_remaining`). The harness is a thin *reader* + *driver* around the unmodified game, not new
game logic. The only genuinely new dependency is Pillow, and only for the human-facing GIF.

## Runtime State Inventory

> This is a **greenfield additive** phase (new test/harness files + one behavior-preserving `tick()`
> extraction). No rename/migration. Inventory included only to confirm nothing stateful is being moved.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — Firestore is mocked, never touched in tests | None |
| Live service config | None — CI workflow is new; branch protection on `main` is a one-time GitHub repo setting (D-09) | Add a manual repo-settings task to enable the required `test` check |
| OS-registered state | None | None |
| Secrets/env vars | CI sets `SDL_VIDEODRIVER`/`SDL_AUDIODRIVER` (workflow env, not secrets). No Firebase creds needed (mocked). `firebase-key.json` stays gitignored/unused in tests | None |
| Build artifacts | New `tests/artifacts/` (gitignored, regenerated). `__pycache__` already gitignored | Add `tests/artifacts/` to `.gitignore` |

**Verified:** branch protection and the gitignore entry are the only two non-code actions. Everything
else is additive files + the in-place `tick()` extraction.

## Common Pitfalls

### Pitfall 1: `tick()` extraction silently reorders frame effects
**What goes wrong:** A subtle reordering (e.g. moving `handle_events` before movement, or hoisting
`player_circle`) changes the trace.
**Why it happens:** The `run()` body has order-dependent guards (`player_circle` only defined when
`not eat_freeze`; collisions guarded by multiple flags).
**How to avoid:** Copy lines 464–552 **verbatim** in the same order; validate against the baseline trace
(Pattern 1). Do NOT refactor while extracting.
**Warning signs:** Baseline-vs-`tick()` trace diff is non-empty on the first frames involving eat-freeze
or death.

### Pitfall 2: `firestore.transactional` decorator fights the mock
**What goes wrong:** `@firestore.transactional` (real, from `firebase_admin.firestore`) tries to drive a
real transaction lifecycle on the mocked `transaction`.
**Why it happens:** Mocking `firestore.client` does not unwrap the decorator on `_update_score`.
**How to avoid:** Patch `cloud_functions.submit_score.main.firestore.transactional` to a pass-through
(`lambda f: f`) in the fixture, so `_update_score` runs as a plain function against the mocked
transaction/doc. Plan a short spike to confirm.
**Warning signs:** AttributeError/odd calls on the transaction mock during `is_new_best` tests.

### Pitfall 3: SDL env set too late
**What goes wrong:** `SDL_VIDEODRIVER=dummy` set after `import pygame` has no effect; CI tries to open a
display and fails.
**Why it happens:** SDL reads the driver env at init.
**How to avoid:** Set env in `harness/headless.py` BEFORE `import pygame`, AND set it in the CI workflow
`env:` block as a belt-and-braces. `conftest.py` should also set it before any test imports pygame.
**Warning signs:** `pygame.error: No available video device` in CI.

### Pitfall 4: Shared mutable board leaks dots across scenarios
**What goes wrong:** A scenario eats dots; the next scenario starts with them missing → non-deterministic
goldens.
**Why it happens:** `board.boards` is a module-level list of lists.
**How to avoid:** Always `copy.deepcopy(boards)` per `Game`/per scenario (the game already does this,
game.py:23). Micro-tests that pass `level` must deep-copy too.
**Warning signs:** A scenario passes alone but fails in the full suite, or `dots_remaining` starts wrong.

### Pitfall 5: Soft-lock threshold N too tight → false positives on legit pauses
**What goes wrong:** The invariant "position changes within N frames" fires during a legitimate pause.
**Why it happens:** `starting`, `dying`, and `eat_freeze` legitimately freeze the player; the dying
phase waits for the death sound + 60 frames (game.py:500-511); starting waits for the start sound.
**How to avoid:** Exempt frames where `g.starting or g.dying or g.eat_freeze` (D-11). Set N generously —
recommend **N = 180 frames (~3s)** of *active* (`moving and not eat_freeze and not starting and not
dying`) no-movement before flagging. Tunable per the manifest.
**Warning signs:** Soft-lock invariant fails on the death/win/box-exit scenarios specifically.

## Code Examples
(All code-shaped patterns are in §Architecture Patterns 1–9 above, each tied to its requirement and
source citation. They are written to be lifted directly into tasks.)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `actions/setup-python@v2/v3` | `@v5`/`@v6` | v6.2.0 current | Pin a current major; always set `python-version` explicitly |
| `actions/checkout@v3` | `@v4`/`@v6` | v6 current | Pin a current major |
| Pillow GIF via `images2gif` | `Image.save(save_all, append_images)` | since Pillow 3.4.0 | Native, no extra dep `[CITED: pillow 3.4.0 release notes]` |

**Deprecated/outdated:** none material to this phase. The mocking-over-emulator choice (D-15) is the
mainstream pattern for validator-only cloud-function tests.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Package names/versions are legit (slopcheck could not run) | Package Legitimacy Audit | Low — all five confirmed via Context7 + PyPI; four already in repo manifests. Planner gates the install with one checkpoint |
| A2 | `@firestore.transactional` needs a pass-through patch to test `_update_score` against mocks | Pattern 8 / Pitfall 2 | Medium — if untrue, tests are simpler; flagged as a spike, not a blocker |
| A3 | pygame **2.6.1** is the right bless-env pin | Standard Stack | Low — latest stable, verified cp312 linux wheel; any 2.6.x is fine |
| A4 | Python **3.12** is the CI pin | Pattern 9 | Low — matches local 3.12.10; pygame/firebase-admin both support it |
| A5 | `firebase-admin==6.*` / `functions-framework==3.*` test pins match what's deployed | Standard Stack | Low — read directly from `cloud_functions/*/requirements.txt` |
| A6 | Soft-lock N=180 active frames avoids false positives | Pitfall 5 | Medium — tunable per manifest; may need adjustment after first golden runs |
| A7 | Frame cap 28800 (8 min) is "generous" enough for a full level | Pattern 4 | Low — overridable per scenario; only matters for the win scenario |

## Open Questions (RESOLVED)

**All three resolved during planning** — resolution paths are baked into the Phase 1 plans; no open blockers remain:
- Q1 (`@firestore.transactional`) → **RESOLVED** in plan 01-06 (spike-first; default to patching `firestore.transactional` to `lambda f: f`).
- Q2 (win-scenario frame counts) → **RESOLVED**: generated via the Claude play-loop (D-10) in plan 01-04, not hand-scripted; the safety frame cap backstops runaways.
- Q3 (`actions/*` major pins) → **RESOLVED** in plan 01-07 (pin current majors `checkout@v6`, `setup-python@v6`).

1. **Does `@firestore.transactional` require patching to test the upsert?** (A2)
   - What we know: the decorator is real under the firebase mock; the inner logic is what we want to test.
   - What's unclear: whether the wrapper short-circuits cleanly with a mocked `transaction`.
   - Recommendation: 30-min spike at the start of the TST-03 task; default to patching
     `firestore.transactional` to `lambda f: f`.

2. **Exact frame counts for the win scenario** (longest golden).
   - What we know: the board has hundreds of dots; a win requires clearing all.
   - What's unclear: total frames to clear via a scripted path.
   - Recommendation: generate via the Claude play-loop (D-10) rather than hand-scripting; let the safety
     cap catch a runaway.

3. **Which `actions/*` majors to pin** (`@v4`/`@v5` vs current `@v6`).
   - Recommendation: pin the current majors (`checkout@v6`, `setup-python@v6`); either works. Decide in the CI task.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All tests | ✓ (local) | 3.12.10 | — |
| pygame (linux py3.12 wheel) | Headless harness in CI | ✓ (wheel exists) | 2.6.1 cp312 manylinux2014 | — `[VERIFIED: pip download succeeded]` |
| GitHub remote | CI (TST-04) | ✓ | github.com/jadrianports/pacman-firebase | — `[VERIFIED: git remote -v]` |
| pygame (local dev machine) | Local test runs | ✗ (no pygame importable in this shell) | — | CI is canonical bless env (D-08); dev installs via `requirements-dev.txt` |
| Java / Firestore emulator | (NOT used — D-15 mocks) | n/a | — | Mocking (locked decision) |
| slopcheck | Package audit | ✗ (sandbox-denied) | — | Manual checkpoint before install (graceful degradation) |

**Missing dependencies with no fallback:** none.
**Missing dependencies with fallback:** local pygame (install via `requirements-dev.txt`); slopcheck
(replaced by a planner checkpoint).

## Validation Architecture

> `.planning/config.json` not present in working dir at research time; treating `nyquist_validation` as
> enabled (default).

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.4.2 (pin) |
| Config file | none today → NEW `tests/conftest.py` (Wave 0); optionally a `[tool.pytest.ini_options]`-free flat setup keeping repo-root import-by-name |
| Quick run command | `pytest -q tests/test_determinism_guard.py tests/test_ghost_micro.py` |
| Full suite command | `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HRN-01 | `tick()` reproduces baseline trace | characterization | `pytest tests/test_golden_traces.py -k baseline` | ❌ Wave 0 |
| HRN-02 | replay deterministic + matches golden | characterization | `pytest tests/test_golden_traces.py` | ❌ Wave 0 |
| HRN-03 | PNG/montage/GIF produced (smoke) | smoke | `pytest tests/test_golden_traces.py -k capture` | ❌ Wave 0 |
| HRN-04 | recorded Claude session replays green | characterization | `pytest tests/test_golden_traces.py -k claude_session` | ❌ Wave 0 |
| TST-01 | 8 scripted + 1 session goldens frozen | characterization | `pytest tests/test_golden_traces.py` | ❌ Wave 0 |
| TST-02 | per-ghost decisive turns | unit | `pytest tests/test_ghost_micro.py` | ❌ Wave 0 |
| TST-03 | validators + upsert | unit | `pytest tests/test_submit_score.py tests/test_get_leaderboard.py` | ❌ Wave 0 |
| TST-04 | full suite green headless | CI | (GitHub Actions) | ❌ Wave 0 |
| D-11 | per-frame invariants on every replay | property | embedded in `test_golden_traces.py` | ❌ Wave 0 |
| D-12 | forbidden-token guard | static | `pytest tests/test_determinism_guard.py` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest -q tests/test_determinism_guard.py tests/test_ghost_micro.py` (fast).
- **Per wave merge:** full headless suite.
- **Phase gate:** full suite green in CI before `/gsd-verify-work`; PLUS the manual Claude adversarial
  hunt attested (D-10).

### Wave 0 Gaps
- [ ] `tests/conftest.py` — sys.path + firebase pre-import patch + `--bless` flag
- [ ] `harness/` package (headless, replay, trace, capture, play_loop)
- [ ] `requirements-dev.txt` (pinned)
- [ ] `tests/golden/manifest.json` + per-scenario `input.jsonl` (goldens blessed AFTER harness proven)
- [ ] `.gitignore` entry for `tests/artifacts/`
- [ ] `.github/workflows/ci.yml`
- [ ] Framework install: `pip install -r requirements-dev.txt`

## Security Domain

> The phase ships NO new production code paths (test/harness only) and explicitly defers leaderboard
> security to the More Competitive milestone. The cloud-function **validator tests** here do, however,
> lock in the existing input-validation controls — which is a security-positive.

### Applicable ASVS Categories
| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | Leaderboard auth is out of scope (S1, deferred to More Competitive) |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A (deferred) |
| V5 Input Validation | yes | TST-03 freezes the existing validators: `^[A-Z]{3}$` initials, `isinstance(score,int)` + `0 ≤ score ≤ MAX_SCORE=500000`, required `machine_id` `[VERIFIED: submit_score/main.py:47-52]` |
| V6 Cryptography | no | No crypto in scope |

### Known Threat Patterns for {Python game + HTTP cloud functions}
| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Forged/over-range score submission | Tampering | Server-side type/range validation (tested by TST-03); deeper anti-cheat = COMP-01, deferred |
| Untrusted JSON body | Tampering | `get_json(silent=True)` + explicit field validation (tested) |
| Secret leakage (`firebase-key.json`) | Information Disclosure | Stays gitignored + unused in tests (mocked); never printed in planning docs (S2) |
| CI supply-chain (unpinned dev deps) | Tampering | `requirements-dev.txt` pinned (D-20); install gated by one human-verify checkpoint (slopcheck unavailable) |

## Sources

### Primary (HIGH confidence)
- `/pygame/pygame` — headless SDL dummy driver (`examples/headless_no_windows_needed.py`), `event.post`/`event.get`/`Event` (`docs/reST/ref/event.md`), `image.save` (`examples/video.py`), `Clock.tick` returns int ms.
- `/pytest-dev/pytest` — `pytest_addoption` + `request.config.getoption` (`doc/en/example/simple.rst`), `monkeypatch` (incl. `setenv`, `syspath_prepend`), `pythonpath`/rootdir (`doc/en/reference/reference.rst`).
- `/python-pillow/pillow` — animated GIF via `Image.save(save_all, append_images, duration, loop)` (`docs/handbook/tutorial.rst`, `image-file-formats.rst`, `releasenotes/3.4.0.rst`).
- `/googlecloudplatform/functions-framework-python` — entrypoint receives `flask.Request`; `create_app(target, source, signature_type)` for testing (`README.md`, llms.txt).
- `/firebase/firebase-admin-python` — `firestore.client()`, `db.transaction()`, `@firestore.transactional`, emulator = separate process via `FIRESTORE_EMULATOR_HOST` (confirms mock-not-emulator choice).
- PyPI (`pip index versions` / `pip download`): pygame 2.6.1 (cp312 manylinux2014 wheel verified), pytest 9.0.3 (pin 8.4.2), Pillow 12.2.0, firebase-admin 7.4.0 (use 6.* to match deploy), functions-framework 3.10.1 (use 3.*).
- Direct source reads: `game.py` (run loop 456-555), `ghost.py` (Ghost.__init__, check_collisions, move_*), `player.py`, `settings.py`, `board.py`, `cloud_functions/*/main.py`, existing `tests/*`.
- `git remote -v` — confirmed `github.com/jadrianports/pacman-firebase`.

### Secondary (MEDIUM confidence)
- `github.com/actions/setup-python` (WebFetch) — current major v6 (v6.2.0), checkout v6; always set `python-version` explicitly.

### Tertiary (LOW confidence)
- none.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libs Context7-confirmed + PyPI-verified; pinned majors read from repo.
- Architecture (tick extraction, trace, replay): HIGH — derived from reading the actual `run()` loop and
  Ghost/Game attributes; sources cited for every pygame/pytest/Pillow API.
- Cloud-function tests: HIGH on the entrypoint/validation approach; MEDIUM on the exact
  `@firestore.transactional` handling (one spike flagged).
- Pitfalls: HIGH — each traced to a specific line in the source.

**Research date:** 2026-06-11
**Valid until:** 2026-07-11 (stable stack; ~7 days only for the `actions/*` major-version note, which moves fast)

## RESEARCH COMPLETE

**Phase:** 1 - Test Safety Net
**Confidence:** HIGH

### Key Findings
- The game is verifiably deterministic (integer pixel math, frame-counter timers, zero `random`/wall-clock) — record/replay is frame-perfect and platform-independent; D-05 exact-integer comparison needs no float policy.
- The `tick()` seam is precise: extract `game.py` lines 464–552 verbatim, leave `timer.tick(FPS)` in `run()` only; D-17 satisfied by simply not calling it in `tick()`. **Baseline-trace-first** (instrument the unmodified `run()`) resolves the chicken-and-egg.
- Nearly all trace fields already exist as `Game` state (`get_targets()` yields `target` tuples; ghost x/y/dir/dead/box are flat attrs) — the harness is a thin reader, not new game logic. Only new dep is Pillow (GIF only).
- Cloud-function tests: mock firebase-admin in `conftest.py` before import (handles C2); test validators via a constructed `flask.Request`; pin test deps to `firebase-admin==6.*`/`functions-framework==3.*` to match deploy. One spike on `@firestore.transactional` under mock.
- CI: pinned `ubuntu-latest` + Python 3.12 + pygame 2.6.1 (cp312 linux wheel verified), `SDL_*=dummy`; runs on push to any branch + PRs to main; branch protection on `main` is a one-time manual repo setting.

### File Created
`C:\Users\James\desktop\projects\pacman-firebase\.planning\phases\01-test-safety-net\01-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Context7 + PyPI verified; majors read from repo manifests |
| Architecture | HIGH | Derived from reading actual source; APIs cited |
| Pitfalls | HIGH | Each traced to a specific source line |
| Cloud-fn transactional handling | MEDIUM | One spike flagged (A2) |
| slopcheck audit | DEGRADED | Sandbox-denied; planner adds one human-verify checkpoint |

### Open Questions (RESOLVED)
- `@firestore.transactional` may need a pass-through patch to test the upsert (spike at TST-03 start). — **RESOLVED:** plan 01-06 spike-first.
- Exact frame counts for the win/long scenarios — generate via the Claude play-loop, not hand-scripting. — **RESOLVED:** plan 01-04 (D-10).
- Which `actions/*` majors to pin (recommend current `@v6`/`@v6`). — **RESOLVED:** plan 01-07.

### Ready for Planning
Research complete. The nine patterns map 1:1 to HRN-01..04 / TST-01..04 and are written to be lifted directly into tasks. Build in design-spec Phase A→B order (harness + baseline-first, then goldens + micro + cloud-fn + CI).
