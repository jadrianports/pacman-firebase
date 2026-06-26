# Phase 6: In-Game Weekly Boards & Got-Passed Banner - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Surface the Phase-4 scope-aware leaderboard API **inside the game**, as a pure client/consumer
feature riding on the Phase-5 `%LOCALAPPDATA%\PacMan\` storage seam. Concretely, this phase delivers:

- **A This Week / All Time toggle** on the in-game Leaderboard screen (BOARD-03).
- **Last week's champion** shown on the weekly board (BOARD-04, e.g. "Last week: BOB").
- **A launch banner** naming whoever passed your score since you last viewed the board (RIVAL-01).
- **Graceful degrade** on all three: offline or first launch → no error, no banner, fully playable (SC-4).

**In scope:** the in-game board UI (`menu.py`), the client API service gaining a `scope` parameter
(`api_service.py`), the launch banner + its local "last-viewed" marker (`main.py`, a new unsigned
marker file under `%LOCALAPPDATA%\PacMan\` via `paths.user_data_path`), and **one small server-side
read-path addition** — a `scope=last_week` branch in `get_leaderboard` (the data is already retained;
see D-01) plus its validator tests.

**Out of scope (other phases / milestones):** the web leaderboard page (Phase 7 — though it can reuse
`scope=last_week`); any new server **data model** (week buckets, retention, HMAC, permanent initials
are all done in Phase 4 — this phase only *reads*); any ghost-AI decision-behavior change (locked
spec — CI golden net stays green); friend groups / season-history archives (deferred); local-file
encryption beyond the Phase-5 obfuscation+HMAC.
</domain>

<decisions>
## Implementation Decisions

### Last-Week Champion Source (BOARD-04)

- **D-01 (Add `scope=last_week` to `get_leaderboard`):** The `weekly` collection already retains last
  week's bucket (Phase 4 **D-09**) and `leaderboard_crypto.previous_week_id()` already exists in both
  function copies — only the **read path** is missing. Add a third scope value that queries
  `week_id == previous_week_id(current_week_id())`, returning the **same `{entries:[{initials,score}]}`
  top-10 shape** as the other scopes; the client takes `entries[0]` for "Last week: BOB". This is a
  read-path addition, **not** a data-model change, so the roadmap's "no new server data model" holds.
  *This is the one place Phase 6 touches the server* — `cloud_functions/get_leaderboard/main.py` and
  `tests/test_get_leaderboard.py`. The composite index (`week_id ASC, score DESC`) created in Phase 4
  already covers this query. Tolerant scope parsing stays (unknown scope → `week`, never a 400).

### Board Toggle & Layout (BOARD-03)

- **D-02 (Extend the existing screen; default This Week):** Build on `menu.py:run_leaderboard` (reached
  from the main-menu "Leaderboard" option) rather than a new screen. It **opens on This Week** — the
  competitive focus, the server's default scope, and the board the banner is about.
- **D-03 (LEFT/RIGHT toggle + tab indicator):** LEFT/RIGHT arrows flip This Week ⇄ All Time, with a
  visible `< This Week | All Time >` indicator showing the active tab. ESC/ENTER still exits (no
  conflict — those are the only bindings the screen currently uses).
- **D-04 ("Last week: BOB" subtitle, This Week only):** Render the champion as a small subtitle just
  under the LEADERBOARD header, shown **only while the This Week board is active** (hidden on All Time,
  where last-week is irrelevant).

### Got-Passed Banner Semantics (RIVAL-01)

- **D-05 (Watches the This Week board):** The banner compares your **this-week best** against the This
  Week board. If you have **no score this week**, there's nothing to be passed on → no banner.
- **D-06 (Name all new passers, capped):** List every *new* passer's initials but cap the visible names
  to keep the banner one readable line (e.g. `JIM, BOB, ACE +2 more`). Initials are 3 chars, so a few
  fit; the cap count is Claude's discretion.
- **D-07 (Reset only on opening the board):** "Since you last looked" means the baseline updates **only
  when the player opens the in-game Leaderboard** — faithful to RIVAL-01's exact wording. So if you
  launch, see the banner, but never open the board, the next launch still shows it (refreshed with
  anyone newly ahead). It does **not** clear merely by launching.

### Banner Presentation (RIVAL-01)

- **D-08 (Line on the main menu):** The banner is a **prominent line on the existing main menu** (e.g.
  under the PAC-MAN title) — non-blocking, no new screen, reuses `menu.py:run_main_menu`. The player
  sees it the moment the menu appears and can act immediately.
- **D-09 (Quick blocking launch fetch, short timeout):** The banner needs the This Week board fetched
  at launch. Do this **once at startup with a SHORT timeout** (a couple of seconds, NOT
  `api_service`'s default 10s); if it's slow or offline, **silently skip the banner** and go straight
  to the menu. No threading — the offline path is already a no-banner no-op (SC-4). The short timeout
  value is Claude's discretion.
- **D-10 (Clears when you open the board):** One coherent rule — opening the in-game Leaderboard both
  **clears the banner on screen** *and* **resets the cross-launch baseline** (D-07). If you start a
  game without opening the board, the banner is still there on return and next launch. It's a single
  line, not a modal.

### Banner Accuracy Mechanics

- **D-11 (Track your own best locally — don't locate yourself on the board):** `machine_id` is stripped
  from all API responses (Phase 4 **D-10**), and your score may be outside the top-10, so the client
  must **not** try to find its own row on the board. Instead **persist your own best score locally** —
  the max you've submitted this week — stamped with `week_id` so it resets on a new week. A "passer" is
  any board entry above this tracked best; entries above your best are by definition not you.
- **D-12 (Detect new passers by initials):** Store the set of **initials that were above your best at
  last view**. A new passer is initials now above you that **weren't** in that set. An already-ahead
  player who merely bumps their score does **not** re-trigger. A rare same-initials collision can
  suppress one passer — accepted as harmless (Phase 5 **D-03**: "a wrong got-passed banner is
  harmless").

### Marker Storage

- **D-13 (Separate unsigned marker file, Phase-5 seam):** The "last-viewed" state lives in a **single
  separate, UNSIGNED file** in `%LOCALAPPDATA%\PacMan\` (Phase 5 **D-03** designed this seam), written
  via `paths.user_data_path(...)`. It holds the marker state: `week_id` + your tracked this-week best
  (D-11) + the initials-above-you set (D-12). It is **not** part of the signed identity blob and is
  **not** tamper-protected — re-signing on every board view would be pointless friction and a wrong
  banner is harmless. A `week_id` mismatch on load re-baselines silently (new week → no stale passers).

### Board Fetch Strategy

- **D-14 (Lazy per view + `scope` param):** Add a `scope` argument to `api_service.get_leaderboard`. On
  opening the board, fetch **only This Week** (plus its last-week subtitle via `scope=last_week`,
  best-effort); fetch **All Time the first time** the player toggles to it; **cache each** for the rest
  of the screen visit. Snappy default open, no wasted calls.
- **D-15 (Degrade per view):** Each view handles its own failure — a failed scope shows the existing
  "Could not connect to leaderboard." line while the other view still works if its fetch succeeded.
  The last-week subtitle simply **hides** if its read fails. Mirrors the current offline pattern
  (`menu.py:140`).

### Empty / Cold-Start States

- **D-16 (No last-week champion → hide subtitle):** When last week has no champion (brand-new install,
  or the first week the game ships), render **nothing** where the subtitle would go — no placeholder,
  no dash. The line appears once last week has a champion.
- **D-17 (Empty This Week wording):** When the This Week board has no scores yet, show **"No scores yet
  this week. Be the first!"**. All Time keeps the existing **"No scores yet. Be the first!"**.
- **D-18 (Cold-start / offline → no banner, no error):** First launch (no marker), offline at launch,
  or no this-week score → **no banner, no error**, straight to the menu (SC-4, locked).

### Board Styling

- **D-19 (No self-highlight; visuals to UI-SPEC):** Do **not** attempt to highlight "your" row — with
  `machine_id` stripped (D-10), matching on initials+score would mis-highlight a same-initials rival or
  miss you entirely. Keep the current styling (rank 1 yellow, the rest white). The tab indicator's look
  and overall board visuals can route to `/gsd-ui-phase` (ROADMAP marks this phase **UI hint: yes**).

### Claude's Discretion (handed to research/planning — design these, don't re-ask the user)

- **Marker file** name + on-disk format (plain JSON is fine — it's unsigned by design, D-13).
- **Short launch-fetch timeout** value (D-09) — pick something snappy (~1–3s) that still works on a
  normal connection.
- **Banner color / exact placement** on the menu (D-08) and the **name cap count** (D-06) — subject to
  `/gsd-ui-phase` if run.
- **Exact `scope` query-param wiring** in `api_service.get_leaderboard` (D-14) and how the three
  per-view caches are held within the board screen's loop.
- **The initials-above-you set representation** (D-12) — a simple set/list of initials strings;
  decide tie-handling for duplicate initials within the set.
- **last-week subtitle fetch coupling** — it's a *separate* `scope=last_week` call (D-01/D-14);
  whether it's issued alongside the week fetch on open or just-in-time is a planner choice.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap (authoritative scope)
- `.planning/ROADMAP.md` § "Phase 6: In-Game Weekly Boards & Got-Passed Banner" — goal, the 4 success
  criteria, the "consumer of the Phase 4 scoped API / no new server data model" note, and the
  "last-viewed marker rides on Phase 5 identity storage" note.
- `.planning/REQUIREMENTS.md` § "Weekly Boards" (BOARD-03, BOARD-04) + § "Rivalry" (RIVAL-01) — the
  exact requirement wording each decision maps to.

### The API this phase consumes (and minimally extends)
- `cloud_functions/get_leaderboard/main.py` — current scope-aware reader (`scope=week|all`, default
  `week`, tolerant parse, top-10, machine_id stripped). **Gets the `scope=last_week` branch (D-01).**
- `cloud_functions/get_leaderboard/leaderboard_crypto.py` — `current_week_id()` /
  `previous_week_id()` already exist (no change needed; the last-week query reuses
  `previous_week_id(current_week_id())`). Note this module is **duplicated byte-for-byte** with
  `cloud_functions/submit_score/leaderboard_crypto.py` — if it were ever changed, both copies must stay
  in sync (this phase should not need to).
- `tests/test_get_leaderboard.py` — validator tests for the reader; **extend for `scope=last_week`**.

### Constraints inherited from prior phases
- `.planning/phases/04-server-hardening-weekly-data-model/04-CONTEXT.md` — **D-06** (week buckets,
  Monday 00:00 UTC, server-time only), **D-07** (best-per-machine-per-week), **D-08** (all-time
  retained, scope-aware), **D-09** (current + last week retained — *this is what makes BOARD-04
  possible*), **D-10** (machine_id stripped from all responses — *this drives D-11/D-12/D-19*).
- `.planning/phases/05-client-identity-hardening/05-CONTEXT.md` — **D-03** (the `%LOCALAPPDATA%\PacMan\`
  directory is the extension seam; the last-viewed marker is a *separate, unsigned* file, not in the
  signed blob, not tamper-protected — *the basis for D-13*).

### Current client baseline (the code being extended)
- `menu.py` — `run_leaderboard` (the board screen to extend: loading screen, offline line, empty-state
  line, rank-1-yellow styling), `run_main_menu` (the banner host, D-08), `run_game_over_screen` (the
  established graceful-degrade notice pattern).
- `api_service.py` — `get_leaderboard()` currently sends **no scope** (server defaults to week); **gains
  a `scope` param** (D-14). `submit_score` already returns `{success, is_new_best}`.
- `main.py` — startup flow (`_load_hmac_secret`, `load_identity`, initials entry, the `while True`
  menu loop). The **banner fetch + compute happens here at launch** (D-08/D-09); `machine_id`/`initials`
  are already resolved here for tracking your own best (D-11).
- `local_storage.py` / `paths.py` — `paths.user_data_path()` resolves `%LOCALAPPDATA%\PacMan\` (with a
  `~/.pacman` dev fallback); the new unsigned marker file lives here (D-13).
- `settings.py` — colors (`COLOR_YELLOW/WHITE/GRAY/...`), fonts (`FONT_MENU/SMALL`), `API_*_URL`,
  `IDENTITY_DIR_NAME`; candidate home for any new marker-filename / timeout constants.

### Tests that MUST stay green (CI merge gate)
- `tests/test_api_service.py` — client API-service tests (get_leaderboard gains a scope param).
- `tests/test_get_leaderboard.py` — server reader tests (extend for `scope=last_week`).
- CI golden net (`tests/test_golden_traces.py`, `tests/test_ghost_micro.py`,
  `tests/test_frame_hash.py`, `tests/test_determinism_guard.py`) — this phase touches no ghost-AI code,
  but the merge gate applies.

### Design specs — STALE baseline (dated 2026-03-26, pre-HMAC / pre-weekly)
- `docs/superpowers/specs/2026-03-26-leaderboard-design.md` — original Firestore/leaderboard shape;
  predates weekly buckets. Context only.
- `docs/superpowers/specs/2026-03-26-api-refactor-exe-design.md` — Cloud-Functions-HTTP-proxy +
  PyInstaller baseline. Context only.

### Codebase maps
- `.planning/codebase/ARCHITECTURE.md` — game state machine + leaderboard architecture (menu/game flow).
- `.planning/codebase/INTEGRATIONS.md` — how the client talks to the Cloud Functions.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`menu.py:run_leaderboard`** — already does loading screen → fetch → render with offline + empty
  states + rank-1-yellow styling. The This Week/All Time toggle, tab indicator, and last-week subtitle
  extend this directly rather than starting fresh.
- **`menu.py:run_main_menu`** — the simple `while True` render+event loop is the natural host for the
  banner line (D-08); add one rendered line + a dismiss-on-board-open flag.
- **Graceful-degrade pattern** — `menu.py:140` "Could not connect to leaderboard." and the
  `run_game_over_screen` identity-error notice are the established tone the offline/no-banner paths
  mirror (D-15/D-18).
- **`paths.user_data_path()`** — resolves `%LOCALAPPDATA%\PacMan\` (dev fallback `~/.pacman`),
  already created `exist_ok=True`; drop the unsigned marker file here (D-13).
- **`cloud_functions/get_leaderboard` scope plumbing** — the `scope`/tolerant-parse/branch structure is
  in place; `scope=last_week` is one more branch reusing `previous_week_id(current_week_id())` (D-01).

### Established Patterns
- **No-new-deps client** — `api_service.py` uses stdlib `urllib`; keep the scope param + marker IO
  stdlib-only (`json`, `os`).
- **Cloud Functions as the only data source** — the client has no Firestore access; anything the board
  needs (incl. last week's champ) must come through the HTTP API. This is why D-01 is a server read,
  not client-side computation.
- **Deterministic, offline-resilient game** — fixed-timestep frames, no wall-clock; the banner's
  launch fetch is best-effort and must never block playability (drives D-09's short timeout, and is why
  a timed/transient splash was rejected).

### Integration Points
- **`main.py` startup** — after identity resolves, do the short-timeout This Week fetch, load the
  marker, compute new passers (D-11/D-12), and pass the banner text into `run_main_menu` (D-08).
- **Board open ↔ marker write** — opening `run_leaderboard` is the single event that clears the banner
  and rewrites the marker baseline (D-07/D-10).
- **Submit ↔ your-best tracking** — when `main.py` submits a score, update the locally tracked
  this-week best (D-11) so the next launch's comparison is accurate.
- **Server deploy** — the `scope=last_week` change requires a `get_leaderboard` redeploy (manual,
  Google Cloud Console, per the api-refactor spec). In-repo gate is the validator tests; live behavior
  depends on the operator deploying.
</code_context>

<specifics>
## Specific Ideas

- **The banner is deliberately faithful to "since you last *viewed the board*"** (not "since last
  launch") — D-07. The user wants the marker to update only on an actual board view, so the prompt to
  go look keeps re-appearing until acted on.
- **Accuracy is intentionally "good enough," not exact** — because `machine_id` is stripped (Phase 4
  D-10) and a wrong banner is harmless (Phase 5 D-03), the design accepts the rare same-initials
  collision (D-12) rather than building heavier identity matching. This mirrors the project's standing
  "right altitude for a friends board" philosophy.
- **This Week is the gravitational center** — default board view (D-02), the board the banner watches
  (D-05), and where last-week's champ sits (D-04). All Time is the secondary "hall of fame."
</specifics>

<deferred>
## Deferred Ideas

- **Full last-week leaderboard view** — `scope=last_week` returns the whole top-10 (D-01) but Phase 6
  only shows `entries[0]` as the champ. A full "last week's board" view is a natural Phase 7 (web) or
  future addition — designed-for, not built here.
- **Self-row highlight on the board** — rejected for now (D-19) due to the machine_id-stripped matching
  limitation; revisit only if a reliable self-identifier ever exists.
- **Season-history archives / friend groups** — already out of scope for v1.1 (BOARD-F1 / SOCL-F1).

None of these are scope creep — discussion stayed within the in-game-boards + banner boundary.
</deferred>

---

*Phase: 6-in-game-weekly-boards-got-passed-banner*
*Context gathered: 2026-06-19*
