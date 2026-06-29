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
