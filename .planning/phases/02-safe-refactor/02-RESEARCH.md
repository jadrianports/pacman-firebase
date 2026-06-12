# Phase 2: Safe Refactor - Research

**Researched:** 2026-06-12
**Domain:** Behavior-preserving refactor of deterministic PyGame game logic, proven via differential oracles + deterministic frame-hashing, behind an existing golden-master test net.
**Confidence:** HIGH (all claims grounded in verbatim reads of `ghost.py`, `game.py`, `player.py`, the Phase 1 net, and the design spec; library specifics confirmed via Context7 pygame docs)

## Summary

This phase has an unusually low *unknowns* surface because the CONTEXT.md already locks 19 decisions and the existing Phase 1 net (golden traces + 15 micro tests + headless `make_ghost`) is the proof engine. The research job was to (a) read the exact turn-priority orderings and structural quirks out of all four `move_*` methods, (b) design the cleanest data schema + hooks that reproduce them byte-for-byte, and (c) settle the verification mechanics (differential-oracle enumeration, frame-hash algorithm, mutation canary, test-tree layout) that the planner needs to write concrete plans.

The single most important finding: **the four movers are NOT cleanly tabular.** Each has a per-direction "primary preference" line at the top that differs across ghosts and even differs in whether it *moves* on that line; a `not turns[dir]` fall-through block; AND a third `turns[dir]` ("forward open") block that differs structurally (blinky/pinky just go straight; clyde/inky branch on the perpendicular target). The ordering inside the fall-through blocks also differs (e.g. dir-2 clyde tries L before U-via-target; blinky tries U-target first). D-01's instinct — "data for the orderings, named hooks for the quirks" — is correct, but the planner must treat **each (ghost × direction) cell** as the unit, not "one ordering per ghost." A naive "one priority list per ghost" schema will silently brick at least three documented quirks.

**Primary recommendation:** Model the mover as a per-ghost profile = a dict keyed by `direction (0-3)`, each value describing the three branches (primary / blocked-fallthrough / forward-open) using small named helper functions for the quirky branches and a shared ordered fall-through executor for the ~90% that IS tabular. Prove equivalence with TWO synthetic differential oracles (mover + `check_collisions`), a `pygame.image.tobytes`-based frame-hash manifest, and a one-shot manual mutation canary — sequenced geometry-first then blinky→inky→pinky→clyde as atomic green commits (D-11). Keep the four `move_*` wrapper names/signatures byte-identical so the 15 micro tests are never touched.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Ghost turn-priority decision | Game logic (`ghost.py`) | — | The fragile precious AI; must stay byte-identical |
| Tile/board geometry math | Game logic (`settings.py` + new `geometry.py`) | rendering (`draw_board`) | Centralizing the `num1/num2/num3` literals shared across game/ghost/player |
| Box-region predicate | Game logic (new `geometry.py`) | — | ~9 duplicated inline checks collapse to one `in_box(x,y,bounds)` |
| Equivalence proof (logic) | Test harness (`tests/`) | — | Synthetic differential oracles bypass `check_collisions` and set inputs directly |
| Equivalence proof (pixels) | Test harness (`tests/`) | rendering | Frame-hash via `pygame.image.tobytes` catches geometry bugs that shift rendering without moving the state trace |

This phase is single-tier (a local PyGame app). The only meaningful boundary is **production game logic vs. test harness**; the entire verification apparatus lives in `tests/` + reuses `harness/`, and never modifies `ghost.py`'s public method surface.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 8.4.2 (pinned `requirements-dev.txt`) | Test runner + `--bless` flag (already wired in `conftest.py`) | Already the project's test framework; the net is built on it |
| pygame | 2.6.1 (pinned `requirements-dev.txt`) | `pygame.image.tobytes(surface, "RGB")` for deterministic frame bytes | Already the game engine; `tobytes` ships in-box, no new dep [CITED: pygame docs — image.tobytes, alias of tostring since 2.1.3] |
| hashlib | stdlib | `hashlib.sha256(frame_bytes).hexdigest()` for the frame-hash manifest | Stdlib, deterministic, zero new dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Pillow | 11.0.0 (pinned, already present) | GIF assembly for the D-19 human before/after gate (existing `harness/capture.py:build_gif`) | End-of-phase human verification only |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `hashlib.sha256(tobytes)` | `pygame.surfarray.array2d` + numpy hash | numpy is NOT a current dependency; adds a dep purely for hashing — `tobytes` already gives a stable byte string with zero deps. **Reject numpy.** |
| Manual mutation canary | `mutmut` / `cosmic-ray` | Full mutation-testing frameworks are heavyweight (config, runtime, CI integration) for a *one-shot, run-once-and-attest* check (D-10). A single hand-edit + observe-RED + revert is lighter and more reliable. **Recommend manual.** |
| `pytest.mark.parametrize` for the full oracle space | programmatic `for` loops inside one test | parametrize at ~7,000+ cases bloats collection time and test IDs; a programmatic loop with a single failing-case accumulator is faster and gives a cleaner first-divergence report. **Recommend loops** (see FOCUS-3). |
| `hypothesis` | property-based fuzzing | The input space is small and fully enumerable; exhaustive beats random sampling for a "provably identical" claim. **Reject hypothesis** — enumerate exhaustively. |

**Installation:** No new packages required. Everything (pytest, pygame, Pillow, hashlib) is already pinned and installed.

**Version verification:** `requirements-dev.txt` pins `pytest==8.4.2`, `pygame==2.6.1`, `Pillow==11.0.0`. CI (`.github/workflows/ci.yml`) runs `ubuntu-latest` + Python `3.12` with `SDL_VIDEODRIVER=dummy`/`SDL_AUDIODRIVER=dummy` — this **is** the Phase 1 D-08 pinned bless env. [VERIFIED: read of `requirements-dev.txt` and `.github/workflows/ci.yml`]

## Package Legitimacy Audit

No external packages are installed in this phase. All tooling (pytest, pygame, Pillow, hashlib) is already present and pinned. **Package Legitimacy Gate: N/A — zero new packages.**

---

## FOCUS-1 — Profile data schema + the structural quirks (D-01/D-03)

### The exact orderings, read out of `ghost.py`

I read all four methods verbatim. Each method is a 4-way `if self.direction == 0/1/2/3` switch. Within each direction there are up to **three branches**:

1. **PRIMARY branch** (the first `if` testing `target[axis] vs pos and turns[dir]`) — "keep going toward target along current axis."
2. **BLOCKED fall-through** (`elif not self.turns[dir]:`) — an ordered ladder of target-seeking then any-open moves.
3. **FORWARD-OPEN branch** (`elif self.turns[dir]:`) — what to do when forward is still open AND the primary didn't fire.

The BLOCKED fall-through ladders are the tabular part. Verbatim orderings (each entry = `(condition, resulting dir)`; conditions are `tgt[ax] >/< pos & turns[d]`, then bare `turns[d]`):

**dir 0 (Right), blocked ladder** — identical for ALL four ghosts (`ghost.py:262-280 / 368-386 / 490-508` and clyde `123-141`):
`tgt.y>↓&t3 → tgt.y<↑&t2 → tgt.x<←&t1 → t3 → t2 → t1`

**dir 1 (Left), blocked ladder** — identical for all four (`286-304 / 401-419 / 517-535 / 156-174`):
`tgt.y>↓&t3 → tgt.y<↑&t2 → tgt.x>→&t0 → t3 → t2 → t0`

**dir 2 (Up), blocked ladder** — **TWO variants:**
- blinky (`311-329`): `tgt.x>→&t0 → tgt.x<←&t1 → tgt.y>↓&t3 → t3 → t0 → t1`
- clyde/inky/pinky (`191-209 / 433-451 / 545-563`): `tgt.x>→&t0 → tgt.x<←&t1 → tgt.y>↓&t3 → t1 → t3 → t0`
  → **The trailing any-open order differs: blinky `t3,t0,t1`; others `t1,t3,t0`.** LANDMINE.

**dir 3 (Down), blocked ladder** — identical for all four (`335-353 / 457-475 / 576-594 / 222-240`):
`tgt.x>→&t0 → tgt.x<←&t1 → tgt.y<↑&t2 → t2 → t0 → t1`

### The PRIMARY + FORWARD-OPEN quirks (the non-tabular part — these are the hooks)

These are where the four ghosts genuinely diverge. Mapping each documented quirk to a concrete cell:

| Quirk | Exact location | Behavior | Hook needed |
|-------|----------------|----------|-------------|
| **Q-a: blinky/pinky go straight on forward-open; clyde/inky branch on perpendicular target** | dir0 forward-open: blinky `281-282`/pinky `509-510` = bare `self.x_pos += speed`; clyde `142-150`/inky `387-395` test `tgt.y` and may turn ↓/↑ first | "forward open" means *continue* for blinky/pinky but *opportunistically turn toward target's y* for clyde/inky | `forward_open` branch is per-cell: `STRAIGHT` vs `SEEK_PERP_Y` |
| **Q-b: inky dir-1 PRIMARY sets direction WITHOUT moving; pinky dir-1 PRIMARY sets direction AND moves** | inky `397-398`: `if tgt.y>↓&t3: self.direction = 3` (NO `y_pos +=`); pinky `512-514`: `if tgt.y>↓&t3: self.direction = 3; self.y_pos += speed` | inky "stutters" — changes facing this frame but doesn't advance; pinky advances same frame | dir-1 PRIMARY hook: `TURN_NO_MOVE` (inky) vs `TURN_AND_MOVE` (pinky). blinky/clyde have NO such primary at dir-1 (their first test is `tgt.x<←&t1`). |
| **Q-c: `if … if … else` non-elif override** | inky forward-open dir0 `388-394` and dir1 `421-427`; clyde same `143-149 / 176-182`; pinky dir-2 forward-open `565-571`; clyde dir-2/dir-3 forward-open `211-217 / 242-248` | second `if` (NOT `elif`) can override the first within the same frame; the final `else` only binds to the *second* `if` | These must be transcribed as literal code in the hook, not as an ordered ladder — an `elif`-based executor would change semantics |

**Additional per-ghost PRIMARY differences (verified):**
- **dir-2 PRIMARY:** blinky/inky test `tgt.y<↑&t2` first (`308 / 430`); clyde/pinky test `tgt.x<←&t1` FIRST then `tgt.y<↑&t2` (`185-190 / 539-544`). Different primary entirely.
- **dir-2 FORWARD-OPEN:** blinky/inky = bare `self.y_pos -= speed` (`330-331 / 452-453`); clyde/pinky = a branch testing `tgt.x` (`210-218 / 564-572`).
- **dir-3 FORWARD-OPEN:** blinky/inky = bare `self.y_pos += speed` (`354-355 / 476-477`); clyde/pinky = branch testing `tgt.x` (`241-249 / 595-603`).
- **dir-1 PRIMARY ladder:** blinky/clyde first test `tgt.x<←&t1`; inky/pinky first test `tgt.y>↓&t3` (the Q-b cell).

### Recommended schema

Per the analysis, **clyde and pinky share one structural shape; blinky and inky share another** — but inky has the Q-b stutter and clyde/inky share Q-a. There is no clean 2-way split. Therefore:

**Recommendation:** a per-ghost profile is a **`dict[int, DirectionRule]`** (keyed by direction 0-3), where `DirectionRule` is a small `namedtuple` (or `@dataclass`) with three fields:

```python
# At top of ghost.py (D-03), module-level data next to the unified mover.
from collections import namedtuple

DirectionRule = namedtuple("DirectionRule", ["primary", "blocked_ladder", "forward_open"])

# `blocked_ladder` is a tuple of (axis, cmp, target_dir) steps — the TABULAR ~90%.
# `primary` and `forward_open` are references to small named functions (the HOOKS) —
# because Q-a/Q-b/Q-c are control-flow, not data.
```

- `blocked_ladder`: a tuple of ordered steps, each `(want_dir, needs_target_cond)` where `needs_target_cond` is `None` for the bare-`turns[d]` tail entries. The unified mover walks this list, takes the first satisfied step, applies the canonical `direction = d; pos ±= speed`. This collapses the dir-0/dir-1/dir-3 ladders (identical across ghosts) and the dir-2 variant (`t3,t0,t1` vs `t1,t3,t0`).
- `primary` and `forward_open`: **named module-level functions** taking `(ghost)` and returning a flag (`MOVED` / `NOT_HANDLED`) so the mover knows whether to fall through. Name them descriptively, e.g. `straight(g)`, `seek_perp_y(g)`, `turn_no_move_down(g)` (inky Q-b), `turn_and_move_down(g)` (pinky Q-b). The original personality comments become the docstrings of each profile (D-03).

**Why dict-of-namedtuple over pure-tuple or pure-dict:** A pure flat tuple loses the named-branch readability the planner/reviewer needs to confirm "same order → same pixel." A pure dict-of-dicts is stringly-typed and easy to typo. `namedtuple` gives field names for free, is immutable (data can't drift), and is the lightest structured value consistent with D-14's "tuple/namedtuple" guidance.

**Do NOT** attempt to encode Q-a/Q-b/Q-c as boolean flags in the schema — D-01 explicitly rejected "everything as data + behavior flags." The override `if…if…else` (Q-c) cannot be expressed as an ordered ladder without changing semantics; keep it as literal Python in a named hook.

---

## FOCUS-2 — Unified mover signature + clyde-as-fallback (D-02)

**The four wrappers stay byte-identical in name and signature** (zero-arg methods returning `(x_pos, y_pos, direction)`):

```python
def move_blinky(self): return self._move(BLINKY_PROFILE)
def move_inky(self):   return self._move(INKY_PROFILE)
def move_pinky(self):  return self._move(PINKY_PROFILE)
def move_clyde(self):  return self._move(CLYDE_PROFILE)
```

This keeps:
- `game.py:move_ghosts` (`L344-362`) **untouched** — it still calls `.move_blinky()`, `.move_inky()`, `.move_pinky()`, `.move_clyde()` by name.
- `tests/test_ghost_micro.py`'s 15 tests **untouched** — they call `g.move_blinky()` etc. and `g.move_clyde()` directly (the measuring instrument is not disturbed).

**Clyde-as-fallback (D-02 locked constraint):** verified in `game.py:move_ghosts` — `.move_clyde()` is called on blinky (`L348`), inky (`L354`), pinky (`L360`), and clyde (`L362`) whenever the ghost is dead or in-box. Because `move_clyde()` simply delegates to `self._move(CLYDE_PROFILE)` and `_move` reads only `self.*` state (`direction`, `target`, `turns`, `x_pos`, `y_pos`, `speed`), **any** ghost instance can reach the clyde profile with no special wiring. The micro test `test_clyde_dead_in_box_fallback_returns_to_target` (a ghost_id=3 ghost, dead+box, asserting `(478, 438, 1)`) pins this exact path and will keep guarding it.

**Landmine:** the wrappers must return *exactly* `(self.x_pos, self.y_pos, self.direction)` and the unified `_move` must apply the trailing wrap clamp (`if self.x_pos < -30: self.x_pos = 900 elif > 900: -30`, identical across all four — `ghost.py:250-253/356-359/478-481/604-607`) before returning. The wrap is shared and tabular; fold it into `_move` once.

---

## FOCUS-3 — Synthetic-exhaustive differential oracle for the mover (D-04/D-05)

### Input space and case count

D-05 enumerates: `direction(4) × all 16 turns[] combos × target-sign-per-axis(3×3) × in_box(2) × dead(2) × speed{1,2,4} × wrap-x-positions`.

- direction: 4
- turns combos: 2^4 = 16
- target sign per axis: target.x ∈ {< x, == x, > x} and target.y ∈ {< y, == y, > y} = 3×3 = 9
- in_box: 2, dead: 2
- speed: 3 ({1,2,4})
- wrap-x representatives: recommend **5** positions — `x = -31` (just past left wrap), `x = -30` (boundary), `x = 450` (interior, no wrap), `x = 900` (boundary), `x = 901` (just past right wrap). (in_box/dead don't affect `_move`'s wrap math, but they DO affect which ladder branches fire via `turns`, already covered.)

**Base count:** 4 × 16 × 9 × 2 × 2 × 3 × 5 = **34,560 cases per ghost** × 4 ghosts = **138,240 oracle calls.** Each call is pure integer arithmetic on a constructed ghost (no rendering in the hot loop). This runs in well under ~5s on CI — trivially inside budget. If runtime is a concern, drop speed to {2} for the in_box/dead cross (those don't exercise speed-sensitive branches differently) — but the full cross is cheap enough to keep. **Recommended CI budget: keep full enumeration; it is < 10s.**

### How to construct cases without `check_collisions`

`turns` is normally computed by `check_collisions()` during `__init__`. To set it **directly** (bypassing geometry), construct via `make_ghost` then overwrite:

```python
g = make_ghost(screen, x, y, target=(tx, ty), speed=spd, direction=d, ghost_id=gid,
               dead=dead, box=box)
g.turns = list(turns_combo)      # the synthetic 4-tuple, bypassing check_collisions
g.in_box = box                   # set the flag the mover reads
g.x_pos, g.y_pos = x, y          # ensure clean start (target sign computed relative to these)
```

`make_ghost` already constructs headless (D-13/D-14) and runs `check_collisions` once in `__init__` — we simply **clobber `g.turns`/`g.in_box` after construction** before calling the mover. The mover reads `self.turns`, so this fully controls the input. (Target-sign cases: pick `tx = x-100 / x / x+100` and `ty = y-100 / y / y+100` to realize the 3×3 sign matrix relative to the chosen `x,y`.)

### Frozen oracle (OLD) construction

Per D-06 (one-shot then delete): **before** refactoring `ghost.py`, copy the current `move_blinky/inky/pinky/clyde` verbatim into a test-only module, e.g. `tests/_legacy_movers.py`, as standalone functions taking a ghost-like object (or as methods on a tiny `_LegacyGhost` mixin). Capture this copy in the SAME commit that introduces the unified mover. The differential test asserts, per ghost, per case:

```python
old = legacy_move_<ghost>(clone_of(g))   # operate on a deep clone so state isn't shared
new = g.move_<ghost>()                    # the new unified path
assert (old.x_pos, old.y_pos, old.direction) == new
```

D-11 runs this **per-ghost atomically**: prove `unified(blinky) == legacy_blinky` → commit green → inky → pinky → clyde. The legacy copy + the differential test are **deleted** once all four are green (D-06); the 15 micro tests + golden traces carry forward as the permanent guard.

### Recommendation: programmatic loops, not parametrize

At 34k+ cases/ghost, `pytest.mark.parametrize` generates 138k test IDs (slow collection, unreadable output). Use **one test per ghost** that loops programmatically and accumulates the FIRST divergence (or a small list) for a clean failure message:

```python
def test_unified_mover_matches_legacy_blinky(screen):
    failures = []
    for d, turns, tsx, tsy, box, dead, spd, x in itertools.product(
            range(4), TURNS_COMBOS, SIGNS, SIGNS, (False, True),
            (False, True), (1, 2, 4), WRAP_XS):
        ...
        if old != new:
            failures.append((d, turns, tsx, tsy, box, dead, spd, x, old, new))
            if len(failures) >= 5: break
    assert not failures, format_divergences(failures)
```

---

## FOCUS-4 — Second differential oracle for `check_collisions` (D-07)

`check_collisions` (`ghost.py:43-115`) holds `num1=(HEIGHT-50)//32`, `num2=WIDTH//30`, `num3=15` and the box literal `350 < x_pos < 550 and 360 < y_pos < 480`. REF-01 centralizes these. Prove the centralization preserves `(turns, in_box)`.

**Enumeration:** `board positions × direction × in_box × dead`. The board is 30 cols × 32 rows. Rather than sampling every pixel, enumerate **every tile center plus the half-tile-offset positions that exercise the `12 <= center % num <= 18` alignment branches** (those branches at `ghost.py:69-107` are the precedence-sensitive part most prone to an off-by-one when literals move). Concretely:
- For each tile (r, c): test `x_pos`/`y_pos` at the tile origin AND at origin + `num3` (=15, the look-ahead offset) AND at the alignment band (`center % num2 == 15`). This is roughly `30×32 × ~3 positions × 4 directions × 2 in_box × 2 dead ≈ 46,000` cases — still cheap.

**Capturing OLD check_collisions before REF-01 edits it:** same pattern as FOCUS-3 — copy the current `check_collisions` body verbatim into `tests/_legacy_movers.py` (or a `_legacy_check_collisions.py`) as a standalone function operating on a constructed ghost, captured in the commit that lands the geometry centralization. Assert `legacy_check_collisions(g) == g.check_collisions()` returns identical `(turns, in_box)` for every case. One-shot, then delete (D-07 = same lifecycle as D-06).

**Sequencing note (D-11):** this oracle is proven FIRST (geometry centralized before any mover work), so the mover oracle (which uses *synthetic* `turns`) can rely on `check_collisions` being already-proven-equivalent. The two oracles are deliberately complementary: the mover oracle does NOT exercise `check_collisions` (it clobbers `turns`), so this second oracle closes that gap.

---

## FOCUS-5 — Deterministic frame-hash (pixel) check (D-08/D-09)

### Algorithm + mechanism

**Recommendation:** `hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()`.

- `pygame.image.tobytes(surface, "RGB")` returns the raw pixel bytes deterministically; it is the recommended alias of `tostring` since pygame 2.1.3 and adds **no dependency** (numpy not required). [CITED: pygame docs — image.tobytes]
- Use format `"RGB"` (not `"RGBA"`) — the game's screen is opaque (`screen.fill('black')` each frame, `game.py:512`), so alpha carries no information and RGB is the leanest stable representation.
- `hashlib.sha256` is stdlib and deterministic. SHA-256 over MD5/CRC purely for collision-resistance hygiene; any stable hash works since this is equality-checking, not security.

### Platform stability

D-09 requires platform stability via the Linux pinned bless env (Phase 1 D-08 = `ubuntu-latest` + Python 3.12 + pygame 2.6.1, `SDL_*=dummy`). Verified concerns:
- **Font rendering** (`draw_misc` renders score text via `freesansbold.ttf`) is the one real cross-platform pixel risk. `conftest.py:_ensure_default_font` copies pygame's bundled `freesansbold.ttf` so the byte-identical font is used everywhere. The frame-hash is therefore stable **only within the pinned bless env** — which is exactly D-09's contract: bless on Linux pinned, regenerate-on-demand elsewhere, and the committed manifest is the Linux-blessed truth. Do NOT assert frame-hash equality on a dev Windows machine; assert it in CI (the bless env).
- **Powerup/flicker animation** (`self.flicker`, `self.counter`) is deterministic (frame-counter driven, design spec "no wall-clock"), so the same frame index always renders identically.

### Manifest format + bless integration

D-09 wants a **committed TEXT manifest** (PNGs stay gitignored per Phase 1 D-06). Recommend `tests/golden/<scenario>/frame_hashes.txt` — one `frame_index sha256hex` line per captured frame, for the golden scenarios. To avoid manifest bloat (death = 4200 frames), **hash a fixed sampled subset** per scenario (e.g. every 20th frame + the terminal frame), recorded alongside the trace. Wire it into the existing `--bless` flow in `test_golden_traces.py`: in `test_baseline_golden`, when `--bless`, also re-render and rewrite `frame_hashes.txt`; otherwise assert the replayed frames' hashes match the committed manifest.

**Why this catches what the trace cannot (D-08 rationale, verified):** `draw_board` (`game.py:130-161`) computes `num1=(HEIGHT-50)//32`, `num2=WIDTH//30` — the SAME literals REF-01 centralizes. A geometry bug (e.g. `TILE_HEIGHT` off by one) would shift every drawn wall/dot pixel while the **state trace stays byte-identical** (the trace records ghost/pac positions and score, not pixels). The frame-hash is the only automated guard for that failure mode. Confirmed: `draw_board` is independent of the mover logic, so this is a genuinely orthogonal proof modality.

---

## FOCUS-6 — Mutation canary (D-10)

**Recommendation: a single manual hand-edit, run once, attested in the verification artifact.** Do NOT pull in `mutmut`/`cosmic-ray` — they are heavyweight (config + their own runner + CI wiring) for a run-once "prove the harness has teeth" check.

**Concrete procedure (attest each step in the phase verification artifact):**
1. After the unified mover is green, deliberately swap two adjacent rungs in one BLOCKED ladder — e.g. in the dir-2 blocked ladder swap `t1` and `t3` so blinky's `t3,t0,t1` becomes `t0,t3,t1` (or swap two `elif` rungs in the unified executor's ordered list).
2. Run the differential oracle (if still present) AND the golden traces (`pytest -k baseline`) AND the micro tests. Confirm at least the golden traces AND the differential oracle go **RED** (the micro tests may or may not trip depending on whether a scenario visits that exact cell — the golden+oracle going red is the required signal).
3. Revert the edit; confirm green again.
4. Record in the verification artifact: the exact mutation, which tests went red, that revert restored green.

This closes the false-green / blind-or-miswired-harness failure mode. Because the differential oracle is deleted after D-06, run the canary **while the oracle still exists** (during the per-ghost proving window) OR target the golden traces alone for the post-deletion attestation. Recommend running it during the proving window so both signals are demonstrated.

---

## FOCUS-7 — Geometry constants placement (D-12/D-16)

### Verified literals to centralize

`num1=(HEIGHT-50)//32` = `(950-50)//32` = **28**; `num2=WIDTH//30` = `900//30` = **30**; `num3` = **15**. Recomputed inline in: `game.py:130-131` (`draw_board`), `game.py:196-197` (`has_dot_nearby`), `game.py:209-210` (`check_collisions`), `ghost.py:45-47` (`check_collisions`), `player.py:41-43` (`check_position`). [VERIFIED: grep + reads]

⚠️ **Naming landmine:** `num1` is the tile **HEIGHT** (vertical, `//num1` indexes rows) and `num2` is the tile **WIDTH** (horizontal, `//num2` indexes cols). `num3` is the look-ahead half-tile offset.

**Recommended constant names:**
```python
# settings.py (D-12 — derived once from existing WIDTH/HEIGHT)
BOARD_ROWS = 32
BOARD_COLS = 30
HUD_HEIGHT = 50                        # the (HEIGHT - 50) playfield reservation
TILE_HEIGHT = (HEIGHT - HUD_HEIGHT) // BOARD_ROWS   # = 28  (was num1)
TILE_WIDTH  = WIDTH // BOARD_COLS                   # = 30  (was num2)
HALF_TILE   = 15                                    # look-ahead offset (was num3)
```

**Recommendation on placement (the D-12-vs-D-16 open choice):** put the **derived tile constants in `settings.py`** (D-12's preference — matches the "constants in settings.py" convention, and `settings.py` already imports nothing heavy), and put the **shared helpers + box bounds + `in_box()` predicate in the new `geometry.py`** (D-16). Rationale: tile dims are flat config (belong with `WIDTH`/`HEIGHT`); the box rectangles + predicate are behavioral helpers (belong in `geometry.py`). `geometry.py` imports `TILE_*` from `settings.py`. This avoids a `player → ghost` import and keeps `settings.py` pure-constants.

**Derive from named `BOARD_ROWS`/`BOARD_COLS`/`HUD_HEIGHT`:** YES — recommended (shown above). It documents the otherwise-mysterious `32`, `30`, `50` and is byte-identical (`(950-50)//32 == 28`, `900//30 == 30`).

### Distinct named position constants (D-13) — guard against accidental unification

Name the look-alike literals as **separate** constants so Phase 3's deliberate unification is the only place they merge:

```python
# geometry.py — TWO box rectangles kept distinct (Phase 3 unifies; NOT now)
GHOST_BOX_BOUNDS_COLLISION = (350, 550, 360, 480)   # ghost.py:111  (x_lo,x_hi,y_lo,y_hi)
GHOST_BOX_BOUNDS_TARGET    = (340, 560, 340, 500)   # game.py get_targets (8 repeats) + the
                                                    # eaten-ghost checks 340<gx<560 & 340<gy<500
# wrap edges kept deliberately distinct (D-13)
GHOST_WRAP_LEFT, GHOST_WRAP_RIGHT = -30, 900        # ghost.py:250-253 etc.
PLAYER_WRAP_RIGHT_TO, PLAYER_WRAP_LEFT_TO = -47, 897  # player.py:101/103
PLAYER_WRAP_RIGHT_EDGE, PLAYER_WRAP_LEFT_EDGE = 900, -50  # player.py:100/102
# get_targets scatter / fixed points (D-13) — caught by trace `target` field anyway
SCATTER_RETURN_TARGET = (380, 400)   # game.py:235
SCATTER_EATEN_TARGET  = (400, 100)   # game.py box-eaten branches
SCATTER_CLYDE_TARGET  = (450, 450)   # game.py:265
```

⚠️ **Verified discrepancy worth flagging:** the two box predicates differ on BOTH axes — collision uses `350<x<550 & 360<y<480`; the target/eaten checks use `340<x<560 & 340<y<500`. This is exactly the BUG-01 inconsistency. Keeping them as two named constants now is what makes Phase 3 a one-line merge with a clean isolation proof (D-14). The `check_collisions` box test uses `self.x_pos`/`self.y_pos` (top-left), while `get_targets` uses `self.{name}_x`/`_y` (also top-left, the stored Game attrs) — both operate on top-left coords, so the predicate signature is uniform.

**Leave inline (D-13):** `draw_board` cosmetic literals (circle radii 4/10, `PI` fractions, line width 3, the `0.5*`/`0.4*` arc offsets). These are rendering, not geometry.

---

## FOCUS-8 — `geometry.py` shared helpers (D-14/D-16)

The ONLY pieces genuinely shared between `Player.check_position` and `Ghost.check_collisions` (D-15 declined full unification — they are divergent):

```python
# geometry.py
from settings import TILE_HEIGHT, TILE_WIDTH

def tile_at(center_x, center_y, level):
    """Row/col tile lookup using the centralized tile dims (was center // num)."""
    return level[center_y // TILE_HEIGHT][center_x // TILE_WIDTH]

def is_walkable(tile_code):
    """The project-wide `< 3` idiom (0=empty,1=dot,2=big dot walkable)."""
    return tile_code < 3

def in_box(x, y, bounds):
    """Structured box predicate collapsing ~9 inline checks. bounds=(x_lo,x_hi,y_lo,y_hi)."""
    x_lo, x_hi, y_lo, y_hi = bounds
    return x_lo < x < x_hi and y_lo < y < y_hi
```

- `in_box(x, y, bounds)` collapses the **~9 repeated checks**: 8 in `get_targets` (`game.py:240,249,258,267,275,282,289,296`) + 1 in `check_collisions` (`ghost.py:111`). Verified counts. Each call passes the appropriate bounds constant (`GHOST_BOX_BOUNDS_TARGET` for get_targets, `GHOST_BOX_BOUNDS_COLLISION` for check_collisions) — so the two-bounds distinction survives until Phase 3.
- `tile_at` / `is_walkable` replace the raw `level[cy//num1][cx//num2]` and `< 3` idioms in both `check_position` and `check_collisions`.

⚠️ **Landmine — do NOT over-share (D-15):** `Ghost.check_collisions` and `Player.check_position` use **different look-ahead structure**. Verified: ghost uses `num3` (=15) AND `num2`/`num1` offsets in its alignment bands (`ghost.py:90-107` mixes `num2` and `num3`); player's alignment bands at `player.py:67-69` use `num2` while `73-75` use `num1`. They also have different guards (`0 < center_x//30 < 29` for ghost vs `center_x//30 < 29` for player) and the gate-tile-9 + `in_box`/`dead` logic is **ghost-only**. Share ONLY the three atomic helpers above; do NOT attempt to factor the band logic into a shared function.

⚠️ **Hard-coded `30` inside the guards:** both `check_collisions` (`0 < self.center_x // 30 < 29`) and `check_position` (`centerx // 30 < 29`) use a literal `30` that happens to equal `TILE_WIDTH`. When centralizing, replace with `TILE_WIDTH` — but verify byte-identity: `center_x // 30 == center_x // TILE_WIDTH` since `TILE_WIDTH == 30`. The `29` bound (= `BOARD_COLS - 1`) should become `BOARD_COLS - 1` for clarity (byte-identical). The differential oracle (FOCUS-4) is what proves these substitutions are safe.

---

## FOCUS-9 — Test-tree layout & plan decomposition (D-11)

### Recommended test-tree layout

Extend the existing flat `tests/` (house style — no nested dirs for test modules; `conftest.py` + `tests/golden/`):

```
tests/
├── _legacy_movers.py            # one-shot frozen OLD movers + OLD check_collisions (deleted after D-06/D-07)
├── test_mover_oracle.py         # synthetic-exhaustive differential oracle (FOCUS-3) — deleted after green
├── test_check_collisions_oracle.py  # geometry differential oracle (FOCUS-4) — deleted after green
├── test_frame_hash.py           # frame-hash assert vs committed manifest (FOCUS-5) — PERMANENT
├── golden/<scenario>/frame_hashes.txt   # committed TEXT manifest (D-09) — PERMANENT
└── (existing) test_ghost_micro.py, test_golden_traces.py  # UNTOUCHED
```

`frame_hash` assertion can alternatively be folded into `test_golden_traces.py`'s existing `--bless` flow rather than a separate file — planner's call; a separate file is cleaner for the bless-write logic.

### D-11 sequence (confirmed)

1. **Geometry first:** centralize `TILE_*`/box/wrap constants + `geometry.py` helpers → prove `check_collisions` oracle green + frame-hash green → atomic commit.
2. **blinky:** extract `BLINKY_PROFILE` + unified `_move`; prove `unified(blinky) == legacy_blinky` across the full synthetic space → commit green.
3. **inky** → commit green. 4. **pinky** → commit green. 5. **clyde** → commit green.
6. Delete `_legacy_movers.py` + the two oracle test files (D-06/D-07); golden traces + 15 micro tests remain.
7. Run the mutation canary (during the proving window, before deletion) + update `CLAUDE.md` Ghost System section (D-17).

### Plan decomposition recommendation (coarse granularity per config)

Given `granularity: coarse` and the per-ghost atomic-commit sequence, recommend **2 PLAN.md files**:

- **Plan A — Geometry centralization (REF-01):** `settings.py` constants, `geometry.py` helpers, substitute literals in game/ghost/player, the `check_collisions` differential oracle, the frame-hash check + manifest. One atomic green commit.
- **Plan B — Data-driven mover (REF-02):** profile schema + unified `_move` + thin wrappers, the synthetic differential oracle, the per-ghost sequence (blinky→inky→pinky→clyde as commits *within* the plan's tasks), the mutation canary, oracle deletion, and the D-17 `CLAUDE.md` doc update.

Two plans cleanly mirror the two requirements (REF-01 / REF-02) and the two proof modalities (geometry/frame-hash vs mover/differential). Splitting per-ghost into 4 plans is overkill at coarse granularity — the per-ghost commits live as ordered tasks inside Plan B. **Do not** combine into one plan: REF-01 must be fully proven-green before REF-02 starts (D-11), so a plan boundary enforces the gate.

---

## FOCUS-10 — Validation Architecture (Nyquist)

`workflow.nyquist_validation: false` in `.planning/config.json` — **the Validation Architecture section is intentionally omitted.** Verification for this phase is the differential oracles + frame-hash + golden traces + mutation canary described above, which exceed Nyquist sampling by construction (exhaustive, not sampled).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Deterministic pixel bytes | Custom surface-walk / per-pixel loop | `pygame.image.tobytes(surface, "RGB")` | Built-in, deterministic, zero dep [CITED: pygame docs] |
| Frame hash | Custom checksum | `hashlib.sha256(...).hexdigest()` | stdlib, collision-safe |
| Mutation testing | `mutmut`/`cosmic-ray` install + config | A single manual edit, run once, attest | One-shot canary (D-10); frameworks are heavyweight for run-once |
| Headless ghost construction | New test fixture | Existing `make_ghost` (`test_ghost_micro.py:41`) | Already builds ghosts in arbitrary states headless (D-13/D-14) |
| Trace diff / equality | New comparison | Existing `harness/trace.py:traces_equal/diff_traces` | Already byte-exact + human-readable diff |
| GIF for human gate | New encoder | Existing `harness/capture.py:build_gif` | HRN-03 already ships it (D-19) |
| Re-bless flow | New script | Existing `--bless` flag in `conftest.py`/`test_golden_traces.py` | D-07/D-09 reuse it |

**Key insight:** Phase 1 built nearly every tool Phase 2 needs. The only genuinely new code is the two one-shot differential oracles, the frozen legacy-mover copy, the frame-hash assert + text manifest, and the profile data + unified `_move`. Everything else is reuse.

---

## Common Pitfalls

### Pitfall 1: Treating each ghost as "one priority list"
**What goes wrong:** A schema with one ordered list per ghost silently bricks Q-a/Q-b/Q-c.
**Why:** The orderings differ *per direction* (dir-2 blinky vs others), and PRIMARY/FORWARD-OPEN branches are control-flow not ordering.
**How to avoid:** Model per (ghost × direction) cell with named hooks for primary/forward-open.
**Warning signs:** Differential oracle goes red only at specific `direction` values.

### Pitfall 2: Using `elif` where the original used `if … if … else`
**What goes wrong:** Q-c override branches change semantics — the second `if` can override the first in the same frame; an `elif` makes them mutually exclusive.
**Why:** `if X: …; if Y: …; else: …` lets BOTH X and Y fire (Y's else binds only to Y).
**How to avoid:** Transcribe those forward-open hooks as literal Python, not as a ladder.
**Warning signs:** Divergence in forward-open cases where both target axes point "toward."

### Pitfall 3: inky vs pinky dir-1 stutter (Q-b)
**What goes wrong:** Copying pinky's "set direction AND move" onto inky (or vice versa).
**Why:** inky dir-1 PRIMARY sets `direction=3` with **no** `y_pos +=` that frame; pinky sets direction AND moves.
**How to avoid:** Two distinct named hooks (`turn_no_move_down` vs `turn_and_move_down`).
**Warning signs:** inky drifts one pixel ahead/behind its golden trace at left-facing turns.

### Pitfall 4: Frame-hash drift from fonts / non-pinned env
**What goes wrong:** Asserting frame-hash on Windows dev → false red (different font rasterization).
**Why:** Score text uses `freesansbold.ttf`; rasterization can differ across SDL builds.
**How to avoid:** Bless + assert frame-hash ONLY in the Linux pinned CI env (D-08/D-09); regenerate elsewhere.
**Warning signs:** Hash mismatch on dev but green in CI.

### Pitfall 5: Shared board mutation across oracle cases
**What goes wrong:** A mutated `level` (dots eaten) leaks between thousands of oracle cases.
**Why:** `board.boards` is a shared module list.
**How to avoid:** `make_ghost` already deep-copies `board.boards` per construction (Pitfall 4 in `test_ghost_micro.py`). Keep using it; don't share a single ghost across cases.

### Pitfall 6: Over-unifying check_position / check_collisions
**What goes wrong:** Factoring the band logic into a shared function introduces conditionals that change behavior.
**Why:** D-15 verified they are structurally divergent (guards, offsets, gate logic, wraps).
**How to avoid:** Share ONLY `tile_at`, `is_walkable`, `in_box`. Leave band logic in place.

---

## Code Examples

### Deterministic frame hash (FOCUS-5)
```python
# Source: pygame docs (image.tobytes) + stdlib hashlib
import hashlib
def frame_hash(pygame, surface):
    return hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()
```

### Bypassing check_collisions to set synthetic inputs (FOCUS-3)
```python
g = make_ghost(screen, x, y, target=(tx, ty), speed=spd, direction=d, ghost_id=gid,
               dead=dead, box=box)
g.turns = list(turns_combo)   # synthetic [R,L,U,D] — overrides check_collisions output
g.in_box = box
result = g.move_blinky()      # (x_pos, y_pos, direction)
```

### Shared box predicate (FOCUS-8)
```python
# geometry.py
def in_box(x, y, bounds):
    x_lo, x_hi, y_lo, y_hi = bounds
    return x_lo < x < x_hi and y_lo < y < y_hi
# usage: in_box(self.x_pos, self.y_pos, GHOST_BOX_BOUNDS_COLLISION)
```

---

## State of the Art

| Old Approach | Current Approach | When | Impact |
|--------------|------------------|------|--------|
| `pygame.image.tostring` | `pygame.image.tobytes` (alias) | pygame 2.1.3 | Use `tobytes`; both identical, `tobytes` is the recommended name [CITED: pygame docs] |

**Deprecated/outdated:** none relevant to this phase. pygame 2.6.1 (pinned) is current and stable.

---

## Runtime State Inventory

This phase edits code + adds tests only. It is a **refactor**, but it does NOT rename any stored key, service config, OS registration, secret, or installed-package name — the public method names (`move_blinky` etc.) and all settings constants are deliberately preserved (D-02/D-12).

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — no DB keys, collection names, or user_ids touched. The golden `trace.jsonl` files are regenerated via `--bless` if blessed, but their *schema* (D-03 fields) is unchanged. | None (traces stay byte-identical by design — that's the whole proof) |
| Live service config | None — no n8n/Datadog/Tailscale/Cloudflare. | None |
| OS-registered state | None — no Task Scheduler/pm2/systemd. | None |
| Secrets/env vars | None — `SDL_VIDEODRIVER`/`SDL_AUDIODRIVER` env are set by harness, name unchanged. | None |
| Build artifacts | `tests/__pycache__/*.pyc` will go stale when test files are deleted (oracle files removed after D-06). Harmless — pytest regenerates. The `build.py` exe is unaffected (game logic byte-identical). | None (pycache self-heals) |

**Verified:** the golden `frame_hashes.txt` manifest is NEW committed text (D-09); the golden `trace.jsonl` must remain byte-identical (re-bless should produce zero diff — if it doesn't, the refactor bricked something). No runtime state outside the repo is affected.

---

## Project Constraints (from CLAUDE.md)

- **Run/test commands:** `python main.py`; `pytest`; `pytest tests/test_api_service.py::test_...`; `python build.py` → `dist/pacman/pacman.exe`. New tests must run under bare `pytest`.
- **Direction convention:** `0=Right, 1=Left, 2=Up, 3=Down` — preserve exactly in the profile data and hooks.
- **Tile codes:** `0=empty,1=dot,2=big dot,3=vert wall,4=horiz wall,5-8=corners,9=gate`; walkability `< 3` (keep the `is_walkable` helper semantically identical, including the gate-tile-9 special case in `check_collisions`).
- **Ghost System doc (D-17):** the "each ghost has its own AI method" paragraph MUST be updated this phase to describe the unified data-driven mover + per-ghost profiles + thin wrappers.
- **Ghosts recreated every frame:** all ghost state lives on `Game` and is passed to constructors — the unified mover must remain stateless beyond `self.*`.
- **`move_clyde` doubles as fallback** for dead/in-box ghosts — preserve (D-02).
- **Constants in `settings.py`:** new derived tile constants belong there (D-12); behavioral helpers in `geometry.py` (D-16).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Frame-hash sampling (every Nth frame + terminal) is sufficient coverage vs. hashing every frame | FOCUS-5 | A geometry bug that shifts pixels only on un-sampled frames escapes; mitigated because geometry bugs are global (shift ALL frames) so any sampled frame catches them. Planner may choose full-frame hashing if manifest size is acceptable. |
| A2 | Full synthetic enumeration (~138k oracle calls) runs < 10s in CI | FOCUS-3 | If slower than budget, drop speed cross on in_box/dead cases; still cheap. Verify on first CI run. |
| A3 | `check_collisions` oracle enumeration (tile centers + half-tile + alignment band, ~46k cases) covers the precedence-sensitive branches | FOCUS-4 | If a band edge case is missed, the golden traces (box_edge/tunnel_wrap scenarios) are the backstop. Could enumerate every integer pixel if paranoid (slower). |
| A4 | The dir-0/dir-1/dir-3 blocked ladders are byte-identical across all four ghosts | FOCUS-1 | LOW — verified by direct read, but the differential oracle is what actually proves it; if wrong, oracle goes red and the planner adds a per-ghost ladder for that direction. |

**Note:** A1-A4 are mechanics the user explicitly delegated to Claude's Discretion (CONTEXT.md). They do not require re-asking the user; the differential oracles + golden traces are self-correcting (red = wrong assumption). The 19 locked decisions are NOT assumptions.

---

## Open Questions

1. **Should the frame-hash assert live in `test_golden_traces.py` (folded into `--bless`) or a separate `test_frame_hash.py`?**
   - What we know: both work; `--bless` already re-records traces in `test_baseline_golden`.
   - What's unclear: whether folding adds too much to one test function.
   - Recommendation: separate `test_frame_hash.py` for clean bless-write logic; planner decides.

2. **Re-run the Phase 1 live adversarial Claude playtest (Phase 1 D-10) for Phase 2?**
   - What we know: CONTEXT.md says "likely unnecessary — the differential proof makes behavior provably identical; a replay would re-exercise known-good behavior."
   - Recommendation: skip the live adversarial hunt; the D-19 before/after GIF + green oracles is the human gate. Planner's call (delegated in CONTEXT.md).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| pytest | All tests | ✓ (pinned) | 8.4.2 | — |
| pygame | Frame-hash, headless ghosts | ✓ (pinned) | 2.6.1 | — |
| Pillow | D-19 human GIF | ✓ (pinned) | 11.0.0 | — |
| hashlib | Frame-hash | ✓ stdlib | — | — |
| GitHub Actions (ubuntu-latest, Py 3.12) | Pinned bless env (D-08), required check (D-09) | ✓ (`.github/workflows/ci.yml`) | Python 3.12 | — |

**Missing dependencies:** none. No new dependency is introduced (D-20 spirit preserved — Pillow remains the only "extra," already present).

---

## Security Domain

`security_enforcement: true`, `security_asvs_level: 1` in config. **However, this phase introduces no new attack surface:** it is a behavior-preserving refactor of local single-player game logic + test code. No network, no input parsing of untrusted data, no auth/session/crypto, no persistence of user data. The cloud-function validators (initials regex, score range) are NOT touched (TST-03 already covers them, Phase 1).

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | N/A (no auth in scope) |
| V3 Session Management | no | N/A |
| V4 Access Control | no | N/A |
| V5 Input Validation | no | The mover/geometry consume only internal game state, never external input |
| V6 Cryptography | no | `hashlib.sha256` used for equality-checking, not security; no crypto requirements |

**Threat patterns:** none applicable — no untrusted input crosses any boundary this phase touches. The refactor cannot introduce an injection/tampering vector because it adds no parsing and no I/O beyond test artifacts written to gitignored `tests/artifacts/`.

---

## Sources

### Primary (HIGH confidence)
- `ghost.py` (full read, L1-609) — exact mover orderings + all three quirks, `check_collisions` literals
- `game.py` (full read, L1-564) — `move_ghosts` clyde-fallback dispatch, `draw_board` geometry, `get_targets` 8 box checks, scatter targets
- `player.py` (full read, L1-120) — `check_position` divergence, wrap edges, tile math
- `settings.py`, `requirements-dev.txt`, `.github/workflows/ci.yml` — constants, pinned versions, bless env
- `tests/test_ghost_micro.py`, `tests/test_golden_traces.py`, `tests/conftest.py`, `harness/trace.py`, `harness/capture.py`, `harness/headless.py` — existing net + `make_ghost` + `--bless` + capture
- `tests/golden/manifest.json` — the 9 golden scenarios (box_edge/tunnel_wrap/eyes_return relevant)
- `/pygame/pygame` (Context7) — `image.tobytes`/`tostring` semantics, `tobytes` recommended since 2.1.3, RGB format, no-numpy byte extraction
- `02-CONTEXT.md` (19 locked decisions), `REQUIREMENTS.md` (REF-01/REF-02), design spec Phase C steps 8-10, `CONVENTIONS.md`

### Secondary (MEDIUM confidence)
- Case-count estimates (FOCUS-3/4) — arithmetic from the enumerated dimensions; runtime is an estimate (A2/A3) to confirm on first CI run.

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Mover schema + quirks: HIGH — every ordering and quirk read verbatim from `ghost.py` and cross-checked against the 15 micro tests.
- Geometry centralization: HIGH — all literals located by grep + read; byte-identity of substitutions verified arithmetically.
- Verification mechanics (oracles/frame-hash/canary): HIGH on approach, MEDIUM on exact runtime budget (A2/A3, self-correcting via red tests).
- Library specifics (pygame `tobytes`): HIGH — confirmed via Context7.

**Research date:** 2026-06-12
**Valid until:** 2026-07-12 (stable — pinned deps, no fast-moving external surface)

## RESEARCH COMPLETE
