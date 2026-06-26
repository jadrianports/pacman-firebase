---
phase: 07-web-leaderboard-page
plan: 01
subsystem: ui
tags: [html, firebase-hosting, open-graph, twitter-card, esm, node-test, static-site]

# Dependency graph
requires:
  - phase: 04-server-hardening
    provides: scope-aware get_leaderboard (week|all|last_week) the page consumes read-only
provides:
  - web/public/index.html static markup contract (stable DOM hooks for app.js + styles.css)
  - Branding head (em-dash title, Open Graph + Twitter Card meta, favicon/stylesheet/module-script links)
  - firebase.json Hosting config (hosting-only, public=web/public) + .firebaserc default project pacman-firebase
  - web/package.json ESM marker enabling node --test imports of app.js (Plan 02)
affects: [07-02-app-js, 07-03-styles-css-assets, 07-04-deploy]

# Tech tracking
tech-stack:
  added: [Firebase Hosting config, Node.js node:test runner (web/), ESM web package]
  patterns:
    - "DOM contract handshake: index.html fixes ids/data-scope/classes; Plan 02 (app.js) and Plan 03 (styles.css) attach independently for parallel wave-2 execution"
    - "Hosting-only firebase.json scoped to web/public so root secrets (firebase-key.json) are never deployable (T-07-02)"
    - "No build step (D-01): plain static HTML/CSS/JS + node:test assertions, zero dependencies"

key-files:
  created:
    - web/public/index.html
    - web/tests/scaffold.test.mjs
    - firebase.json
    - .firebaserc
    - web/package.json
  modified: []

key-decisions:
  - "Tab DOM order mirrors in-game 'This Week | All Time'; tab--active starts on All Time (D-08 web divergence)"
  - "Self-hosted Press Start 2P via @font-face in styles.css (Plan 03) over Google Fonts — honors D-16 zero third-party tracking, so no preconnect/preload added to head"
  - "Single root firebase.json layout (D-02) with static files under web/public; web/package.json sits at web/ (outside public) so it is never served"
  - "cleanUrls + 1h Cache-Control on static assets; no rewrites/functions blocks (hosting-only, page calls already-deployed get_leaderboard directly — D-03)"

patterns-established:
  - "Stable DOM hook contract: .wordmark, nav#tabbar > button.tab[data-scope], #subtitle[hidden], ol#board > li.state-msg, button#refresh, #hint"
  - "node:test scaffold assertions co-located under web/tests/, path-resolved to repo root"

requirements-completed: [WEB-01, WEB-03]

# Metrics
duration: 2min
completed: 2026-06-25
---

# Phase 7 Plan 01: Web Leaderboard Scaffold Summary

**Static index.html board skeleton with full social-share branding head, plus root Firebase Hosting config (pacman-firebase → web/public) and an ESM marker — the DOM + deploy foundation wave-2 plans build against.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-06-25T21:32:28Z
- **Completed:** 2026-06-25T21:34:34Z
- **Tasks:** 2
- **Files modified:** 5 (all created)

## Accomplishments
- `web/public/index.html`: full semantic board skeleton (wordmark, This Week | All Time tab bar default-active All Time, hidden last-week subtitle slot, seeded `Loading...` board, Refresh control, hint) with verbatim in-game copy.
- Complete branding head: `PAC-MAN — Leaderboard` em-dash title, Open Graph + Twitter Card meta with absolute 1200×630 `og-preview.png` url, favicon + stylesheet + `type="module"` app.js links.
- Root `firebase.json` (hosting-only, `public=web/public`, cleanUrls, 1h asset cache, ignore drops `firebase.json`/dotfiles/node_modules) + `.firebaserc` pinning default project `pacman-firebase`.
- `web/package.json` ESM marker (`{ type: module, private }`) so Plan 02's `node --test` can import app.js — no deps, no build step.
- 17 `node:test` assertions covering markup contract, branding head, and hosting config — all passing.

## Task Commits

Each task was committed atomically:

1. **Task 1: index.html semantic skeleton + branding head** - `6b3d844` (feat)
2. **Task 2: Firebase Hosting config + ESM marker** - `5b492d8` (feat)

## Files Created/Modified
- `web/public/index.html` - Static markup contract + branding head (DOM hooks consumed by Plan 02/03).
- `web/tests/scaffold.test.mjs` - node:test assertions for markup + branding head + hosting config (17 tests).
- `firebase.json` - Firebase Hosting config (hosting-only, public=web/public).
- `.firebaserc` - Default Firebase project = pacman-firebase.
- `web/package.json` - ESM type marker (no dependencies, no build step).

## Decisions Made
- DOM tab order mirrors in-game `This Week | All Time`; `tab--active` starts on All Time per the web's D-08 divergence (in-game opens on This Week).
- Chose self-hosted Press Start 2P (`@font-face` in Plan 03's styles.css) over Google Fonts to honor D-16 zero-tracking — so no preconnect/preload hint was added to the head.
- Single root `firebase.json` layout (D-02) with `web/package.json` outside `web/public` so it is never deployed.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None. (Git reported the standard LF→CRLF working-copy warnings on Windows; committed files store LF — no action needed.)

## Known Stubs
None. The referenced `styles.css`, `app.js`, `favicon.svg`, and `og-preview.png` are intentionally not-yet-created — they are the deliverables of Plan 02 (app.js) and Plan 03 (styles.css + assets). index.html references them by design to fix the contract; this is not a stub, it is the wave-2 handshake.

## Threat Flags
None. firebase.json hosting scope (`web/public` only) actively mitigates T-07-02 (root admin key never deployable); no new trust boundary beyond the plan's threat model was introduced.

## User Setup Required
None - no external service configuration required this plan. (Operator `firebase deploy --only hosting` is deferred to Plan 04.)

## Next Phase Readiness
- DOM contract is fixed and frozen: Plan 02 (`app.js` logic) and Plan 03 (`styles.css` + assets) can run in parallel in wave 2, attaching to stable hooks independently.
- Hosting config validates and is a one-command operator deploy to `pacman-firebase.web.app` — gated for Plan 04.
- No blockers.

## Self-Check: PASSED

All 5 created files verified on disk; both task commits (`6b3d844`, `5b492d8`) verified in git log.

---
*Phase: 07-web-leaderboard-page*
*Completed: 2026-06-25*
