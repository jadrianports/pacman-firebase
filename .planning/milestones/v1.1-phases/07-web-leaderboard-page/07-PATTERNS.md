# Phase 7: Web Leaderboard Page - Pattern Map

**Mapped:** 2026-06-26
**Files analyzed:** 6 new files (1 modified: none)
**Analogs found:** 6 / 6 (all are *behavior/logic* analogs — this is the project's first web/HTML/CSS/JS surface, so no *same-language* analog exists for any file)

> **Net-new language surface.** The repo is Python/PyGame with zero prior HTML/CSS/JS.
> Every web file below is net-new *as code*, but each has a strong *behavior* analog already
> shipped in `menu.py` (`run_leaderboard`) and `api_service.py`. The planner should copy the
> **logic, wording, states, and data contract** from those analogs, translating PyGame render
> calls into DOM/CSS. Source-of-truth values (URL, colors) live in `settings.py`.

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `web/public/app.js` | client logic / store | request-response + lazy cache | `menu.py:run_leaderboard` (view state, cache, toggle, states) + `api_service.py:get_leaderboard` (fetch+parse) | logic-match (cross-language) |
| `web/public/index.html` | view / markup | static structure + OG/branding | `menu.py:run_leaderboard` render layout (header, tab bar, subtitle, rank rows, hint) | logic-match (cross-language) |
| `web/public/styles.css` | styling / config | n/a (presentation) | `settings.py` color constants + `07-UI-SPEC.md` tokens | token-match |
| `firebase.json` (root or `web/`) | config | n/a (hosting) | `cloud_functions/*` deploy convention (manual operator deploy) | partial (no hosting config exists yet) |
| `web/public/og-preview.png` | asset | n/a (static image, ~1200×630) | none (net-new branding asset) | no analog |
| `web/public/favicon.svg` (+ `.ico`) | asset | n/a (static icon) | none (net-new branding asset) | no analog |

## Pattern Assignments

### `web/public/app.js` (client logic, request-response + lazy cache)

**Analog A — fetch + parse contract:** `api_service.py:get_leaderboard` (lines 30-40)
```python
def get_leaderboard(self, scope=None, timeout=10):
    try:
        url = self.leaderboard_url
        if scope:
            url += f"?{urlencode({'scope': scope})}"
        ...
        return data.get("entries")   # -> list, or None on any failure
    except Exception:
        return None
```
Copy this exactly as JS `fetch`: `fetch(`${LEADERBOARD_URL}?scope=${scope}`)` → `await resp.json()` → return `data.entries`; on **any** throw/non-ok return `null`. Preserve the **null = offline** sentinel — the whole render branch below keys off it.

**Analog B — view state, lazy cache, toggle, render states:** `menu.py:run_leaderboard` (lines 167-261)

- **Per-view lazy cache + sentinel truth table** (lines 167-170):
```python
views = {"week": _UNFETCHED, "all": _UNFETCHED}
active = "week"
# None=offline, []=empty, [...]=data
```
Mirror in JS: `const views = { week: UNFETCHED, all: UNFETCHED }; let active = "all";`
**DIVERGENCE (D-08): web opens on `all`, not `week`.** Fetch All Time on load; fetch This Week (+ last_week subtitle) lazily on first toggle.

- **Lazy-fetch on toggle** (lines 256-261):
```python
active = "all" if active == "week" else "week"
if views[active] is _UNFETCHED:
    _show_loading(...)
    views[active] = api_service.get_leaderboard(scope="all")
```
Translate: on tab tap, if `views[active] === UNFETCHED` show `Loading...`, fetch, store. When This Week first activates, also fetch `scope=last_week` for the subtitle.

- **Last-week champion** (lines 176-177):
```python
last_week = api_service.get_leaderboard(scope="last_week")
last_week_initials = last_week[0]["initials"] if last_week else None
```
JS: `entries?.[0]?.initials ?? null`; render subtitle only on This Week view AND when non-null (hide otherwise — D-09).

- **Three-way render state** (lines 222-242) — branch identically:
  - `entries === null` → `"Could not connect to leaderboard."`
  - `entries.length === 0` → empty text per active view (see Shared/Copy below)
  - else → rank rows, **rank-1 yellow, 2–10 white** (line 239: `COLOR_YELLOW if i == 0 else COLOR_WHITE`)

- **Refresh control (D-10, net-new vs in-game LEFT/RIGHT):** re-pull `active` view only, overwrite its cache slot, re-render. No analog keybind; this is the web's added affordance.

- **Rank row format** (lines 233-238): `{rank}. {INITIALS} {dots} {score}`. In-game uses char-count dot fill (`LEADERBOARD_LINE_WIDTH`); web should render dot-leaders via CSS (flex + `border-bottom`/overflow dots) rather than literal `.` padding, since the monospace column approach is specified in UI-SPEC. Thousands separators on score are Claude's discretion (D-21).

### `web/public/index.html` (view, static structure + OG/branding)

**Analog:** `menu.py:run_leaderboard` render order (lines 191-247) — replicate as DOM:
1. `PAC-MAN` wordmark (in-game header "LEADERBOARD" yellow, line 191 → web wordmark per D-14)
2. Tab bar `This Week | All Time` (lines 197-205) — active label yellow, inactive gray
3. Last-week subtitle slot (lines 215-220) — This Week only, hidden when empty
4. Board container (rank rows / state message region)
5. Refresh control + hint

**No analog — head/meta (net-new):** OG + Twitter Card tags, `<title>PAC-MAN — Leaderboard</title>` (D-14), favicon link, font preload for Press Start 2P. Use UI-SPEC § Copywriting Contract for exact strings. Use Context7 for current Open Graph / Twitter Card meta tag syntax if unsure.

### `web/public/styles.css` (styling, presentation)

**Analog — color source-of-truth:** `settings.py` (lines 61-63):
```python
COLOR_YELLOW = (255, 255, 0)   # #FFFF00  -> accent: wordmark, active tab, rank-1, refresh focus
COLOR_WHITE  = (255, 255, 255) # #FFFFFF  -> rank rows 2-10
COLOR_GRAY   = (128, 128, 128) # #808080  -> hints, subtitle, inactive tab, empty/offline lines, dots
```
Background `#000000` (in-game `screen.fill("black")`, line 186). Panel/tab surface `#10102E` per UI-SPEC. Honor the UI-SPEC spacing scale (4px multiples), 44px min touch targets for tabs + Refresh, and the two-family type system (Press Start 2P for wordmark/tabs only, monospace stack for rank/score/body). Visual build routes through the **`frontend-design` skill** (D-05, hard directive).

### `firebase.json` (config, hosting)

**No direct analog** (no hosting config exists). Convention analog: backend is deployed by a **manual operator step** (CLAUDE.md / Memory: Phase 4/6 manual function redeploys); hosting mirrors this with `firebase deploy --only hosting`. Config points `hosting.public` at the static dir (e.g. `web/public`). Decide root-vs-`web/` placement (D-02, Claude's discretion). Use Context7 for current `firebase.json` hosting schema. **Same Firebase/GCP project** as the functions: `pacman-991339031546` (D-03).

### `web/public/og-preview.png` & `web/public/favicon.svg`

**No analog — net-new branding assets.** ~1200×630 OG image (D-13) and Pac-Man favicon (D-14), designed via the `frontend-design` pass. Referenced from `index.html` head.

## Shared Patterns

### Data source (single seam)
**Source:** `settings.py:82` — `API_LEADERBOARD_URL = "https://get-leaderboard-991339031546.asia-southeast1.run.app"`
**Apply to:** `app.js` — hardcode as a JS constant mirroring this (D-03). The browser fetches it directly; CORS `*` is already set server-side (`get_leaderboard/main.py` lines 26-33). No proxy, no auth, no server change this phase.

### API response contract (consume, never modify)
**Source:** `cloud_functions/get_leaderboard/main.py` (lines 38-91)
- `scope` query param: `week | all | last_week`; default + unknown → `week` (tolerant, never 400).
- Response shape: `{ "entries": [ { "initials": str, "score": int } ] }`, top-10.
- `machine_id` is **stripped** (lines 82-90) → web cannot identify "you" → **no self-row highlight** (D-19 carry-over). Rank-1-yellow is positional only.
- 500 path still returns `{ "entries": [], "error": ... }` — treat non-200 as offline (`null`) in the client.

### Graceful-degrade tone (house style)
**Source:** `menu.py:run_leaderboard` (lines 222-230) + `api_service.py` (lines 39-40, broad `except → None`)
**Apply to:** all `app.js` fetches — never hard-error; each view degrades independently (a failed scope shows the offline line while the other cached view still renders); the last-week subtitle simply hides on failure.

### Verbatim copy strings (parity, D-12)
**Source:** `menu.py:run_leaderboard` (lines 139, 180-181, 224) + UI-SPEC § Copywriting Contract
| Element | Exact string |
|---------|--------------|
| Loading | `Loading...` |
| Offline | `Could not connect to leaderboard.` |
| Empty — This Week | `No scores yet this week. Be the first!` |
| Empty — All Time | `No scores yet. Be the first!` |
| Tabs | `This Week` \| `All Time` |
| Subtitle | `Last week: {INITIALS}` (This Week only, hide when none) |
| Tab title | `PAC-MAN — Leaderboard` |

## No Analog Found (use UI-SPEC / frontend-design instead)

| File | Role | Reason |
|------|------|--------|
| `firebase.json` | config | No Firebase Hosting config in repo yet (functions deployed manually, no hosting prior) |
| `web/public/og-preview.png` | asset | First social-share asset in the project |
| `web/public/favicon.svg` | asset | First favicon in the project |
| `styles.css` (visual chrome beyond color tokens) | styling | No prior CSS; arcade chrome is designed fresh via `frontend-design` (D-05) within UI-SPEC tokens |

## Metadata

**Analog search scope:** repo root (`menu.py`, `api_service.py`, `settings.py`), `cloud_functions/get_leaderboard/`
**Files scanned:** 5
**Pattern extraction date:** 2026-06-26
