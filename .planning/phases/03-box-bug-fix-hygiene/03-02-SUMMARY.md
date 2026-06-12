---
phase: 03-box-bug-fix-hygiene
plan: 02
subsystem: testing
tags: [ghost-ai, geometry, golden-traces, differential-oracle, bug-fix]

# Dependency graph
requires:
  - phase: 01-test-safety-net
    provides: golden-master traces, micro per-ghost tests, headless harness, montage/GIF capture, Claude play-loop
  - phase: 02-safe-refactor
    provides: centralized geometry.py with the two box constants (GHOST_BOX_BOUNDS_TARGET / _COLLISION) kept distinct for this fix to unify
provides:
  - "Unified GHOST_BOX_BOUNDS = (350, 550, 360, 480) consumed by both get_targets and check_collisions"
  - "BUG-01 — the milestone's one sanctioned behavior change — landed proven-isolated to the box ring"
  - "Differential oracle methodology proving get_targets delta is ring-only and check_collisions byte-identical (transient, deleted)"
affects: [future-milestones, any phase touching ghost targeting or the ghost box]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Differential oracle + belt-check + teeth-check then one-shot-delete (Phase-2 lineage) for proving a constant-collapse is ring-only"
    - "Oracle proof as platform-independent isolation evidence when golden re-bless must be deferred to Linux CI"

key-files:
  created: []
  modified:
    - geometry.py
    - game.py
    - ghost.py
    - tests/golden/box_edge/trace.jsonl
    - tests/golden/box_exit/trace.jsonl

key-decisions:
  - "BUG-01: unify the two ghost-box constants onto the COLLISION value (350,550,360,480); collision box wins (D-01); get_targets is the only value change (D-02), check_collisions byte-identical by construction"
  - "ALL 9 golden traces diverge (not just box_edge/box_exit as D-06 assumed) — every one rooted at the SAME single in-ring inky flip at frame 340, (400,358); deterministic replay amplifies one legitimate ring decision across all scenarios"
  - "Golden re-bless deferred to Linux CI of ALL 9 traces (never on Windows — float drift would corrupt masters); oracle proof stands as authoritative platform-independent isolation evidence in the interim"

patterns-established:
  - "Oracle-as-proof: when re-bless must wait for Linux CI, the differential oracle (ring-only diff + byte-identical belt-check) is the authoritative isolation evidence; golden traces are corroborating, not primary"

requirements-completed: [BUG-01]

# Metrics
duration: ~2h (across original execution + checkpoint pause + finalize)
completed: 2026-06-12
---

# Phase 3 Plan 02: BUG-01 Unify Ghost-Box Bounds Summary

**Collapsed geometry.py's two inconsistent ghost-box rectangles into a single `GHOST_BOX_BOUNDS = (350, 550, 360, 480)`, shifting `get_targets` onto the tighter box (the milestone's one sanctioned behavior change) while `check_collisions` stays byte-identical — proven ring-only by a differential oracle, teeth-checked, then deleted.**

## Performance

- **Duration:** ~2h (original execution + human-verify checkpoint pause + finalize)
- **Completed:** 2026-06-12
- **Tasks:** 3 (Task 1 oracle, Task 2 unify+repoint+delete, Task 3 playtest + human GIF gate)
- **Files modified:** 5 (geometry.py, game.py, ghost.py, 2 golden trace.jsonl)

## Accomplishments
- Unified `GHOST_BOX_BOUNDS = (350, 550, 360, 480)` in geometry.py — both old constants (`GHOST_BOX_BOUNDS_TARGET`, `GHOST_BOX_BOUNDS_COLLISION`) removed; module docstring reconciled (the "Do NOT merge these" / D-15-landmine prose is gone, replaced by single-constant prose + historical-divergence guard comment).
- Repointed both importers: `game.py:get_targets` (import + 8 call sites = 9 refs) now uses `GHOST_BOX_BOUNDS` (THE behavior-delta site — D-02); `ghost.py:384` `check_collisions` renamed onto `GHOST_BOX_BOUNDS` (value unchanged → byte-identical by construction).
- Built, ran, and proved a transient differential oracle (get_targets ring-only-diff), belt-check (check_collisions byte-identical), and teeth-check (out-of-ring perturbation → RED → revert → green), then deleted it in the same commit as the fix — re-blessed traces + 15 micro-tests are the permanent guard.
- 15 micro per-ghost tests stayed GREEN untouched; settings.py box-exit constants UNCHANGED.
- Claude adversarial playtest (HRN-04) near the box: clean (no soft-lock / pen-mouth oscillation / wall-clip / eaten-eyes glitch), vision-reviewed both before/after montages.
- Human before/after GIF gate (D-08): APPROVED — the human confirmed nothing is broken or glitchy (the change is so surgical the playthroughs look essentially identical, which is the expected/correct outcome).

## Task Commits

1. **Task 1: differential oracle + belt-check + teeth-check** — `a40ce4c` (test)
2. **Task 2: unify GHOST_BOX_BOUNDS + repoint both importers + teeth-check then delete oracle (BUG-01)** — `f45a712` (fix) — the SINGLE trace-touching commit (geometry + game + ghost + oracle deletion + box trace re-bless intent)
3. **Task 3: Claude adversarial playtest + human before/after GIF gate** — no commit (verification only; artifacts gitignored)

**Plan metadata:** this SUMMARY + tracking commit (docs)

## Files Created/Modified
- `geometry.py` — single `GHOST_BOX_BOUNDS = (350, 550, 360, 480)`; both old constants removed; docstring reconciled; historical-divergence guard comment.
- `game.py` — import + 8 `in_box(..., GHOST_BOX_BOUNDS)` call sites in get_targets (the only value change).
- `ghost.py` — line 4 import + line 384 `in_box(self.x_pos, self.y_pos, GHOST_BOX_BOUNDS)` (name-only rename, value identical).
- `tests/golden/box_edge/trace.jsonl`, `tests/golden/box_exit/trace.jsonl` — box scenarios (re-bless intent; see Deferred section — actual re-bless of ALL 9 is a Linux-CI step).
- `tests/test_box_bounds_oracle.py` — created in Task 1, proven green, DELETED in Task 2 (transient by design, Phase-2 one-shot-then-delete lifecycle). Absent at end of phase by design.

## Oracle Proof (authoritative, platform-independent)

The differential oracle is the primary isolation evidence (golden traces are corroborating). Across the enumerated input space:

- **get_targets differential oracle:** 18,496 `get_targets` comparisons (old TARGET box (340,560,340,500) vs new COLLISION box (350,550,360,480)). 1,728 divergences — **100% in-ring** (inside TARGET, outside COLLISION), **zero out-of-ring**. Every position outside the ring produced byte-identical targeting old-vs-new.
- **check_collisions belt-check:** byte-identical old-vs-new across the enumerated state space — mechanically proving the name-only rename leaves collision/movement/box-exit unchanged.
- **teeth-check:** an out-of-ring perturbation drove the oracle RED, revert restored green — the oracle is not vacuously green.

This proof is float-drift-free and platform-independent, so it holds as authoritative even while the golden re-bless is deferred to Linux CI.

## Decisions Made
- **D-01: collision box wins** — unified onto (350,550,360,480) (the tighter COLLISION value), making get_targets the only value change and check_collisions a name-only rename.
- **Oracle-as-proof under deferred re-bless** — because the golden re-bless must run on Linux (Windows float drift would corrupt masters), the oracle proof is treated as the authoritative isolation evidence in the interim; golden traces are corroborating.

## Deviations from Plan

### 1. [Key finding — broader trace footprint than D-06 assumed] ALL 9 golden scenarios diverge, not just box_edge/box_exit

- **Found during:** Task 2 (re-bless inspection)
- **Plan expectation (D-06):** ONLY the `box_edge` + `box_exit` golden traces would move; the other 7 scenarios would stay byte-identical.
- **Reality:** ALL 9 golden scenarios diverge — but **every single one is rooted at the SAME single in-ring decision**: frame 340, inky at **(400, 358)** [verified in-ring: inside TARGET (340,560,340,500), outside COLLISION (350,550,360,480) — y=358 sits in the 2px ring band between COLLISION y_lo=360 and TARGET y_lo=340], where the unified tighter box flips inky from "aim at gate (SCATTER_EATEN_TARGET, [400,100])" to "chase player" one frame sooner.
- **Why this is still isolated:** the sim is deterministic and every scenario shares the same opening inky box-exit, so that one legitimate in-ring flip cascades through all 9 traces via deterministic replay. The oracle independently proves no out-of-ring change is possible (zero out-of-ring divergences across 18,496 comparisons), so isolation holds at the CODE level even though the TRACE footprint is broader than D-06 assumed. The cascade is amplification of one legitimate ring decision, not new out-of-ring behavior.
- **Impact:** the deferred Linux re-bless must re-record ALL 9 trace.jsonl files (not just 2), confirming every bless diff is rooted at the frame-340 in-ring inky flip. See "Deferred / Required Before Merge".

---

**Total deviations:** 1 (a finding that broadens the trace footprint but does not weaken isolation — the oracle proof shows the code-level delta is ring-only).
**Impact on plan:** None to correctness/isolation. The fix is exactly as sanctioned; only the golden-trace re-bless scope grew from 2 files to 9.

## Deferred / Required Before Merge

**DEFERRED LINUX RE-BLESS — REQUIRED pre-merge, NEVER on Windows.**

`pytest tests/test_golden_traces.py --bless` must run on Linux/WSL/CI to:
1. Re-record **ALL 9** trace.jsonl masters (superseded the D-06 "2 files only" assumption — see deviation above).
2. Confirm every bless diff is rooted at the frame-340, (400,358) in-ring inky flip (aim-at-gate → chase-player one frame sooner).
3. Be folded/amended onto `f45a712` (or committed in the same PR) so history keeps the fix as the single trace-touching change and CI goes green.

Until this runs, **the 9 golden traces are RED on Windows BY DESIGN** — Windows must not bless (platform float drift would corrupt the masters). This is the one remaining gate before the Phase-3 PR can merge CI-green. The oracle proof above stands as the authoritative, platform-independent isolation evidence in the interim.

## Issues Encountered
None during planned work. The all-9-traces finding (above) was surfaced by the oracle/re-bless inspection and is documented as a deviation, not an unresolved issue.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- BUG-01 code is complete and proven ring-only-isolated by the oracle; the milestone's one sanctioned behavior change has landed.
- **Blocker before Phase-3 PR can merge CI-green:** the deferred Linux re-bless of all 9 golden traces (see above). Phase 3 is code-complete but NOT yet CI-green/mergeable on Windows by design.

## Self-Check: PASSED

- `geometry.py:24` → `GHOST_BOX_BOUNDS = (350, 550, 360, 480)` present (1×); old `_TARGET`/`_COLLISION` names absent from all .py — VERIFIED
- `game.py` → 9 `GHOST_BOX_BOUNDS` refs (import + 8 sites) — VERIFIED
- `ghost.py:384` → `in_box(self.x_pos, self.y_pos, GHOST_BOX_BOUNDS)` — VERIFIED
- `geometry.py` → "Do NOT merge" prose gone (0 matches) — VERIFIED
- `tests/test_box_bounds_oracle.py` → deleted (absent) — VERIFIED
- Commit `a40ce4c` (test) exists in `git log` — VERIFIED
- Commit `f45a712` (fix) exists in `git log` — VERIFIED

**Honest status note:** golden traces are currently RED on Windows pending the deferred Linux re-bless of all 9 masters — this is by design (see Deferred section), not a failure.

---
*Phase: 03-box-bug-fix-hygiene*
*Completed: 2026-06-12*
