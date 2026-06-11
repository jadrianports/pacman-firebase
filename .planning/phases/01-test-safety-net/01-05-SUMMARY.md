---
phase: 01-test-safety-net
plan: 05
subsystem: test-safety-net
tags: [characterization, ghost-ai, headless, pytest]
requires:
  - "01-01 (venv + headless deps + conftest SDL-dummy/sys.path)"
provides:
  - "TST-02: micro per-ghost decision characterization (check_collisions + move_blinky/inky/pinky/clyde) pinned at decisive board states"
  - "make_ghost() headless Ghost-construction helper (reusable by future micro tests)"
affects:
  - "Phase 2 tick()/movement-duplication collapse — these tests are the per-decision safety net"
tech-stack:
  added: []
  patterns:
    - "Headless Ghost construction against SDL-dummy surface (D-14, no ghost.py change)"
    - "copy.deepcopy(board.boards) per case to prevent dot/tile leakage (Pitfall 4)"
    - "Characterization: run the method, pin its exact return as the spec literal"
key-files:
  created:
    - "tests/test_ghost_micro.py"
  modified: []
decisions:
  - "Flee-vs-chase is expressed via the TARGET tuple (runaway vs chase), not the powerup flag — move_* reads self.target directly; powerup only changes which target game.get_targets picks, so toggling powerup inside a move_* call does not by itself change the decision. The flee/chase tests therefore vary the target (above vs below) at one fixed intersection."
  - "Decisive intersection chosen at (384, 50) dir 0: check_collisions yields turns [False, True, True, True] (right walled), forcing each move_* to branch on the target — the cleanest state for a flip-on-target characterization."
metrics:
  duration: "~12 min"
  completed: "2026-06-11"
  tasks: 2
  files: 1
  tests_added: 15
---

# Phase 1 Plan 05: Micro Per-Ghost Decision Characterization Summary

Headless characterization tests that pin the EXACT current per-ghost decisions
(`check_collisions` + `move_blinky`/`move_inky`/`move_pinky`/`move_clyde`) at
hand-curated decisive board states, so any Phase 2 movement-collapse drift names
the precise ghost + situation — `ghost.py` is untouched (D-14).

## What Was Built

`tests/test_ghost_micro.py` (NEW, 15 tests, all passing):

- **`make_ghost(...)` helper** — constructs a `Ghost` from the full
  `ghost.py:6-7` `__init__` signature headlessly: dummy `pygame.Surface((45,45))`
  images, `eaten_ghost=[False]*4`, and a `copy.deepcopy(board.boards)` as `level`
  (never the shared module list — Pitfall 4). Module-scoped `screen` fixture
  opens an SDL-dummy surface (drivers forced by `conftest.py` before pygame
  import).

- **`check_collisions` characterization (Task 1, 5 tests)** — pins the exact
  `(turns, in_box)` at: the decisive intersection (384,50) → `[False,True,True,True]`;
  box edge inside (450,420) → `in_box True`; box edge outside (340,420) →
  `in_box False`; tunnel-mouth left edge (0,460) → else-branch forces L+R open
  `[True,True,False,False]`.

- **`move_*` decisive-state characterization (Task 2, 10 tests)** — each asserts
  the exact `(x, y, dir)` integer tuple the current code returns:
  - Multi-way intersection + flee-vs-chase: all four ghosts at (384,50) dir 0
    (right walled) turn **UP `(384,48,2)`** with a chase target above, **DOWN
    `(384,52,3)`** with a runaway target below — the decision flips purely on the
    target tuple.
  - Tunnel mouth: `move_inky` dir1 at x=-28 wraps to `(900,460,1)`; `move_pinky`
    dir0 at x=898 wraps to `(-30,460,0)`.
  - Box edge / dead fallback: `move_clyde` dead & in_box at (480,438) dir2 with
    box-gate target → `(478,438,1)` (the "eyes" return-to-box move Phase 2 must
    preserve).

## Tasks

| Task | Name | Commit | Files |
| ---- | ---- | ------ | ----- |
| 1 | Headless helper + check_collisions characterization | `f1133c5` | tests/test_ghost_micro.py |
| 2 | move_blinky/inky/pinky/clyde decisive-state characterization | `b53bb10` | tests/test_ghost_micro.py |

## Verification

```
./.venv/Scripts/python.exe -m pytest tests/test_ghost_micro.py -q
15 passed in 0.13s
```

- All four `move_*` methods AND `check_collisions` are pinned with exact literal
  integer/bool values (not ranges or truthiness).
- All four archetypes present: multi-way intersection, tunnel mouth, box edge,
  flee-vs-chase.
- `git diff HEAD -- ghost.py` is empty (D-14 honored).
- `copy.deepcopy(board.boards)` used per case (Pitfall 4 mitigated; threat T-05-T).

## Deviations from Plan

**1. [Clarification, not a code change] Flee-vs-chase modeled via the target tuple, not the powerup flag.**
- **Found during:** Task 2 discovery (running `move_blinky` with `powerup=True`).
- **Observation:** `move_*` methods read `self.target` directly and never read
  `self.powerup`. In the live game, `powerup` only changes which target
  `game.get_targets()` selects (chase Pac-Man vs runaway corner). So toggling
  `powerup` on the constructed Ghost does NOT by itself change the move decision.
- **Resolution:** The flee-vs-chase characterization varies the **target** (chase
  target above vs runaway target below) at one fixed intersection — which is the
  real mechanism by which flee differs from chase. This faithfully characterizes
  current behavior and still satisfies D-13 "flee-vs-chase using runaway vs the
  get_targets target". No source changed. (The plan's wording suggested setting
  `powerup True`; doing so alone is behaviorally inert here, so the stronger,
  honest signal is the target flip.)
- **Files modified:** tests/test_ghost_micro.py only.

No `ghost.py` (or any source) behavior was changed. No "bug" was corrected — the
tests lock in current behavior exactly as required for the upcoming tick()
extraction safety net.

## Known Stubs

None. Every test asserts concrete literal values captured from the live code.

## Self-Check: PASSED

- `tests/test_ghost_micro.py` — FOUND.
- Commit `f1133c5` — FOUND.
- Commit `b53bb10` — FOUND.
