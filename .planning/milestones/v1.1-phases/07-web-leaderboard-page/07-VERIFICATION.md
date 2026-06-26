---
phase: 07-web-leaderboard-page
verified: 2026-06-26T00:00:00Z
status: passed
score: 17/17 must-haves verified
overrides_applied: 0
re_verification: false
---

# Phase 7: Web Leaderboard Page — Verification Report

**Phase Goal:** Anyone with the link can view the leaderboard from a phone without launching the game. A public, mobile-first Firebase Hosting page that mirrors the in-game This Week / All Time boards by consuming the existing get_leaderboard API.
**Verified:** 2026-06-26
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| WEB-01 | 01, 02, 04 | Public web page on Firebase Hosting displays leaderboard, fetching from existing API | SATISFIED | `firebase.json` + `.firebaserc` configure hosting; `app.js` fetches `get-leaderboard-991339031546`; live page confirmed HTTP 200 |
| WEB-02 | 03, 04 | Web page is mobile-first / readable on a phone in arcade style matching the game | SATISFIED | `styles.css` mobile-first with `max-width:480px`, 44px touch targets, arcade palette; Playwright-confirmed at 390px phone width |
| WEB-03 | 01, 02, 03, 04 | Web page mirrors in-game boards — both This Week and All Time views | SATISFIED | `onTabClick`/`loadView` implement lazy per-view fetch+cache; `boardMarkup` mirrors `menu.py`; both views confirmed live |

All three phase requirements (WEB-01, WEB-02, WEB-03) are satisfied. No orphaned requirements: REQUIREMENTS.md maps exactly WEB-01/02/03 to Phase 7 and all three are accounted for by Plans 01-04.

---

## Goal Achievement

### ROADMAP Success Criteria

| # | Success Criterion | Status | Evidence |
|---|-------------------|--------|----------|
| SC-1 | A public web page hosted on Firebase Hosting displays the leaderboard, fetching from the existing Cloud Functions API | VERIFIED | `firebase.json` `hosting.public = web/public`; `.firebaserc` default = `pacman-firebase`; `app.js` LEADERBOARD_URL = `https://get-leaderboard-991339031546.asia-southeast1.run.app`; live deploy confirmed |
| SC-2 | The page is mobile-first and readable on a phone, in an arcade style matching the game | VERIFIED | `styles.css` 325 LOC, `--bg:#000000`/`--panel:#10102E`/`--accent:#FFFF00`, mobile-first base with `@media(min-width:600px)`, `.tab`/`.refresh` both `min-height:var(--touch)` (44px); Playwright 390x844 confirmed |
| SC-3 | The page mirrors the in-game boards — both "This Week" and "All Time" views are available | VERIFIED | `app.js` implements lazy-per-view cache (`UNFETCHED` sentinel), `activeView` defaults `"all"` (D-08), `onTabClick` lazy-loads This Week; verbatim copy matches `menu.py` three-way render |

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Page has PAC-MAN wordmark, This Week / All Time tab pair, subtitle slot, board container, Refresh control | VERIFIED | `index.html`: `<h1 class="wordmark">PAC-MAN</h1>`, `nav#tabbar` with `#tab-week`/`#tab-all`, `<p id="subtitle" hidden>`, `<ol id="board">`, `<button id="refresh">Refresh</button>` |
| 2 | Browser tab title reads "PAC-MAN — Leaderboard" (em dash) and Pac-Man favicon is linked | VERIFIED | `<title>PAC-MAN — Leaderboard</title>` (U+2014), `<link rel="icon" type="image/svg+xml" href="favicon.svg">` in index.html |
| 3 | Pasting URL unfurls a rich OG / Twitter card (~1200x630 image) | VERIFIED | All OG tags present: `og:image` absolute URL, `og:image:width=1200`, `og:image:height=630`; Twitter `summary_large_image` card; `og-preview.png` exists on disk (1200x630 per test suite IHDR check) |
| 4 | `firebase deploy --only hosting` targets pacman-firebase project and serves web/public | VERIFIED | `firebase.json`: `hosting.public = "web/public"`, cleanUrls, no rewrites/functions blocks; `.firebaserc`: `projects.default = "pacman-firebase"` |
| 5 | On load the page fetches and shows the All Time board (default D-08) | VERIFIED | `activeView = "all"` module default; `init()` calls `await loadView("all")` then `renderActive()`; `#tab-all` carries `tab--active` in static HTML |
| 6 | Tapping This Week lazily fetches weekly board first time, caches it; last-week subtitle shows/hides correctly | VERIFIED | `onTabClick` checks `views[scope] === UNFETCHED` before fetching; `loadView("week")` also fetches `last_week` once; `renderActive()` shows subtitle only when `activeView === "week"` AND `lastWeekInitials(lastWeek) !== null` |
| 7 | Tapping All Time shows cached all-time board (no refetch) | VERIFIED | `onTabClick` only calls `loadView` when `UNFETCHED`; All Time loaded in `init()` so subsequent tab is served from `views.all` cache |
| 8 | On failed fetch the active view shows "Could not connect to leaderboard."; other cached view still renders | VERIFIED | `fetchEntries` returns `null` on any error/non-ok; `boardMarkup(null, view)` returns `<li class="state-msg">Could not connect to leaderboard.</li>`; `onRefresh` only resets `views[activeView]`, leaves other slot intact |
| 9 | Empty board shows view-correct "Be the first!" line; rank 1 visually distinct from ranks 2-10 | VERIFIED | `EMPTY_TEXT.week = "No scores yet this week. Be the first!"`, `EMPTY_TEXT.all = "No scores yet. Be the first!"`; `boardMarkup` applies `rank-row--first` only to `i === 0`; CSS: `.rank-row--first { color: var(--accent) }` (yellow) |
| 10 | Refresh re-pulls currently active view and re-renders it | VERIFIED | `onRefresh()` sets `views[activeView] = UNFETCHED`, paints Loading, calls `await loadView(activeView)`, then `renderActive()`; `#refresh` wired in `init()` |
| 11 | Full retro arcade: black background, yellow accents, deep-navy panel, pixel-font wordmark/tabs, monospace rank rows | VERIFIED | `styles.css`: `--bg:#000000`, `--panel:#10102E`, `--accent:#FFFF00`; `.wordmark` + `.tab` use `--font-display` (Press Start 2P); `.rank-row` uses `--font-mono`; accent reserved to exactly 4 uses |
| 12 | Mobile-first: tab + Refresh >= 44px touch targets; layout fits narrow viewport without horizontal scroll | VERIFIED | `.tab { min-height: var(--touch) }`, `.refresh { min-height: var(--touch) }`, `--touch: 44px`; base styles phone-first; `.page { max-width: 480px }`; Playwright confirmed no horizontal scroll at 390px |
| 13 | Rank 1 yellow; ranks 2-10 white; CSS dot-leaders (not literal dots) | VERIFIED | `.rank-row--first { color: var(--accent) }`; `.rank-row { color: var(--white) }`; `.rank-row .dots` uses `radial-gradient` (pellets); `boardMarkup` emits `<span class="dots" aria-hidden="true"></span>` with no text content |
| 14 | Pac-Man favicon in browser tab; ~1200x630 arcade OG preview image exists | VERIFIED | `favicon.svg`: valid SVG, `viewBox="0 0 32 32"`, `#FFFF00` fill, wedge mouth, no `<script>`; `og-preview.png` on disk; style.test.mjs IHDR check asserts 1200x630 |
| 15 | Served locally, page renders retro-arcade board, opens All Time, toggles This Week, refreshes, readable at phone width | VERIFIED | Playwright (Chromium 390x844) confirmed all 18/18 checks: wordmark, tab order, live scores (JAP 7,540), This Week empty state, cache, Refresh, 44px targets, title, favicon, offline graceful degrade |
| 16 | Operator publishes with `firebase deploy --only hosting` to existing pacman-firebase project | VERIFIED | `firebase.json` + `.firebaserc` configure this; SUMMARY confirms operator ran deploy; live page confirmed |
| 17 | Live `https://pacman-firebase.web.app` loads both boards via get_leaderboard API; no server/API change | VERIFIED | Playwright 6/6 live checks: HTTP 200, All Time with live scores, This Week toggles; live `get_leaderboard?scope=all` returns HTTP 200; no cloud_functions/ files modified |

**Score: 17/17 truths verified**

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `web/public/index.html` | Static markup + branding head | VERIFIED | 63 lines; all DOM hooks present; title, OG/Twitter meta, favicon, stylesheet, module script |
| `web/public/app.js` | ES module: fetch/cache/render/toggle/refresh | VERIFIED | 226 lines; exports `buildLeaderboardUrl`, `lastWeekInitials`, `boardMarkup`, `formatScore`, `loadView`, `init`; XSS escaping via `escapeHtml`; self-guarded `init()` |
| `web/public/styles.css` | Retro arcade stylesheet, mobile-first | VERIFIED | 325 lines; all 5 color tokens; all DOM-hook selectors; 44px touch targets; @font-face self-hosted; @media responsive; pellet dot-leaders |
| `web/public/favicon.svg` | Pac-Man vector favicon | VERIFIED | Valid SVG, `viewBox="0 0 32 32"`, `#FFFF00` fill, wedge + eye, no `<script>` |
| `web/public/og-preview.png` | ~1200x630 arcade OG preview | VERIFIED | File exists; PNG IHDR width=1200 height=630 per test assertions |
| `web/public/fonts/PressStart2P-Regular.ttf` | Self-hosted pixel font (D-16) | VERIFIED | 118KB TTF; no woff2 on disk (see WR-01 below) |
| `firebase.json` | Hosting config pointing at web/public | VERIFIED | `hosting.public="web/public"`, cleanUrls, 1h asset Cache-Control, no functions/rewrites blocks |
| `.firebaserc` | Default project = pacman-firebase | VERIFIED | `projects.default="pacman-firebase"` |
| `web/package.json` | ESM type marker | VERIFIED | `{"type":"module","private":true}`, no dependencies |
| `web/tests/scaffold.test.mjs` | 17 node:test assertions for markup + hosting config | VERIFIED | All 17 assertions present and green |
| `web/tests/app.test.mjs` | 15 node:test assertions for data/render/interaction | VERIFIED | All 15 assertions present including XSS escaping, cache, init guard |
| `web/tests/style.test.mjs` | 16 node:test assertions for CSS + favicon + PNG | VERIFIED | All 16 assertions present; IHDR dimension check |

---

## Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `web/public/index.html` | `web/public/app.js` | `<script type="module" src="app.js">` | WIRED | Line 33 of index.html |
| `web/public/index.html` | `web/public/styles.css` | `<link rel="stylesheet" href="styles.css">` | WIRED | Line 30 of index.html |
| `firebase.json` | `web/public` | `hosting.public` | WIRED | `"public": "web/public"` |
| `web/public/app.js` | `https://get-leaderboard-991339031546.asia-southeast1.run.app` | `fetch` with `?scope=week\|all\|last_week` | WIRED | `LEADERBOARD_URL` constant, `buildLeaderboardUrl(scope)`, `fetchEntries(scope)` all present and connected |
| `web/public/app.js` | `web/public/index.html` DOM hooks | `getElementById`/`querySelector` on `#board`, `#tab-all`, `#tab-week`, `#subtitle`, `#refresh` | WIRED | `renderActive`, `init`, `paintLoading` all use `getElementById` to target the Plan 01 DOM contract |
| `web/public/styles.css` | `web/public/index.html` DOM hooks | selectors `.wordmark`, `.tab`, `.tab--active`, `.board`, `.rank-row`, `.rank-row--first`, `.dots`, `.state-msg`, `.refresh`, `.subtitle`, `.hint` | WIRED | All 11 required selectors confirmed in styles.css |
| `web/public/index.html` | `web/public/og-preview.png` | `og:image`/`twitter:image` absolute URL | WIRED | Both meta tags reference `https://pacman-firebase.web.app/og-preview.png`; file exists |
| `web/public/index.html` | `web/public/favicon.svg` | `<link rel="icon" href="favicon.svg">` | WIRED | Line 26; file exists |

---

## Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `web/public/app.js` board rendering | `views[activeView]` | `fetchEntries(scope)` → `globalThis.fetch(buildLeaderboardUrl(scope))` → `data.entries` | Yes — fetches live API; returns entries array or null | FLOWING |
| `web/public/app.js` subtitle | `lastWeek` | `fetchEntries("last_week")` on first This Week load | Yes — fetches live `scope=last_week` | FLOWING |
| `web/public/app.js` → `#board` | `boardMarkup(views[activeView], activeView)` | `renderActive()` writes via `board.innerHTML` | Yes — three-way branch with real entries or sentinel states | FLOWING |

All data paths flow from live API fetch through cache to DOM. No static/hardcoded data is rendered except the Loading/offline/empty sentinel strings (which are the correct behavior).

---

## Behavioral Spot-Checks

All behavioral verification was performed by the executor with node:test and Playwright before this verification. Results recorded here for completeness.

| Behavior | Method | Result | Status |
|----------|--------|--------|--------|
| 48/48 node:test assertions (scaffold + app + style) | `node --test web/tests/scaffold.test.mjs web/tests/app.test.mjs web/tests/style.test.mjs` | 48 pass, 0 fail | PASS |
| Page opens on All Time (D-08 default) | Playwright at 390x844 | `#tab-all` carries `tab--active`; All Time board rendered first | PASS |
| This Week toggle lazy-loads, empty state renders verbatim | Playwright | "No scores yet this week. Be the first!" shown; subtitle hidden | PASS |
| Offline graceful degrade | Playwright with network blocked | "Could not connect to leaderboard." shown, no crash | PASS |
| No horizontal scroll at phone width | Playwright 390x844 | Confirmed — mobile-first CSS with `max-width:480px` and box-sizing | PASS |
| Live `https://pacman-firebase.web.app` HTTP 200 | Playwright against live URL | HTTP 200; All Time live scores (JAP 7,540); This Week empty state | PASS |
| Live `get_leaderboard?scope=all` endpoint HTTP 200 | Playwright / curl equivalent | HTTP 200 confirmed | PASS |

---

## Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `web/public/styles.css` | 23 | `url("fonts/PressStart2P-Regular.woff2")` in @font-face — file does not exist on disk (only `.ttf` present) | WARNING (WR-01) | Browser 404s the woff2 request, falls back to `format("truetype")` TTF on line 24. Page renders correctly. Non-fatal cosmetic/perf issue (extra failed HTTP request, slightly slower font load). Already identified in code review. A future `woff2` conversion drops in with no CSS change. |

No `TBD`, `FIXME`, or `XXX` markers found in any web/public or web/tests file.

The `return null` occurrences in `app.js` lines 61 and 65 (`fetchEntries`) are NOT stubs — they are the intentional offline sentinel (`null` = no data / connection failed), which is the exact design of the data contract that flows through to `boardMarkup`'s three-way branch.

---

## Human Verification Completed

Human verification was completed prior to this automated review as part of Plan 04 (Task 1: checkpoint:human-verify). All items below were confirmed:

1. **Local phone-width visual verification** — Playwright (Chromium) at 390x844px: arcade look confirmed (black void, navy panel, yellow wordmark/rank-1, pellet dot-leaders), All Time default, This Week toggle, Refresh, 44px touch targets, no horizontal scroll, title + favicon present, offline graceful degrade.

2. **Live deployment** — Operator ran `firebase deploy --only hosting`; `https://pacman-firebase.web.app` returns HTTP 200 with live API scores on both boards (Playwright 6/6 live checks).

No pending human verification items remain.

---

## Gaps Summary

No gaps. All 17 must-haves are VERIFIED. The only finding is WR-01 (WARNING, non-fatal): the `@font-face` references a `.woff2` file that does not exist on disk, causing a 404 before the browser falls back to the shipped `.ttf`. This does not block any must-have truth and the page renders correctly with the fallback font. The code review already recorded this as a known non-blocking issue.

---

_Verified: 2026-06-26_
_Verifier: Claude (gsd-verifier)_
