---
type: codebase-map
focus: concerns
doc: CONCERNS
generated: 2026-06-01
last_mapped_commit: 5e8d4b1773c03b4d3953200a764d658a431911de
---

# Concerns, Tech Debt & Risks

Scope: a hobby/learning Pac-Man clone. Severity is judged relative to that context — none of these block the game from running, but several would bite during future feature work. Ordered roughly by impact.

## Security

### S1 — Leaderboard endpoints are public and unauthenticated; scores are forgeable  ·  Medium
`cloud_functions/submit_score/main.py` and `get_leaderboard/main.py` are HTTP functions with `Access-Control-Allow-Origin: *` and **no auth**. Identity is the client-generated `machine_id` (a local `uuid.uuid4()`), and `initials`/`score` come straight from the request body. Anyone can `POST` any `initials` + any `score` up to `MAX_SCORE` (500,000) under any `machine_id`. The only guards are the regex (`^[A-Z]{3}$`), the int/range check, and the per-`machine_id` best-score upsert.
- **Impact:** the public leaderboard can be trivially spoofed/poisoned.
- **Acceptable for a toy project**, but document the trust boundary. If it ever matters: add an app-level shared secret / signed payload, App Check, server-side rate limiting, or move identity server-side.

### S2 — Service-account key present on disk  ·  Low (currently well-handled)
`firebase-key.json` is a real Google service-account private key (project `pacman-firebase`). **Good news, verified:** it is git-ignored (`.gitignore:19`) and `git log --all -- firebase-key.json` shows it was **never committed**. The risk is only that a future `git add -f` or a tooling mistake could leak it.
- **Action:** keep it ignored; never paste its contents anywhere (including planning docs). The deployed functions use Application Default Credentials (`initialize_app()` with no args), so this file is not needed at runtime in the cloud.

### S3 — `.claude/settings.local.json` is committed despite `/.claude` in `.gitignore`  ·  Low
The file is tracked (most recent commit `5e8d4b1` "Update settings.local.json") even though `.gitignore` lists `/.claude` (twice). `.gitignore` does not untrack already-tracked files. It contains only local permissions + enabled-plugins config (no secrets), so impact is minimal — but it's an inconsistency and leaks local tool config.

## Tech Debt / Maintainability

### D1 — Massive duplication across the four ghost movement methods  ·  High (maintainability)
`ghost.py` is ~600 lines, dominated by `move_blinky`, `move_inky`, `move_pinky`, `move_clyde` — each a ~120-line `if direction == 0/1/2/3` ladder that is ~90% identical, differing only in subtle turn-preference ordering that encodes "personality." `move_clyde` is also reused as the fallback mover for dead/in-box ghosts.
- **Impact:** any change to turning/wrap logic must be replicated 4×; high risk of the variants drifting out of sync; very hard to test or reason about.
- **Direction:** extract the shared skeleton (a parameterized turn-priority table) so each personality is data, not a copied method.

### D2 — Pervasive magic numbers and duplicated tile math  ·  High (readability)
Tile geometry is recomputed inline in at least three modules:
```python
num1 = (HEIGHT - 50) // 32   # game.py, ghost.py, player.py
num2 = WIDTH // 30
num3 = 15
```
plus hardcoded pixel literals throughout (`900`, `870`, `-30`, `-47`, box bounds, target points like `(400, 100)`, `(380, 400)`, `(450, 450)`). `settings.py` centralizes top-level constants but none of this tile/positional math.
- **Direction:** derive tile size once (a shared helper or `settings`), name the board geometry, and replace literals.

### D3 — Inconsistent "ghost box" region definition  ·  Medium (latent bug)
The central-box region is defined with **different bounds in two places**:
- `game.py:get_targets` → `340 < x < 560 and 340 < y < 500`
- `ghost.py:check_collisions` → `350 < x_pos < 550 and 360 < y_pos < 480`

These overlap but are not the same rectangle, so "am I in the box?" can disagree between targeting and collision/turn logic at the edges. This is fragile and a likely source of subtle ghost-exit/targeting glitches. Define the box once and reuse it.

### D4 — Two parallel collision implementations to keep in sync  ·  Medium
`Player.check_position` and `Ghost.check_collisions` independently reimplement very similar tile-walkability/turn-legality logic against the same `boards` grid (with the ghost version additionally handling gate tile `9`). Changes to the maze or movement rules must be mirrored in both.

### D5 — Two overlapping build definitions  ·  Low
`build.py` (documented as `python build.py`) and `pacman.spec` describe the same PyInstaller bundle. The `.spec` is git-ignored, so `build.py` is the source of truth, but having both invites confusion about which to use.

### D6 — Duplicate, unused asset directories  ·  Low
`assets/ghost_images/` and `assets/player_images/` duplicate `assets/ghosts/` and `assets/pacman/` but are not referenced by any code (game.py loads from `assets/ghosts/`, player.py from `assets/pacman/`). Dead weight in the repo and the PyInstaller bundle (`--add-data=assets;assets` ships everything). Safe to delete after confirming no external reference.

## Correctness / Robustness

### C1 — Object construction has rendering side effects  ·  Medium
`Ghost.__init__` calls `self.check_collisions()` and `self.draw()` (which `blit`s to the screen) as part of construction, and `Game.create_ghosts()` runs every frame. Construction, simulation, and rendering are entangled, which:
- makes ghosts impossible to instantiate for a unit test without a real surface, and
- couples draw order to object-creation order.

### C2 — `firebase_admin` initialized at import time in each function  ·  Low
Both cloud functions call `initialize_app()` and `firestore.client()` at module import (guarded by `if not firebase_admin._apps`). Standard for Functions, but it means import-time failures (bad creds/permissions) surface as cold-start errors rather than per-request handling.

### C3 — Broad `except Exception` hides real errors  ·  Low
`api_service.py` returns `None` on *any* exception (including programming errors like a JSON schema change), and the cloud functions catch-all to a generic `500`. Good for offline UX, but it can mask bugs during development. Consider narrowing or at least logging client-side.

## Documentation Drift

### DOC1 — `CLAUDE.md` ghost box-exit timing doesn't match `settings.py`  ·  Low
`CLAUDE.md` states "Pinky after ~2 sec, Clyde after ~4 sec," but `settings.py` sets `BOX_EXIT_DELAY_PINKY = 30` and `BOX_EXIT_DELAY_CLYDE = 60` frames. At `FPS = 60` those are ≈0.5 s and ≈1 s, not 2 s / 4 s. (Inky = 0 is consistent — "exits immediately.") Either the delays were tuned down without updating the doc, or the prose is approximate. Reconcile the doc with the constants.

### DOC2 — Dead "Change Initials" reference  ·  Low
`menu.py:run_main_menu`'s docstring lists a `'Change Initials'` return value, but `MENU_OPTIONS = ["Play", "Leaderboard", "Quit"]` has no such entry, and `CLAUDE.md` confirms initials are permanent. Stale docstring.

## Process / Quality Gaps

### P1 — No CI, no enforced style, key logic untested  ·  Medium
No `.github/workflows`, no linter/formatter config, and tests cover only `api_service.py` + `local_storage.py` (see `TESTING.md`). The highest-complexity, highest-risk code — ghost AI (`ghost.py`), the game loop (`game.py`), and the backend validators — has **zero** automated coverage. Combined with D1/D2, this makes gameplay changes risky to verify.

### P2 — Unpinned client dependencies  ·  Low
Client `requirements.txt` pins nothing (`pygame`, `pyinstaller`); a future pygame major release could change rendering/audio behavior. Backend pins major versions only (`3.*`, `6.*`). Consider pinning for reproducible builds.

---

## Quick Triage

| ID | Concern | Severity | Type |
|----|---------|----------|------|
| S1 | Forgeable, unauthenticated leaderboard | Medium | Security |
| S2 | Service-account key on disk (ignored, never committed) | Low | Security |
| S3 | `.claude/settings.local.json` tracked despite ignore | Low | Security |
| D1 | 4× duplicated ghost movement methods | High | Debt |
| D2 | Magic numbers / duplicated tile math | High | Debt |
| D3 | Inconsistent ghost-box bounds (2 definitions) | Medium | Debt/Bug |
| D4 | Two parallel collision implementations | Medium | Debt |
| D5 | Overlapping `build.py` vs `pacman.spec` | Low | Debt |
| D6 | Unused duplicate asset folders | Low | Debt |
| C1 | Rendering side effects in `Ghost.__init__` | Medium | Correctness |
| C2 | Import-time Firebase init | Low | Correctness |
| C3 | Broad `except` hides errors | Low | Correctness |
| DOC1 | Box-exit timing doc vs settings mismatch | Low | Docs |
| DOC2 | Dead "Change Initials" docstring | Low | Docs |
| P1 | No CI; core logic & backend untested | Medium | Process |
| P2 | Unpinned client deps | Low | Process |
