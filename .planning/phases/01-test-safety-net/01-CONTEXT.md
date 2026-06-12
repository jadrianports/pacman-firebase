# Phase 1: Test Safety Net - Context

**Gathered:** 2026-06-11
**Status:** Ready for planning

<domain>
## Phase Boundary

A frame-perfect **safety net** exists that captures, replays, and visually verifies *today's*
ghost-AI + game-loop behavior — so any later change (Phase 2 refactor, Phase 3 box-fix) is provably
caught at the exact frame and ghost.

**Delivers:** a headless record/replay harness (steppable `tick()` extracted from `game.py` only,
SDL dummy drivers), golden-master traces of canonical playthroughs, micro per-ghost characterization
tests, cloud-function validator tests, and GitHub Actions CI — all green on push.

**Scope anchor (locked upstream — do NOT re-open here):**
- **No change to `ghost.py` AI logic.** Targeting (`get_targets`) and turn-preference ordering
  (`move_blinky/inky/pinky/clyde`) are THE SPEC. The only sanctioned behavior change in the whole
  milestone is Phase 3's `GHOST_BOX_BOUNDS` unification — NOT this phase.
- `tick()` extraction is a **behavior-preserving change to `game.py` only**, validated against a
  baseline trace captured from the *existing* `run()` loop first (resolves the chicken-and-egg).
- Refactor (Phase 2) and bug-fix (Phase 3) are later phases. This phase only builds the net.
</domain>

<decisions>
## Implementation Decisions

### Golden-master scenario coverage
- **D-01:** Canonical set = **targeted short scripts + one long Claude-played session** (not just one
  or the other). Short scripts isolate a behavior so a failure points at it; the long session catches
  interactions nobody thought to script.
- **D-02:** Targeted scripts = the design spec's 5 (**box-exit, power-pellet chase, ghost-eat, death,
  win**) **plus three extra**, chosen because Phase 2/3 stress them: **ghost-at-box-edge approaches**
  (Phase 3 BUG-01 changes exactly these frames), **tunnel wrap-around** (Phase 2 touches wrap math),
  and **dead-ghost return-to-box / "eyes"** (uses the `move_clyde` fallback Phase 2 collapses). The
  long session is expected to also exercise these organically.

### Trace format & strictness
- **D-03:** Per-frame snapshot records the design spec's **observable** fields
  (`frame`, `pacman{x,y,dir}`, `ghosts[{name,x,y,dir,dead,box}]`, `score`, `lives`, `powerup`,
  `dots_remaining`, `game_over`, `game_won`) **plus each ghost's current `target` tuple**. Rationale:
  Phase 2 explicitly refactors targeting/geometry, so recording `target` catches targeting drift even
  when pixels happen to coincide. `target` is a deliberate behavior output, not churny internals.
- **D-04:** Do **not** capture maximal internal state (box-exit timer counters, powerup countdown,
  `eat_freeze`/`starting`/`dying`/`flicker`/`counter`) — that would couple the trace to internals the
  refactor may legitimately reshape, producing false positives.
- **D-05:** Comparison is **exact**. Note (verified): all positions/speeds are **integers**
  (`PLAYER_SPEED=2`, ghost speeds ∈ {1,2,4}, integer start coords, `x_pos += speed`) → every trace
  value is an exact integer, so traces are effectively **platform-independent** and need no float
  rounding policy.

### Golden artifacts & re-bless
- **D-06:** **Commit only the JSONL golden traces + the input sequences** that reproduce them. **All
  PNG frames / montages / GIFs are gitignored and regenerated on demand** (deterministically derivable
  from committed input → build scratch, not source). Keeps the repo lean; CI diffs text only.
- **D-07:** **Re-bless** via a `pytest --bless` flag (or small script) that regenerates traces AND
  prints a **human-readable diff** (which scenarios / frames / fields changed) for review before the
  change is committed. This naturally proves Phase 3's "isolated to box edges": anything that moved
  outside the box shows up in the diff. (Did NOT pick machine-enforced scope-fail — diff review is
  enough; revisit only if Phase 3 wants the stronger guardrail.)

### CI environment, triggers & gate
- **D-08:** **Linux-only** (`ubuntu-latest`) with **pinned Python + pygame versions**, and that pinned
  env is the **canonical environment goldens are blessed in** — so dev and CI always agree and traces
  never drift between machines. (Bless through the pinned env, not a bare Windows shell.)
- **D-09:** CI runs on **push to any branch + PRs to `main`**, and **green is a required check**
  (branch protection on `main`) — a brick cannot reach `main`. GitHub remote confirmed to exist
  (`github.com/jadrianports/pacman-firebase`).

### Claude playtest (HRN-04 vs deterministic CI)
- **D-10:** Resolve the non-determinism tension by **splitting capture from hunt**: record ONE
  Claude-played session's per-frame inputs and commit it as a **deterministic, CI-replayable golden
  scenario**. The **live observe→decide→act adversarial bug-hunt stays a MANUAL phase-verification
  gate** (run at verification / before merge) — it needs Claude in the loop and can't be
  deterministic-green. Its pass is attested in the phase verification artifact, not a committed file.

### Adversarial invariants & determinism guard
- **D-11:** The adversarial checks become **standing per-frame invariants asserted on EVERY scenario
  replay in CI**: `score ∈ [0, MAX_SCORE=500000]`; Pac-Man center never inside a wall tile (no
  wall-clip); **no soft-lock** — position must change within N frames while `moving` and **NOT** in a
  known pause phase (`eat_freeze`/`starting`/`dying`). Catches a "self-consistent but bricked" trace
  the diff alone wouldn't flag.
- **D-12:** Add a **determinism guard test** that **hard-fails CI** if `random`/`randint`/`shuffle`/
  `time.time`/`get_ticks`/`datetime` appears in `game.py`/`ghost.py`/`player.py` — protects the
  foundational property the whole net depends on.

### Micro per-ghost characterization tests (TST-02)
- **D-13:** **Hand-curate decisive board states per ghost** (multi-way intersection, tunnel mouth,
  box edge, flee-vs-chase), **informed by states the long golden session actually visits**, and assert
  the exact turn each `move_*` makes — so a failure names the exact ghost + situation. (Not
  auto-sampled from traces — that overlaps the golden diff and gives a less self-explanatory failure.)
- **D-14:** Construct `Ghost` **headlessly against the SDL-dummy surface** (the `__init__`
  draw/`check_collisions` side-effect, concern C1, is harmless under `SDL_VIDEODRIVER=dummy`) — no
  change to `ghost.py`.

### Cloud-function validator tests (TST-03)
- **D-15:** **Mock `firebase-admin`** — patch `firebase_admin.initialize_app` / `firestore.client`
  **in a `conftest.py` before import** (resolves the import-time-init, concern C2). Test the
  validators via the HTTP entrypoint (bad initials→400, `score>MAX_SCORE`→400, non-int→400, missing
  `machine_id`→400) and the `is_new_best` upsert decision against a **mocked transaction/doc**. No
  source refactor, no Firestore emulator (no Java) — matches the existing patch-the-I/O test style.
- **D-16:** Write tests against the **current working-tree** `cloud_functions/*/main.py` (they have
  uncommitted modifications — those are the code that ships).

### Harness execution
- **D-17:** `timer.tick(FPS)` stays **only in the interactive `run()` path**; the record/replay
  harness steps `tick()` in a **tight, uncapped loop** for a fast suite, and `tick()` must **not read
  the throttle's return value** (stays sleep-independent).
- **D-18:** Scripted **input format = sparse `{frame, key}` event JSONL** beside each golden trace;
  recorded Claude/long sessions serialize to the **same format**; injection via **`pygame.event.post`**
  (the real input path — exercises `handle_events`).
- **D-19:** Each scenario/session runs **to a natural terminal state** (`game_won`, or `game_over`
  after all lives) **bounded by a generous safety frame cap** that doubles as a soft-lock backstop
  (fails loudly instead of hanging CI).

### Dev/harness dependencies
- **D-20:** Test/harness deps live in a **new pinned `requirements-dev.txt`** (matches the existing
  flat `requirements.txt` style; CI installs it). Use **pygame's own `image.save` for PNG frames +
  surface-blitting for montages (zero new dep)**; add **Pillow only for GIF assembly**. All dev-only —
  none enter the shipped `.exe`, so the "avoid new client runtime deps" constraint does not apply.
  (Did NOT introduce `pyproject.toml` — leave dependency-pinning hygiene to Phase 3's HYG-01.)

### Claude's Discretion
The user explicitly left these planner-level mechanics to Claude — settle them during
research/planning without re-asking:
- Golden-artifact **directory layout** (e.g., `tests/golden/<scenario>/{input.jsonl, trace.jsonl}`)
  and the **scenario manifest/registry** format CI iterates over.
- `conftest.py` **`sys.path` / import handling** (repo-root import-by-top-level-name; no config files
  exist today) and the firebase-admin pre-import patch wiring.
- **Scenario naming conventions** and the exact soft-lock frame threshold `N` (tuned to avoid
  false positives on legitimate pauses).
- Exact pinned versions for Python and pygame in CI / `requirements-dev.txt`.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone design & requirements (read first)
- `docs/superpowers/specs/2026-06-02-solid-foundation-design.md` — **the** design contract: the
  deterministic-game insight, the test-harness architecture (headless, `tick()`, trace format,
  frame/montage/GIF capture, play-loop), the Cardinal Rule, "maximum paranoia" verification, and the
  Phase A (Harness) + Phase B (Golden master) build sequence this phase implements. **MUST read.**
- `.planning/ROADMAP.md` §"Phase 1: Test Safety Net" — the 5 success criteria, the Cardinal Rule
  (net→refactor→fix, never reorder), and the Non-Goal (don't change ghost-AI decision behavior).
- `.planning/REQUIREMENTS.md` — definitions of **HRN-01..04** (harness) and **TST-01..04** (tests)
  this phase satisfies.

### Codebase maps (existing system)
- `.planning/codebase/ARCHITECTURE.md` — state machine, `Game.run()` loop, the "ghosts recreated
  every frame" pattern, `create_ghosts()`, score/leaderboard data flow, backend architecture.
- `.planning/codebase/TESTING.md` — current test layout/patterns (the patch-the-I/O style to mirror),
  coverage map, and the explicit gaps this phase fills.
- `.planning/codebase/CONCERNS.md` — C1 (Ghost `__init__` rendering side-effect), C2 (import-time
  firebase init), D3 (the two box-bound definitions — Phase 3), P1 (no CI), P2 (unpinned deps).
- `.planning/codebase/CONVENTIONS.md` — naming/style conventions new test + harness code should match.

### Code touch-points (verified during scout)
- `game.py` — `Game.run()` is the loop to extract `tick()` from (behavior-preserving, this file only);
  `get_targets()` produces the per-ghost `target` tuples recorded in the trace; `update_ghost_speeds()`
  sets speeds ∈ {1,2,4}.
- `ghost.py` — `check_collisions` + `move_blinky/inky/pinky/clyde` are the micro-test targets
  (read-only this phase; **do not modify**).
- `settings.py` — `MAX_SCORE=500000`, `FPS=60`, `PLAYER_SPEED=2`, `BOX_EXIT_DELAY_*`, `MENU_OPTIONS`.
- `cloud_functions/submit_score/main.py` + `cloud_functions/get_leaderboard/main.py` — TST-03 targets;
  test the **working-tree** versions (uncommitted mods).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`tests/test_api_service.py` + `tests/test_local_storage.py`** establish the house test style to
  copy: patch external I/O (`patch("api_service.urlopen", ...)`), a `_mock_response` context-manager
  helper, and `tmp_path`/`monkeypatch` fixtures. The cloud-function tests (D-15) mirror this by
  patching `firebase-admin` instead of `urlopen`.
- **Determinism is already a property of the code** — no `random`, no wall-clock, fixed-timestep
  frame counters, integer pixel math. The harness exploits this; the determinism guard (D-12) locks
  it in.
- **`get_targets()`** already computes the `target` tuples the trace records (D-03) — no new logic to
  expose them.

### Established Patterns
- **Ghosts recreated every frame** from state on the `Game` object (`create_ghosts()` rebuilds 4
  `Ghost`s); `Ghost.__init__` has draw + `check_collisions` side-effects (C1) → headless construction
  works under SDL dummy (D-14) with no `ghost.py` change.
- **No `pytest.ini`/`pyproject.toml`/`conftest.py` today**; pytest runs from repo root with
  import-by-top-level-name. The new `conftest.py` (D-15) is the first config file and handles the
  firebase-admin pre-import patch.
- **Flat `requirements.txt`** (unpinned `pygame`, `pyinstaller`) → `requirements-dev.txt` (D-20)
  follows the same flat-but-pinned shape; full client-dep pinning is Phase 3 (HYG-01).

### Integration Points
- **`tick()`** extracted from `Game.run()`'s while-body (game.py only) is the seam the harness drives;
  inputs injected via `pygame.event.post` upstream of `handle_events`.
- **GitHub Actions** workflow is new (`.github/workflows/` absent today); runs `pytest` headless on
  `ubuntu-latest` with `SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy`.
- **Box-bound constants** (`game.py:get_targets` `340<x<560 & 340<y<500` vs `ghost.py:check_collisions`
  `350<x<550 & 360<y<480`) are recorded by the net now so Phase 3's unification is provably isolated —
  not touched this phase.

</code_context>

<specifics>
## Specific Ideas

- "Maximum paranoia" is the explicit bar: the user repeatedly chose the more thorough option (all
  targeted scripts + long session, standing invariants, determinism guard, required-to-merge CI).
  Downstream planning should bias toward completeness over minimalism for this phase.
- The re-bless diff (D-07) and the box-edge targeted script (D-02) are deliberately built **now** to
  serve Phase 3's "isolated to the box region" proof — plan them with that downstream use in mind.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. (The refactor, box-bug fix, and hygiene items are
already scoped to Phases 2 and 3 in the roadmap; arcade-accuracy and leaderboard hardening are parked
for later milestones.)

</deferred>

---

*Phase: 1-Test Safety Net*
*Context gathered: 2026-06-11*
