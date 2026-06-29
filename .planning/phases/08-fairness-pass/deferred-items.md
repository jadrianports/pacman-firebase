# Phase 08 — Deferred Items

## Golden-master trace re-bless (deferred to a single Linux/Docker pass after D-10)

**Discovered during:** Plan 08-02 (FAIR-01/FAIR-02 implementation), Task 2 full-suite check.

**What:** After FAIR-01 (corner-kiss-safe catch) and FAIR-02 (1.85 px/frame chase tier),
the 10 recorded golden-trace baselines in `tests/test_golden_traces.py` necessarily
diverge from the new deterministic behavior:

- `test_baseline_golden[box_exit, power_chase, ghost_eat, death, win, box_edge, tunnel_wrap, eyes_return, claude_session_01]`
- `test_claude_session_replays_green`

The divergence is the intended behavior change of this phase (slower chasers travel
~20px less over the trace window; Pac-Man no longer dies on a corner-kiss so its
position drifts downstream). It is NOT a regression.

**Why deferred (not fixed here):**
- Project memory + 08-RESEARCH: golden traces must be re-blessed **on Linux only**
  (use a `python:3.12` Docker container), never on Windows — Windows re-bless would
  bake platform-specific frame hashes into the committed goldens.
- Plan 08-02 verification scope is explicitly the fast non-golden proofs
  (`test_fairness_unit.py`, `test_ghost_micro.py`, `test_determinism_guard.py`), all
  green. Golden re-bless is a separate, post-D-10-playtest operator step so the dials
  (`GHOST_CATCH_DISTANCE`, `GHOST_CHASE_SPEED_NUM/DEN`) settle before recording.

**Resolution step (operator, post-D-10):** run the golden harness with `--bless` inside
a Linux `python:3.12` Docker container, then commit the refreshed
`tests/golden/` traces.

**RESOLVED — Plan 08-04, Task 2/3 (2026-06-30):** One deliberate `pytest --bless` ran in a
`python:3.12` Linux Docker container (effective `pygame 2.6.1`, SDL 2.28.4, `SDL_*=dummy`),
covering FAIR-01 + FAIR-02 + FAIR-03 together under the D-10-signed-off constants
(`GHOST_CATCH_DISTANCE=24`, `GHOST_CHASE_SPEED_NUM=40`, `GHOST_CHASE_SPEED_DEN=20`,
`PLAYER_TURN_WINDOW_MARGIN=6`). All 9 `trace.jsonl` (8 changed; `box_exit` integer state
unaffected) and all 9 `frame_hashes.txt` regenerated and committed in one re-bless commit.
The `death` game_over terminal and `ghost_eat` eat both still fired — no `input.jsonl`
re-authoring needed. No float leaked into any trace (CLEAN).

---

## Out-of-scope: `pygame` vs `pygame-ce` `gaussian_blur` packaging conflict (NOT a fairness item)

**Discovered during:** Plan 08-04 Task 2, the full-suite `pytest -q` run in the Linux container.

**What:** 12 UI/juice render tests fail in the pinned Linux env with
`AttributeError: module 'pygame.transform' has no attribute 'gaussian_blur'` at `theme.py:45`:
- `tests/test_juice.py` (2), `tests/test_juice_firewall.py` (1),
  `tests/test_menu_render.py` (8), `tests/test_theme.py` (1).

**Why it happens (root cause):** `requirements.txt` pins `pygame-ce==2.5.7` (the app's real
runtime, which *has* `pygame.transform.gaussian_blur`), but `requirements-dev.txt` pins
`pygame==2.6.1`. CI installs both files in order, so the `pygame` import namespace resolves to
upstream `pygame 2.6.1` (installed last) — and upstream pygame has **no** `gaussian_blur`
(it is a `pygame-ce`-only extension used by the UI-redesign / Phase-9 juice code in `theme.py`).

**Pre-existing & out of scope:** This is purely a packaging/env conflict; it is independent of
the fairness constants and the golden fixtures, and reproduces with or without this plan's
re-bless. It is **not** part of the Phase-8 golden net (9 traces + 15 micro + frame-hash +
determinism guard), which is fully green. Per the executor scope boundary it was logged here,
not fixed in this fairness re-bless.

**Resolution step (operator, future):** reconcile the pygame distribution across
`requirements.txt`/`requirements-dev.txt` so the env that runs the UI/juice tests provides
`gaussian_blur` (e.g. align both on `pygame-ce`, or guard `theme.glow_text` for plain `pygame`).
Verify the frame-hash manifests still match after any pygame-distribution change (Pitfall 3).
