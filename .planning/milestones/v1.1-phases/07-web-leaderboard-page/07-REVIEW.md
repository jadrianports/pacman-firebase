---
phase: 07-web-leaderboard-page
reviewed: 2026-06-26T00:00:00Z
depth: standard
files_reviewed: 11
files_reviewed_list:
  - .firebaserc
  - firebase.json
  - web/package.json
  - web/public/app.js
  - web/public/index.html
  - web/public/styles.css
  - web/public/favicon.svg
  - web/tests/app.test.mjs
  - web/tests/scaffold.test.mjs
  - web/tests/style.test.mjs
findings:
  critical: 0
  warning: 2
  info: 3
  total: 5
status: issues_found
---

# Phase 07: Code Review Report

**Reviewed:** 2026-06-26
**Depth:** standard
**Files Reviewed:** 11 (10 source + the 1 added font asset confirmed on disk)
**Status:** issues_found

## Summary

A small, no-build vanilla ES module + CSS leaderboard page served by Firebase
Hosting against a public read-only Cloud Function. The security-critical surfaces
hold up under adversarial review:

- **XSS:** `escapeHtml` covers `& < > " '` and is applied to every untrusted field
  (`initials`, formatted `score`) before it reaches `innerHTML`. Rank text and CSS
  classes are built only from controlled values (`i + 1`, fixed literals). The
  `boardMarkup` hostile-`<img>` test confirms the mitigation. No XSS sink found.
- **Secrets / published scope:** `hosting.public` is `web/public`, which contains
  only `app.js`, `styles.css`, `index.html`, `favicon.svg`, `og-preview.png`, and
  `fonts/`. No credentials, `.env`, or service-account files are inside the
  published root; tests and `package.json` live outside it. The hardcoded
  `LEADERBOARD_URL` is an intentionally public read endpoint (T-07-02 accepted).
- **Fetch error handling:** `fetchEntries` wraps fetch + json + shape-check in a
  single try/catch that collapses every failure to the `null` offline sentinel —
  it never throws. `init()` is import-guarded by `typeof document === "undefined"`
  so node:test imports stay inert. ESM exports/imports are consistent.

No Critical issues. The defects below are a broken/missing font asset reference
(404 on every load) and a missing-defense-in-depth header gap, plus minor
robustness/a11y notes.

## Warnings

### WR-01: styles.css references a `woff2` font that does not exist on disk (404 on every page load)

**File:** `web/public/styles.css:21-28` (and `firebase.json:12`)
**Issue:** The `@font-face` `src` lists `fonts/PressStart2P-Regular.woff2` as the
first source, but only `PressStart2P-Regular.ttf` exists in `web/public/fonts/`
(confirmed: the woff2 is absent). Every browser load will issue a request for the
woff2, receive a 404, then fall back to the `.ttf`. The font still renders, so the
style tests (which assert `ttf || woff2`) pass and mask the gap — but the published
site makes a guaranteed failing request on each visit. Compounding this, the
`firebase.json` cache header pattern is `**/*.@(js|css|svg|png|woff2)`: it targets
the nonexistent `woff2` and does **not** match `.ttf`, so the 118 KB font that is
actually served has no `Cache-Control` at all.
**Fix:** Either generate and commit the woff2 (preferred — smaller, and aligns the
CSS + cache pattern), or drop the woff2 from the `src` list and add `ttf` to the
header pattern:
```css
@font-face {
  font-family: "Press Start 2P";
  src: url("fonts/PressStart2P-Regular.ttf") format("truetype");
  ...
}
```
```json
"source": "**/*.@(js|css|svg|png|ttf|woff2)"
```

### WR-02: Hosting config sets no security headers for a page that injects remote API data into the DOM

**File:** `firebase.json:10-20`
**Issue:** The `headers` block configures only `Cache-Control`. The page renders
data fetched from a third-party Cloud Run origin into `innerHTML`. Escaping is the
primary defense and is correct, but there is no second layer: no
`Content-Security-Policy`, no `X-Content-Type-Options: nosniff`, no
`Referrer-Policy`. A CSP (e.g. restricting `script-src 'self'` and limiting
`connect-src` to the leaderboard origin) would neutralize any future regression in
the escaping path and is cheap to add given a `headers` block already exists.
**Fix:** Add a document-scoped header rule, e.g.:
```json
{
  "source": "**/*.html",
  "headers": [
    { "key": "Content-Security-Policy",
      "value": "default-src 'none'; script-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; connect-src https://get-leaderboard-991339031546.asia-southeast1.run.app" },
    { "key": "X-Content-Type-Options", "value": "nosniff" },
    { "key": "Referrer-Policy", "value": "no-referrer" }
  ]
}
```

## Info

### IN-01: Malformed API rows render the literal string "undefined" / "0"

**File:** `web/public/app.js:136-137`, `114-117`
**Issue:** For an entry missing fields, `escapeHtml(entry?.initials)` yields
`"undefined"` and `formatScore(entry?.score)` yields `"undefined"` (NaN→`String`)
or `"0"` for a `null` score (`Number(null) === 0`). The server enforces shape, so
this is a robustness/defensive gap rather than a live bug, but a malformed payload
would print literal `undefined` cells instead of degrading cleanly.
**Fix:** Guard the fields, e.g. `escapeHtml(entry?.initials ?? "—")` and have
`formatScore` treat `null`/`undefined` as `"—"` rather than `0`/`"undefined"`.

### IN-02: `#tab-week` lacks an initial `aria-selected` in the static HTML

**File:** `web/public/index.html:43-44`
**Issue:** `#tab-all` ships with `aria-selected="true"` but `#tab-week` has no
`aria-selected` attribute until `renderActive()` runs. Before app.js executes (or
if the module fails to load), the tablist exposes an incomplete selection state to
assistive tech. `renderActive()` fixes both on first paint, so this only affects
the pre-JS / failed-load window.
**Fix:** Add `aria-selected="false"` to the `#tab-week` button in the static markup.

### IN-03: Caching of `app.js` with `max-age=3600` and no cache-busting can serve stale logic

**File:** `firebase.json:12-18`
**Issue:** `app.js` is cached for an hour with no content hash in the filename, so a
logic fix can take up to 60 minutes to reach returning visitors. `index.html` is
not matched by the pattern so it stays fresh, but it references `app.js` by a
stable name. This is acceptable for a low-churn static page; noted for awareness.
**Fix:** If faster propagation matters, lower `max-age` for `js`/`css` or adopt
hashed filenames; otherwise document the 1-hour propagation window as intentional.

---

_Reviewed: 2026-06-26_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
