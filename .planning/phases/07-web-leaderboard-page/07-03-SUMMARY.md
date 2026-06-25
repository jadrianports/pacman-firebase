---
phase: 07-web-leaderboard-page
plan: 03
subsystem: ui
tags: [css, retro-arcade, frontend-design, press-start-2p, web-font, favicon, open-graph, og-image, pillow, node-test, static-site]

# Dependency graph
requires:
  - phase: 07-web-leaderboard-page
    provides: "Plan 01 frozen index.html DOM contract (.wordmark / .tabbar / .tab / .tab--active / #subtitle / .board / .rank-row / .rank-row--first / .dots / .state-msg / .refresh / .hint) + the head links to styles.css, favicon.svg, and the absolute og-preview.png url"
provides:
  - web/public/styles.css — retro-arcade stylesheet (UI-SPEC tokens, mobile-first, 44px touch targets, pellet dot-leaders)
  - web/public/favicon.svg — Pac-Man vector favicon
  - web/public/og-preview.png — 1200x630 arcade social-share card
  - web/public/fonts/PressStart2P-Regular.ttf — self-hosted pixel display face (D-16 zero third-party)
  - web/tests/style.test.mjs — 16 node:test assertions (CSS tokens/selectors/touch targets + favicon root + PNG IHDR)
affects: [07-04-deploy]

# Tech tracking
tech-stack:
  added: [self-hosted Press Start 2P TTF webfont, Pillow OG-card generator (build-time only)]
  patterns:
    - "frontend-design skill drives the visual layer (D-05) — distinctive arcade identity, not a templated dark theme"
    - "Accent yellow (#FFFF00) reserved to exactly 4 uses (wordmark, active tab, rank-1 row, Refresh focus); white=ranks 2-10, gray=everything supporting"
    - "Signature device: dot-leaders rendered as pure-CSS maze pellets (radial-gradient), never literal '.' glyphs — app.js emits an empty .dots span"
    - "Self-hosted pixel font via @font-face TTF (D-16): no Google Fonts request, no preconnect; format() fallback chain to system monospace"
    - "OG/Twitter card is a real raster PNG (not SVG) so unfurlers accept it; generated build-time with Pillow from .venv (no shipped dep)"

key-files:
  created:
    - web/public/styles.css
    - web/public/favicon.svg
    - web/public/og-preview.png
    - web/public/fonts/PressStart2P-Regular.ttf
    - web/tests/style.test.mjs
  modified: []

key-decisions:
  - "Self-hosted the Press Start 2P TTF (118KB, OFL) directly via format(\"truetype\") rather than Google Fonts — honors D-16/T-07-05; fontTools was unavailable so no woff2 conversion, but the @font-face also lists a woff2 src so a future conversion drops in with no CSS change"
  - "Dot-leaders implemented as a repeating radial-gradient of gray pellets in .rank-row .dots — the maze-dot motif IS the leader fill (frontend-design signature), aligning the score column without monospace-padding hacks"
  - "Wordmark/tab font sizes use clamp() (28px/16px upper bounds per UI-SPEC) so the pixel font shrinks on a 320px viewport without horizontal scroll while hitting the spec sizes on a normal phone"
  - "CRT scanlines confined to navy/black gradients (page wash + .board::before) so the arcade-cabinet depth never spends the reserved accent yellow"
  - "OG card built with Pillow using the real downloaded Press Start 2P TTF for an authentic pixel wordmark; 3 sample rank rows show rank-1 yellow + white rows + pellet leaders"

patterns-established:
  - "frontend-design token system: --bg/--panel/--accent/--white/--gray + a 4px-multiple spacing scale (--xs..--2xl) + a 44px --touch exception"
  - "Per-rule touch-target contract: .tab and .refresh each carry min-height:44px, asserted by isolating the rule block in style.test.mjs"
  - "Branding-asset test pattern: parse PNG IHDR bytes (width@16, height@20) in node:test to assert exact 1200x630 without an image lib"

requirements-completed: [WEB-02, WEB-03]

# Metrics
duration: 9min
completed: 2026-06-26
---

# Phase 7 Plan 03: Retro-Arcade Visual Layer + Branding Assets Summary

**Full Pac-Man arcade stylesheet (black void, navy CRT board, yellow reserved to 4 uses, pellet dot-leaders) built through the frontend-design skill, plus a self-hosted Press Start 2P pixel font, a vector Pac-Man favicon, and a real 1200x630 arcade OG share card — all attached to the frozen Plan 01 DOM contract.**

## Performance

- **Duration:** ~9 min
- **Started:** 2026-06-26T05:50:00Z (approx)
- **Completed:** 2026-06-26T05:59:00Z (approx)
- **Tasks:** 2
- **Files modified:** 5 (all created)

## Accomplishments
- `web/public/styles.css` — mobile-first retro-arcade stylesheet honoring every UI-SPEC token. Locked palette as CSS custom props (`--bg:#000000`, `--panel:#10102E`, `--accent:#FFFF00`, `--white:#FFFFFF`, `--gray:#808080`, echoing settings.py COLOR_*). Accent yellow reserved to exactly 4 uses (wordmark glow, active tab, rank-1 row, Refresh focus). `.tab`/`.refresh` carry 44px touch targets; a `@media (min-width:600px)` desktop-centering query layers on top of the phone base.
- **frontend-design skill (D-05) drove the visual identity** — the signature device is the dot-leaders rendered as the maze PELLETS Pac-Man eats (pure-CSS `radial-gradient` in `.rank-row .dots`), with restrained CRT scanlines (navy/black only) on the page and board for cabinet depth, and a neon marquee glow on the wordmark.
- Two-family type system (D-06): self-hosted **Press Start 2P** TTF via `@font-face` (D-16 zero third-party — no Google Fonts request, no preconnect) for the wordmark + tab labels only; a monospace stack for rank/score/body so numbers stay legible and the pellet column aligns.
- `web/public/favicon.svg` — hand-authored Pac-Man disc (`viewBox 0 0 32 32`, `#FFFF00`, wedge mouth + eye, no `<script>`), satisfying the existing `rel="icon"` link.
- `web/public/og-preview.png` — a real **1200x630** arcade share card (black void, navy panel, authentic pixel `PAC-MAN` wordmark, Pac-Man eating a pellet trail, rank-1 yellow + white rows with pellet dot-leaders), satisfying the absolute `og:image`/`twitter:image` url.
- `web/tests/style.test.mjs` — 16 node:test assertions (color tokens, every DOM-hook selector, both type families, `@font-face` self-host, responsive `@media`, per-rule 44px touch targets, pellet dot-leaders, favicon root/viewBox/yellow/no-script, PNG IHDR 1200x630, og:image + favicon reference resolution). 33/33 web tests pass with scaffold.test.mjs.

## Task Commits

Each task was committed atomically:

1. **Task 1: styles.css — retro arcade, mobile-first (frontend-design skill)** - `c74de7c` (feat)
2. **Task 2: Branding assets — Pac-Man favicon.svg + 1200x630 og-preview.png** - `b9885a4` (feat)

## Files Created/Modified
- `web/public/styles.css` - Retro-arcade stylesheet (tokens, mobile-first, 44px touch targets, pellet dot-leaders, scanlines, wordmark glow).
- `web/public/favicon.svg` - Pac-Man vector favicon (yellow disc, wedge mouth, eye).
- `web/public/og-preview.png` - 1200x630 arcade OG/Twitter share card.
- `web/public/fonts/PressStart2P-Regular.ttf` - Self-hosted pixel display face (OFL, 118KB).
- `web/tests/style.test.mjs` - node:test CSS + favicon + PNG assertions (16 tests).

## Decisions Made
- **frontend-design skill was invoked** for the visual build (D-05 hard directive): the brief was grounded in Pac-Man's own world — the maze pellets — and the dot-leaders became the signature element rather than generic decorative dots.
- Self-hosted the Press Start 2P **TTF** (downloaded from the OFL google/fonts repo) via `format("truetype")` instead of Google Fonts. `fontTools` was not installed in `.venv` so no woff2 was produced; the `@font-face` lists a `.woff2` src first anyway, so dropping in a converted woff2 later needs no CSS edit. A self-hosted TTF satisfies T-07-05 (no third-party request) identically to a woff2.
- Wordmark/tab font sizes use `clamp()` with the UI-SPEC values (28px / 16px) as upper bounds so the pixel font never forces horizontal scroll at 320px.
- CRT scanlines kept to navy/black gradients so the cabinet atmosphere never spends the reserved accent yellow.

## Deviations from Plan

None — plan executed exactly as written. (The plan listed `web/public/fonts/` woff2 as the preferred font format; a self-hosted TTF was used because `fontTools` is not installed and adding it is a package-install excluded from auto-fix. This is the plan's own explicitly-allowed fallback path within the self-host directive, not a deviation — D-16 zero-tracking is fully honored.)

## Issues Encountered
- `fontTools` (for TTF→woff2 conversion) is not in `.venv`. Resolved by self-hosting the TTF directly — browsers accept `format("truetype")` in `@font-face`, so the zero-tracking goal (D-16/T-07-05) is met without installing a new dependency (D-01).
- `node --test web/tests/` (directory form) errors on Node 24 ("Cannot find module") — a runner quirk, not a test failure. Running the files explicitly (`scaffold.test.mjs style.test.mjs`) passes 33/33.
- Standard Windows LF→CRLF working-copy warnings on commit; committed blobs store LF — no action needed.

## Known Stubs
None. All four artifacts are real and wired to the frozen index.html references; the OG image is a genuine 1200x630 raster, the favicon a valid scalable SVG, the stylesheet a complete 80+-line arcade theme.

## Threat Flags
None. The plan's threat model is fully satisfied: T-07-05 mitigated by self-hosting the font (no Google request); T-07-01 — favicon.svg contains no `<script>` and the CSS/PNG are static author-controlled assets; T-07-SC — the Pillow generator is a build-time author tool run from `.venv`, no runtime dep is shipped. No new trust boundary or security surface was introduced.

## User Setup Required
None - no external service configuration required this plan. (Live publish is the operator `firebase deploy --only hosting` step, gated for Plan 04.)

## Next Phase Readiness
- The visual layer is complete and attached to the DOM contract; Plan 04 can deploy `web/public` (index.html + app.js + styles.css + favicon.svg + og-preview.png + fonts/) to `pacman-firebase.web.app`.
- WEB-02 (mobile-first arcade style) and the visual half of WEB-03 (boards that look like the in-game boards) are delivered. Final on-phone visual fidelity is confirmed at Plan 04's end-of-phase human-verify checkpoint (WEB-02 is inherently visual).
- No blockers.

## Self-Check: PASSED

All 5 created files verified on disk; both task commits (`c74de7c`, `b9885a4`) verified in git log; 33/33 web tests pass.

---
*Phase: 07-web-leaderboard-page*
*Completed: 2026-06-26*
