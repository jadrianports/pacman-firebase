# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — Solid Foundation

**Shipped:** 2026-06-12
**Phases:** 3 | **Plans:** 11 | **Tasks:** 23 | **Commits:** 84 | **Span:** ~10 days

### What Was Built
- A frame-perfect **safety net**: steppable `Game.tick()` + record/replay harness, 9 golden-master traces (8 scripted + 1 Claude session), 15 micro per-ghost characterization tests, a frame-hash manifest, and a static determinism guard — all CI-gated and merge-blocking on `main`.
- Visual + Claude verification channels: zero-dependency blit montages (for Claude's vision), Pillow GIFs (for the human), and a Claude observe→decide→act play-loop whose inputs replay deterministically.
- A **byte-identical refactor** behind the net: centralized board geometry (REF-01) and the 4× ghost mover collapsed into a data-driven `_move` + per-ghost `*_PROFILE`s (REF-02).
- The one sanctioned behavior change: **ghost-box bounds unified** (BUG-01), oracle-proven isolated to the box ring, goldens re-blessed on Linux CI.
- Repo hygiene (HYG-01..04): pinned deps, untracked local settings, fixed doc drift, removed dead assets.

### What Worked
- **The Cardinal Rule** (net → byte-identical refactor → isolated fix, never reordered) kept "must-NOT-change" and "must-change" work in separate phases. This was the single highest-leverage decision — it made an accidental regression structurally distinguishable from the one intended change.
- **One-shot differential oracles** — build an exhaustive oracle (384k geometry cases, 138k mover cases, 18,496 box-bounds comparisons), prove byte-identity / ring-isolation, teeth-check it, then delete it in the same commit. Cheap, disposable insurance; the mover oracle caught a real dir-3 ladder bug before it shipped.
- **Golden traces as a merge gate** gave the confidence to refactor fragile, hand-tuned ghost AI at all — the whole milestone thesis ("safe to extend") held.
- **Atomic, independently-green hygiene commits** — each of the 4 hygiene changes left golden traces byte-identical and the suite green, so any one is trivially revertible.

### What Was Inefficient
- **Float non-determinism across platforms** forced golden-trace re-bless onto Linux/CI only; Windows dev runs showed the goldens as "RED by design," and the BUG-01 re-bless was deferred for days. That left a genuinely confusing intermediate state ("code-complete but not CI-green").
- **STATE.md prose drifted from git reality** — it still described the Linux re-bless as *pending* well after it had landed (commit `7c120e5`) and verification passed 10/10. Manual state hygiene lagged the actual work.
- **A human gate (D-19) lingered unclosed** — the Phase-2 before/after GIF gate was never formally ticked and surfaced as an open artifact at milestone close (acknowledged + deferred, since the automated proof and the Phase-3 GIF gate already covered it).

### Patterns Established
- **"Behind the net" rule** — never touch ghost AI or the game loop without the golden net green first.
- **One-shot oracle** — exhaustive differential oracle, prove, teeth-check, delete in the proving commit. Permanent artifacts (frame-hash manifests, micro tests) stay; oracles don't.
- **Linux/CI-only re-bless** — golden masters are blessed on Linux/CI, never on Windows (float drift corrupts them). Decide the bless platform up front.
- **Zero-dep visual proof** — blit montages need no new dependency; reserve Pillow for the human GIF.

### Key Lessons
1. **Sequence must-not-change before must-change, in separate phases.** Mixing them makes a brick indistinguishable from an intended change. The Cardinal Rule was worth its overhead.
2. **Pin the determinism platform for golden masters from day one.** Cross-platform float drift turned a green suite into false-red on the dev machine and stalled the merge.
3. **Exhaustive differential oracles are cheap and disposable** — they pay for themselves on the first real bug caught (the dir-3 ladder), then delete cleanly.
4. **Reconcile STATE.md against git immediately after deferred work lands.** A stale "pending" note outlived the work that resolved it and had to be cleaned up at close.

### Cost Observations
- Model profile: `quality` (opus-heavy) per `.planning/config.json`.
- Model mix / per-session token cost: not instrumented this milestone.
- Notable: zero new client runtime dependencies added (montage rendering done with blit; Pillow used only for the human GIF, dev-only).

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 Solid Foundation | 3 | 11 | Established the safety-net-first / Cardinal-Rule discipline and CI merge gate |

### Cumulative Quality

| Milestone | Tests (passed/skipped) | CI Gate | Zero-Dep Additions |
|-----------|------------------------|---------|--------------------|
| v1.0 Solid Foundation | 61 passed / 9 skipped | ✅ merge-blocking on `main` | blit montage capture |

### Top Lessons (Verified Across Milestones)

1. *(pending second milestone to cross-validate)* — Safety net before refactor.
2. *(pending second milestone to cross-validate)* — Pin determinism platform for golden masters.
