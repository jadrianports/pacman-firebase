# Phase 3: Box-Bug Fix + Hygiene - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-12
**Phase:** 3-Box-Bug Fix + Hygiene
**Areas discussed:** Unified box value, Isolation-proof depth, Fix-vs-hygiene split, Hygiene specifics (dep pins + .gitignore/CLAUDE.md), Claude playtest gate, .exe rebuild gate, check_collisions belt-check

---

## Unified box value

The two box rectangles are concentric (center ≈450,420); `TARGET (340,560,340,500)` = `COLLISION (350,550,360,480)` inflated ~10px(x)/~20px(y) per side. The design spec calls the unification intentional but does NOT prescribe a value.

| Option | Description | Selected |
|--------|-------------|----------|
| Collision box wins | Unify onto (350,550,360,480); only `get_targets` shifts; physical `in_box` flag byte-identical; smallest/most surgical delta | ✓ |
| Measure the true pen | Derive bounds from real gate/wall tiles; most "correct" but BOTH subsystems nudge, may override hand-tuning | |
| Targeting box wins | Unify onto (340,560,340,500); targeting unchanged but the higher-impact movement/exit `in_box` flag grows — riskier | |
| You decide — research recommends | Defer to research to measure + recommend the smallest/cleanest diff | |

**User's choice:** Collision box wins → `GHOST_BOX_BOUNDS = (350, 550, 360, 480)`
**Notes:** Picks the principled-and-minimal option — the physical pen becomes the single source of truth, `ghost.py` is a name-only change, behavior delta confined to `game.py:get_targets`.

---

## Isolation-proof depth

SC#2 requires the change be "provably isolated to the box region." The delta is now confined to `get_targets`.

| Option | Description | Selected |
|--------|-------------|----------|
| Add targeted oracle | Phase-2-style differential oracle: freeze old vs new `get_targets`, exhaustively enumerate, assert delta confined to the ring; + teeth-check + one-shot-then-delete | ✓ |
| Roadmap proof only | Golden-trace diff + box_edge scenario + re-bless + montages + GIF gate; no new throwaway oracle | |
| You decide — proportional | Run trace diff first; add oracle only if the diff surfaces something surprising | |

**User's choice:** Add targeted oracle (on top of the roadmap proof)
**Notes:** Consistent with the "maximum paranoia" through-line from Phases 1–2.

---

## Fix-vs-hygiene split

Cardinal Rule: never mix a must-NOT-change step with a must-change step. BUG-01 changes behavior (re-bless); HYG-01..04 are behavior-neutral. `branching_strategy: none` → work on `main`.

| Option | Description | Selected |
|--------|-------------|----------|
| Hygiene first, box fix isolated + last | 4 behavior-neutral atomic hygiene commits (CI green throughout), then the box fix as the sole trace-touching final commit; one Phase-3 PR | ✓ |
| Box fix first, then hygiene | Do the risky re-bless first while the proof is fresh, then cleanup — inverts "fix last" | |
| You decide — atomic discipline | Planner sequences per the established atomic-commit discipline | |

**User's choice:** Hygiene first, box fix isolated + last
**Notes:** Applies the milestone Cardinal Rule inside the phase; PR diff reads "all green/unchanged, then ONE commit that moves only box-edge frames."

---

## Hygiene specifics — dependency pinning (HYG-01)

`requirements.txt` currently has bare `pygame` / `pyinstaller`. Dev/test deps already pinned in Phase 1.

| Option | Description | Selected |
|--------|-------------|----------|
| Exact pins (==), client only | Pin pygame & pyinstaller to exact CI-green versions; leave backend (3.*/6.*) untouched | ✓ |
| Exact pins, client + backend | Also tighten backend cloud_functions pins — beyond HYG-01's "client" scope | |
| Compatible-release (~=) | Pin major.minor, allow patches — weaker reproducibility | |

**User's choice:** Exact pins (==), client only
**Notes:** Matches the "reproducible builds" intent; backend is a separate deploy surface, out of HYG-01 scope.

---

## Hygiene specifics — .gitignore / CLAUDE.md (HYG-02)

Baseline regardless: `git rm --cached .claude/settings.local.json` + dedupe duplicate `/.claude`. The fork: `CLAUDE.md` is gitignored + untracked today, yet HYG-03 edits it.

| Option | Description | Selected |
|--------|-------------|----------|
| Track CLAUDE.md | Un-ignore (remove `.gitignore` line 26) + commit; makes the HYG-03 doc fix durable/shared | ✓ |
| Keep CLAUDE.md local | Leave it gitignored/untracked; HYG-03's edit stays local-only | |
| You decide | Planner resolves the tracking question | |

**User's choice:** Track CLAUDE.md
**Notes:** It's the project-instructions doc, already edited in Phase 2 (D-17); ignoring it is an accident. Rest of `/.claude` stays ignored.

---

## Claude playtest gate

The oracle + golden traces prove WHERE the change is confined; a playtest probes whether the new box-edge dynamics play right.

| Option | Description | Selected |
|--------|-------------|----------|
| Required end-of-phase gate | Live observe→decide→act session hunting box-exit soft-locks, pen-mouth oscillation, wall-clips, eaten-eyes targeting glitches | ✓ |
| Optional — planner decides | Leave to planner; oracle + traces + montages + GIF may suffice | |
| Skip it | Don't require a playtest | |

**User's choice:** Required end-of-phase gate
**Notes:** Phase 2 skipped it (behavior was provably identical); Phase 3 has a real intentional edge change, so emergent dynamics are newly possible.

---

## .exe rebuild gate

CI runs pytest headless and never builds the PyInstaller bundle.

| Option | Description | Selected |
|--------|-------------|----------|
| Required: build + smoke-run | `python build.py` → launch `dist/pacman/pacman.exe` → play a few frames; human end-of-phase step | ✓ |
| Build only, no run | Confirm it packages, but don't launch | |
| Skip — trust grep + CI | Rely on the no-references grep + green CI | |

**User's choice:** Required: build + smoke-run
**Notes:** Catches packaging/asset-path regressions (deletion + pyinstaller pin) that the headless suite structurally cannot.

---

## check_collisions belt-check

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — add it | Oracle also asserts `check_collisions` byte-identical old-vs-new; symmetric isolation proof; one-shot-then-delete | ✓ |
| No — redundant | Rename is obviously safe; 15 micro-tests already pin `check_collisions` | |

**User's choice:** Yes — add it
**Notes:** Nearly free; proves the "name-only change" claim mechanically.

---

## Claude's Discretion

- Exact `get_targets` oracle enumeration bounds + player-position handling (mirror Phase 2 D-05/D-07).
- Exact pinned version strings (`pip freeze` from CI-green env).
- Whether to leave a comment at the unified constant guarding against future re-split.
- Plan decomposition consistent with hygiene-first / fix-last.
- Whether the `.exe` smoke-run is scripted-headless or manual; reuse Phase 1 HRN-03 montage/GIF path.

## Deferred Ideas

- Overlapping `build.py` vs `pacman.spec` (CONCERNS D5) — not in Phase 3 scope; future hygiene pass.
- Backend dependency pinning (cloud_functions) — out of HYG-01 (client-only); future "More Competitive" milestone.
