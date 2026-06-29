# Re-bless note: WR-03 pre-move-catch fix

Follow-up golden re-bless after the WR-03 fix (`fe8f845`). Production code is final; only the
committed golden FIXTURES were stale because FAIR-01 now samples the player's **pre-move** center
in `_catches` (`game.py`), shifting catch timing by `<= PLAYER_SPEED` px. That moves a few
death/ghost_eat-adjacent outcomes by a frame or two.

## What ran

- **One deliberate Linux/Docker re-bless** — `python:3.12` container, effective `pygame 2.6.1`
  (SDL 2.28.4), `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy`, `MSYS_NO_PATHCONV=1` for the
  Git Bash mount. CI-exact install (`requirements.txt` then `requirements-dev.txt`). NEVER on
  Windows (frame-hash font rasterization differs — Pitfall 3).
- Bless: `pytest --bless` over `test_golden_traces.py` + `test_frame_hash.py` -> 23 passed, 1 skipped.
- Asserting golden net in the SAME container with `GSD_FRAME_HASH_ENV=1`
  (`test_golden_traces` + `test_frame_hash` + `test_ghost_micro` + `test_determinism_guard`)
  -> **44 passed**, including the `death` game_over terminal and `ghost_eat` eat registration
  (`assert_invariants`). No `input.jsonl` re-authoring needed (Pitfall 2 did not trigger).

## Result

- Regenerated where the trace actually moved: `ghost_eat`, `power_chase`, `eyes_return`,
  `win`, `claude_session_01` (trace.jsonl + frame_hashes.txt). The other 4 scenarios
  (`box_exit`, `box_edge`, `death`, `tunnel_wrap`) were byte-identical under the <=2px shift,
  so the bless left them unchanged.
- `grep -rlE '[0-9]+\.[0-9]+' tests/golden/*/trace.jsonl` -> CLEAN (positions stayed integer).
- `ghost.py` byte-identical vs `3ad5305` (zero diff) — ghost decision logic untouched.
- Signed-off constants unchanged: `GHOST_CATCH_DISTANCE=24`, `GHOST_CHASE_SPEED_NUM=40`,
  `GHOST_CHASE_SPEED_DEN=20`, `PLAYER_TURN_WINDOW_MARGIN=6`.

Out of scope (unchanged): the pre-existing `pygame`/`pygame-ce` `gaussian_blur` packaging
conflict (12 UI/juice failures) — see `deferred-items.md`. Not a fairness regression; the
golden net is green.
