# Phase 1: Test Safety Net - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-11
**Phase:** 1-Test Safety Net
**Areas discussed:** Scenario coverage, Golden artifacts, CI matrix & triggers, Claude playtest gate, Trace field strictness, Dev/harness dependencies, Micro per-ghost test design, Adversarial invariants, Determinism guard, Scripted-input format, Cloud-function test strategy, Headless frame-throttle, Session terminal condition

---

## Scenario coverage

| Option | Description | Selected |
|--------|-------------|----------|
| Targeted scripts + 1 long session | Short named scripts isolating one behavior + one long Claude-played session | ✓ |
| Just the spec's 5 scripted scenarios | box-exit, power chase, ghost-eat, death, win only | |
| Broader matrix | The 5 + tunnel-wrap, multi-eat chain, full game-over, level-clear | |

**User's choice:** Targeted scripts + 1 long session.
**Follow-up (which extra targeted scripts):** selected **all** of ghost-at-box-edge approaches, tunnel wrap-around, dead-ghost return-to-box (eyes) — *and* "long session covers these" (interpreted as: build all three targeted scripts AND rely on the long session — maximum thoroughness).

---

## Golden artifacts

| Option | Description | Selected |
|--------|-------------|----------|
| Traces + inputs only; visuals regenerated | Commit JSONL traces + input sequences; gitignore PNG/montage/GIF | ✓ |
| Also commit one reference montage per scenario | + one blessed montage PNG each | |
| Commit everything | Traces + montages + GIFs in git | |

**User's choice:** Traces + inputs only; visuals regenerated.

**Re-bless mechanism:**

| Option | Description | Selected |
|--------|-------------|----------|
| Bless flag that surfaces the diff | Regenerate + print human-readable diff before commit | ✓ |
| Bless + auto-fail on unexpected scope | + machine-enforced expected-change scope | |
| You decide | Planner picks | |

**User's choice:** Bless flag that surfaces the diff.

---

## CI matrix & triggers

| Option | Description | Selected |
|--------|-------------|----------|
| Linux-only, pinned env is canonical | ubuntu-latest + pinned Python/pygame as the bless env | ✓ |
| Windows-only | windows-latest, matches dev + ship target | |
| Both (Linux gate + Windows job) | matrix | |

**User's choice:** Linux-only, pinned env is canonical.

**Triggers / gate:**

| Option | Description | Selected |
|--------|-------------|----------|
| Push to any branch + PRs to main; required to merge | branch protection on main | ✓ |
| PRs to main only | | |
| Push everywhere, not required to merge | advisory | |

**User's choice:** Push to any branch + PRs to main; green required to merge.
**Notes:** GitHub remote confirmed to exist during scout (`github.com/jadrianports/pacman-firebase`).

---

## Claude playtest gate

| Option | Description | Selected |
|--------|-------------|----------|
| Freeze session as replayable input trace; live hunt stays manual | Record one session's inputs as a deterministic CI golden; live adversarial hunt is a manual gate | ✓ |
| CI-replay only; drop live hunt as standing gate | | |
| You decide | | |

**User's choice:** Freeze session as replayable input trace; live hunt stays manual.

---

## Trace field strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Observable + per-ghost target | Spec's observable fields + each ghost's target tuple | ✓ |
| Strict observable only | Spec list as-is | |
| Maximal internal state | + box timers, powerup countdown, phase flags | |

**User's choice:** Observable + per-ghost target.
**Notes:** Claude verified all positions/speeds are integers → exact-integer, platform-independent traces; no float rounding policy needed.

---

## Dev/harness dependencies

| Option | Description | Selected |
|--------|-------------|----------|
| requirements-dev.txt; pygame for PNG+montage, Pillow only for GIF | flat pinned dev file; minimal new dep | ✓ |
| Introduce pyproject.toml with [optional-dependencies] | | |
| You decide | | |

**User's choice:** requirements-dev.txt; pygame for PNG+montage, Pillow only for GIF.

---

## Micro per-ghost test design

| Option | Description | Selected |
|--------|-------------|----------|
| Hand-curated decisive states, informed by the traces | Per-ghost decisive board states; exact-turn assertions | ✓ |
| Auto-sample states from the golden traces | | |
| You decide | | |

**User's choice:** Hand-curated decisive states, informed by the traces.

---

## Adversarial invariants

| Option | Description | Selected |
|--------|-------------|----------|
| Standing invariants on every replay | score range, no wall-clip, phase-aware no-soft-lock asserted every replay | ✓ |
| Invariants only in the manual live hunt | | |
| You decide | | |

**User's choice:** Standing invariants on every replay.

---

## Determinism guard

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — fail CI on forbidden non-determinism | static/AST test bans random/time.time/get_ticks/datetime in core | ✓ |
| Yes, but advisory only | warning, not failure | |
| Skip it | | |

**User's choice:** Yes — fail CI on forbidden non-determinism.

---

## Scripted-input format

| Option | Description | Selected |
|--------|-------------|----------|
| Sparse (frame, key) event list | {frame, key} JSONL beside the trace; injected via pygame.event.post | ✓ |
| Dense per-frame direction array | | |
| You decide | | |

**User's choice:** Sparse (frame, key) event list.

---

## Cloud-function test strategy (TST-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Mock firebase-admin; test entrypoint + upsert unit | conftest patches before import; assert validators + is_new_best | ✓ |
| Extract pure validators + upsert helper, then unit-test | small backend refactor | |
| Firestore emulator (real transaction) | needs Java; cuts against Linux-only-fast | |

**User's choice:** Mock firebase-admin; test entrypoint + upsert unit.
**Notes:** Code read during discussion — `submit_score/main.py` does `initialize_app()`/`firestore.client()` at import (C2), validators are inline, `_update_score` is `@firestore.transactional`. Tests target the uncommitted working-tree code.

---

## Headless frame-throttle

| Option | Description | Selected |
|--------|-------------|----------|
| Throttle only in interactive run(); replay runs uncapped | tick() sleep-independent; harness tight-loops | ✓ |
| Keep timer.tick(FPS) in the harness too | | |
| You decide | | |

**User's choice:** Throttle only in interactive run(); replay runs uncapped.

---

## Session terminal condition

| Option | Description | Selected |
|--------|-------------|----------|
| Run to natural terminal + safety frame cap | win / all-lives game-over, bounded by a cap that backstops soft-locks | ✓ |
| Fixed frame budget per scenario | | |
| You decide | | |

**User's choice:** Run to natural terminal + safety frame cap.

---

## Claude's Discretion

Left to the planner/researcher (user confirmed): golden-artifact directory layout & scenario manifest
format; `conftest.py` sys.path / firebase-admin pre-import patch wiring; scenario naming conventions
and the soft-lock frame threshold `N`; exact pinned Python/pygame versions.

## Deferred Ideas

None — discussion stayed within phase scope.
