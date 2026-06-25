---
phase: 07-web-leaderboard-page
plan: 02
subsystem: web
tags: [esm, fetch, dom, node-test, tdd, leaderboard, xss-escaping, static-site]

# Dependency graph
requires:
  - phase: 07-web-leaderboard-page
    plan: 01
    provides: index.html DOM contract (#board, #tab-all, #tab-week, #subtitle, #refresh) + web/package.json ESM marker
  - phase: 04-server-hardening
    provides: scope-aware get_leaderboard (week|all|last_week) consumed read-only
provides:
  - web/public/app.js — page behavioral core (fetch/cache/render/toggle/refresh) against the Plan 01 DOM contract
  - Exported pure functions (buildLeaderboardUrl, fetchEntries, lastWeekInitials, formatScore, boardMarkup, loadView) reusable by node:test
affects: [07-03-styles-css-assets, 07-04-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "null = offline sentinel: fetchEntries mirrors api_service.get_leaderboard's broad except-to-None, the single value the three-way render branch keys off"
    - "Lazy per-view cache (UNFETCHED Symbol): All Time loads on open (D-08), This Week + last-week subtitle load on first toggle (D-11), Refresh re-pulls only the active slot (D-10)"
    - "HTML-string render with escapeHtml on all API data — no raw initials/score reach innerHTML (T-07-01 XSS defense in depth)"
    - "Self-guarded init(): typeof document === undefined short-circuits so node:test imports never touch fetch"

key-files:
  created:
    - web/public/app.js
    - web/tests/app.test.mjs
  modified: []

key-decisions:
  - "boardMarkup returns an escaped HTML string (not DOM nodes) so the pure render branch is unit-testable in node without a DOM; renderActive writes it via innerHTML (escaped = the mitigation)"
  - "Added exported _resetState() test seam to isolate module-level cache/state between node:test cases (not in plan; test-only, no production surface)"
  - "Dot-leader emitted as an empty <span class=dots> (CSS-rendered in Plan 03), not literal '.' padding — matches UI-SPEC monospace column approach"

patterns-established:
  - "Cross-language logic port: menu.py:run_leaderboard view-state/cache/toggle + api_service.get_leaderboard fetch contract translated verbatim to browser fetch + DOM"

requirements-completed: [WEB-01, WEB-03]

# Metrics
duration: 5min
completed: 2026-06-25
---

# Phase 7 Plan 02: Web Leaderboard app.js Summary

**No-dependency ES module that fetches the live get_leaderboard function and renders the This Week / All Time boards into the Plan 01 DOM contract — lazy per-view cache, verbatim in-game copy, escaped API data, and a Refresh that re-pulls only the active view.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-06-25T21:39:35Z
- **Completed:** 2026-06-25T21:44:30Z
- **Tasks:** 2 (both TDD)
- **Files modified:** 2 (both created)

## Accomplishments
- `web/public/app.js` (226 lines): full behavioral core as a single ESM with zero dependencies and no build step (D-01).
  - **Data layer:** `LEADERBOARD_URL` (hardcoded mirror of `settings.API_LEADERBOARD_URL`, D-03), `buildLeaderboardUrl` (scope-encoded via `URLSearchParams`), `fetchEntries` (returns the entries array or the `null` offline sentinel — never throws, mirroring `api_service.get_leaderboard`), `lastWeekInitials`, and a lazy per-view cache (`views` + `UNFETCHED` Symbol, `loadView`).
  - **Render layer:** `boardMarkup` three-way branch (offline / empty / rank rows) with verbatim in-game copy, rank-1 carrying `rank-row--first`, and `escapeHtml` on all API data; `formatScore` with en-US thousands separators.
  - **Interaction:** `renderActive` (board + tab highlight + last-week subtitle show/hide, D-09), `onTabClick` (lazy toggle, D-11), `onRefresh` (active-view-only re-pull, D-10), and a self-guarded `init()` defaulting to All Time (D-08).
- `web/tests/app.test.mjs`: 15 `node:test` assertions over the pure functions with a stubbed `globalThis.fetch` — URL encoding, fetch success/non-ok/throw/missing-entries, last-week cases, initial state, lazy cache, all three render branches (verbatim strings), rank-1 highlight, XSS escaping, and init() inertness without a document.
- Full web suite green: 32 assertions (17 scaffold + 15 app) passing.

## Task Commits

Each task followed the TDD RED → GREEN gate, committed atomically:

1. **Task 1 RED — failing data-layer tests** - `0882643` (test)
2. **Task 1 GREEN — data layer (url/fetch/cache/last-week)** - `adeb813` (feat)
3. **Task 2 RED — failing render + interaction tests** - `a5c9d19` (test)
4. **Task 2 GREEN — render, toggle, refresh, DOM bootstrap** - `4a2df98` (feat)

## Files Created/Modified
- `web/public/app.js` - The page's behavioral core (data + render + interaction), targeting the Plan 01 DOM hooks.
- `web/tests/app.test.mjs` - node:test coverage of the pure data/render functions with a stubbed fetch.

## Decisions Made
- `boardMarkup` returns an **escaped HTML string** rather than DOM nodes, so the render branch is unit-testable in node without a DOM; `renderActive` applies it via `innerHTML`. Escaping every API value is the T-07-01 mitigation, so innerHTML of an already-escaped string is safe.
- Added a test-only `_resetState()` export to isolate module-level cache/state between `node:test` cases (not specified in the plan; no production surface — pure test seam).
- Dot-leader rendered as an empty `<span class="dots">` for CSS to fill in Plan 03, not literal `.` padding — matches the UI-SPEC monospace column approach.

## Deviations from Plan

None of the auto-fix rules (1-4) triggered. The only additions beyond the literal task text are test ergonomics (the `_resetState()` seam) and the documented HTML-string render choice, both explicitly permitted by the plan ("Return DOM nodes (preferred) or an HTML string built with ESCAPED values"). Plan executed as written.

## Issues Encountered
- `node --test web/tests/` (directory form) does not glob on this Node v24 / Windows setup — it tries to resolve the directory as a module and errors. Resolution: pass explicit file paths (`node --test web/tests/app.test.mjs`), exactly as the plan's `<verify>` block specifies. No code impact.
- Standard Windows LF→CRLF working-copy warnings on commit; committed blobs store LF — no action needed.

## Known Stubs
None. The empty `<span class="dots">` is intentional — it is styled by `styles.css` in Plan 03 (the wave-2 handshake), not a data stub. `favicon.svg` / `styles.css` / `og-preview.png` referenced by index.html remain Plan 03 deliverables.

## Threat Flags
None. No new trust boundary beyond the plan's threat model. T-07-01 (XSS) is actively mitigated: every `initials`/`score` value is HTML-escaped before reaching `innerHTML`; the three render states are static literals. The `LEADERBOARD_URL` constant is the accepted public, non-secret read endpoint (T-07-02). No auto-poll — Refresh is user-initiated only (T-07-03).

## User Setup Required
None. Live behavior (fetch against the deployed function, both views, Refresh on a phone) is confirmed in Plan 04's human-verify checkpoint.

## Next Phase Readiness
- Behavioral core is complete and green against the frozen DOM contract. Plan 03 (`styles.css` + assets) can attach to the same hooks (`.rank-row`, `.rank-row--first`, `.state-msg`, `.dots`, `.tab--active`, `#subtitle[hidden]`) independently.
- Plan 04 deploys hosting and runs the live human-verify. No blockers.

## Self-Check: PASSED

Both created files verified on disk; all four task commits (`0882643`, `adeb813`, `a5c9d19`, `4a2df98`) verified in git log. Full web test suite green (32/32).

---
*Phase: 07-web-leaderboard-page*
*Completed: 2026-06-25*
