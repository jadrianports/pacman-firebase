# Phase 6: In-Game Weekly Boards & Got-Passed Banner - Pattern Map

**Mapped:** 2026-06-20
**Files analyzed:** 9 (5 modified, 1–2 new, 3 test files)
**Analogs found:** 9 / 9 (every touched file extends an existing analog — this is a wiring/consumer phase, no greenfield infrastructure)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `cloud_functions/get_leaderboard/main.py` (MODIFY) | route / handler | request-response (Firestore read) | self — existing `scope=="all"`/weekly branch (lines 43–60) | exact (same file, new branch) |
| `api_service.py` (MODIFY) | service / API client | request-response | self — existing `get_leaderboard` (lines 29–36) + `submit_score` (10–27) | exact |
| `menu.py:run_leaderboard` (MODIFY) | component / screen | request-response + event-driven | self — `run_leaderboard` (113–171); toggle keys from `run_initials_entry` (95–108) | exact |
| `menu.py:run_main_menu` (MODIFY) | component / screen | event-driven | self — `run_main_menu` (11–44); passive-notice from `run_game_over_screen` (209–214) | exact |
| `main.py:main` (MODIFY) | controller / orchestrator | request-response (launch fetch) | self — startup flow (46–111), submit path (98–100) | exact |
| Marker IO (NEW — `local_storage.py` fn or new `marker.py`) | store / persistence | file-I/O | `local_storage._write/_read_identity_blob` (64–108) as the **anti-pattern**; `_safe_remove` (248–254) for tone | role-match (inverted: plain JSON, no HMAC) |
| `settings.py` (MODIFY — constants) | config | n/a | existing `IDENTITY_DIR_NAME`/`IDENTITY_FILE_NAME` (83–84), `FONT_*`/`COLOR_*` (61–70) | exact |
| `tests/test_get_leaderboard.py` (MODIFY) | test | n/a | `test_scope_week_queries_weekly` (123–138), `_stub_stream` (42–56) | exact |
| `tests/test_api_service.py` (MODIFY) | test | n/a | `test_submit_score_sends_signature_field` (41–58), `test_get_leaderboard_*` (76–94) | exact |

Client week-id source (O-1) **RESOLVED**: the repo-root `leaderboard_crypto.py` exposes only `canonical_message`, `sign_submission`, `obfuscate`, `de_obfuscate`, `sign_identity_blob`, `verify_identity_blob` — **no `current_week_id`**. Therefore the client must compute Monday-UTC inline with stdlib `datetime` (RESEARCH §4 option (c)). Mirror the server helper below.

## Pattern Assignments

### `cloud_functions/get_leaderboard/main.py` (route, request-response) — D-01 / BOARD-04

**Analog:** itself — the existing scope dispatch.

**Scope parse to extend** (lines 38–39), add `"last_week"` to the allow-list:
```python
scope = (request.args.get("scope") or "week").lower()
if scope not in ("week", "all"):   # → add "last_week"
    scope = "week"
```

**Weekly query branch to clone** (lines 55–60) — the new `last_week` branch is this branch with `previous_week_id(current_week_id())` instead of `current_week_id()`:
```python
query = (
    db.collection("weekly")
    .where("week_id", "==", leaderboard_crypto.current_week_id())
    .order_by("score", direction=firestore.Query.DESCENDING)
    .limit(10)
)
```
New branch (insert as `elif scope == "last_week":` before the weekly `else`):
```python
elif scope == "last_week":
    last = leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())
    query = (
        db.collection("weekly")
        .where("week_id", "==", last)
        .order_by("score", direction=firestore.Query.DESCENDING)
        .limit(10)
    )
```

**Projection loop — UNCHANGED** (lines 62–68): keep `{"initials": data["initials"], "score": data["score"]}` (machine_id/week_id/updated_at stripped, D-10).

**Helpers (no change)** `cloud_functions/get_leaderboard/leaderboard_crypto.py`:
- `current_week_id(now=None)` (66–77): Monday-UTC `%Y-%m-%d`.
- `previous_week_id(week_id)` (80–83): parses `%Y-%m-%d`, subtracts 7 days, returns string.

**Landmine — do NOT touch** the dual-import block (lines 13–16: `if __package__: from . import leaderboard_crypto / else: import leaderboard_crypto`). It is load-bearing for deploy vs. test import roots. Call helpers module-qualified, exactly as line 57 already does.

---

### `api_service.py` (service, request-response) — D-14 / D-15

**Analog:** the current `get_leaderboard` (lines 29–36).

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

**Change:** add `scope=None, timeout=10`; build the query string with stdlib `urlencode` (add `from urllib.parse import urlencode` next to the line-2 import). Keep the `try/except → None` contract (the board treats `None` as offline at `menu.py:138`, `[]` as empty at `menu.py:143`):
```python
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
`scope=None` → no param → server defaults to `week` (preserves the no-arg caller + `test_get_leaderboard_success`). `timeout=10` preserves the board default; only the launch fetch passes the short value (D-09). **Do NOT hardcode the short timeout here** (Pitfall 2).

---

### `menu.py:run_leaderboard` (component, request-response + event-driven) — D-02/03/04/16/17/19

**Analog:** itself (113–171) for structure; `run_initials_entry` (95–108) for the LEFT/RIGHT key handling pattern.

**Current single-fetch (line 127)** becomes per-view lazy cache. Use a distinct sentinel so the three meaningful states never collide (Pitfall 1):
- `_UNFETCHED = object()` (module-level) → needs fetch; `None` → offline; `[]` → empty; `list` → data.

**Header render to keep** (lines 134–136), then insert tab indicator + subtitle below it:
```python
header = header_font.render("LEADERBOARD", True, COLOR_YELLOW)
header_rect = header.get_rect(center=(WIDTH // 2, 80))
screen.blit(header, header_rect)
```
Per UI-SPEC y-anchors: tab indicator `< This Week | All Time >` at **y=128** (24px `FONT_SMALL`; active side `COLOR_YELLOW`, inactive + separators `COLOR_GRAY`); last-week subtitle `Last week: {INITIALS}` at **y=152** (`COLOR_GRAY`, This Week only, hide if `None`/`[]` — D-16); first entry stays y=180 step 50.

**Degrade/empty branches to reuse + specialize** (lines 138–146):
```python
if entries is None:
    msg = entry_font.render("Could not connect to leaderboard.", True, COLOR_GRAY)  # keep verbatim (D-15)
elif len(entries) == 0:
    msg = entry_font.render("No scores yet. Be the first!", True, COLOR_GRAY)  # D-17: This Week → "No scores yet this week. Be the first!"
```
Make the empty-state string conditional on `active`.

**Entry render — keep byte-for-byte** (lines 148–157), incl. rank-1 yellow / rest white (line 154). No self-highlight (D-19). Keep 50px row pitch.

**Event loop** (164–169): keep ESC/ENTER exit; add LEFT/RIGHT to flip `active` between `"week"`/`"all"`, lazy-fetching `all` on first switch (show existing `Loading...`, 119–124). Pattern for LEFT/RIGHT mirrors `run_initials_entry` lines 103–106. Replace the hint string (line 160) with `LEFT/RIGHT: switch board   ESC/ENTER: back`.

**Board-open side effect (D-07/D-10)** — O-2/O-3: opening this screen must rewrite the marker baseline + clear the banner, using the This Week entries it already fetched. Planner decides the seam (pass `tracked_best`/marker helpers in, or return the week entries to `main.py`). Update the single call site `main.py:109` accordingly.

---

### `menu.py:run_main_menu` (component, event-driven) — D-08

**Analog:** itself (11–44); passive-notice rendering from `run_game_over_screen` (209–214).

**Title render to keep** (22–24), add a banner line beneath at **y=230** (per UI-SPEC), `COLOR_YELLOW`, `FONT_SMALL`, rendered only when truthy:
```python
title = title_font.render("PAC-MAN", True, COLOR_YELLOW)
title_rect = title.get_rect(center=(WIDTH // 2, 150))
screen.blit(title, title_rect)
```
**Passive-notice pattern to mirror** (`run_game_over_screen`, 209–214) — conditional, non-blocking line:
```python
if identity_error:
    notice = hint_font.render("Score not saved — identity error", True, COLOR_GRAY)
    notice_rect = notice.get_rect(center=(WIDTH // 2, 540))
    screen.blit(notice, notice_rect)
```
Apply the same shape: add `banner_text=None` param; render `banner_text` (yellow, y=230) only when truthy. Banner copy (UI-SPEC): `{A}, {B}, {C} passed you this week!`, over-cap → `{A}, {B}, {C} +{K} more passed you this week!` (cap = 3, `sorted(new_passers)`).

---

### `main.py:main` (controller, request-response) — D-05/08/09/11/12/18

**Analog:** itself — identity-resolve block (58–61), submit path (98–100), menu loop (72–110).

**Insert banner compute after identity resolves (after line 61), before the loop (line 72):**
1. Load marker (§marker below). Absent → no banner (D-18).
2. No `tracked_best`/`initials` for current week → no banner (D-05).
3. Short-timeout fetch: `api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)`. `None` → skip banner (D-09/D-18). **No threading.**
4. Compute passers, pass `banner_text` into `run_main_menu`.

**Passer compute (D-11/D-12)** — store the SET of initials above your best at last view:
```python
above_now = {e["initials"] for e in this_week_entries if e["score"] > tracked_best}
new_passers = sorted(above_now - set(marker.get("initials_above", [])))
banner_text = _format_banner(new_passers) if new_passers else None  # cap=3, D-06
```

**Submit-path hook to extend** (lines 98–100) — after a successful submit, update the locally tracked this-week best:
```python
response = api.submit_score(machine_id, initials, score, signature)
is_new_best = response is not None and response.get("is_new_best", False)
# ADD: update marker tracked_best = max(tracked_best, score) if this week; re-baseline on week rollover
```

**Board call site** (108–109) is the single place to wire the baseline rewrite (O-2/O-3):
```python
elif choice == "Leaderboard":
    run_leaderboard(screen, timer, api)   # signature gains marker/tracked_best per O-3
```

---

### Marker file IO (store, file-I/O) — D-13 (NEW behavior)

**Anti-analog (do the OPPOSITE of):** `local_storage._write_identity_blob` / `_read_identity_blob` (64–108). The identity blob is obfuscated + HMAC-signed + `{"sig","blob"}` envelope, and present-but-invalid fail-closes as TAMPERED. **The marker is plain JSON, unsigned, best-effort** — any read failure → treat as "no marker", re-baseline silently.

**Tone analog to copy:** `_safe_remove` (248–254) — best-effort, never raises:
```python
def _safe_remove(path):
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass
```

**Path:** `paths.user_data_path(MARKER_FILE_NAME)` (paths.py:30–32) — resolves `%LOCALAPPDATA%\PacMan\` with `~/.pacman` dev fallback; `user_data_dir()` already does `makedirs(exist_ok=True)` (paths.py:26), so just `json.dump`/`json.load` inside try/except.

**Shape:** `{"week_id": "2026-06-15", "tracked_best": 8000, "initials_above": ["JIM", "BOB"]}`. On load, if `marker["week_id"] != client_current_week_id()` → discard (silent re-baseline, D-13).

**Client week-id (O-1 resolved):** compute Monday-UTC inline with stdlib, mirroring server `current_week_id` (leaderboard_crypto.py:73–77):
```python
from datetime import datetime, timezone, timedelta
now = datetime.now(timezone.utc)
monday = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
week_id = monday.strftime("%Y-%m-%d")
```

---

### `settings.py` (config) — new constants

**Analog:** existing constant blocks (lines 61–70 colors/fonts, 83–89 identity/file names).

Add next to `IDENTITY_FILE_NAME` (line 84):
```python
MARKER_FILE_NAME = "last_viewed.json"        # unsigned marker, D-13
BANNER_FETCH_TIMEOUT_SECONDS = 2             # short launch fetch, D-09 (UI-SPEC DECIDED: 2s)
```
Reuse existing `COLOR_YELLOW`/`COLOR_GRAY`/`COLOR_WHITE` (61–63) and `FONT_SMALL`/`FONT_MENU` (69–70) — no new colors/fonts (UI-SPEC).

---

### `tests/test_get_leaderboard.py` (test) — extend for `last_week`

**Analog:** `test_scope_week_queries_weekly` (123–138) + `_stub_stream` (42–56) + `make_request(query_string=...)` (24–27).

Mirror exactly (import helper as line 125 does):
```python
from cloud_functions.get_leaderboard import leaderboard_crypto
db.collection.assert_called_with("weekly")
db.collection.return_value.where.assert_called_with(
    "week_id", "==", leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())
)
```
Add: `test_scope_last_week_queries_weekly_with_previous_week`, `test_scope_last_week_projects_only_initials_and_score` (mirror 161–172), and confirm `last_week` is now allow-listed (extend `test_garbage_scope_falls_back_to_week` reasoning, 150–158).

---

### `tests/test_api_service.py` (test) — extend for scope + timeout

**Analog:** `test_submit_score_sends_signature_field` (41–58, the request-capture via `_fake_urlopen(req, timeout=None)`) + `test_get_leaderboard_success/_empty/_network_error` (76–94).

The `_fake_urlopen(req, timeout=None)` signature already captures `timeout` — assert it threads through:
```python
def _fake_urlopen(req, timeout=None):
    captured["url"] = req.get_full_url()
    captured["timeout"] = timeout
    return _mock_response({"entries": []})
```
Add: `test_get_leaderboard_sends_scope_param` (assert `scope=last_week`/`scope=all` in `req.get_full_url()`), `test_get_leaderboard_no_scope_omits_param` (URL == base), `test_get_leaderboard_passes_timeout` (short value threads through).

## Shared Patterns

### Graceful degrade (SC-4)
**Source:** `menu.py:138–146` (None→offline line, []→empty line) and `run_game_over_screen:209–214` (passive gray notice).
**Apply to:** every board view (D-15), the last-week subtitle (hide on fail, D-16), and the launch banner (skip on `None`, D-18). `COLOR_GRAY`, `FONT_SMALL`, centered.
```python
if entries is None:
    msg = entry_font.render("Could not connect to leaderboard.", True, COLOR_GRAY)
```

### Best-effort local IO (never raise)
**Source:** `local_storage._safe_remove` (248–254); `api_service` `try/except → None` (26–27, 35–36).
**Apply to:** all marker read/write (D-13) and the launch fetch. Swallow every exception; a wrong/missing marker is harmless.

### Per-user storage location
**Source:** `paths.user_data_path` (30–32) → `user_data_dir()` (7–27), `%LOCALAPPDATA%\PacMan\` (`~/.pacman` fallback, `exist_ok=True`).
**Apply to:** the marker file. Do not build a new resolver.

### Centered-blit screen rendering
**Source:** every `menu.py` screen — `font.render(text, True, COLOR)` → `.get_rect(center=(WIDTH//2, y))` → `screen.blit`. Loop on `timer.tick(FPS)` + `screen.fill("black")` + `pygame.display.flip()`.
**Apply to:** tab indicator, subtitle, banner line. y-anchors fixed by UI-SPEC (tab 128, subtitle 152, banner 230).

### Stdlib-only networking
**Source:** `api_service.py` uses `urllib.request`; add `urllib.parse.urlencode`. `json`/`os`/`datetime` for marker.
**Apply to:** all new client code. **No new dependencies** (PyInstaller + stdlib-only contract).

## No Analog Found

None. Every touched file extends an existing analog in the same file or a sibling module. The only genuinely "new" artifact is the unsigned marker file, which is deliberately modeled as the **inverse** of the existing signed identity blob (plain JSON vs. obfuscated+HMAC envelope) using the established `_safe_remove` best-effort tone and `paths.user_data_path` storage seam.

## Metadata

**Analog search scope:** repo root (`api_service.py`, `menu.py`, `main.py`, `paths.py`, `local_storage.py`, `settings.py`, `leaderboard_crypto.py`), `cloud_functions/get_leaderboard/`, `tests/`.
**Files scanned:** 9 read + 1 grep (root `leaderboard_crypto.py` for O-1).
**Resolved open questions:** O-1 (client has no `current_week_id` → compute Monday-UTC inline with stdlib `datetime`).
**Pattern extraction date:** 2026-06-20
