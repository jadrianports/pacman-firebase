# Phase 2: Safe Refactor - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 2-Safe Refactor
**Areas discussed:** Mover abstraction, Proof depth, Geometry home, Collision DRY, Doc drift, Branch & merge, Human gate

---

## Mover abstraction (REF-02)

**Q1 — How to represent the four methods' non-priority quirks in one unified mover?**

| Option | Description | Selected |
|--------|-------------|----------|
| Priorities as data + thin per-ghost hooks | Orderings as data; structural quirks as small named code branches | ✓ |
| Everything as data (priorities + behavior flags) | Each ghost one data record incl. quirk flags; single code path | |
| You decide after a line-by-line diff | Researcher diffs all four first, then picks | |

**Q2 — Public interface, given game.py dispatch + 9 micro-tests call the four names?**

| Option | Description | Selected |
|--------|-------------|----------|
| Keep four names as thin delegating wrappers | game.py dispatch byte-identical, net's micro-tests untouched | ✓ |
| Collapse to a single `move()` method | Purest collapse, but rewrite dispatch + 9 micro-tests | |
| You decide during planning | Discretion once couplings mapped | |

**Q3 — Where do the per-ghost movement profiles live?**

| Option | Description | Selected |
|--------|-------------|----------|
| In ghost.py, as module-level profile data | Colocated with the mover; comments → docstrings | ✓ |
| In settings.py with other constants | Follows convention but bloats flat config with behavioral tables | |
| A new dedicated module (ghost_profiles.py) | Cleanest separation; new file + import, splits ghost behavior | |

**Notes:** Locked constraint surfaced — the clyde profile is the dead/in-box fallback (game.py:move_ghosts calls `.move_clyde()` on any ghost), so every ghost must reach it.

---

## Proof depth

**Q1 — How much extra equivalence proof beyond the Phase 1 net?**

| Option | Description | Selected |
|--------|-------------|----------|
| Differential oracle across the whole decision space | Keep old methods as oracle, prove byte-identical, then delete | ✓ |
| Targeted micro-tests for the known quirks only | Pin the flagged quirks; far less tooling | |
| Rely on the existing Phase 1 net as-is | Trust goldens + micro + montages | |

**Q2 — How should the differential oracle enumerate the decision space?**

| Option | Description | Selected |
|--------|-------------|----------|
| Synthetic exhaustive — set inputs directly | Full cross-product; proves same function | ✓ |
| Realistic — drive real check_collisions over a grid | Board-produced states only; more expensive | |
| Both | Synthetic + realistic; largely redundant | |

**Q3 — Lifecycle of the legacy methods + differential test?**

| Option | Description | Selected |
|--------|-------------|----------|
| One-shot gate, then delete legacy + differential test | Proof in git history; total dedup | ✓ |
| Permanent test-only oracle in CI | Frozen snapshot in tests/; permanent guard but can rot | |
| You decide during planning | Discretion once harness built | |

**Q4 — Add a deterministic automated rendering check (geometry)?**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — automated frame-identical (pixel-hash) check | Deterministic counterpart to the mover oracle | ✓ |
| No — Claude's montage eyeballing is enough | Leaner; trusts vision | |
| You decide during planning | Discretion | |

**Q5 — Also cover check_collisions with a differential oracle (REF-01)?**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — differential check_collisions over the board grid | Locks turn-legality + the in_box flag Phase 3 edits | ✓ |
| No — golden traces + frame-hash cover it | Risk: unvisited-position turn-legality drift | |
| You decide during planning | Discretion | |

**Q6 — How is the frame-hash 'before' baseline captured/stored?**

| Option | Description | Selected |
|--------|-------------|----------|
| Committed golden frame-hash manifest, blessed in pinned env | Tiny text, permanent rendering guard | ✓ |
| Ephemeral old-vs-new comparison in one CI job | No committed hashes; more CI plumbing | |
| You decide during planning | Discretion | |

**Q7 — Prove the verification itself has teeth (mutation/canary)?**

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — mutation canary proves oracles go RED | Closes the false-green / blind-harness failure mode | ✓ |
| No — the exhaustive oracles are self-evidently sensitive | Skips the wiring check | |
| You decide during planning | Discretion | |

**Q8 — Sequence the refactor for verification?**

| Option | Description | Selected |
|--------|-------------|----------|
| Per-ghost atomic commits, each proven green before the next | Drift bisects to one ghost/step | ✓ |
| Land the full refactor, then verify once at the end | Fewer commits; lost bisection on failure | |
| You decide during planning | Discretion | |

**Notes:** User chose "more questions" repeatedly here — verification is the paranoia core; eight decisions captured before moving on.

---

## Geometry home (REF-01)

**Q1 — Where does the centralized tile/board geometry live?**

| Option | Description | Selected |
|--------|-------------|----------|
| In settings.py, derived once as named constants | Matches convention; smallest structural change | ✓ |
| A new dedicated geometry module (geometry.py) | Cleanest; attractive if Collision DRY consolidates | (partial — see D-16) |
| You decide during planning | Discretion | |

**Q2 — How far does literal-extraction reach?**

| Option | Description | Selected |
|--------|-------------|----------|
| Tile math + all semantic position literals | TILE_*, distinct wrap edges, box rectangles, scatter targets; draw-cosmetics inline | ✓ |
| Tile math + box bounds only; defer the rest | Smaller; partial REF-01 | |
| You decide during planning | Discretion | |

**Q3 — How are the two box regions represented?**

| Option | Description | Selected |
|--------|-------------|----------|
| Structured box value + a shared in_box() predicate | Collapses ~9 checks; sets up Phase 3's one-line unification | ✓ |
| Named scalar bounds, comparisons left inline | Simpler now; Phase 3 touches every site | |
| You decide during planning | Discretion | |

---

## Collision DRY (concern D4)

**Q1 — How much collision consolidation, given the two impls are structurally divergent?**

| Option | Description | Selected |
|--------|-------------|----------|
| Defer full unification; share only identical atomic helpers | Tile-coord conversion, walkability, in_box predicate | ✓ |
| Fold in full unification now (one shared fn + gate flag) | Provable-safe but heavily conditionalized; adds scope | |
| Defer entirely — leave both methods as-is beyond geometry naming | Smallest; atomic duplication remains | |

**Q2 — Where do the shared atomic helpers + in_box() live?**

| Option | Description | Selected |
|--------|-------------|----------|
| A small shared module (geometry.py) | Keeps settings.py pure; no player→ghost import | ✓ |
| Keep helpers in ghost.py, import into player/game | No new file; awkward player→ghost coupling | |
| You decide during planning | Discretion | |

**Notes:** Finding shared with the user — the two collision methods are *more* divergent than CONCERNS D4 implies (different control flow, num1/num2 vs num3 offsets, gate+in_box ghost-only, different guard/wrap). Full unification was declined on inspection, not deferred for time.

---

## Doc drift (this refactor creates)

**Q1 — Fix CLAUDE.md 'Ghost System' drift in Phase 2 or defer to Phase 3 (HYG-03)?**

| Option | Description | Selected |
|--------|-------------|----------|
| Fix in Phase 2 — update CLAUDE.md with the refactor | Active guidance doc accurate at every commit | ✓ |
| Defer to Phase 3 hygiene (HYG-03) | Batches doc fixes; window of stale docs | |
| You decide during planning | Discretion | |

---

## Branch & merge

**Q1 — Sequence branch/merge, given Phase 1 is verified but unmerged?**

| Option | Description | Selected |
|--------|-------------|----------|
| Merge Phase 1 to main first, then Phase 2 from main | Land the foundation; Phase 2 PR gated by the net; avoids combined PR | ✓ |
| Stack Phase 2 on the current Phase 1 branch | Fastest now; one large combined PR | |
| New Phase 2 branch off the Phase 1 branch | Distinct PRs but a dependency chain | |

---

## Human gate

**Q1 — What does the human review at the end-of-phase gate?**

| Option | Description | Selected |
|--------|-------------|----------|
| Before/after GIF of a canonical playthrough + green proof | Reuses HRN-03 GIF; visceral confidence in the precious AI | ✓ |
| Trust the green oracles + CI (no visual gate) | Leanest; relies fully on the proof | |
| Montages (the same Claude eyeballs) + green proof | Static stills + green CI | |

---

## Claude's Discretion

- Exact profile data schema (tuple/dict shape, quirk-flag/hook names) and how each method's ordering is transcribed.
- Exact constant names; whether tile constants live in settings.py or co-locate into geometry.py; optional BOARD_ROWS/COLS/HUD_HEIGHT derivation.
- Hash algorithm + representative wrap-boundary positions / enumeration bounds for the synthetic oracles; CI runtime budget.
- Whether the Phase 1 live adversarial Claude playtest is re-run for Phase 2 (likely unnecessary given the math proof).
- Plan decomposition consistent with the per-ghost atomic-commit sequence; test-tree layout for the new oracles/frame-hash/canary.

## Deferred Ideas

- Full `Player.check_position` / `Ghost.check_collisions` unification (concern D4) — declined for Phase 2 (the two are genuinely divergent); candidate for a future dedicated refactor pass, not a current roadmap phase.
