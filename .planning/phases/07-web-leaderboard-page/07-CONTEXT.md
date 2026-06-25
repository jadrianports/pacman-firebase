# Phase 7: Web Leaderboard Page - Context

**Gathered:** 2026-06-26
**Status:** Ready for planning

<domain>
## Phase Boundary

A public, **mobile-first Firebase Hosting page** that is a **pure consumer** of the
already-shipped `get_leaderboard` Cloud Function and **mirrors the in-game This Week / All Time
boards** in full retro arcade style (WEB-01/02/03). Concretely, this phase delivers:

- A static web page hosted on **Firebase Hosting** that fetches the existing API directly from the
  browser (CORS `*` already enabled server-side) — WEB-01.
- **Mobile-first, full retro arcade** look matching the game — WEB-02.
- **This Week / All Time** views mirroring the in-game boards, plus the **"Last week: BOB"**
  champion subtitle on This Week — WEB-03.

**In scope:** a new `web/` folder in this repo holding plain static HTML/CSS/JS + `firebase.json`
+ Open Graph/preview assets + favicon; client-side fetch of `get_leaderboard` (`scope=week|all|last_week`);
the tab toggle, per-view lazy fetch + cache, refresh control, and loading/offline/empty states;
a static OG preview image; Pac-Man branding (tab title, favicon, on-page header).

**Out of scope (other phases / milestones):** any **server / API change** — the API is finished
(Phases 4 + 6); score **submission from the web** (read-only page); accounts/auth/comments;
self-row highlighting (`machine_id` is stripped from responses — the page cannot identify "you",
same constraint as Phase 6 D-19); a custom domain (default Firebase domain this phase); analytics
/ tracking; the browser/pygbag game build (the separate "Easier to Share" milestone).
</domain>

<decisions>
## Implementation Decisions

### Tech Stack & Build (WEB-01)

- **D-01 (Plain static HTML/CSS/JS — no framework, no build step):** One `index.html` + a small JS
  file + CSS, no npm/bundler/framework. Fetches the API directly via browser `fetch`. Matches the
  project's stdlib-only / no-new-deps ethos and is trivial to deploy on Firebase Hosting for a single
  read-only page. (Vite/vanilla and React/Svelte both rejected as over-tooled for one static board.)
- **D-02 (Code lives in a new `web/` folder in this repo):** Keep the page (e.g. `web/public/` +
  `web/firebase.json`, or root `firebase.json` with `public: web/`) alongside the game. Single git
  history, one source of truth, easy deploy. (Separate repo rejected.)
- **D-03 (Firebase Hosting in the same Firebase/GCP project as the backend):** Host in the existing
  project that already runs the Cloud Functions/Firestore (`pacman-991339031546`). The
  `get_leaderboard` URL is hardcoded as a JS constant (mirror of `settings.API_LEADERBOARD_URL`).
  **Deploy is a manual operator step** (`firebase deploy --only hosting`) — same pattern as the
  Phase 4/6 manual function redeploys; the in-repo gate is the page + its config, live publish
  depends on the operator running it.

### Visual Style (WEB-02)

- **D-04 (Full retro arcade):** Black background, Pac-Man yellow accents, retro/pixel typography,
  chunky rank list, arcade chrome. Lean hard into matching the game (not "arcade-inspired but clean").
- **D-05 (Drive the visual design with the `frontend-design` skill — user directive):** The UI work
  must invoke the **`frontend-design` skill** for a distinctive, intentional arcade design rather
  than templated defaults. This is an explicit user instruction — the planner/executor (or a
  `/gsd-ui-phase` pass) MUST route the visual build through `frontend-design`. ROADMAP marks this
  phase **UI hint: yes**.
- **D-06 (One pixel webfont + system fallback):** Load a single retro font (e.g. Google Fonts
  "Press Start 2P") for headers/titles, with a **system-font fallback for body/score text** so small
  numbers stay readable on a phone. (System-only rejected — loses the arcade typography.)

### Board Layout & Views (WEB-03)

- **D-07 (Tab toggle / segmented control):** A `This Week | All Time` tab pair at the top; tap to
  switch, only one board visible at a time. Mirrors the in-game LEFT/RIGHT toggle (Phase 6 D-03).
  Cleanest on mobile. (Stacked-both-boards rejected — long phone scroll, less arcade-screen feel.)
- **D-08 (Default view on load = All Time — deliberate divergence from in-game):** The web page
  **opens on All Time** (the hall of fame), unlike the in-game board which defaults to This Week
  (Phase 6 D-02). This is an intentional, locked choice for the web context — lead with the
  all-time greats; the visitor taps to This Week for the live competition.
- **D-09 ("Last week: BOB" champion subtitle on This Week):** A small champion line under the header,
  shown **only on the This Week view**, fetched via `scope=last_week` and taking `entries[0]`.
  Exactly mirrors the in-game board (Phase 6 D-04). **Hidden if last week has no champion** (Phase 6
  D-16). (A full last-week board view was considered — see Deferred — but this phase mirrors the
  in-game board, so only the champion subtitle ships.)

### Refresh & Data Freshness

- **D-10 (Fetch on load + explicit Refresh control):** Fetch when the page opens and a visible
  "Refresh" control to re-pull the active view on demand. No auto-poll (wasteful, battery/API drain),
  no reload-only (feels stale). Refresh re-pulls the currently active view.
- **D-11 (Lazy per view + cache — mirror in-game D-14):** Fetch a board the **first time its tab is
  shown**, cache it for the page visit; the All Time default loads on open, This Week (+ its
  last-week subtitle) loads on first toggle. Refresh re-pulls the active view. Mirrors the in-game
  lazy-per-view caching (Phase 6 D-14). (Fetch-both-up-front rejected — extra initial calls.)

### Loading / Offline / Empty States

- **D-12 (Mirror in-game wording):** On fetch failure show **"Could not connect to leaderboard."**;
  empty This Week shows **"No scores yet this week. Be the first!"** and empty All Time shows
  **"No scores yet. Be the first!"** (Phase 6 D-17). Each view degrades independently — a failed
  scope shows the offline line while the other view still works (mirror Phase 6 D-15). The last-week
  subtitle simply hides if its read fails (Phase 6 D-16).

### Sharing & Discovery

- **D-13 (Open Graph + preview image):** Add Open Graph + Twitter Card meta (title, description,
  image) so pasting the link into iMessage/WhatsApp/Discord unfurls a rich arcade card. Requires
  **one static preview image (~1200×630)**. Serves the "something friends actually share" goal.
- **D-14 (Full Pac-Man branding):** Tab title like **"PAC-MAN — Leaderboard"**, a **Pac-Man
  favicon**, and an on-page arcade-yellow **"PAC-MAN"** title over the boards. Makes the tab and the
  shared card instantly recognizable. (Branding specifics are part of the `frontend-design` pass, D-05.)
- **D-15 (Default Firebase domain — no custom domain this phase):** Ship on
  `<project>.web.app` / `.firebaseapp.com`. Zero DNS setup, free, works immediately. A custom domain
  can be added later without rework (see Deferred).
- **D-16 (No analytics / zero tracking):** No analytics scripts, no cookies, nothing to consent to.
  Privacy-friendly, simplest. A view counter was considered and declined.

### Claude's Discretion (handed to research/planning — design these, don't re-ask the user)

- Exact `web/` directory layout and whether `firebase.json` sits at repo root or under `web/`.
- The retro font choice (D-06 names "Press Start 2P" as an example — pick a suitable pixel font) and
  the system-fallback stack for body/score text.
- Concrete arcade visuals, layout proportions, tab-control styling, colors beyond the locked
  black + Pac-Man-yellow direction — **routed through the `frontend-design` skill** (D-05) and/or
  `/gsd-ui-phase`.
- The static OG preview image design (D-13) and the favicon artwork (D-14).
- How the per-view cache + active-view state is held in the page's JS (D-11), and the exact
  `fetch` wiring / scope query-param construction against `get_leaderboard`.
- Score number formatting (e.g. thousands separators) and rank rendering details.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap (authoritative scope)
- `.planning/ROADMAP.md` § "Phase 7: Web Leaderboard Page" — goal, the 3 success criteria, and the
  "pure consumer of the finished API — intentionally last so it mirrors the boards exactly" note.
- `.planning/REQUIREMENTS.md` § "Web Leaderboard" (WEB-01, WEB-02, WEB-03) — the exact requirement
  wording each decision maps to.

### The API this phase consumes (READ-ONLY — no changes this phase)
- `cloud_functions/get_leaderboard/main.py` — the scope-aware reader the page fetches:
  `scope=week|all|last_week`, default `week`, tolerant parse (unknown → `week`, never 400), top-10,
  **`machine_id` stripped from all responses**, returns `{ "entries": [ { "initials", "score" } ] }`.
  **The web page only calls this; it does NOT modify it.**
- `.planning/codebase/INTEGRATIONS.md` — endpoint URLs, request/response contracts, CORS (`*`),
  and the "Auth: None / scores are public-read" shape the browser relies on.
- `settings.py` — `API_LEADERBOARD_URL` (`https://get-leaderboard-991339031546.asia-southeast1.run.app`)
  is the source-of-truth URL to mirror as a JS constant (D-03).

### The in-game boards being mirrored (parity source)
- `.planning/phases/06-in-game-weekly-boards-got-passed-banner/06-CONTEXT.md` — **D-02** (in-game
  default = This Week; web deliberately diverges to All Time, D-08), **D-03** (This Week/All Time
  toggle being mirrored, D-07), **D-04/D-16** (last-week champion subtitle + hide-when-none, D-09),
  **D-14** (lazy-per-view + cache, mirrored in D-11), **D-15** (per-view degrade), **D-17** (empty
  wording mirrored in D-12), **D-19** (no self-row highlight — `machine_id` stripped, applies here too).
- `menu.py` — `run_leaderboard` is the in-game board whose wording/states/styling the web page
  mirrors (loading, "Could not connect to leaderboard.", empty-state lines, rank-1-yellow styling).

### Design specs — STALE baseline (dated 2026-03-26, pre-HMAC / pre-weekly)
- `docs/superpowers/specs/2026-03-26-leaderboard-design.md` — original Firestore/leaderboard shape;
  predates weekly buckets and the HTTP-proxy API. Context only — the live contract is the
  `get_leaderboard` function above, not this doc.
- `docs/superpowers/specs/2026-03-26-api-refactor-exe-design.md` — Cloud-Functions-HTTP-proxy +
  Firebase project baseline. Context only.

### Codebase maps
- `.planning/codebase/ARCHITECTURE.md` — game state machine + leaderboard architecture.
- `.planning/codebase/INTEGRATIONS.md` — how the client talks to the Cloud Functions (the same API
  the web page now consumes from the browser).

### Tooling the visual build MUST use
- **`frontend-design` skill** (D-05) — user directive: drive the arcade visual design through this
  skill, not templated defaults. (Optionally formalized via `/gsd-ui-phase 7`.)
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`get_leaderboard` Cloud Function (live)** — already serves `scope=week|all|last_week`, top-10,
  `machine_id`-stripped, with `Access-Control-Allow-Origin: *`. The browser can fetch it directly —
  no proxy, no server work. This is the single data source for the whole page.
- **In-game board wording/states (`menu.py:run_leaderboard`)** — the exact loading / "Could not
  connect" / empty-state strings and rank-1-yellow styling to mirror for parity (D-12).
- **`settings.py` API URLs + colors** — `API_LEADERBOARD_URL` and the game's color palette
  (`COLOR_YELLOW/WHITE/...`) are the reference values to echo in the web page's JS/CSS.

### Established Patterns
- **No-new-deps, stdlib-only ethos** — the project deliberately avoids runtime deps (client uses
  stdlib `urllib`). The web page mirrors this with plain HTML/CSS/JS and no build pipeline (D-01).
- **Cloud Functions as the only data source** — clients (game and now web) have no Firestore access;
  everything comes through the HTTP API. The web page is one more consumer.
- **Graceful degrade is the house style** — offline/empty never errors hard; mirror the in-game
  no-error tone (D-12).
- **Manual operator deploy for backend/hosting** — Phases 4/6 redeployed functions by hand; Firebase
  Hosting publish is the analogous manual step here (D-03).

### Integration Points
- **Browser → `get_leaderboard`** — `fetch(\`${LEADERBOARD_URL}?scope=...\`)` per view; parse
  `entries`, render rank/initials/score. The only network seam in the page.
- **`web/` ↔ Firebase Hosting** — `firebase.json` (hosting config) + a `public`/static dir; deployed
  to the existing Firebase project (D-03), served on the default `.web.app` domain (D-15).
- **OG/branding assets** — static preview image + favicon referenced from `index.html` meta/head
  (D-13/D-14).
</code_context>

<specifics>
## Specific Ideas

- **The web page deliberately leads with All Time, not This Week (D-08)** — unlike every in-game
  default. The user wants the public page to open on the hall of fame; the live weekly fight is one
  tap away. This is a conscious divergence, not an oversight — downstream agents must not "fix" it to
  match the game default.
- **`frontend-design` is a hard directive, not a suggestion (D-05)** — the user explicitly asked for
  the skill to drive the visuals. The arcade look should be distinctive and intentional, not a
  generic dark-theme template.
- **Share-first framing** — OG preview card (D-13) + recognizable Pac-Man branding (D-14) exist
  because this is a link friends paste to each other. It should look like *something* the moment it
  unfurls, before anyone even taps it.
- **Right altitude for a friends board** — default domain (D-15), no analytics (D-16), read-only,
  no auth. Same "good enough, low-ceremony" philosophy that runs through the whole milestone.
</specifics>

<deferred>
## Deferred Ideas

- **Full last-week leaderboard view** — `scope=last_week` returns the whole top-10, but this phase
  mirrors the in-game board, which only surfaces the champion (D-09). A full "last week's board" tab
  is a natural future addition (already flagged in Phase 6's deferred list) — designed-for, not built
  here.
- **Custom domain** — ship on the default Firebase domain now (D-15); a memorable custom domain can
  be added later without rework (operator DNS step).
- **Analytics / view counter** — declined for now (D-16); could add a privacy-friendly counter later
  if there's appetite to know reach.
- **Score submission from the web / accounts / live auto-refresh** — out of scope; the page is a
  read-only mirror. Auto-poll was explicitly rejected (D-10).

None of these are scope creep — discussion stayed within the web-leaderboard-page boundary.
</deferred>

---

*Phase: 7-web-leaderboard-page*
*Context gathered: 2026-06-26*
