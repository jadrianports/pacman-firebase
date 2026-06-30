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

## Milestone: v1.1 — More Competitive

**Shipped:** 2026-06-26
**Phases:** 4 (Phases 4-7) | **Plans:** 15 | **Tasks:** 25 | **Commits:** ~126 (incl. docs) | **Span:** ~12 days
**Verification:** 4/4 phases PASSED (5/5, 4/4, 10/10, 17/17 must-haves)

### What Was Built
- **Server as the enforcement boundary (Phase 4):** `submit_score` with a 50k sanity ceiling, HMAC-SHA256 signature verification, server-locked permanent initials, and a week-bucketed write + lazy prune in one read-before-write Firestore transaction; scope-aware `get_leaderboard` (`week|all|last_week`) with `machine_id` never projected; both Cloud Run services redeployed live with a Secret Manager secret and an Enabled weekly composite index.
- **Tamper-evident client identity (Phase 5):** identity consolidated into a single obfuscated, HMAC-signed blob in `%LOCALAPPDATA%\PacMan\`, migrate-then-remove of legacy plaintext, fail-closed TAMPERED sentinel, and the build baking the gitignored shared secret in non-literally — closing the signing↔verification loop end-to-end.
- **In-game weekly competition (Phase 6):** This Week / All Time toggle, last-week champion subtitle, and a launch got-passed banner — all graceful offline/first-launch.
- **Public web leaderboard (Phase 7):** a no-dependency ESM page on Firebase Hosting mirroring the in-game boards, arcade-styled via the frontend-design skill, XSS-safe, mobile-first, live at `pacman-firebase.web.app`.

### What Worked
- **One backend change powering three features.** Week-bucketing + a scope-aware API was the single seam every competitive feature consumed; sequencing it first (Phase 4) made Phases 5-7 pure consumers and kept the data model from churning.
- **Splitting one mechanism across two phases with a shared contract.** HMAC server-verify (Phase 4) and client-sign (Phase 5) shared a byte-identical canonical-JSON wire format and a loop-closing oracle test, so the halves met exactly on first integration.
- **Graceful-degrade as a first-class requirement.** Every networked feature (boards, banner, web fetch) had an explicit offline/first-launch no-op path, so the game stayed fully playable with no leaderboard.
- **Parallel waves against a frozen DOM contract (Phase 7).** Plan 01 fixed the `index.html` hook contract; `app.js` and `styles.css` then built independently in parallel wave 2 with no file overlap.

### What Was Inefficient
- **The milestone audit went stale mid-flight.** `v1.1-MILESTONE-AUDIT.md` was written (`gaps_found`) against a snapshot before Phase 7 existed; Phase 7 shipped and verified the same day, leaving the audit's headline ("milestone not complete") false at close. An audit is a point-in-time snapshot — re-run it after the last phase lands, or it misleads.
- **Operator-paced cloud steps create "code-complete but not live" gaps.** BOARD-04's `scope=last_week` and the Phase 4 deploy both depended on a manual Cloud Run redeploy; the in-repo gate (validator tests green) and live behavior diverged until the operator acted.
- **Inherently-manual verification can't close in-repo.** The 2-player got-passed E2E (UAT Test 4) needs a live second player; it stayed `human_needed`/deferred despite all code paths being unit-verified.
- **SUMMARY frontmatter drift.** Phase 6 summaries lacked `requirements-completed` frontmatter and no phase carried `one_liner:` fields, so the milestone-complete CLI scraped noisy accomplishment lines (including a stray `Final decision: O-3` and a review-rule heading) that had to be hand-cleaned.

### Patterns Established
- **Server owns the clock.** Week-id math runs server-side (Monday-UTC) to defeat client-clock spoofing; the client mirrors it only for display.
- **Client crypto is obfuscation + HMAC, never local encryption.** The server is the enforcement boundary; local secrets are extractable, so stronger local crypto would be theater.
- **Frozen DOM/interface contract before parallel fan-out.** Fix the hook contract in wave 1, build behavior + style in parallel wave 2.
- **Deliberate, documented divergences (D-08).** The web page defaults to All Time while in-game defaults to This Week — recorded as an intentional decision so it isn't "fixed" later.

### Key Lessons
1. **Re-run the milestone audit after the final phase lands.** A stale audit is worse than none — it asserts a false status at the exact moment of record-keeping.
2. **Sequence the shared seam first.** When N features ride one backend change, build that change first and make the rest consumers — it stops the data model from churning under half-built UIs.
3. **A split mechanism needs a shared, tested contract at the seam.** The canonical-JSON wire format + loop-closing oracle made the client/server HMAC halves meet on first try.
4. **Tag operator-paced cloud steps explicitly as deferred-until-live.** Track the "code green vs. deployed" gap in STATE.md so "done" never implies "live."
5. **Put `one_liner:` / `requirements-completed:` in SUMMARY frontmatter.** Clean machine-readable summaries make milestone close a formatting-free archive step.

### Cost Observations
- Model profile: `quality` (opus-heavy) per `.planning/config.json`.
- Model mix / per-session token cost: not instrumented this milestone.
- Notable: zero new client *runtime* dependencies for the crypto/identity work (stdlib-only HMAC + obfuscation); the web page ships as no-dependency ESM with a self-hosted font (zero third-party tracking, D-16).

---

## Milestone: v1.2 — Feels Right

**Shipped:** 2026-06-30
**Phases:** 2 (Phases 8-9) | **Plans:** 9 | **Tasks:** 20 | **Commits:** ~43 (incl. docs) | **Span:** ~1 day
**Verification:** golden net green with no re-bless (FEEL-*) / one deliberate re-bless (FAIR-*); death-cadence + blink-readability playtest human-approved

### What Was Built
- **Fairness pass (Phase 8):** corner-kiss catches removed via an integer center-to-center squared-distance check against `GHOST_CATCH_DISTANCE` (FAIR-01), a widened pre-turn cornering window registering queued turns ~4-6px early (FAIR-03), and a per-ghost integer-rational chase-speed accumulator (FAIR-02) — all in `game.py`/`player.py`/`settings.py` with `ghost.py` byte-identical, batched behind one Linux/Docker golden re-bless (24/40/20/6).
- **Arcade juice (Phase 9):** a death wedge-spin collapse (FEEL-01), eat-ghost points popup 200/400/800/1600 + brief freeze (FEEL-02), frightened-end white blink (FEEL-04), and a "READY!" round-open beat (FEEL-05) — every effect gated behind the `Game.juice` firewall so the `juice=False` replay path stayed byte-identical and shipped with no re-bless.

### What Worked
- **The juice firewall let cosmetic work ship for free.** Gating every FEEL effect behind `Game.juice` (default `False`, the path goldens + frame-hash replays run) meant four visible features landed with zero re-bless — the firewall pattern paid for itself exactly as designed, including the deterministic eat-ghost freeze.
- **Batching all behavior changes behind one re-bless.** The three FAIR-* items shipped together behind a single deliberate Linux/Docker re-bless — the v1.0 Phase-3 box-fix discipline reused, keeping the intended outcome-shift cleanly separable from any accidental regression.
- **`ghost.py` byte-identical as a hard guard.** Confining all fairness logic to `game.py`/`player.py` kept the precious targeting/profile code untouched and provable — the core-value guard never had to be argued, only diffed.
- **RED feature tests pinned to exact future symbols.** 09-01 stood up RED tests naming the 09-02/03/04 symbols before they existed, so each later wave had a green target and the firewall/determinism guards stayed live throughout.

### What Was Inefficient
- **FEEL-03 was wired then reverted.** A full plan (09-04) implemented the eat-ghost sound before the asset question was settled; sourcing/licensing a fit-for-purpose `.wav` wasn't worth it, so the wiring was cut and reverted. Asset availability should gate the plan, not surface mid-implementation.
- **FAIR-02 was built before the playtest proved it was needed.** The chase-speed accumulator shipped, then the D-10 playtest dialed chase ghosts to player speed (2.0 px/frame), making FAIR-02 a tunable no-op — with FAIR-01 + FAIR-03 fixed, cornering alone was a sufficient escape. The mechanism preceded the evidence it was necessary.
- **The pygame vs pygame-ce pin conflict persists.** `requirements.txt` pins pygame-ce (has `gaussian_blur`) but `requirements-dev.txt` pins pygame (lacks it, installed last), so ~12 UI/juice/theme render tests fail in the dev/CI env — carried unresolved, tracked in 08 deferred-items.

### Patterns Established
- **Firewall-gated cosmetics.** Any subsystem whose byte-identity is golden-gated can absorb new visual/audio work for free if every effect gates behind the default-off flag the replays run through. Generalizes beyond juice.
- **Playtest-gated tuning constants.** Ship behavior as named `settings.py` dials and let the human set them at sign-off (fairness constants 24/40/20/6; FAIR-02 dialed to a no-op). The tunable survives even when this milestone's value is "off."
- **Validate the asset before planning the feature.** A feature that needs an external asset (sound, sprite) should confirm the asset exists/licenses cleanly before a plan wires it.

### Key Lessons
1. **Validate asset availability before planning an asset-dependent feature.** FEEL-03 cost a wire-then-revert cycle because the `.wav` sourcing was never settled up front.
2. **Don't implement a mechanism before the playtest proves it's needed.** FAIR-02's accumulator became a no-op once cornering (FAIR-01/03) was confirmed sufficient — the cheaper fix subsumed the expensive one.
3. **The firewall pattern is the reusable asset, not just a v1.2 trick.** A default-off flag the goldens replay through turns an entire class of risky-looking changes (cosmetics) into no-re-bless work.
4. **A behavior dial that ships "off" is still worth keeping.** FAIR-02 as a tunable no-op leaves the lever in place for a future difficulty pass without re-deriving it.

### Cost Observations
- Model profile: `quality` (opus-heavy) per `.planning/config.json`.
- Model mix / per-session token cost: not instrumented this milestone.
- Notable: zero new dependencies — juice rendered with `pygame.draw` primitives + `BLEND_RGB_ADD` (white tint), no new asset; fastest milestone yet (2 phases / 9 plans in ~1 day).

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Plans | Key Change |
|-----------|--------|-------|------------|
| v1.0 Solid Foundation | 3 | 11 | Established the safety-net-first / Cardinal-Rule discipline and CI merge gate |
| v1.1 More Competitive | 4 | 15 | Server became the enforcement boundary; one-backend-seam-first sequencing; split-mechanism shared contracts |
| v1.2 Feels Right | 2 | 9 | Firewall-gated cosmetics (no re-bless); playtest-gated tuning dials; fastest milestone (~1 day) |

### Cumulative Quality

| Milestone | Tests (passed/skipped) | CI Gate | Zero-Dep Additions |
|-----------|------------------------|---------|--------------------|
| v1.0 Solid Foundation | 61 passed / 9 skipped | ✅ merge-blocking on `main` | blit montage capture |
| v1.1 More Competitive | 146 passed / 9 skipped | ✅ merge-blocking on `main` | stdlib-only HMAC/obfuscation; no-dependency ESM web page |
| v1.2 Feels Right | golden net green (1 FAIR re-bless · 0 FEEL re-bless) | ✅ merge-blocking on `main` | `pygame.draw` + `BLEND_RGB_ADD` juice, no new asset |

### Top Lessons (Verified Across Milestones)

1. **State/docs drift from reality is the recurring failure mode.** v1.0: STATE.md described a re-bless as "pending" after it landed. v1.1: the milestone audit asserted "not complete" after the final phase shipped. Reconcile point-in-time artifacts (STATE.md, audits) against git/disk *immediately* after the work they describe lands.
2. **Decide where the source of truth lives, up front.** v1.0: pin the determinism platform for golden masters (Linux/CI only). v1.1: the server owns week-math and the enforcement boundary. Both milestones turned on putting authority where it can't be spoofed/corrupted.
3. **Disposable proof at the seam.** v1.0: one-shot differential oracles prove byte-identity then delete. v1.1: a loop-closing oracle test proves the client/server HMAC halves meet. Build the proof exactly where two things must agree.
