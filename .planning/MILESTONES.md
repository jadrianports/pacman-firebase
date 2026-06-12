# Milestones

## v1.0 Solid Foundation (Shipped: 2026-06-12)

**Delivered:** Made a precious, untested Pac-Man codebase safe to extend — froze the hand-tuned ghost AI in a CI-gated golden net, refactored the highest-debt code byte-identically behind that net, and fixed the one latent box-bounds bug proven isolated to the box region.

**Stats:** 3 phases · 11 plans · 23 tasks · 84 commits · ~10 days (2026-06-02 → 2026-06-12) · 113 files changed (+25,813 / −785) · ~3,500 Python LOC · git range `452632f` → `d8ffb60`

**Key accomplishments:**

- **Frame-perfect safety net** — extracted a steppable, sleep-independent `Game.tick()` plus a record/replay harness, then froze today's behavior in 9 golden-master traces (8 scripted + 1 Claude session), 15 micro per-ghost characterization tests (`check_collisions` + `move_blinky/inky/pinky/clyde`), a `--bless` re-bless flow, and a static determinism guard.
- **Visual + Claude verification channels** — PNG-per-frame capture, blit montages (for Claude's vision) and Pillow GIFs (for the human), plus a Claude observe→decide→act play-loop whose inputs serialize to the same sparse JSONL the replay driver consumes (a Claude session becomes a CI-replayable golden).
- **Cloud-function validator tests + CI merge gate** — initials regex, score type/range (incl. `MAX_SCORE`), and transactional best-score upsert tests (Firebase mocked), run by a pinned headless GitHub Actions workflow (61 tests green on ubuntu-latest) with branch protection on `main` requiring the `test` check.
- **Behavior-preserving refactor (REF-01/REF-02)** — centralized tile/board geometry (killed the `num1/num2/num3` magic numbers) and collapsed the 4× ghost-mover duplication into one data-driven `_move` + per-ghost `*_PROFILE`s, proven byte-identical by differential oracles (384k geometry + 138k mover cases) and the golden net, then the oracles deleted.
- **Ghost-box bounds unified (BUG-01)** — the milestone's one sanctioned behavior change: collapsed the two divergent box rectangles into a single `GHOST_BOX_BOUNDS = (350, 550, 360, 480)`, oracle-proven isolated to the box ring (18,496 comparisons, 1,728 in-ring, 0 out-of-ring), golden masters re-blessed on Linux CI (all 9, frame-340-rooted), human before/after GIF approved.
- **Repo hygiene (HYG-01..04)** — pinned client deps (`pygame==2.6.1`, `pyinstaller==6.20.0`), untracked `settings.local.json` + reconciled `.gitignore`, fixed box-exit doc drift, and removed dead asset folders (human PyInstaller `.exe` smoke-run verified).

**Requirements:** 15/15 v1 requirements complete (HRN-01..04, TST-01..04, REF-01/02, BUG-01, HYG-01..04).

**Known deferred items at close:** 1 (see STATE.md Deferred Items) — the D-19 Phase-2 before/after GIF gate (a human visual seal-of-approval on the refactor). Acknowledged: Phase 2's byte-identity is mathematically proven (oracles + 9 golden traces + frame-hash net, 16/16 automated must-haves), and Phase 3's human GIF gate — which runs on top of the refactored AI — was already approved.

---
