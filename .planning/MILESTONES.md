# Milestones

## v1.2 Feels Right (Shipped: 2026-06-30)

**Delivered:** Made the game feel fair and alive without touching a single ghost personality — corner-kiss catches are gone (center-to-center collision), cornering registers a few pixels early, and the arcade juice that was missing (death animation, eat-ghost popup, frightened-end warning, READY! beat) all rides the existing juice firewall so it shipped with no golden re-bless.

**Stats:** 2 phases (8-9) · 9 plans · 20 tasks · 1 day (2026-06-29 → 2026-06-30) · git range `feat(08-01)` → `docs(09-05)`

**Key accomplishments:**

- **Corner-kisses are fair (FAIR-01)** — collision switched to an integer center-to-center squared-distance check against `GHOST_CATCH_DISTANCE` (24), replacing the 40×40 / 36×36 AABB overlap, so a ghost passing diagonally past a corner no longer registers a catch. Implemented entirely in `game.py`; `ghost.py` left byte-identical.
- **Smooth cornering (FAIR-03)** — widened the four player-only pre-turn windows in `Player.check_position` by `PLAYER_TURN_WINDOW_MARGIN` so a queued turn registers ~4-6px before the junction; the ghost windows are byte-identical.
- **Escape rebalance scaffolding (FAIR-02)** — added a per-ghost integer-rational step accumulator for the lethal chase tier. Per the D-10 playtest the player dialed chase ghosts to 2.0 px/frame (= player speed), so FAIR-02 ships as a **tunable no-op**: escape is cornering-based, not speed-based (accepted SC2 override).
- **Arcade juice, all firewall-gated (FEEL-01/02/04/05)** — death wedge-spin collapse (`pygame.draw.polygon`), eat-ghost points popup (200/400/800/1600) with a brief freeze, frightened-end white blink over the last ~2s of the power window, and a "READY!" round-open beat — every effect gated behind `Game.juice` so the `juice=False` path stays byte-identical.
- **Core value held, golden-safe** — `ghost.py` byte-identical throughout; one deliberate Linux/Docker (`python:3.12`, pygame 2.6.1) re-bless of all 9 traces + frame-hash manifests under the D-10 fairness constants (24 / 40 / 20 / 6) covered all three FAIR changes together; every FEEL effect shipped with **no re-bless**.

**Requirements:** 7/8 v1.2 requirements complete (FAIR-01/02/03, FEEL-01/02/04/05). **FEEL-03** (distinct eat-ghost sound) **cut/descoped** — wired in 09-04 then reverted; sourcing/licensing a `.wav` wasn't worth the chore. A code-review pass also fixed a pre/post-move catch-sampling skew (WR-03).

---

## v1.1 More Competitive (Shipped: 2026-06-26)

**Delivered:** Turned the client-trusted leaderboard into something friends can actually compete on — the server became the enforcement boundary (HMAC-verified, sanity-ceilinged, server-locked initials, week-bucketed), the client signs its submissions and hides a tamper-evident identity, and the weekly fight surfaces both in-game and on a public mobile web page.

**Stats:** 4 phases · 15 plans · 25 tasks · ~12 days (2026-06-14 → 2026-06-26) · ~1,000 LOC web/cloud_functions (HTML/CSS/JS + Python)

**Key accomplishments:**

- **Server is now the enforcement boundary (Phase 4)** — `submit_score` gained a 50k sanity ceiling, HMAC-SHA256 signature verification (constant-time, grace-flagged), server-locked permanent initials, and a week-bucketed write + lazy prune, all in one read-before-write Firestore transaction; `get_leaderboard` became scope-aware (`?scope=week|all|last_week`) with `machine_id` never projected. Both Cloud Run services redeployed live with the secret in Secret Manager and an Enabled weekly composite index.
- **Tamper-evident client identity (Phase 5)** — identity moved out of the game folder into `%LOCALAPPDATA%\PacMan\` as a single obfuscated, HMAC-signed blob, with seamless migrate-then-remove of the two legacy plaintext files and a fail-closed TAMPERED sentinel that blocks submit without silently regenerating.
- **Closed the signing↔verification loop end-to-end** — client `leaderboard_crypto.py` mirrors the server wire-format; valid runs are HMAC-signed and POSTed in the `"signature"` field and accepted by the live server; the build bakes the gitignored shared secret in non-literally.
- **In-game weekly competition (Phase 6)** — This Week / All Time board toggle, last week's champion subtitle, and a launch "got-passed" banner naming whoever beat your score since you last looked — all degrading gracefully offline/first-launch.
- **Public web leaderboard, live (Phase 7)** — a no-dependency ESM page on Firebase Hosting (`pacman-firebase.web.app`) that mirrors the in-game boards with a lazy per-view cache and XSS-safe rendering, styled through the frontend-design skill (retro-arcade palette, self-hosted Press Start 2P, dot-leaders, OG share card), mobile-first and phone-verified.

**Requirements:** 14/14 v1.1 requirements complete (IDENT-01..03, COMP-01..03, BOARD-01..04, WEB-01..03, RIVAL-01).

**Known deferred items at close:** 2 (see STATE.md Deferred Items) — Phase 6's live 2-player got-passed E2E (UAT Test 4) and the BOARD-04 `scope=last_week` live-redeploy check. Both are inherently manual (need a 2nd live player / operator redeploy) and cannot be automated in-repo; all code paths are unit-verified green.

**Note:** The `v1.1-MILESTONE-AUDIT.md` (status `gaps_found`) was written against an earlier snapshot before Phase 7 was built — its sole blocker ("Phase 7 not started") was closed the same day by Phase 7's passing verification (17/17 must-haves). The milestone is complete; the audit file is retained as a stale historical artifact.

---

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
