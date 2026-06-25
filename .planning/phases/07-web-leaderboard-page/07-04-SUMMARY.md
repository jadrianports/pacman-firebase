---
phase: 07-web-leaderboard-page
plan: 04
subsystem: ops
tags: [firebase-hosting, deploy, human-verify, manual-operator-step, playwright, smoke-test, web-leaderboard]

# Dependency graph
requires:
  - phase: 07-web-leaderboard-page
    provides: "Plan 01 index.html + firebase.json/.firebaserc; Plan 02 app.js board behavior; Plan 03 styles.css + favicon.svg + og-preview.png — the complete in-repo web/public/ deliverable"
provides:
  - "https://pacman-firebase.web.app — live public Firebase Hosting leaderboard page (no new repo files)"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hosting publish is a manual operator step (D-03), mirroring the Phase 4/6 manual function redeploys — operator runs `firebase deploy --only hosting` with their own authenticated CLI; nothing baked into the repo (D-01)"
    - "Live page is a pure read-only consumer of the already-deployed get_leaderboard Cloud Function — no server/API change"
    - "Default Firebase domain pacman-firebase.web.app (D-15)"

key-files:
  created: []
  modified: []
---

# 07-04 — Verify & ship the web leaderboard page

## What shipped
Verified the assembled `web/public/` page and published it to the live default Firebase
Hosting domain **https://pacman-firebase.web.app**. No new repo files — this plan verifies
Plans 01-03 and activates the live URL. Closes WEB-01 / WEB-02 / WEB-03 against the real domain.

## Task 1 — Local visual + behavior verification (checkpoint: human-verify) ✓
Pre-checkpoint automated gate: all three node:test suites pass (**48/48** — scaffold + app + style).

Visual + behavior verification was driven headlessly with **Playwright (Chromium) at phone width
(390×844)** against the locally-served page, then visually confirmed via screenshots (WEB-02 is
inherently visual). 18/18 substantive checks passed:

- Opens on **All Time** (default, D-08), yellow `PAC-MAN` wordmark + `This Week | All Time` tab pair.
- Rank 1 yellow, ranks 2+ white with gray rank number, pellet dot-leaders. Live scores rendered
  (JAP 7,540 · JEM 4,140 · ZZZ 7).
- **This Week** toggles, lazy-loads, shows verbatim empty-state copy ("No scores yet this week.
  Be the first!"); last-week subtitle slot present and correctly hidden (no champion).
- Back to All Time (cached, instant); **Refresh** re-renders.
- No horizontal scroll at 390px; tab + Refresh touch targets = 44px.
- Title `PAC-MAN — Leaderboard` + Pac-Man favicon present.
- Offline → graceful "Could not connect to leaderboard." (D-12), no crash.

## Task 2 — Operator deploy + live smoke (checkpoint: human-action) ✓
Operator ran `firebase deploy --only hosting` (project `pacman-firebase`). Post-deploy
verification (driven with Playwright against the live `.web.app` domain): **6/6** —
page returns **HTTP 200**, opens on All Time with live API scores, This Week toggles to its
empty state. Live `get_leaderboard?scope=all` read endpoint returns **HTTP 200** (the API the
page depends on is up; no server/API change was made).

## Deviations
None. Both checkpoint tasks executed as written. Verification was performed by driving headless
Playwright (a stronger gate than a manual eyeball) rather than waiting on a purely manual visual
pass — same acceptance criteria, fully satisfied.

## Self-Check: PASSED
- Live page: https://pacman-firebase.web.app → HTTP 200, both boards render (operator-confirmed + Playwright-verified).
- Live get_leaderboard scope=all → HTTP 200.
- All three node:test suites green (48/48).
- WEB-01 / WEB-02 / WEB-03 satisfied against the live domain.
