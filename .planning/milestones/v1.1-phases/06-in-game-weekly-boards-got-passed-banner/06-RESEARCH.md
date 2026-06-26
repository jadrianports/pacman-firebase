# Phase 6: In-Game Weekly Boards & Got-Passed Banner - Research

**Researched:** 2026-06-19
**Domain:** Python/PyGame desktop client + a single Cloud Functions read-path addition (Firestore Python admin SDK)
**Confidence:** HIGH (all findings read directly from the working-tree code being touched)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
The 19 decisions D-01..D-19 in `06-CONTEXT.md` are LOCKED. Summarized so the planner does not re-decide:

- **D-01** Add `scope=last_week` branch to `get_leaderboard` (read-path only; queries `week_id == previous_week_id(current_week_id())`; same `{entries:[{initials,score}]}` top-10 shape; tolerant parse stays — unknown scope → `week`, never 400). The one server touch.
- **D-02** Extend `menu.py:run_leaderboard` (not a new screen); opens on This Week.
- **D-03** LEFT/RIGHT toggles This Week ⇄ All Time; visible `< This Week | All Time >` tab indicator; ESC/ENTER still exits.
- **D-04** "Last week: BOB" subtitle under the LEADERBOARD header, This Week view only.
- **D-05** Banner compares your this-week best vs the This Week board; no this-week score → no banner.
- **D-06** Name all NEW passers, capped to one readable line (`JIM, BOB, ACE +2 more`); cap count = Claude's discretion.
- **D-07** Baseline resets ONLY when the player opens the in-game Leaderboard (not on launch).
- **D-08** Banner is a prominent line on the existing main menu (under PAC-MAN title); reuses `run_main_menu`; non-blocking.
- **D-09** Quick BLOCKING launch fetch with a SHORT timeout (~1-3s, Claude's discretion; NOT api_service's 10s default); slow/offline → silently skip banner. No threading.
- **D-10** Opening the board clears the on-screen banner AND resets the cross-launch baseline (one rule, single line not a modal).
- **D-11** Track your own this-week best LOCALLY (max submitted this week), stamped with `week_id`; never locate yourself on the board.
- **D-12** Detect new passers by initials: store the SET of initials above your best at last view; a new passer is initials now above you that weren't in that set. Same-initials collision may suppress one passer — accepted as harmless.
- **D-13** Single SEPARATE UNSIGNED marker file in `%LOCALAPPDATA%\PacMan\` via `paths.user_data_path(...)`; holds `week_id` + tracked best + initials-above set; NOT in the signed identity blob, NOT tamper-protected; week_id mismatch on load → silent re-baseline.
- **D-14** Add a `scope` arg to `api_service.get_leaderboard`; lazy per view (This Week on open, last-week subtitle best-effort, All Time on first toggle); cache each per screen visit. Stdlib only.
- **D-15** Each view degrades independently — failed scope shows "Could not connect to leaderboard."; last-week subtitle hides on failure.
- **D-16** No last-week champion → render NOTHING (no placeholder, no dash).
- **D-17** Empty This Week → "No scores yet this week. Be the first!"; All Time keeps "No scores yet. Be the first!".
- **D-18** Cold-start / offline / no this-week score → no banner, no error, straight to menu.
- **D-19** No self-row highlight; keep current styling (rank 1 yellow, rest white). Tab-indicator/board visuals route to `/gsd-ui-phase`.

### Claude's Discretion (design these — do not re-ask the user)
- Marker file NAME + on-disk format (plain JSON fine — unsigned by design).
- Short launch-fetch timeout VALUE (~1-3s).
- Banner COLOR / exact placement on the menu, and the name CAP count (subject to `/gsd-ui-phase`).
- Exact `scope` query-param wiring in `api_service.get_leaderboard`, and how the three per-view caches are held in the board loop.
- The initials-above set REPRESENTATION (set/list of strings); tie-handling for duplicate initials.
- last-week subtitle fetch coupling (alongside the week fetch on open, or just-in-time).

### Deferred Ideas (OUT OF SCOPE)
- Full last-week leaderboard view (Phase 7 / future) — Phase 6 only shows `entries[0]`.
- Self-row highlight on the board (rejected — D-19).
- Season-history archives / friend groups (BOARD-F1 / SOCL-F1).
- Web leaderboard page (Phase 7).
- Any new server DATA model (week buckets/retention/HMAC/permanent initials are Phase 4 — this phase only READS).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BOARD-03 | Player can toggle This Week / All Time in-game | `menu.py:run_leaderboard` event loop + `api_service.get_leaderboard(scope)` — see §2, §3 |
| BOARD-04 | Previous week's champion shown ("Last week: BOB") | server `scope=last_week` branch (D-01) + `entries[0]` subtitle — see §1, §4 |
| RIVAL-01 | Launch banner names players who passed you since last board view | launch fetch in `main.py` + unsigned marker file + passer compute — see §5, §6, §7 |
</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Run the game: `python main.py`; tests: `pytest`; build: `python build.py`.
- **Stdlib-only client networking** — `api_service.py` uses `urllib`; no new client deps (CLAUDE.md "Leaderboard" + CONTEXT "Established Patterns").
- Cloud Functions act as HTTP API proxy — **no Firebase credentials in the client**; client has NO Firestore access. Anything the board needs (incl. last-week champ) must come through the HTTP API.
- Game is **fully playable offline** — leaderboard features gracefully degrade. (SC-4 is a hard contract.)
- `paths.py`: `resource_path()` for bundled assets, `data_path()` for next-to-exe user data, `user_data_path()` for `%LOCALAPPDATA%\PacMan\` per-user data.
- Constants live in `settings.py`.
- **Memory note (golden re-bless via Linux Docker):** golden traces re-bless on Linux only (`python:3.12` container). This phase should NOT touch ghost AI, so no re-bless is expected; if a golden test ever fails, that is a red flag, not a re-bless trigger.
- **Memory note (CRLF breaks must_haves parse):** normalize any generated PLAN.md to LF.
- **Memory note (.venv is the real Python env):** run tests/build via `.venv/Scripts/python.exe`.

## Summary

Phase 6 is a pure consumer/UI phase plus one tiny server read-path branch. Everything it extends already exists and was read directly: the board screen (`menu.py:run_leaderboard`, lines 113-171), the main menu host (`menu.py:run_main_menu`, lines 11-44), the client API (`api_service.py:get_leaderboard`, lines 29-36), the startup flow (`main.py:main`, lines 46-111), the per-user storage seam (`paths.user_data_path`, lines 30-32), and the server reader (`cloud_functions/get_leaderboard/main.py`, lines 24-71) with its week-math helpers (`leaderboard_crypto.previous_week_id`, lines 80-83). The work is small, well-bounded, and almost entirely additive.

The one genuinely tricky area is the banner's passer-detection mechanics (D-11/D-12) and where to thread a short network timeout at launch (D-09) without disturbing the existing 10s default. Both are solvable with the patterns already in the codebase. No ghost-AI code is involved, so the CI golden net is not at risk — confirmed by reading the touch-set.

**Primary recommendation:** Implement in four additive slices — (1) server `scope=last_week` branch + its validator tests; (2) `api_service.get_leaderboard(scope=None, timeout=10)` param + tests; (3) the board screen toggle/subtitle/empty-state extensions; (4) the marker file + launch banner compute in `main.py`. No new dependencies; stdlib `json`/`os`/`urllib` only.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Last-week champion lookup (BOARD-04) | API / Backend (`get_leaderboard`) | — | Client has no Firestore access; must come through HTTP (CLAUDE.md). `previous_week_id` math is server-side already. |
| This Week / All Time toggle UI (BOARD-03) | Client (`menu.py`) | API (data) | UI/event handling is client; data is fetched via existing API scopes. |
| `scope` request plumbing | Client (`api_service.py`) | — | Stdlib urllib query-param assembly. |
| Launch banner fetch + compute (RIVAL-01) | Client (`main.py` startup) | API (data) | Startup orchestration + local marker comparison are client-only; only the board read is remote. |
| Last-viewed marker persistence (D-13) | Client (`paths.user_data_path` → `%LOCALAPPDATA%\PacMan\`) | — | Per-user local state; unsigned, not part of identity blob. |
| Your-best tracking on submit (D-11) | Client (`main.py` submit path) | — | Local max-this-week, week-stamped; never on the board. |

## Standard Stack

No new packages. Everything uses what is already imported.

### Core (already present, no install)
| Module | Where | Purpose |
|--------|-------|---------|
| `urllib.request` (`urlopen`, `Request`) | `api_service.py` | HTTP GET/POST to Cloud Functions |
| `urllib.parse` (`urlencode`) | **add** to `api_service.py` | Build the `?scope=` query string safely |
| `json`, `os` | client modules | Marker file read/write (stdlib only, D-13) |
| `pygame` | `menu.py`, `main.py` | Rendering + event loop |
| `firebase_admin.firestore` | `cloud_functions/get_leaderboard/main.py` | The `where(...).order_by(...).limit(10).stream()` query (already used) |

**Installation:** none. Do NOT add client dependencies — it would break the stdlib-only contract and the PyInstaller build assumptions.

## Package Legitimacy Audit

Not applicable — this phase installs **no external packages**. All code uses the Python standard library plus modules/SDKs already vendored in the repo (`pygame`, `firebase_admin`, `functions_framework`). No registry verification needed.

## Architecture Patterns

### Per-decision technical notes (the actionable core)

---

### §1 — D-01 / BOARD-04: server `scope=last_week` branch
**File:** `cloud_functions/get_leaderboard/main.py` (lines 24-71)
**Helper (no change):** `cloud_functions/get_leaderboard/leaderboard_crypto.py:previous_week_id` (lines 80-83), `current_week_id` (lines 66-77)

Current structure (lines 38-41) parses scope tolerantly:
```python
scope = (request.args.get("scope") or "week").lower()
if scope not in ("week", "all"):
    scope = "week"
```
Add `"last_week"` to the allowed set, then add a third branch in the `try` block alongside the existing `if scope == "all" / else (weekly)` (lines 43-60). The last-week branch is the weekly branch with a different `week_id`:
```python
# allow-list now includes last_week
if scope not in ("week", "all", "last_week"):
    scope = "week"
...
elif scope == "last_week":
    last = leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())
    query = (
        db.collection("weekly")
        .where("week_id", "==", last)
        .order_by("score", direction=firestore.Query.DESCENDING)
        .limit(10)
    )
```
The projection loop (lines 62-68) and return shape are unchanged — still `{entries:[{initials,score}]}`, machine_id/week_id/updated_at stripped (D-10). **The composite index `week_id ASC, score DESC` from Phase 4 already covers this query** (same shape as the `week` branch, just a different equality value).

**Import note (CONTEXT landmine confirmed):** lines 13-16 use the `if __package__: from . import leaderboard_crypto / else: import leaderboard_crypto` dual-import. Keep calling helpers as `leaderboard_crypto.previous_week_id(...)` (module-qualified, as the `week` branch already does on line 57) so both deploy-time and test-time import paths work.

**`previous_week_id` accepts/returns the `%Y-%m-%d` string** (verified lines 80-83): `previous_week_id(current_week_id())` is exactly the composition CONTEXT specifies — no new math.

**Server is DUPLICATED byte-for-byte** with `cloud_functions/submit_score/leaderboard_crypto.py` (header lines 3-6). This phase needs NO crypto change, so no sync needed — but do not "tidy" the duplication.

**Tests to extend:** `tests/test_get_leaderboard.py`. The weekly chain stub helper `_stub_stream` (lines 42-56) and the `make_request(query_string=...)` builder (lines 24-27) already exist. Add tests mirroring `test_scope_week_queries_weekly` (lines 123-138):
- `test_scope_last_week_queries_weekly_with_previous_week` — assert `db.collection.assert_called_with("weekly")` and `db.collection.return_value.where.assert_called_with("week_id", "==", leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id()))`. Import the helper the same way line 125 does: `from cloud_functions.get_leaderboard import leaderboard_crypto`.
- `test_scope_last_week_projects_only_initials_and_score` — mirror lines 161-172.
- (Optional) extend `test_garbage_scope_falls_back_to_week` reasoning — confirm `last_week` is now a recognized value, not a fallback.

---

### §2 — D-14 / D-15: `scope` client param on `api_service.get_leaderboard`
**File:** `api_service.py` (lines 29-36)
**Current:**
```python
def get_leaderboard(self):
    try:
        req = Request(self.leaderboard_url, method="GET")
        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("entries")
    except Exception:
        return None
```
**Change:** add `scope` and `timeout` parameters (the `timeout` param also serves D-09, §5 below). Use `urllib.parse.urlencode` for safety:
```python
from urllib.parse import urlencode  # add at top with the existing urllib import

def get_leaderboard(self, scope=None, timeout=10):
    try:
        url = self.leaderboard_url
        if scope:
            url = f"{url}?{urlencode({'scope': scope})}"
        req = Request(url, method="GET")
        with urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data.get("entries")
    except Exception:
        return None
```
Default `scope=None` → no query param → server defaults to `week` (preserves every existing caller and existing test `test_get_leaderboard_success` which calls `get_leaderboard()` with no args). Default `timeout=10` preserves the current 10s for the board screen (D-09 only overrides at launch).

**Return contract unchanged:** `entries` list on success, `[]` on empty, `None` on any failure (verified by `test_get_leaderboard_success/_empty/_network_error`, lines 76-94). The board screen already treats `None` as offline (`menu.py:138`) and `[]` as empty (`menu.py:143`).

**Tests to extend:** `tests/test_api_service.py`. The existing pattern captures the request via a fake urlopen (see `test_submit_score_sends_signature_field`, lines 41-58, and the `_fake_urlopen(req, timeout=None)` signature). Add:
- `test_get_leaderboard_sends_scope_param` — capture `req.full_url` (or `req.get_full_url()`) and assert it contains `scope=last_week` / `scope=all`.
- `test_get_leaderboard_no_scope_omits_param` — assert no `?scope` when called with no args (URL equals the base).
- `test_get_leaderboard_passes_timeout` — capture the `timeout` kwarg in the fake urlopen and assert the short value threads through (supports D-09).

---

### §3 — D-02/D-03/D-04/D-16/D-17/D-19: board screen toggle + subtitle + empty states
**File:** `menu.py:run_leaderboard` (lines 113-171)

Current flow: one-shot `entries = api_service.get_leaderboard()` (line 127) before the render loop, then a static loop rendering `entries` (None/empty/list branches, lines 138-157), ESC/ENTER to exit (lines 167-169).

**Required reshape (additive, D-14 lazy caching):**
- Hold per-view cache state in the function scope, e.g. `views = {"week": <unfetched-sentinel>, "all": <unfetched-sentinel>}` and `active = "week"` (opens on This Week, D-02). Use a distinct sentinel (e.g. a module-level `_UNFETCHED = object()`) so you can tell "not yet fetched" from `None` (offline) and `[]` (empty) — all three are meaningful (D-15).
- Fetch This Week on open (`get_leaderboard(scope="week")` → really call with `scope=None` or `scope="week"`; both hit week). Fetch All Time lazily the first time the player toggles to it (D-14): on LEFT/RIGHT, if the target view is still the sentinel, show the existing "Loading..." then fetch and cache it.
- Last-week subtitle (D-04): a separate best-effort `get_leaderboard(scope="last_week")` call; take `entries[0]["initials"]` for "Last week: XXX". Render the subtitle just under the LEADERBOARD header (line 134 renders header at y=80; subtitle goes ~y=130, above the y=180 first entry on line 156). **Show only while `active == "week"`** (D-04). If the call returns `None`/`[]`, render nothing (D-16) — no placeholder. Coupling (alongside week fetch on open vs. just-in-time) is planner discretion (D-14).
- Tab indicator (D-03): render `< This Week | All Time >` with the active side highlighted. Exact visuals route to `/gsd-ui-phase` (D-19) — implement a functional version (e.g. active tab COLOR_YELLOW, inactive COLOR_GRAY).
- Empty-state wording (D-17): the existing `len(entries) == 0` branch (lines 143-146) currently renders "No scores yet. Be the first!". Make it conditional on `active`: This Week → "No scores yet this week. Be the first!"; All Time → keep the existing string.
- Offline per-view (D-15): the `entries is None` branch (lines 138-142) already renders "Could not connect to leaderboard." — keep it; it now applies to whichever view's fetch failed, while the other cached view still renders if its fetch succeeded.
- Styling (D-19): keep rank-1-yellow / rest-white (lines 154). Do NOT add self-highlight.

**Event loop additions (lines 164-169):** add `pygame.K_LEFT` / `pygame.K_RIGHT` to flip `active` between `"week"` and `"all"` (lazy-fetch on first switch to `all`). ESC/ENTER still exits (no binding conflict — confirmed those are the only keys handled today).

**Board-open side effect (D-07/D-10):** opening `run_leaderboard` is the single event that clears the banner and rewrites the marker baseline. `run_leaderboard` needs access to the marker write + the current This Week board + the player's tracked best + initials. Cleanest seam: pass the data it needs in (e.g. `machine_id`/`initials`/`tracked_best`/marker helpers) OR have `main.py` perform the baseline rewrite immediately after `run_leaderboard` returns, using the This Week entries the screen just fetched. **Recommendation:** have the board screen return (or `main.py` recompute) the baseline so the marker is rewritten on every board open. The planner should decide the exact seam; note that the board already fetched This Week, so passing those entries back avoids a duplicate network call.

---

### §4 — D-13: the unsigned marker file
**File (new behavior, no new module strictly required — can live in `local_storage.py` or a small new `marker.py`):** write via `paths.user_data_path(<MARKER_FILE_NAME>)`.

**Contrast with the SIGNED identity blob (read from `local_storage.py`):** the identity blob (`_write_identity_blob`, lines 64-81) is obfuscated + HMAC-signed + wrapped in a `{"sig", "blob"}` envelope, and a present-but-invalid blob is fail-closed as TAMPERED (lines 84-108). **The marker is the OPPOSITE by design (D-13):** plain JSON, no obfuscation, no HMAC, no envelope. A wrong/missing/corrupt marker is harmless — on any read failure, treat it as "no marker" and re-baseline silently.

**Suggested shape (planner discretion on names/format):**
```json
{"week_id": "2026-06-15", "tracked_best": 8000, "initials_above": ["JIM", "BOB"]}
```
- `MARKER_FILE_NAME` constant in `settings.py` next to `IDENTITY_FILE_NAME` (line 84). Suggest e.g. `"last_viewed.json"`.
- Write: `os.makedirs` is already handled by `user_data_dir()` (paths.py line 26, `exist_ok=True`), so just `json.dump` to `user_data_path(MARKER_FILE_NAME)`. Wrap in try/except — never raise (mirror the best-effort tone of `_safe_remove`, local_storage.py lines 248-254).
- Read: `try: json.load` → on `FileNotFoundError`/`JSONDecodeError`/any exception return `None` (cold-start, D-18).
- **Week-mismatch re-baseline (D-11/D-12/D-13):** on load, if `marker["week_id"] != current_week_id_equivalent`, discard the marker (treat as fresh this week → no stale passers). NOTE: the CLIENT has no `current_week_id()` of its own — `leaderboard_crypto` at repo root is the Phase 5 CLIENT copy; verify whether it exposes week math. If it does not, the client cannot compute the Monday-UTC week id locally. **Open question O-1 below** — the planner must resolve how the client knows "the current week" for stamping. Options: (a) reuse a client-side `current_week_id()` if the root `leaderboard_crypto` has it; (b) stamp using a value derived from the board response; (c) compute Monday-UTC client-side with stdlib `datetime` (acceptable since a wrong week only causes a harmless re-baseline, D-13). Recommend (c) for self-containment given "wrong banner is harmless."

---

### §5 — D-08/D-09/D-18: launch banner fetch (short timeout)
**File:** `main.py:main` (lines 46-111)

Insert the banner computation AFTER identity resolves (after line 61, where `machine_id`/`initials`/`identity_tampered` are known) and BEFORE the main `while True` loop (line 72). Sequence:
1. Load the marker (§4). If absent → no banner (D-18, cold start).
2. If the marker has no `tracked_best` for the current week (or `initials is None`) → no banner (D-05: no this-week score → nothing to be passed on).
3. Best-effort This Week fetch with a SHORT timeout: `api.get_leaderboard(scope="week", timeout=SHORT_TIMEOUT)` — the `timeout` param added in §2. **This is exactly why §2 adds a `timeout` param instead of hardcoding 10s** (D-09: do NOT change the default). `SHORT_TIMEOUT` (~1-3s) → a new `settings.py` constant, e.g. `BANNER_FETCH_TIMEOUT_SECONDS = 2`. On `None` (offline/slow) → silently skip banner (D-09/D-18).
4. Compute new passers (§6) and pass the resulting banner text into `run_main_menu` (D-08).

**No threading** (D-09) — a single blocking call with a short timeout is the locked approach; `urlopen(req, timeout=...)` raises on timeout and `get_leaderboard` already swallows it to `None`. The offline path is already a no-op. The blocking call happens once, before the menu loop, so it never blocks gameplay or frame timing (no wall-clock inside the game loop — Determinism §pitfalls).

**Banner host (D-08):** `run_main_menu` (lines 11-44) renders title at y=150 (line 23) and options starting at y=350 (line 30) — ample room for a banner line beneath the title (~y=230). Add a `banner_text=None` param to `run_main_menu`; render the line only when truthy (color/placement → `/gsd-ui-phase`, D-08). The banner persists across menu re-entries until the board is opened (D-07/D-10), so `main.py` keeps the banner string in a variable across the loop and clears it only after `run_leaderboard` returns.

---

### §6 — D-11/D-12: passer-detection mechanics
**Where:** `main.py` (compute at launch §5, and update on submit).

**Track your own best (D-11):** the local `tracked_best` is the max score you've submitted THIS WEEK, stamped with `week_id`. On every successful submit in `main.py` (lines 98-100, after `api.submit_score`), update the marker's `tracked_best = max(tracked_best, score)` (only if it's this week; re-baseline if the stamped week rolled over). Do NOT try to find your row on the board — `machine_id` is stripped (D-10, confirmed server lines 65-67) and your score may be outside top-10.

**Detect new passers (D-12):**
- `above_now = {e["initials"] for e in this_week_entries if e["score"] > tracked_best}` — every board entry strictly above your tracked best is, by definition, not you (you're at `tracked_best` or below your own best).
- `new_passers = above_now - set(marker["initials_above"])` — initials now above you that weren't above you at last view.
- Banner shows `new_passers` (capped, D-06). An already-ahead player bumping their score does NOT re-trigger (they were already in the set). A same-initials collision can suppress one passer — accepted (D-12).
- **Tie/duplicate handling (Claude's discretion):** a `set` of initials strings is the natural representation; duplicate initials in the board collapse to one entry — acceptable per the "harmless" philosophy. If the planner prefers, a list preserves count, but the set is simplest and matches D-12's wording ("the SET of initials").

**Baseline rewrite on board open (D-07/D-10):** when `run_leaderboard` opens, recompute `initials_above` from the freshly-fetched This Week board against the current `tracked_best`, and write the marker (`week_id`, `tracked_best`, `initials_above`). This is the ONLY place `initials_above` is reset. Launching alone does not reset it (the next launch recomputes new passers against the SAME stored set, so the banner re-appears, refreshed — D-07).

**Cap (D-06):** show first N initials then `+K more` (e.g. `JIM, BOB, ACE +2 more`). N is Claude's discretion; pick something that fits one line at FONT_SMALL across WIDTH=900 (suggest N=3 or 4). Final visual to `/gsd-ui-phase`.

---

### Anti-Patterns to Avoid
- **Locating "your" row on the board** — forbidden by D-11/D-19; `machine_id` is stripped server-side. Track your best locally instead.
- **Signing/obfuscating the marker** — D-13 explicitly forbids it; re-signing on every view is pointless friction. Plain JSON only.
- **Hardcoding the short timeout inside `get_leaderboard`** — would clobber the 10s board-screen default (D-09). Thread it as a parameter.
- **Threading the launch fetch** — D-09 rejects it; a single short blocking call before the menu loop is the locked design.
- **Touching `leaderboard_crypto` crypto/canonical-message functions** — out of scope; the byte-for-byte duplication invariant (submit_score ↔ get_leaderboard) must not drift.
- **Adding a client dependency** — breaks the stdlib-only + PyInstaller contract.
- **Tidying the dual-import block in `get_leaderboard/main.py`** — it is load-bearing for deploy vs. test import roots.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Last-week champion derivation | Client-side week math + a separate API to enumerate weeks | Server `scope=last_week` branch (D-01) returning `entries[0]` | Client has no Firestore access; the data + index already exist server-side |
| Query-string assembly | Manual string concatenation with `?scope=` | `urllib.parse.urlencode` | Already stdlib; escapes safely; no new dep |
| Per-user storage location | A new path resolver | `paths.user_data_path()` (paths.py:30) | Already resolves `%LOCALAPPDATA%\PacMan\` with `~/.pacman` dev fallback and `exist_ok=True` |
| Offline/empty rendering | New degrade UI | Existing `menu.py:138-146` None/empty branches | Established graceful-degrade pattern (D-15 mirrors `menu.py:140`) |
| Tamper-proof marker | HMAC/obfuscation envelope like identity.dat | Plain JSON, best-effort read | D-13: marker is intentionally unsigned; wrong banner is harmless |

**Key insight:** Almost every piece this phase needs already exists in the codebase one layer over. The phase is wiring + one server branch, not new infrastructure.

## Runtime State Inventory

This is partly a "new local state" phase (the marker) rather than a rename/refactor, but the inventory matters for the marker + server deploy:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data (client) | NEW unsigned marker file under `%LOCALAPPDATA%\PacMan\` (D-13). No migration of existing data — it's brand new. | Create on first board open / first submit; tolerate absence. |
| Stored data (server) | Firestore `weekly` collection already retains current + last week (Phase 4 D-09). **No data-model change.** | None — read-only addition. |
| Live service config | The `get_leaderboard` Cloud Function must be **manually redeployed** for `scope=last_week` to go live (Google Cloud Console, per api-refactor spec). In-repo gate = validator tests only. | Plan must include a deploy step / human checkpoint; live BOARD-04 depends on the operator deploying. |
| OS-registered state | None. | None — verified (no Task Scheduler / services touched). |
| Secrets/env vars | None new. HMAC secret unchanged; marker is unsigned (no secret). | None. |
| Build artifacts | PyInstaller exe bundles `menu.py`/`main.py`/`api_service.py` — a rebuild ships the new UI. `paths.user_data_path` already handles frozen vs dev. No new bundled asset (no new font/image) unless `/gsd-ui-phase` adds one. | Rebuild exe to ship; verify marker writes under frozen `%LOCALAPPDATA%` path. |

## Common Pitfalls

### Pitfall 1: Sentinel confusion in the board cache
**What goes wrong:** Using `None` both for "not fetched yet" and "fetch failed (offline)" makes lazy caching re-fetch a genuinely-offline view every frame, or render empty-state for an offline view.
**How to avoid:** Use a distinct `_UNFETCHED` sentinel object. `None` = offline (render "Could not connect"), `[]` = empty (render the empty-state string), list = data, sentinel = needs fetch.
**Warning sign:** Network call inside the render loop firing repeatedly.

### Pitfall 2: Clobbering the 10s default timeout
**What goes wrong:** Adding D-09's short timeout by editing `urlopen(req, timeout=10)` directly slows... no, it SPEEDS up the board screen's fetch too, causing spurious "Could not connect" on slow-but-working connections when browsing the board.
**How to avoid:** Add a `timeout` parameter defaulting to 10; only the launch fetch passes the short value.

### Pitfall 3: Client week-id stamping has no server helper
**What goes wrong:** The marker stamps `week_id`, but the client may not have a `current_week_id()` (the root `leaderboard_crypto` is the Phase 5 client copy — needs verification). Stamping the wrong week could either never re-baseline or always re-baseline.
**How to avoid:** Either reuse a client week helper if present, or compute Monday-UTC with stdlib `datetime` (matches server logic, `leaderboard_crypto.py:66-77`). A wrong week is harmless (D-13 re-baselines silently), so a self-contained stdlib computation is acceptable. See O-1.

### Pitfall 4: Banner blocking on a dead network at launch
**What goes wrong:** A too-long timeout makes the game appear to hang before the menu on offline launch.
**How to avoid:** Short timeout (~2s, D-09); `get_leaderboard` already swallows the timeout to `None` → skip banner. Never thread; never retry.

### Pitfall 5: Marker write raising and crashing startup
**What goes wrong:** A read-only `%LOCALAPPDATA%` or disk error in `json.dump` could crash if unguarded.
**How to avoid:** Wrap all marker IO in try/except returning silently — mirror `_safe_remove` (local_storage.py:248-254) and the graceful-degrade contract (SC-4).

### Pitfall 6: CI golden net (false alarm risk)
**What goes wrong:** Believing this phase could regress ghost AI.
**Reality:** The touch-set (`menu.py`, `main.py`, `api_service.py`, `settings.py` constants, `cloud_functions/get_leaderboard/`, new marker code, tests) contains **no ghost-AI / sim code**. `tests/test_golden_traces.py`, `test_ghost_micro.py`, `test_frame_hash.py`, `test_determinism_guard.py` should stay green untouched. **Do NOT re-bless.** If any golden test fails, it indicates accidental scope creep, not a legitimate change.

### Pitfall 7: CRLF in generated PLAN.md
**What goes wrong:** A CRLF PLAN.md silently parses 0 must_haves in gsd-tools (memory note).
**How to avoid:** Normalize plan files to LF.

## Code Examples

### Server last_week branch (verified against current main.py structure)
```python
# cloud_functions/get_leaderboard/main.py — add to the existing scope dispatch
# Source: read of working-tree main.py lines 38-60 + leaderboard_crypto.py lines 66-83
scope = (request.args.get("scope") or "week").lower()
if scope not in ("week", "all", "last_week"):
    scope = "week"
...
elif scope == "last_week":
    last = leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())
    query = (
        db.collection("weekly")
        .where("week_id", "==", last)
        .order_by("score", direction=firestore.Query.DESCENDING)
        .limit(10)
    )
```

### Client scope+timeout param (verified against current api_service.py)
```python
# api_service.py — Source: read of working-tree lines 1-2, 29-36
from urllib.parse import urlencode

def get_leaderboard(self, scope=None, timeout=10):
    try:
        url = self.leaderboard_url
        if scope:
            url = f"{url}?{urlencode({'scope': scope})}"
        with urlopen(Request(url, method="GET"), timeout=timeout) as resp:
            return json.loads(resp.read()).get("entries")
    except Exception:
        return None
```

### Passer compute (per D-11/D-12)
```python
# main.py — launch banner compute
above_now = {e["initials"] for e in this_week_entries if e["score"] > tracked_best}
new_passers = sorted(above_now - set(marker.get("initials_above", [])))
banner_text = _format_banner(new_passers) if new_passers else None  # cap per D-06
```

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| Single unscoped leaderboard fetch | Scope-aware reader (`week`/`all`, now `+last_week`) | Phase 4 added scope; Phase 6 adds one branch |
| Plaintext identity files next to exe | Signed/obfuscated blob in `%LOCALAPPDATA%\PacMan\` | Phase 5; the marker rides the SAME directory but is unsigned (D-13) |

Firestore Python admin query syntax (`.where(field, "==", value).order_by(field, direction=...).limit(n).stream()`) is already in use on lines 45-61 and is the pattern to copy verbatim — no need to re-confirm via Context7 since the working code demonstrates it. (If the planner wants version confirmation, the SDK is `firebase_admin.firestore`; the `.where(field, op, value)` positional form is what the repo uses today and tests assert against — `tests/test_get_leaderboard.py:136-138`.)

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The Phase-4 composite index `week_id ASC, score DESC` covers the `last_week` query (same shape, different equality value) | §1 | LOW — if the index were per-value it would fail at runtime, but composite indexes are field-based not value-based; CONTEXT D-01 explicitly states the index "already covers this query" [CITED: 06-CONTEXT.md D-01] |
| A2 | `urllib.parse.urlencode` is the right stdlib tool and is not already imported | §2 | LOW — verified `api_service.py` imports only `urllib.request` (lines 1-2); urlencode is stdlib |
| A3 | The client can compute Monday-UTC week-id with stdlib `datetime` for marker stamping | §4, O-1 | LOW — a wrong week only triggers a harmless silent re-baseline (D-13). Still flagged as O-1 for the planner to confirm the cleanest source. |
| A4 | No new bundled asset is required (no new font/image) unless `/gsd-ui-phase` adds one | Runtime Inventory | LOW — current screens reuse `freesansbold.ttf` and existing colors |

## Open Questions

**O-1 — How should the client know "the current week" to stamp the marker (D-11/D-13)?**
- What we know: the server computes `current_week_id()` (Monday-UTC) in `leaderboard_crypto.py:66-77`. The client has a `leaderboard_crypto` at repo root (Phase 5 copy) used for `obfuscate`/`sign_submission`.
- What's unclear: whether the client copy exposes `current_week_id()`. (Not read this session — quick check: `grep current_week_id` in the root `leaderboard_crypto.py`.)
- Recommendation: if present, reuse it; otherwise compute Monday-UTC inline with stdlib `datetime` (4 lines, mirrors server). A wrong week is harmless (D-13), so do not over-engineer. **Planner: pick one and note it.**

**O-2 — Seam for the board-open baseline rewrite (D-07/D-10).**
- What we know: opening `run_leaderboard` must clear the banner AND rewrite the marker, using the This Week board the screen already fetched.
- What's unclear: whether `run_leaderboard` writes the marker itself (needs `tracked_best`/`machine_id`/marker helpers passed in) or returns the fetched This Week entries to `main.py` to do the write.
- Recommendation: pass what the screen needs (or return the entries) so the marker is rewritten exactly once per board open without a duplicate network call. Planner decides the signature; keep the screen testable.

**O-3 — Does the existing `run_leaderboard` call site in `main.py:109` need new args?**
- `run_leaderboard(screen, timer, api)` today. Banner clear (D-10) and baseline rewrite (O-2) will likely require additional params (marker path, tracked_best). The planner should define the final signature in one place and update the single call site (main.py:109).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python stdlib (`urllib`, `json`, `os`, `datetime`) | client changes | ✓ | runtime Python | — |
| `pygame` | UI | ✓ (already imported) | repo-pinned | — |
| `firebase_admin` / `functions_framework` | server function (test + deploy) | ✓ (already used) | repo-pinned | — |
| pytest + werkzeug/flask test deps | tests | ✓ (existing test suite uses them) | repo-pinned | — |
| Google Cloud Console access | live `scope=last_week` deploy | external/manual | — | In-repo validator tests gate; live behavior needs operator deploy |

**Missing dependencies with no fallback:** none for in-repo work. The only external dependency is the manual `get_leaderboard` redeploy for live BOARD-04 — handled as a deploy/checkpoint step, not a code blocker.

## Sources

### Primary (HIGH confidence) — direct working-tree reads
- `menu.py` (lines 11-44 `run_main_menu`, 113-171 `run_leaderboard`, 138-146 degrade/empty branches, 154 styling)
- `api_service.py` (lines 1-2 imports, 10-27 `submit_score`, 29-36 `get_leaderboard`)
- `main.py` (lines 13-43 `_load_hmac_secret`, 46-111 `main`: identity resolve 58-61, submit 98-100, menu loop 72-110, board call 108-109)
- `paths.py` (lines 7-32 `user_data_dir`/`user_data_path`, 35-50 resource/data_path)
- `local_storage.py` (signed-blob write 64-81, fail-closed read 84-108, `_safe_remove` 248-254)
- `settings.py` (colors 61-65, fonts 67-71, API URLs 76-77, identity constants 79-89)
- `cloud_functions/get_leaderboard/main.py` (dual-import 13-16, scope parse 38-41, branches 43-60, projection 62-68)
- `cloud_functions/get_leaderboard/leaderboard_crypto.py` (`current_week_id` 66-77, `previous_week_id` 80-83, duplication note 3-6)
- `tests/test_get_leaderboard.py` (stub helpers 42-63, scope tests 111-172, `make_request` 24-27)
- `tests/test_api_service.py` (request-capture pattern 41-58, get_leaderboard tests 76-94)
- `tests/conftest.py` (`leaderboard_module` fixture 113-128, mock seam 96-110)
- `.planning/phases/06-in-game-weekly-boards-got-passed-banner/06-CONTEXT.md` (D-01..D-19, canonical refs)
- `.planning/REQUIREMENTS.md` (BOARD-03/04, RIVAL-01)
- `CLAUDE.md` (project constraints)

### Secondary
- None needed — all behavior verified against working-tree code rather than external docs.

## Metadata

**Confidence breakdown:**
- Server `scope=last_week`: HIGH — exact existing branch structure + helper read; tests have a direct template.
- Client `scope`/timeout param: HIGH — current signature + test pattern read.
- Board UI changes: HIGH on mechanics (read the loop), MEDIUM on exact visuals (routed to `/gsd-ui-phase` by D-19).
- Marker + banner mechanics: HIGH on the D-11/D-12 algorithm; MEDIUM on the client week-id source (O-1).

**Research date:** 2026-06-19
**Valid until:** ~2026-07-19 (stable — internal code, no fast-moving external deps)
