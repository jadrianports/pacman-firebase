# Phase 3: Box-Bug Fix + Hygiene - Context

**Gathered:** 2026-06-12
**Status:** Ready for planning

<domain>
## Phase Boundary

Land the **one sanctioned gameplay change** of the entire Solid-Foundation milestone — unify the two
divergent ghost-box rectangles into a single `GHOST_BOX_BOUNDS`, **provably isolated to the box
region** — then finish repo hygiene. All of it rides on the Phase 1 net + Phase 2 refactor.

**In scope (BUG-01, HYG-01..04):**
- **BUG-01** — Collapse `geometry.py`'s two box constants (`GHOST_BOX_BOUNDS_COLLISION`,
  `GHOST_BOX_BOUNDS_TARGET`) into a single `GHOST_BOX_BOUNDS`, used by both `game.py:get_targets` and
  `ghost.py:check_collisions`. Behavior change is intentional and confined to the box region.
- **HYG-01** — Pin client deps in `requirements.txt`.
- **HYG-02** — Untrack `.claude/settings.local.json`; reconcile `.gitignore`.
- **HYG-03** — Fix doc drift (`CLAUDE.md` box-exit timing; dead "Change Initials" docstring).
- **HYG-04** — Delete dead duplicate asset folders.

**Scope anchors (locked upstream — do NOT re-open):**
- **Non-Goal / Cardinal Rule.** Ghost-AI *decision* behavior (targeting math in `get_targets`,
  turn-preference ordering in the `move_*` profiles) is THE SPEC. The box-bounds unification is the
  **only** sanctioned behavior change in the whole milestone; everything else stays byte-identical.
  Never mix a must-NOT-change step with a must-change step.
- **No new gameplay, no arcade-accuracy, no behavior tweaks** beyond BUG-01. Arcade-accurate ghosts
  are parked for the future "More Fun" milestone as an opt-in toggle.
- Final phase of Milestone 1 (2 of 3 phases complete).

</domain>

<decisions>
## Implementation Decisions

### Box-bounds unification (BUG-01)
- **D-01:** **`GHOST_BOX_BOUNDS = (350, 550, 360, 480)` — the collision box wins.** The two existing
  rectangles are *concentric* (same center ≈(450, 420)); `GHOST_BOX_BOUNDS_TARGET (340,560,340,500)`
  is just `GHOST_BOX_BOUNDS_COLLISION (350,550,360,480)` inflated ~10px on each x-edge and ~20px on
  each y-edge (`TARGET ⊃ COLLISION`). Unify onto the **tighter** collision box because it already
  drives the *physical* `in_box` flag (turn legality, box-exit timing, dead-ghost revival); the looser
  targeting heuristic conforms to physics, not vice versa. This is the **smallest, most surgical**
  version of the sanctioned change. (Rejected: "measure the true pen" — more correct in the abstract
  but nudges BOTH subsystems and risks overriding intentional hand-tuning; "targeting box wins" —
  changes the higher-impact movement/exit subsystem, riskier.)
- **D-02 [Guardrail]:** The behavior delta is therefore confined to **`game.py:get_targets` only**.
  `ghost.py:check_collisions` keeps the value `(350,550,360,480)` — it is a **name-only change**
  (`GHOST_BOX_BOUNDS_COLLISION` → `GHOST_BOX_BOUNDS`), so the `in_box` movement/exit subsystem is
  byte-identical *by construction* and the **15 existing box micro-tests stay green and untouched**
  (don't disturb the measuring instrument). Mechanically: collapse the two `geometry.py` constants into
  one `GHOST_BOX_BOUNDS`, repoint both importers. (This is the "near-one-line change" Phase 2 D-14 set
  up.) Expected delta direction: in the ring between the old rectangles, an eaten/returning ghost
  switches from "aim at the gate (`SCATTER_EATEN_TARGET`)" to "chase the player" a touch sooner.

### Isolation proof / verification ("maximum paranoia" — BUG-01 SC#2)
- **D-03:** **Add a targeted `get_targets` differential oracle** (Phase 2 D-06/D-07 lineage). Freeze
  old `get_targets` (TARGET box) vs new (COLLISION box); enumerate **exhaustively** across ghost
  position × board × `dead`/`eaten`/`powerup` states; assert outputs differ **ONLY** for positions in
  the ring (in TARGET, not in COLLISION) and are **identical everywhere else**. Proves isolation across
  the *whole input space*, not just states the golden scenarios visit.
- **D-04:** **`check_collisions` belt-check** — the same oracle *also* asserts `check_collisions`
  output is byte-identical old-vs-new across the enumerated states, mechanically proving the
  name-only-rename claim (D-02). Makes the proof symmetric: `get_targets` changed-only-in-the-ring AND
  `check_collisions` provably-unchanged.
- **D-05:** **Teeth-check + one-shot-then-delete.** Before trusting green, perturb `get_targets`
  *outside* the ring and confirm the oracle goes RED (the D-10 mutation-canary discipline). Both
  oracle + belt-check are proven green in one commit, then **deleted** (D-06 lifecycle) — the
  re-blessed golden traces + 15 micro-tests carry forward as the permanent guard.
- **D-06:** **Roadmap proof is retained underneath the oracle:** golden-trace diff (per-frame `target`
  tuple is already recorded — Phase 1 D-03 — so box-edge diffs are directly visible) shows **only
  box-edge frames move**; **re-bless those frames in Linux CI** (D-08 authority — never bless on
  Windows; platform pixel/float differences); before/after **montages** Claude reads with its own
  vision; the rest of every trace verified untouched. The `box_edge`/`box_exit` golden scenarios were
  authored for exactly this.
- **D-07:** **Required Claude adversarial playtest** (HRN-04 / Phase 1 D-10) for the box change.
  A live observe→decide→act session hunting box-exit soft-locks, ghosts oscillating at the pen mouth,
  wall-clips near the box, and eaten-eyes targeting glitches. Phase 2 *skipped* the playtest (behavior
  was provably identical there); Phase 3 has a real intentional edge change, so emergent dynamics the
  oracle/traces don't model are newly possible — the playtest probes whether the new edge behavior
  actually plays right.
- **D-08:** **Human GIF gate retained** (Phase 2 D-19; `human_verify_mode = end-of-phase`) — a
  before/after canonical-playthrough GIF the owner watches to viscerally confirm the box change is what
  they intended (and nothing else moved).

### Sequencing & commits
- **D-09:** **Hygiene first, box fix isolated and LAST.** Land HYG-01..04 as **four behavior-neutral
  atomic commits** (deps / untrack+gitignore / docs / dead assets) — golden traces byte-identical and
  **CI green at every step** — THEN the box fix as the final, isolated commit (the **only** commit that
  touches/re-blesses golden traces and carries the oracle). Applies the milestone Cardinal Rule
  ("fix isolated and last") *inside* the phase: the PR diff reads "everything green and unchanged, then
  ONE commit that moves exactly the box-edge frames." **One Phase-3 PR, cleanly ordered commits**
  (`branching_strategy: none` → work on `main`, isolation via atomic commits, not a branch).

### Hygiene specifics
- **D-10 (HYG-01):** **Exact `==` pins** for `pygame` and `pyinstaller` in `requirements.txt`, set to
  the **CI-green versions** (pinning pyinstaller too keeps the `.exe` bundle reproducible). **Backend
  `cloud_functions` pins left untouched** (`3.*`/`6.*`) — HYG-01 scopes to *client* deps and the
  backend is a separate deploy surface. (Dev/test deps were already pinned in Phase 1.)
- **D-11 (HYG-02):** **Track `CLAUDE.md`** — remove its `.gitignore` line (currently line 26) and
  commit it, so the HYG-03 doc-drift fix is durable, version-controlled, and shared (it's the
  project-instructions doc, already edited in Phase 2 D-17). Baseline that happens regardless:
  `git rm --cached .claude/settings.local.json` and **dedupe the duplicate `/.claude`** line. The rest
  of `/.claude` stays ignored (local GSD tooling).
- **D-12 [Guardrail] (HYG-03):** Reconcile the `CLAUDE.md` "Ghost Box Exit" **prose** ("~2 sec / ~4
  sec") to match the constants `BOX_EXIT_DELAY_PINKY = 30` / `BOX_EXIT_DELAY_CLYDE = 60` frames @60fps
  (≈0.5 s / 1 s; Inky = 0 is already consistent). **Edit the doc, NOT the constants** — changing the
  delays would be a *second, unsanctioned* behavior change that moves golden traces. Also remove the
  dead `'Change Initials'` docstring reference from `menu.py:run_main_menu`
  (`MENU_OPTIONS = ["Play", "Leaderboard", "Quit"]`).
- **D-13 (HYG-04):** Delete `assets/ghost_images/` and `assets/player_images/` (verified byte-duplicate
  filenames of the live `assets/ghosts/` and `assets/pacman/`; the only reference anywhere is the
  design spec instructing their deletion). `build.py:8 --add-data=assets;assets` ships the whole folder,
  so deletion also slims the bundle.
- **D-14:** **Required `.exe` rebuild + smoke-run gate** for HYG-04. After asset deletion + the
  pyinstaller pin, run `python build.py`, launch `dist/pacman/pacman.exe`, and play a few frames to
  confirm the bundle still loads assets and runs. A **human end-of-phase step** — headless CI never
  builds the PyInstaller bundle, so a broken bundle / dropped asset / pyinstaller-pin regression would
  otherwise go undetected by the test suite.

### Claude's Discretion
Settle during research/planning without re-asking:
- Exact **oracle enumeration bounds** and player-position handling for the `get_targets` differential
  oracle (mirror Phase 2 D-05/D-07 synthetic-exhaustive construction + `make_ghost` headless harness).
- Exact **pinned version strings** (source via `pip freeze` from the known-good CI env).
- Whether to leave a one-line comment at the unified `GHOST_BOX_BOUNDS` noting the historical
  divergence, to guard against a future accidental re-split.
- **Plan decomposition** (e.g. one hygiene plan with ordered atomic commits + one box-fix plan, or a
  single plan with ordered tasks), consistent with D-09 hygiene-first/fix-last.
- Whether the `.exe` smoke-run (D-14) is a scripted headless launch-a-few-frames or a manual human
  launch; reuse the Phase 1 HRN-03 montage/GIF path for D-06/D-08.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone design & requirements (read first)
- `docs/superpowers/specs/2026-06-02-solid-foundation-design.md` — **the** design contract.
  **Phase D, step 11** = the box-bounds unification (confirms it's an *intentional, isolated* change
  and deliberately does **NOT** prescribe which rectangle wins — that's D-01 here). **Phase E, steps
  12–15** = the four hygiene items, fully prescribed. Also the Cardinal Rule, the Non-Goal, and the
  "maximum paranoia" 4-way verification bar. **MUST read.**
- `.planning/ROADMAP.md` §"Phase 3: Box-Bug Fix + Hygiene" — the 5 success criteria (incl. the exact
  conflicting bounds, the `PINKY=30`/`CLYDE=60` doc fix, the named asset folders), the Cardinal Rule,
  the Non-Goal, and the verification bar.
- `.planning/REQUIREMENTS.md` — definitions of **BUG-01** and **HYG-01..04** + traceability.

### Prior-phase decisions this phase depends on
- `.planning/phases/02-safe-refactor/02-CONTEXT.md` — **D-13/D-14** (the two named box constants +
  `in_box()` predicate were built *specifically* so this unification is a one-line change with a clean
  isolation proof), **D-06** (one-shot-then-delete oracle lifecycle), **D-10** (mutation-canary /
  teeth-check), **D-08/D-09** (Linux pinned env is the canonical `--bless` env; CI required check +
  branch protection on `main`), **D-19** (human before/after GIF gate).
- `.planning/phases/01-test-safety-net/01-CONTEXT.md` — the net Phase 3 verifies against: golden traces
  record each ghost's per-frame `target` tuple (D-03 → box-edge targeting diffs are directly visible),
  the `--bless` human-readable diff flow, the determinism guard, the `box_edge`/`box_exit` golden
  scenarios, HRN-03 frame/montage/GIF capture, and the HRN-04 Claude observe→decide→act play-loop
  (reused for D-07).

### Codebase maps
- `.planning/codebase/CONCERNS.md` — the exact Phase-3 catalog: **D3** (box bounds, both definitions),
  **P2** (unpinned client deps), **S3** (`settings.local.json` tracked despite ignore), **DOC1**
  (box-exit timing drift), **DOC2** ("Change Initials" docstring), **D6** (dead asset folders).
- `.planning/codebase/ARCHITECTURE.md` — ghost system, `get_targets`/`move_ghosts` dispatch, the
  `in_box` flow, ghosts-recreated-every-frame.
- `.planning/codebase/TESTING.md` — house test style + the Phase 1 net layout the new oracle extends.

### Code touch-points (verified during scout, 2026-06-12)
- `geometry.py:18-34` — `GHOST_BOX_BOUNDS_COLLISION = (350,550,360,480)`,
  `GHOST_BOX_BOUNDS_TARGET = (340,560,340,500)`, `in_box(x, y, bounds)`. **BUG-01 collapses these to one
  `GHOST_BOX_BOUNDS = (350,550,360,480)` and repoints both importers.**
- `game.py:18` (`import GHOST_BOX_BOUNDS_TARGET`) + `game.py:240-301` (`get_targets`, ~8
  `in_box(..., GHOST_BOX_BOUNDS_TARGET)` call sites) — **THE behavior-delta site.**
- `ghost.py:4` (`import GHOST_BOX_BOUNDS_COLLISION`) + `ghost.py:384` (`check_collisions` box test) —
  **name-only change, value unchanged.**
- `settings.py:56-58` — `BOX_EXIT_DELAY_INKY=0` / `PINKY=30` / `CLYDE=60` (HYG-03 reconciles the doc to
  these; **do NOT change them**).
- `CLAUDE.md` "Ghost Box Exit" section (prose "~2 sec / ~4 sec") — reconcile to ≈0.5 s / 1 s; **also
  un-ignore + track this file** (currently gitignored at `.gitignore:26` and untracked).
- `menu.py:run_main_menu` docstring — remove the dead `'Change Initials'` return value.
- `requirements.txt` — `pygame`, `pyinstaller` (unpinned) → exact `==` pins.
- `.gitignore:24-25` (duplicate `/.claude`), `:26` (`CLAUDE.md`, remove); `.claude/settings.local.json`
  (tracked → `git rm --cached`).
- `assets/ghost_images/`, `assets/player_images/` — delete (byte-dupes of `assets/ghosts/`,
  `assets/pacman/`); `build.py:8` `--add-data=assets;assets`.
- `tests/test_ghost_micro.py` — 15 micro tests pin `check_collisions`/`in_box` at the
  `350<x<550 & 360<y<480` box; **stay green untouched.** `tests/test_golden_traces.py` —
  `box_edge`/`box_exit` scenarios + `--bless` flow for the re-bless.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **The Phase 1/2 proof machinery is the engine.** `make_ghost` (headless ghost construction in
  arbitrary states) is exactly the harness the `get_targets` differential oracle (D-03) + belt-check
  (D-04) need. The `--bless` flow extends to re-blessing the box-edge frames (D-06). HRN-03
  frame/montage/GIF capture serves the montages (D-06) and human GIF (D-08). The HRN-04 play-loop is
  the required playtest (D-07).
- **`geometry.py` is pre-wired for this fix** (Phase 2 D-14): two named box constants + an `in_box()`
  predicate already factored out, so BUG-01 is a constant-collapse + repoint, not a logic rewrite.
- **Golden traces record the per-frame `target` tuple** (Phase 1 D-03) → the box-edge targeting delta
  is directly visible in the trace diff without new instrumentation.

### Established Patterns
- **One-shot-then-delete oracle + teeth-check** (Phase 2 D-06/D-10): coexist old+new in one green
  commit, prove via differential oracle, prove the oracle has teeth via a deliberate perturbation, then
  delete — the re-blessed golden net is the permanent guard.
- **Atomic, independently-green commits** (Phase 2 D-11 per-ghost discipline) → here: per-HYG-item
  commits + an isolated final box-fix commit.
- **Linux CI is the canonical bless/assert authority** (Phase 1/2 D-08); Windows is dev-only (the
  frame-hash manifest is a Windows placeholder per STATE).

### Integration Points
- Unified `GHOST_BOX_BOUNDS` plugs into the **unchanged** `in_box()` predicate, consumed by
  `game.py:get_targets` (value changes) and `ghost.py:check_collisions` (value unchanged).
- New oracle + belt-check live in `tests/`, run in the existing Phase 1 CI (ubuntu, pinned, headless),
  gated as the required check on the Phase-3 PR against `main`.
- `.exe` smoke-run (D-14) is a manual/Windows gate outside CI — the one verification CI structurally
  cannot perform.

</code_context>

<specifics>
## Specific Ideas

- **"Maximum paranoia" is the consistent through-line** (Phases 1→2→3). For the one sanctioned change
  the user chose the *strongest* proof on every axis: a differential oracle over the whole input space
  (D-03), a symmetric belt-check that the untouched side is provably untouched (D-04), a teeth-check
  before trusting green (D-05), the full roadmap trace/re-bless/montage proof (D-06), AND *both* human
  gates — a required adversarial playtest (D-07) and the before/after GIF (D-08) — plus a required
  `.exe` smoke-run (D-14) to cover the gap headless CI leaves.
- **Surgical-minimal on the change itself.** Picking the collision box (D-01) confines the delta to a
  single function and makes one whole subsystem byte-identical by construction — the smallest possible
  footprint for the milestone's only sanctioned behavior change.
- **Risk-isolation discipline carries into the commit structure** (D-09): behavior-neutral hygiene
  first and CI-green throughout, the behavior change isolated and last as the sole trace-touching
  commit — the Cardinal Rule applied at commit granularity.

</specifics>

<deferred>
## Deferred Ideas

- **Overlapping build definitions (CONCERNS D5)** — `build.py` vs the gitignored `pacman.spec` describe
  the same bundle. Low severity, **NOT in Phase 3 scope** (not a BUG/HYG requirement). Candidate for a
  future hygiene pass.
- **Backend dependency pinning** (`cloud_functions` `3.*`/`6.*` → exact) — explicitly left out of
  HYG-01 (client-only). A natural item for the future "More Competitive" milestone when the backend is
  hardened (alongside COMP-01 anti-cheat).

(Leaderboard anti-cheat S1, full collision unification D4, `Ghost.__init__` side-effects C1, broad
`except` C3 are already routed to future milestones or were declined in Phase 2 — not raised here.
Discussion stayed within phase scope; no user scope-creep to redirect.)

</deferred>

---

*Phase: 3-Box-Bug Fix + Hygiene*
*Context gathered: 2026-06-12*
