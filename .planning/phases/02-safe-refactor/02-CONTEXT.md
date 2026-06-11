# Phase 2: Safe Refactor - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Clean up the two highest-debt areas of the gameplay code **behind the Phase 1 net**, with
**mathematical + visual proof the hand-tuned ghost AI is byte-for-byte unchanged**:

- **REF-01** — Centralize tile/board geometry and remove inline magic numbers.
- **REF-02** — Collapse the 4× ghost-movement duplication into one data-driven turn-priority table.

**Scope anchors (locked upstream — do NOT re-open here):**
- **Byte-for-byte identical ghost AI.** Targeting (`get_targets`) and turn-preference ordering
  (`move_blinky/inky/pinky/clyde`) are THE SPEC. Green golden traces = mathematically unchanged.
  The refactor is only safe *behind the passing net* (Cardinal Rule: net → refactor → fix).
- **The two inconsistent box-region rectangles stay as TWO separate named constants this phase.**
  Unifying them into a single `GHOST_BOX_BOUNDS` is the one sanctioned behavior change — **Phase 3
  (BUG-01), not now** (ROADMAP SC#1).
- **No new gameplay, no arcade-accuracy, no behavior tweaks.** Arcade-accurate ghost mode is parked
  for the future More Fun milestone as an opt-in toggle.
- Hygiene (deps, untrack `settings.local.json`, dead assets) and pre-existing doc drift are **Phase 3**
  (HYG-01..04). The single doc exception folded into Phase 2 is the *new* drift this refactor creates
  (see D-17).
</domain>

<decisions>
## Implementation Decisions

### Mover refactor (REF-02)
- **D-01:** Represent the unified mover as **per-ghost priority data + thin per-ghost hooks** for the
  structural quirks. The turn-priority orderings become data (the "table" the roadmap asks for); the
  oddities that are NOT pure ordering stay as small, named, documented per-ghost code branches. One
  unified mover, ~90% of the duplication collapsed. (Did NOT pick "everything as data + behavior
  flags" — modeling every quirk in a schema is higher-risk than keeping weird logic as obvious code.)
- **D-02:** Keep `move_blinky` / `move_inky` / `move_pinky` / `move_clyde` as **thin delegating
  wrappers** that call the unified mover with that ghost's profile. → `game.py:move_ghosts` dispatch
  stays byte-identical AND the Phase 1 net's 9 micro-tests (which assert on those names directly) are
  **untouched** — we don't disturb the measuring instrument while proving nothing changed.
  **Locked constraint:** the clyde profile *is* the dead/in-box fallback mover; `game.py:move_ghosts`
  calls `.move_clyde()` on any ghost (blinky/inky/pinky) when dead or in-box, so every ghost must be
  able to reach the clyde profile.
- **D-03:** The four per-ghost **movement profiles live as module-level data at the top of
  `ghost.py`**, next to the unified mover that consumes them. The original personality comments
  ("blinky turns on collision", "pinky turns when advantageous", etc.) become per-profile docstrings.
  (Not `settings.py` — those are behavioral tables, not flat config. Not a new module — `ghost.py`
  shrinks dramatically anyway and behavioral data stays colocated with behavioral code.)

### Equivalence proof (the "maximum paranoia" verification strategy)
The Phase 1 net catches drift only on states the canonical scenarios actually *visit*. A refactor's
real risk is a transcription error in a decision state no scenario hits — so Phase 2 adds **exhaustive
differential proof** on top of the inherited net.
- **D-04:** Prove the mover refactor with a **differential oracle across the whole decision space** —
  keep the 4 original methods as a frozen oracle, prove the new unified mover byte-identical, then
  delete. (Not just targeted micro-tests; not net-only.)
- **D-05:** Enumerate the oracle **synthetically and exhaustively** — construct a ghost and set the
  inputs directly: `direction (4) × all 16 turns[] combos × target-sign per axis (3×3) × in_box/dead
  (2×2)`, across the real ghost speeds `{1,2,4}` and wrap-boundary x positions. Bypasses
  `check_collisions` to cover the mover's ENTIRE input space (safe over-coverage of even impossible
  states). If old == new here, they are provably the same function. (Not a realistic board-position
  grid — the golden traces already give realistic integration coverage.)
- **D-06:** **One-shot gate, then delete.** Both implementations coexist in one commit where the
  differential test is green (proof preserved in git history); then delete the 4 legacy methods AND
  the differential test. Total dedup; single source of truth; the golden traces + 15 micro tests carry
  forward as the permanent regression guard. (Not a permanent test-only oracle — a frozen copy of the
  code we're deleting would rot.)
- **D-07:** Build a **second differential oracle for `check_collisions`** (which REF-01 edits — it
  holds `num1/num2/num3` + a box-bound literal and feeds `turns[]`/`in_box` to the movers). Enumerate
  `board positions × direction × in_box/dead`, run OLD vs NEW, assert identical `(turns, in_box)`.
  Proves geometry centralization is behavior-preserving for turn-legality (the change most prone to an
  off-by-precedence slip) and locks the `in_box` flag Phase 3 later edits. Same one-shot-then-delete
  lifecycle as D-06. (The mover oracle uses *synthetic* `turns[]`, so it deliberately does NOT cover a
  `check_collisions` change — this closes that gap.)
- **D-08:** Add a **deterministic automated frame-identical (pixel-hash) check** for rendering. The
  golden state-trace records positions/score but NOT pixels; `draw_board` uses the same `num1/num2`
  math being centralized, so a geometry bug could shift rendering while the trace stays byte-identical.
  Assert rendered frames are byte-identical before/after via an image hash/diff. The deterministic
  counterpart to the mover oracle. (This is *in addition to* the roadmap-mandated Claude montage
  eyeballing — SC#3 — which still happens.)
- **D-09:** The frame-hash baseline is a **committed golden frame-hash manifest (TEXT)** for the golden
  scenarios, blessed in the **Linux pinned env** (Phase 1 D-08) so it's platform-stable; PNGs stay
  gitignored (Phase 1 D-06) and regenerate on demand. Re-bless via the same `--bless` flow. A
  permanent, cheap, text-only rendering guard. (Note: permanent here is fine because it's tiny text —
  unlike the mover legacy in D-06, which is a large code copy and so gets deleted.)
- **D-10:** Add a **mutation canary** that proves the verification has teeth *before* we trust it:
  deliberately perturb one mover branch (e.g. swap two `elif` rungs), confirm the differential oracle
  AND golden traces go RED, then revert. Closes the false-green / blind-or-miswired-harness failure
  mode that could otherwise silently undermine the whole phase. Run once; attested in the phase
  verification artifact.
- **D-11:** **Sequence the refactor as per-ghost atomic commits, each independently proven green:**
  centralize geometry first (prove `check_collisions` oracle + frame-hash green) → extract blinky's
  profile and prove `unified-mover(blinky) == legacy move_blinky` → commit green → inky → pinky →
  clyde. Any drift bisects to one ghost/step; never stack an unproven change on another. The
  differential oracle runs per-ghost as you go.

### Geometry centralization (REF-01)
- **D-12:** Derived **tile constants live in `settings.py`**, computed once
  (`TILE_HEIGHT`/`TILE_WIDTH`/`HALF_TILE` from `WIDTH`/`HEIGHT`), replacing the inline
  `num1=(HEIGHT-50)//32` (=28), `num2=WIDTH//30` (=30), `num3=15` recomputed in `game.py`, `ghost.py`,
  and `player.py`. Matches the existing "constants in settings.py" convention. (See D-16 — shared
  *helpers* go in a new `geometry.py`; the planner may co-locate the constants there instead if
  cleaner.)
- **D-13:** Extraction reaches **all semantic position literals**, not just tile math: `TILE_*`, the
  ghost-vs-player **wrap edges kept deliberately distinct** (ghost `-30`/`900`; player `900`/`-47` and
  `-50`/`897`), the **two box rectangles** as two distinct named constants (NOT unified — Phase 3), and
  the `get_targets` **scatter target points**. Leave pure draw-cosmetic literals (circle radii, `PI`
  fractions, line widths in `draw_board`) inline — they're rendering, not geometry. Naming the
  look-alike wrap/box literals explicitly **guards against a future accidental unification**.
  (Scatter-target edits are caught by the golden trace's recorded `target` field — Phase 1 D-03.)
- **D-14:** Represent each of the two box regions as a **structured value (tuple/namedtuple) + a shared
  `in_box(x, y, bounds)` predicate**. Collapses the ~9 repeated inline box checks (≈8 in `get_targets`
  + 1 in `check_collisions`); keeps two distinct bounds now; then **Phase 3 unifies by pointing both at
  ONE bounds constant** — a near-one-line change that keeps BUG-01's "isolated to the box region" proof
  clean. Sets up Phase 3 the way Phase 1 set up for Phase 2.

### Collision consolidation (concern D4 — the spec's OPTIONAL step)
- **D-15:** **Defer full Player/Ghost collision unification; share only the identical atomic helpers.**
  **Finding (verified in code):** `Player.check_position` and `Ghost.check_collisions` are *more
  divergent* than CONCERNS D4 implies — different control flow (ghost checks all four directions
  unconditionally; player checks only the reverse per current heading), different look-ahead offsets
  (`num1`/`num2` vs `num3`), gate-tile-9 + `in_box` only on the ghost, a different guard
  (`0 < cx//30 < 29` vs `cx//30 < 29`), and different wrap thresholds. A full unification would be a
  heavily *conditionalized* function possibly more complex than two clear methods, for marginal gain —
  and D4 is not a required Phase 2 requirement (only REF-01/REF-02 are). So share only the trivially
  identical pieces: the tile-coordinate conversion (`center // tile_dim`), the `< 3` walkability test,
  and the `in_box()` predicate.
- **D-16:** Those shared atomic helpers + the `in_box()` predicate live in a **small new `geometry.py`
  module**, imported by `game.py`/`ghost.py`/`player.py`. Keeps `settings.py` pure-constants and avoids
  a new `player → ghost` import. (Planner decides whether the D-12 tile constants co-locate into
  `geometry.py` or stay in `settings.py`.)

### Scope-edge & process
- **D-17:** **Fix the doc drift this refactor creates, in Phase 2.** Update `CLAUDE.md`'s "Ghost
  System" section (currently "each ghost has its own AI method …") to describe the unified data-driven
  mover + per-ghost profiles + thin wrappers, in the same phase that creates the change — so the active
  guidance doc is accurate at every commit. HYG-03 (Phase 3) remains for *pre-existing* drift
  (box-exit timing, "Change Initials"). Codebase maps (`.planning/codebase/*.md`, esp. CONCERNS D1/D2
  now resolved) refresh separately via `/gsd-map-codebase`, not hand-edited here.
- **D-18:** **Merge Phase 1 to `main` first, then start Phase 2 from `main`.** Phase 1 (the net + CI
  merge-gate) is independently valuable and already verified; ship it (`/gsd-ship`) so `main` gets the
  net, then the Phase 2 PR runs the net as a required check (Phase 1 D-09 branch protection). Matches
  the Cardinal Rule (land the foundation first) and STATE's "awaiting merge"; avoids a giant combined
  PR. (Process implication: Phase 1 ships before Phase 2 execution begins.)
- **D-19:** **Human end-of-phase gate = before/after GIF + green proof.** Reuse the Phase 1 GIF path
  (HRN-03) to produce a before/after canonical-playthrough GIF the human watches to viscerally confirm
  identical ghost behavior, alongside the green oracles/CI. Math gives certainty; the GIF gives the
  owner direct confidence in the precious AI. (`human_verify_mode = end-of-phase`.)

### Claude's Discretion
The user explicitly left these planner/researcher-level mechanics to Claude — settle during
research/planning without re-asking:
- Exact **profile data schema** (tuple vs dict shape; names of the per-ghost behavior-quirk flags/hooks)
  and how each method's ordering is transcribed into data.
- Exact **constant names** (`TILE_HEIGHT` etc.) and the **box-constant names** chosen to make Phase 3's
  unification cleanest; whether tile constants live in `settings.py` (D-12) or co-locate into
  `geometry.py` (D-16); whether to derive tile dims from named `BOARD_ROWS`/`BOARD_COLS`/`HUD_HEIGHT`.
- **Hash algorithm** for the frame-hash and the exact set of representative wrap-boundary positions /
  enumeration bounds for the synthetic oracles; **CI runtime budget** for the exhaustive tests.
- Whether the Phase 1 **live adversarial Claude playtest** (Phase 1 D-10, a manual gate) is re-run for
  Phase 2 — likely unnecessary since the differential proof makes behavior provably identical (a
  replay would just re-exercise known-good behavior); planner's call.
- **Plan decomposition** (how many plans; geometry plan vs per-ghost mover plans) consistent with the
  D-11 per-ghost atomic-commit sequence.
- Exact **test-tree layout** for the new oracles / frame-hash / canary (Phase 1 left directory layout
  to discretion).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone design & requirements (read first)
- `docs/superpowers/specs/2026-06-02-solid-foundation-design.md` — **the** design contract. Phase C
  (steps 8–10) is exactly this phase: step 8 = centralize geometry / kill magic numbers (preserve the
  two box constants), step 9 = data-driven ghost turn-priority table ("read the exact ordering out of
  each `move_*` and express it as data; same values, same order → same pixel"), step 10 = the
  *optional* collision unification (D4). Also the deterministic-game insight, the Cardinal Rule, and
  "maximum paranoia" verification. **MUST read.**
- `.planning/ROADMAP.md` §"Phase 2: Safe Refactor" — the 3 success criteria, the Cardinal Rule
  (net → byte-identical refactor → isolated fix, never reorder), and the Non-Goal (don't change
  ghost-AI decision behavior; box-bounds unification is Phase 3).
- `.planning/REQUIREMENTS.md` — definitions of **REF-01** and **REF-02** (the only required Phase 2
  requirements).

### Prior-phase decisions this phase depends on
- `.planning/phases/01-test-safety-net/01-CONTEXT.md` — the net Phase 2 refactors behind. Especially:
  D-03 (trace records each ghost's `target` tuple → catches targeting/geometry drift even when pixels
  coincide), D-05 (exact integer comparison), D-06 (commit traces + inputs; gitignore/regenerate
  PNGs/montages/GIFs), D-07 (`--bless` human-readable diff), D-08 (Linux pinned env is the canonical
  bless env), D-09 (CI required check + branch protection on `main`), D-12 (determinism guard),
  D-13/D-14 (micro-test states + headless `make_ghost` construction).

### Codebase maps (existing system)
- `.planning/codebase/ARCHITECTURE.md` — ghosts-recreated-every-frame, `create_ghosts`/`move_ghosts`
  dispatch, `Game` state-on-the-orchestrator, the `move_clyde`-as-fallback pattern.
- `.planning/codebase/CONCERNS.md` — D1 (4× mover duplication → REF-02), D2 (magic numbers → REF-01),
  D3 (the two box bounds — Phase 3), D4 (two parallel collision impls — deferred per D-15), C1 (Ghost
  `__init__` render side-effect, harmless headless).
- `.planning/codebase/CONVENTIONS.md` — naming/style new constants + code must match (direction key
  `0=R,1=L,2=U,3=D`; tile codes; `< 3` walkability idiom; "lift literals into settings.py").
- `.planning/codebase/TESTING.md` — house test style + the Phase 1 net layout the new oracles extend.

### Code touch-points (verified during scout)
- `ghost.py` — `move_blinky/inky/pinky/clyde` (`L117/256/362/484`, ~120 lines each) become thin
  wrappers over one data-driven mover (D-01/D-02/D-03); `check_collisions` (`L43-115`) holds
  `num1/num2/num3` + box literal `350<x<550 & 360<y<480` and gets the differential oracle (D-07).
- `game.py` — `move_ghosts` (`L344-362`) dispatch (clyde fallback) stays byte-identical; `draw_board`
  (`L130-161`), eat-dot tile math (`L196-219`), and `get_targets` box checks (`L240-296`, ~8 repeats)
  + scatter targets are geometry touch-points (D-13/D-14).
- `player.py` — `check_position` (`L39-87`, divergent from ghost per D-15), wrap (`L99-103`,
  `900`/`-47`/`-50`/`897`), tile math (`L41-43`).
- `settings.py` — home for `TILE_*` + position constants (D-12); currently `WIDTH=900`, `HEIGHT=950`,
  `FPS=60`, `PLAYER_SPEED=2`, ghost starts, `BOX_EXIT_DELAY_*`.
- `tests/test_ghost_micro.py` — 15 micro tests call `move_*` by name (the interface D-02 preserves) via
  `make_ghost`; `tests/test_golden_traces.py` — 9 goldens + mirrored tile math + bless flow.
- **New:** `geometry.py` (D-16) — shared helpers + `in_box()` predicate.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Phase 1 net is the proof engine.** `tests/test_ghost_micro.py`'s `make_ghost` helper already
  constructs ghosts headlessly in arbitrary states (direction/target/speed/dead/box) — the exact
  harness the synthetic-exhaustive differential oracles (D-05/D-07) need. The golden-trace `--bless`
  flow extends naturally to the frame-hash manifest (D-09). Frame/montage/GIF capture (HRN-03) already
  exists for the human GIF gate (D-19).
- **`get_targets` already emits the `target` tuples** recorded in the trace (Phase 1 D-03) — so any
  geometry edit to scatter targets is caught by the golden traces without new instrumentation.
- **Determinism is a code property** (no `random`/wall-clock; integer pixel math) — what makes the
  exhaustive oracles and frame-hash deterministic and reliable. The Phase 1 determinism guard (D-12)
  hard-fails if that property is ever broken.

### Established Patterns
- **The four `move_*` are ~90% identical** ladders differing in turn-priority ordering + a few
  structural quirks: (a) Blinky goes straight on a clear forward path while Clyde/Inky/Pinky seek the
  target even when forward is open; (b) `move_inky` dir-1 sets `self.direction = 3` WITHOUT moving that
  frame, whereas `move_pinky` dir-1 sets direction AND moves; (c) several branches use `if … if …
  else` (not `elif`) where the second test overrides the first. These quirks are why D-01 keeps them as
  explicit hooks rather than pure data.
- **`move_clyde` is reused as the dead/in-box fallback** for every ghost (`game.py:move_ghosts`) — the
  unified design must route any dead/in-box ghost through the clyde profile (D-02 constraint).
- **Tile math + box checks are duplicated** across `game.py`/`ghost.py`/`player.py` (D2); the box
  predicate alone repeats ~9×. Direction convention `0=R,1=L,2=U,3=D` and `< 3` walkability are
  project-wide.

### Integration Points
- The unified mover plugs into the **unchanged `game.py:move_ghosts` dispatch** via the four wrapper
  names (D-02). New `geometry.py` is imported by `game/ghost/player` (D-16). `settings.py` gains
  `TILE_*` + position constants (D-12).
- New tests (mover differential oracle, `check_collisions` differential oracle, frame-hash check +
  golden hash manifest, mutation canary) live in `tests/` and run in the **existing Phase 1 CI**
  (ubuntu pinned, headless), gated as a required check on the Phase 2 PR against `main` (D-18).

</code_context>

<specifics>
## Specific Ideas

- **"Maximum paranoia" is the explicit through-line** (continued from Phase 1). The user consistently
  chose the strongest proof: a differential oracle over the *whole* decision space (not just visited
  states), synthetic-exhaustive enumeration, a second oracle for `check_collisions`, a deterministic
  frame-hash for rendering, AND a mutation canary that proves the oracles themselves have teeth before
  trusting green. Downstream planning should bias toward completeness over minimalism for the
  verification work — but keep the *refactor itself* minimal (defer D4, leave draw-cosmetics inline).
- **Two refactors, two proof modalities, symmetric:** mover logic ⇒ differential oracle (state);
  geometry/rendering ⇒ frame-hash (pixels) + `check_collisions` oracle (logic). Both ride on the Phase
  1 golden+micro net.
- **Everything is sequenced to serve the NEXT phase** (the Phase 1 → 2 pattern repeats): the structured
  box value + `in_box()` predicate (D-14) is built now specifically so Phase 3's BUG-01 unification is
  a one-line change with a clean isolation proof.
- **Verified finding worth flagging to the planner:** the two collision implementations (D-15) are
  genuinely divergent, not "same logic + gate flag" — full unification was *declined* on inspection,
  not deferred for time.

</specifics>

<deferred>
## Deferred Ideas

- **Full `Player.check_position` / `Ghost.check_collisions` unification (concern D4).** Declined for
  Phase 2 after verifying the two are structurally divergent (different control flow, offsets, guards,
  wraps); only the identical atomic helpers are shared (D-15). A candidate for a future dedicated
  refactor/hygiene pass if it's ever worth the conditionalized complexity — not tied to a current
  roadmap phase.
- (Box-bounds unification, dependency pinning, untracking `settings.local.json`, dead-asset removal,
  and pre-existing doc drift are already scoped to **Phase 3** — not "deferred ideas," just not this
  phase.)

</deferred>

---

*Phase: 2-Safe Refactor*
*Context gathered: 2026-06-12*
