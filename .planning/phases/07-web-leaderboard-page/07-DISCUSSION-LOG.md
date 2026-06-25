# Phase 7: Web Leaderboard Page - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-26
**Phase:** 7-web-leaderboard-page
**Areas discussed:** Tech stack & build, Arcade visual style, Board layout & views, Refresh & data states, Link preview (Open Graph), URL / custom domain, Analytics, Branding & favicon

---

## Tech Stack & Build

| Option | Description | Selected |
|--------|-------------|----------|
| Plain static HTML/CSS/JS | One index.html + small JS + CSS, no framework/build/npm; fetches API directly | ✓ |
| Vite + vanilla JS | Dev server + bundler, no framework, adds node toolchain | |
| Framework (React/Svelte) | Component model + build pipeline; overkill for one static board | |

**User's choice:** Plain static HTML/CSS/JS
**Notes:** Matches the project's stdlib-only / no-new-deps ethos for a single read-only page.

| Option | Description | Selected |
|--------|-------------|----------|
| New /web folder in this repo | Page + firebase.json alongside the game; single history, easy deploy | ✓ |
| Separate repo | Isolated; splits history, adds coordination overhead | |

**User's choice:** New /web folder in this repo
**Notes:** Firebase Hosting captured as a manual operator deploy step (mirrors Phase 4/6 redeploys).

---

## Arcade Visual Style

| Option | Description | Selected |
|--------|-------------|----------|
| Full retro arcade | Black bg, Pac-Man yellow, pixel font, chunky list, maze motifs | ✓ |
| Arcade-inspired but clean | Dark theme + yellow + readable web font, lighter chrome | |
| Let /gsd-ui-phase decide | Lock direction only, defer to UI-SPEC | |

**User's choice:** Full retro arcade — **+ explicit instruction to invoke the `frontend-design` skill**
**Notes:** The user appended "invoke /frontend-design skill" — locked as D-05, a hard directive that the visual build route through `frontend-design`, not templated defaults.

| Option | Description | Selected |
|--------|-------------|----------|
| One pixel webfont + system fallback | Retro font for headers, system fallback for readable score text | ✓ |
| System fonts only | No external font request; fastest, but loses arcade typography | |

**User's choice:** One pixel webfont + system fallback

---

## Board Layout & Views

| Option | Description | Selected |
|--------|-------------|----------|
| Tab toggle (segmented) | This Week \| All Time tabs, one board visible; mirrors in-game LEFT/RIGHT | ✓ |
| Both boards stacked | Scroll to see both; long phone scroll | |
| Let /gsd-ui-phase decide | Lock reachability, defer control | |

**User's choice:** Tab toggle (segmented)

| Option | Description | Selected |
|--------|-------------|----------|
| This Week | Opens on the live weekly board (matches in-game default) | |
| All Time | Opens on the all-time hall of fame | ✓ |

**User's choice:** All Time
**Notes:** Deliberate divergence from the in-game This-Week default (D-08) — the public page leads with the hall of fame.

| Option | Description | Selected |
|--------|-------------|----------|
| Champion subtitle on This Week | "Last week: BOB" line via scope=last_week; mirrors in-game | ✓ |
| Full last-week board | A third view of last week's whole top-10 | |
| Skip last week | This Week + All Time only | |

**User's choice:** Champion subtitle on This Week
**Notes:** Full last-week board noted as a deferred future addition.

---

## Refresh & Data States

| Option | Description | Selected |
|--------|-------------|----------|
| Fetch on load + refresh button | Loads on open + on-demand Refresh control | ✓ |
| Fetch on load only | Reload page to update; can feel stale | |
| Auto-poll every N seconds | "Live" feel but wasteful | |

**User's choice:** Fetch on load + refresh button

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy per view + cache | Fetch a board on first show, cache for visit; mirrors in-game D-14 | ✓ |
| Fetch both up front | Load all views on open; instant switches | |

**User's choice:** Lazy per view + cache

| Option | Description | Selected |
|--------|-------------|----------|
| Mirror in-game wording | "Could not connect…" / "No scores yet this week. Be the first!" | ✓ |
| Web-specific copy | Fresh web-tailored messages | |

**User's choice:** Mirror in-game wording

---

## Link Preview (Open Graph)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — OG tags + preview image | OG/Twitter meta + ~1200×630 arcade preview card | ✓ |
| OG text only, no image | Title + description, no image asset | |
| Skip it | No preview metadata | |

**User's choice:** Yes — OG tags + preview image

---

## Branding & Favicon

| Option | Description | Selected |
|--------|-------------|----------|
| Full Pac-Man branding | "PAC-MAN — Leaderboard" tab title, Pac-Man favicon, arcade-yellow on-page title | ✓ |
| Minimal | Plain "Leaderboard" title, default favicon | |
| Let frontend-design decide | Fold branding into the frontend-design pass | |

**User's choice:** Full Pac-Man branding

---

## URL / Custom Domain

| Option | Description | Selected |
|--------|-------------|----------|
| Default Firebase domain | <project>.web.app, zero DNS setup | ✓ |
| Custom domain | Memorable, adds DNS verification step | |
| Default now, custom later | Default this phase, note custom as follow-up | |

**User's choice:** Default Firebase domain
**Notes:** Custom domain noted as a deferred follow-up (addable later without rework).

---

## Analytics

| Option | Description | Selected |
|--------|-------------|----------|
| No tracking | Zero analytics/cookies; privacy-friendly | ✓ |
| Lightweight counter | Privacy-friendly view counter | |

**User's choice:** No tracking
**Notes:** Declined; could revisit a privacy-friendly counter later.

---

## Claude's Discretion

- Exact `web/` directory layout and `firebase.json` placement.
- Retro font choice + system-fallback stack (D-06).
- Concrete arcade visuals/colors/tab styling — routed through `frontend-design` (D-05) / `/gsd-ui-phase`.
- OG preview image design + favicon artwork.
- Per-view cache/state handling in JS + scope query-param wiring.
- Score number formatting and rank rendering.

## Deferred Ideas

- Full last-week leaderboard view (whole top-10) — future addition.
- Custom domain — addable later without rework.
- Analytics / view counter — declined for now.
- Web score submission / accounts / live auto-refresh — out of scope (read-only mirror).
