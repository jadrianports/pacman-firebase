# PyGame Glow-Up — Brand Match Implementation Plan (2 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle the four standalone `menu.py` screens to the web-page retro-arcade aesthetic (Press Start 2P pixel font, reserved yellow accent, navy panels, CRT scanlines) using the `theme.py` primitives — gameplay untouched.

**Architecture:** Fork `redesign/brand-match` off `redesign/base`. For each `menu.py` screen, extract the per-frame drawing out of its event loop into a pure `_render_*(screen, ...)` function, restyle that function with `theme.pixel_font` / `theme.glow_text` / `theme.scanline_overlay`, and have the existing loop call it. The loops' event handling, return values, lazy caches, and verbatim copy strings are preserved exactly — only rendering changes. `game.py` is not touched, so the deterministic golden traces are structurally safe.

**Tech Stack:** Python 3.12, pygame-ce 2.5.7, `theme.py` (from plan 1), pytest. **No new dependencies.**

## Deviation from spec (requires sign-off before execution)

The design spec named **pygame_gui** for Brand Match's menus. This plan hand-draws with `theme.py` instead. Rationale: these screens are static (no widgets that benefit from retained mode); pygame_gui would add a dependency + PyInstaller theme/data-file bundling + a rewrite of `menu.py`'s loops (which carry quit-propagation and lazy-cache contracts). Hand-drawing achieves the same faithful look with a minimal-diff restyle and zero new deps. The visual outcome the spec wants is met either way. **If you prefer the pygame_gui route, say so and this plan is rewritten.**

## Global Constraints

- **Branch:** `redesign/brand-match`, forked from `redesign/base` (which has pygame-ce + `theme.py`).
- **Scope:** ONLY `menu.py` rendering + `tools/contact_sheet.py` capture hooks + new tests. **`game.py` and all simulation code are NOT touched** — the gameplay golden traces must stay structurally untouched.
- **No new dependencies.** Use `theme.py` (`pixel_font`, `SIZE_*`, `glow_text`, `scanline_overlay`) and `settings.COLOR_*` only.
- **Preserve behavioral contracts verbatim** in every `menu.py` function:
  - `run_main_menu` returns the selected option string; renders the optional `banner_text` in yellow when truthy.
  - `run_initials_entry` returns the 3-letter string; UP/DOWN change letter, LEFT/RIGHT move slot, ENTER confirm.
  - `run_leaderboard` returns `(quit_requested, week_entries)`; opens on This Week (D-02); LEFT/RIGHT toggle; All Time lazy-fetched once on first toggle; `_UNFETCHED`/`None`/`[]`/`[...]` truth table; ESC/ENTER back.
  - `run_game_over_screen` returns after SPACE; `"quit"` on window close.
- **Verbatim copy strings (do not reword):** `"This Week"`, `"All Time"`, `"Last week: {initials}"`, `"No scores yet this week. Be the first!"`, `"No scores yet. Be the first!"`, `"Could not connect to leaderboard."`, `"Score not saved — identity error"`, `"NEW BEST!"`, `"VICTORY!"`, `"GAME OVER"`, `"ENTER YOUR INITIALS"`.
- **Reserved accent:** yellow `COLOR_YELLOW` (#FFFF00) for titles/active/rank-1 only; white for normal, gray for supporting.
- **Glow discipline:** title `radius=6`, menu items `radius=4` (the demo's `radius=10` was too mushy — dialed back per the spec's "tasteful" note).
- **Suite:** stays green. Baseline on this branch is `150 passed, 9 skipped`; new tests add to the pass count, the 9 skips (Linux golden traces) remain.
- **Python env:** run tests/scripts via `.venv/Scripts/python.exe`.

---

### Task 1: Branch + backdrop helper + restyle the main menu

**Files:**
- Create branch `redesign/brand-match`
- Modify: `menu.py` (add `_draw_backdrop`, extract `_render_main_menu`, restyle `run_main_menu`)
- Test: `tests/test_menu_render.py` (created here)

**Interfaces:**
- Consumes: `theme.pixel_font`, `theme.SIZE_*`, `theme.glow_text`, `theme.scanline_overlay`; `settings.WIDTH/HEIGHT/COLOR_*/MENU_OPTIONS`.
- Produces:
  - `menu._draw_backdrop(screen)` — fills navy and blits the cached scanline overlay; called first by every `_render_*`.
  - `menu._render_main_menu(screen, selected, banner_text=None)` — draws one main-menu frame.

- [ ] **Step 1: Create the branch**

```bash
git switch redesign/base
git switch -c redesign/brand-match
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_menu_render.py`:

```python
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest
from settings import WIDTH, HEIGHT, COLOR_YELLOW
import menu


@pytest.fixture(autouse=True)
def _pygame():
    pygame.init()
    pygame.display.set_mode((WIDTH, HEIGHT))
    yield


def _has_color(surface, rgb, band=None, tol=40):
    """True if any pixel in the (optional) y-band is within `tol` per channel of
    rgb. Tolerance (not exact match) so the translucent scanline overlay darkening
    a glyph pixel by ~18% doesn't cause false negatives."""
    y0, y1 = band if band else (0, surface.get_height())
    tr, tg, tb = rgb
    for y in range(y0, y1, 2):
        for x in range(0, surface.get_width(), 2):
            r, g, b = surface.get_at((x, y))[:3]
            if abs(r - tr) <= tol and abs(g - tg) <= tol and abs(b - tb) <= tol:
                return True
    return False


def test_main_menu_renders_yellow_title_and_active_option():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_main_menu(screen, selected=0)
    # title band (top ~quarter) carries the yellow glow
    assert _has_color(screen, COLOR_YELLOW, band=(80, 260))
    # selected option (index 0) is yellow somewhere in the options band
    assert _has_color(screen, COLOR_YELLOW, band=(320, 600))


def test_main_menu_banner_renders_without_error():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_main_menu(screen, selected=1, banner_text="JAM passed you this week!")
    assert _has_color(screen, COLOR_YELLOW, band=(200, 260))
```

- [ ] **Step 3: Run it to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py -v`
Expected: FAIL with `AttributeError: module 'menu' has no attribute '_render_main_menu'`.

- [ ] **Step 4: Implement the backdrop helper and the extracted renderer**

In `menu.py`, update the imports at the top to add `theme` and the dims/colors used:

```python
import pygame
import theme
from paths import resource_path
from settings import (
    WIDTH, HEIGHT, FPS,
    COLOR_YELLOW, COLOR_WHITE, COLOR_GRAY, COLOR_RED, COLOR_GREEN,
    MENU_OPTIONS, LEADERBOARD_LINE_WIDTH,
)
```

(Remove the now-unused `FONT_TITLE, FONT_MENU, FONT_SMALL` from the import — the pixel sizes come from `theme` now.)

Add these helpers near the top of `menu.py`, after the `_UNFETCHED` sentinel:

```python
COLOR_BACKDROP = (6, 6, 18)  # deep navy-black, matches the web page body


def _draw_backdrop(screen):
    """Fill the navy backdrop and lay the CRT scanline overlay. Every screen
    starts here so the whole app shares one arcade canvas."""
    screen.fill(COLOR_BACKDROP)
    screen.blit(theme.scanline_overlay((WIDTH, HEIGHT), spacing=3, alpha=45), (0, 0))


def _blit_center(screen, surface, center):
    screen.blit(surface, surface.get_rect(center=center))


def _render_main_menu(screen, selected, banner_text=None):
    """Draw one main-menu frame: glowing pixel title, optional banner, and the
    Play/Leaderboard/Quit options with the selected one glowing yellow."""
    _draw_backdrop(screen)

    title = theme.glow_text("PAC-MAN", theme.pixel_font(theme.SIZE_TITLE), COLOR_YELLOW, radius=6)
    _blit_center(screen, title, (WIDTH // 2, 150))

    if banner_text:
        banner = theme.pixel_font(theme.SIZE_SMALL).render(banner_text, True, COLOR_YELLOW)
        _blit_center(screen, banner, (WIDTH // 2, 230))

    menu_font = theme.pixel_font(theme.SIZE_MENU)
    for i, option in enumerate(MENU_OPTIONS):
        y = 350 + i * 70
        if i == selected:
            surf = theme.glow_text(option, menu_font, COLOR_YELLOW, radius=4)
            rect = surf.get_rect(center=(WIDTH // 2, y))
            screen.blit(surf, rect)
            cursor = theme.glow_text(">", menu_font, COLOR_YELLOW, radius=4)
            screen.blit(cursor, cursor.get_rect(midright=(rect.left - 16, y)))
        else:
            surf = menu_font.render(option, True, COLOR_WHITE)
            _blit_center(screen, surf, (WIDTH // 2, y))
```

Then replace the drawing block inside `run_main_menu`'s loop. The loop keeps `timer.tick(FPS)`, event handling, and `pygame.display.flip()`; the body between `timer.tick(FPS)` and the event loop becomes a single call:

```python
    title_font = None  # (delete the three pygame.font.Font lines at the top of run_main_menu)
    selected = 0

    while True:
        timer.tick(FPS)
        _render_main_menu(screen, selected, banner_text)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(MENU_OPTIONS)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(MENU_OPTIONS)
                elif event.key == pygame.K_RETURN:
                    return MENU_OPTIONS[selected]

        pygame.display.flip()
```

(Delete the three `pygame.font.Font(resource_path("freesansbold.ttf"), ...)` lines that opened `run_main_menu`; the `title_font = None` line above is a marker — remove it, do not leave a dangling assignment.)

- [ ] **Step 5: Run the test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py -v`
Expected: both tests PASS.

- [ ] **Step 6: Run the full suite (nothing else regressed)**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: `152 passed, 9 skipped` (150 prior + 2 new).

- [ ] **Step 7: Commit**

```bash
git add menu.py tests/test_menu_render.py
git commit -m "feat(brand): retro-arcade main menu via theme primitives"
```

---

### Task 2: Restyle the initials-entry screen

**Files:**
- Modify: `menu.py` (extract `_render_initials`, restyle `run_initials_entry`)
- Test: `tests/test_menu_render.py` (append)

**Interfaces:**
- Consumes: `theme`, `_draw_backdrop`, `_blit_center` (from Task 1).
- Produces: `menu._render_initials(screen, letters, slot)` — draws one initials-entry frame; `letters` is a list of three 0-25 ints, `slot` the active index.

- [ ] **Step 1: Write the failing test (append)**

```python
def test_initials_renders_active_slot_yellow():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_initials(screen, letters=[0, 1, 2], slot=1)
    # header present (yellow band near top)
    assert _has_color(screen, COLOR_YELLOW, band=(160, 240))
    # the active slot glyph row carries yellow
    assert _has_color(screen, COLOR_YELLOW, band=(360, 440))
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py::test_initials_renders_active_slot_yellow -v`
Expected: FAIL — `_render_initials` not defined.

- [ ] **Step 3: Implement the renderer and rewire the loop**

Add to `menu.py`:

```python
def _render_initials(screen, letters, slot):
    """Draw one initials-entry frame: header, three bracketed letter slots (the
    active one glows yellow with up/down arrows), and the control hint."""
    _draw_backdrop(screen)

    header = theme.glow_text("ENTER YOUR INITIALS", theme.pixel_font(theme.SIZE_HEADING),
                             COLOR_YELLOW, radius=4)
    _blit_center(screen, header, (WIDTH // 2, 200))

    letter_font = theme.pixel_font(theme.SIZE_TITLE)
    hint_font = theme.pixel_font(theme.SIZE_SMALL)
    total_width = 3 * 80 + 2 * 40
    start_x = (WIDTH - total_width) // 2
    for i in range(3):
        letter_char = chr(ord("A") + letters[i])
        x = start_x + i * 120 + 40
        if i == slot:
            bracket = theme.glow_text(f"[ {letter_char} ]", letter_font, COLOR_YELLOW, radius=4)
            _blit_center(screen, bracket, (x, 400))
            _blit_center(screen, hint_font.render("^", True, COLOR_GRAY), (x, 330))
            _blit_center(screen, hint_font.render("v", True, COLOR_GRAY), (x, 470))
        else:
            bracket = letter_font.render(f"[ {letter_char} ]", True, COLOR_WHITE)
            _blit_center(screen, bracket, (x, 400))

    hint = hint_font.render("UP/DOWN: change letter   LEFT/RIGHT: move   ENTER: confirm",
                            True, COLOR_GRAY)
    _blit_center(screen, hint, (WIDTH // 2, 600))
```

In `run_initials_entry`, delete the three `pygame.font.Font(...)` lines at the top, keep the `letters`/`slot` setup, and replace the draw block in the loop with:

```python
    while True:
        timer.tick(FPS)
        _render_initials(screen, letters, slot)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    letters[slot] = (letters[slot] - 1) % 26
                elif event.key == pygame.K_DOWN:
                    letters[slot] = (letters[slot] + 1) % 26
                elif event.key == pygame.K_LEFT:
                    slot = (slot - 1) % 3
                elif event.key == pygame.K_RIGHT:
                    slot = (slot + 1) % 3
                elif event.key == pygame.K_RETURN:
                    return "".join(chr(ord("A") + l) for l in letters)

        pygame.display.flip()
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py::test_initials_renders_active_slot_yellow -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: `153 passed, 9 skipped`.

- [ ] **Step 6: Commit**

```bash
git add menu.py tests/test_menu_render.py
git commit -m "feat(brand): retro-arcade initials entry"
```

---

### Task 3: Restyle the leaderboard screen

**Files:**
- Modify: `menu.py` (extract `_render_leaderboard`, restyle the draw block of `run_leaderboard`; `_show_loading` restyled too)
- Test: `tests/test_menu_render.py` (append)

**Interfaces:**
- Consumes: `theme`, `_draw_backdrop`, `_blit_center`; `LEADERBOARD_LINE_WIDTH`.
- Produces: `menu._render_leaderboard(screen, active, entries, last_week_initials)` — draws one leaderboard frame for the given `active` view (`"week"`/`"all"`), `entries` (`None`=offline, `[]`=empty, list=data), and optional `last_week_initials`.

- [ ] **Step 1: Write the failing test (append)**

```python
def test_leaderboard_data_rank1_yellow_and_tab_active():
    screen = pygame.Surface((WIDTH, HEIGHT))
    entries = [{"initials": "JAP", "score": 7540}, {"initials": "JEM", "score": 4140}]
    menu._render_leaderboard(screen, active="week", entries=entries, last_week_initials="ZZZ")
    # rank-1 row is yellow
    assert _has_color(screen, COLOR_YELLOW, band=(160, 220))


def test_leaderboard_offline_shows_verbatim_copy():
    screen = pygame.Surface((WIDTH, HEIGHT))
    # None == offline; renders without error. We assert the renderer handles the
    # sentinel (no exception) — copy correctness is covered by the string constant.
    menu._render_leaderboard(screen, active="all", entries=None, last_week_initials=None)


def test_leaderboard_empty_renders():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_leaderboard(screen, active="week", entries=[], last_week_initials=None)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py::test_leaderboard_data_rank1_yellow_and_tab_active -v`
Expected: FAIL — `_render_leaderboard` not defined.

- [ ] **Step 3: Implement the renderer and rewire**

Add to `menu.py`:

```python
_EMPTY_TEXT = {
    "week": "No scores yet this week. Be the first!",
    "all": "No scores yet. Be the first!",
}


def _render_leaderboard(screen, active, entries, last_week_initials):
    """Draw one leaderboard frame: glowing header, This Week | All Time tab bar
    (active side yellow), optional last-week subtitle (This Week only), and the
    board — offline/empty messages or dot-leader rows with rank 1 in yellow."""
    _draw_backdrop(screen)
    entry_font = theme.pixel_font(theme.SIZE_BODY)
    hint_font = theme.pixel_font(theme.SIZE_SMALL)

    header = theme.glow_text("LEADERBOARD", theme.pixel_font(theme.SIZE_HEADING),
                             COLOR_YELLOW, radius=5)
    _blit_center(screen, header, (WIDTH // 2, 80))

    # Tab bar: only the active label is yellow; separators/inactive gray.
    prefix = entry_font.render("< ", True, COLOR_GRAY)
    week_label = entry_font.render("This Week", True,
                                   COLOR_YELLOW if active == "week" else COLOR_GRAY)
    sep = entry_font.render(" | ", True, COLOR_GRAY)
    all_label = entry_font.render("All Time", True,
                                  COLOR_YELLOW if active == "all" else COLOR_GRAY)
    suffix = entry_font.render(" >", True, COLOR_GRAY)
    runs = (prefix, week_label, sep, all_label, suffix)
    tab_w = sum(s.get_width() for s in runs)
    tx, ty = WIDTH // 2 - tab_w // 2, 128
    for surf in runs:
        screen.blit(surf, (tx, ty - surf.get_height() // 2))
        tx += surf.get_width()

    if active == "week" and last_week_initials:
        subtitle = entry_font.render(f"Last week: {last_week_initials}", True, COLOR_GRAY)
        _blit_center(screen, subtitle, (WIDTH // 2, 158))

    if entries is None:
        _blit_center(screen, entry_font.render("Could not connect to leaderboard.", True, COLOR_GRAY),
                     (WIDTH // 2, HEIGHT // 2))
    elif len(entries) == 0:
        _blit_center(screen, entry_font.render(_EMPTY_TEXT[active], True, COLOR_GRAY),
                     (WIDTH // 2, HEIGHT // 2))
    else:
        for i, entry in enumerate(entries):
            rank = f"{i + 1}."
            initials = entry["initials"]
            score = str(entry["score"])
            fill = max(0, LEADERBOARD_LINE_WIDTH - len(rank) - len(initials) - len(score))
            line = f"{rank} {initials} {'.' * fill} {score}"
            color = COLOR_YELLOW if i == 0 else COLOR_WHITE
            _blit_center(screen, entry_font.render(line, True, color), (WIDTH // 2, 180 + i * 50))

    hint = hint_font.render("LEFT/RIGHT: switch board   ESC/ENTER: back", True, COLOR_GRAY)
    _blit_center(screen, hint, (WIDTH // 2, HEIGHT - 80))
```

Also restyle `_show_loading` to use the backdrop + pixel font:

```python
def _show_loading(screen):
    """Render the navy 'Loading...' frame (shown before a fetch)."""
    _draw_backdrop(screen)
    loading = theme.pixel_font(theme.SIZE_HEADING).render("Loading...", True, COLOR_WHITE)
    _blit_center(screen, loading, (WIDTH // 2, HEIGHT // 2))
    pygame.display.flip()
```

In `run_leaderboard`: delete the three `pygame.font.Font(...)` lines and the inline `empty_text` dict; update the two `_show_loading(screen, header_font)` calls to `_show_loading(screen)`; replace the entire draw block inside the loop (everything between `screen.fill("black")`/header and the `for event` loop) with:

```python
    while True:
        timer.tick(FPS)
        _render_leaderboard(screen, active, views[active], last_week_initials)

        for event in pygame.event.get():
            week_entries = views["week"] if views["week"] is not _UNFETCHED else None
            if event.type == pygame.QUIT:
                return True, week_entries
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return False, week_entries
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    active = "all" if active == "week" else "week"
                    if views[active] is _UNFETCHED:
                        _show_loading(screen)
                        views[active] = api_service.get_leaderboard(scope="all")

        pygame.display.flip()
```

The fetch-on-open lines before the loop (`_show_loading(screen)`, `views["week"] = ...`, `last_week = ...`, `last_week_initials = ...`) stay; just drop the `header_font` argument.

- [ ] **Step 4: Run the new tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py -k leaderboard -v`
Expected: all three PASS.

- [ ] **Step 5: Run the full suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: `156 passed, 9 skipped`.

- [ ] **Step 6: Commit**

```bash
git add menu.py tests/test_menu_render.py
git commit -m "feat(brand): retro-arcade leaderboard (tabs, dot-leaders, states)"
```

---

### Task 4: Restyle the game-over screen

**Files:**
- Modify: `menu.py` (extract `_render_game_over`, restyle `run_game_over_screen`)
- Test: `tests/test_menu_render.py` (append)

**Interfaces:**
- Consumes: `theme`, `_draw_backdrop`, `_blit_center`; `COLOR_RED/COLOR_GREEN`.
- Produces: `menu._render_game_over(screen, score, is_new_best, game_won, identity_error)`.

- [ ] **Step 1: Write the failing test (append)**

```python
def test_game_over_lose_is_red_win_is_green():
    screen = pygame.Surface((WIDTH, HEIGHT))
    from settings import COLOR_RED, COLOR_GREEN
    menu._render_game_over(screen, score=1234, is_new_best=False, game_won=False, identity_error=False)
    assert _has_color(screen, COLOR_RED, band=(200, 320))
    screen2 = pygame.Surface((WIDTH, HEIGHT))
    menu._render_game_over(screen2, score=1234, is_new_best=True, game_won=True, identity_error=False)
    assert _has_color(screen2, COLOR_GREEN, band=(200, 320))
    # NEW BEST! is yellow
    assert _has_color(screen2, COLOR_YELLOW, band=(440, 520))


def test_game_over_identity_error_renders():
    screen = pygame.Surface((WIDTH, HEIGHT))
    menu._render_game_over(screen, score=10, is_new_best=False, game_won=False, identity_error=True)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py::test_game_over_lose_is_red_win_is_green -v`
Expected: FAIL — `_render_game_over` not defined.

- [ ] **Step 3: Implement the renderer and rewire**

Add to `menu.py`:

```python
def _render_game_over(screen, score, is_new_best, game_won, identity_error=False):
    """Draw one game-over/victory frame: glowing title (green win / red loss),
    score, optional NEW BEST!, optional identity-error notice, and the hint."""
    _draw_backdrop(screen)
    title_font = theme.pixel_font(theme.SIZE_TITLE)
    score_font = theme.pixel_font(theme.SIZE_MENU)
    hint_font = theme.pixel_font(theme.SIZE_SMALL)

    if game_won:
        title = theme.glow_text("VICTORY!", title_font, COLOR_GREEN, radius=6)
    else:
        title = theme.glow_text("GAME OVER", title_font, COLOR_RED, radius=6)
    _blit_center(screen, title, (WIDTH // 2, 250))

    _blit_center(screen, score_font.render(f"Score: {score}", True, COLOR_WHITE), (WIDTH // 2, 400))

    if is_new_best:
        best = theme.glow_text("NEW BEST!", score_font, COLOR_YELLOW, radius=4)
        _blit_center(screen, best, (WIDTH // 2, 480))

    if identity_error:
        _blit_center(screen, hint_font.render("Score not saved — identity error", True, COLOR_GRAY),
                     (WIDTH // 2, 540))

    _blit_center(screen, hint_font.render("Press SPACE for menu", True, COLOR_GRAY),
                 (WIDTH // 2, HEIGHT - 100))
```

In `run_game_over_screen`: delete the three `pygame.font.Font(...)` lines and replace the draw block in the loop with:

```python
    while True:
        timer.tick(FPS)
        _render_game_over(screen, score, is_new_best, game_won, identity_error)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "menu"

        pygame.display.flip()
```

- [ ] **Step 4: Run the new tests**

Run: `.venv/Scripts/python.exe -m pytest tests/test_menu_render.py -k game_over -v`
Expected: both PASS.

- [ ] **Step 5: Run the full suite**

Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: `158 passed, 9 skipped`.

- [ ] **Step 6: Commit**

```bash
git add menu.py tests/test_menu_render.py
git commit -m "feat(brand): retro-arcade game-over / victory screen"
```

---

### Task 5: Wire the contact-sheet capture for all four screens + generate the sheet

**Files:**
- Modify: `tools/contact_sheet.py` (`_capture_states` renders the four real screens)
- Test: manual run (produces `tools/_contact/brand-match.png`)

**Interfaces:**
- Consumes: `menu._render_main_menu/_render_initials/_render_leaderboard/_render_game_over`.
- Produces: a 4-up contact sheet of the restyled screens for this branch.

- [ ] **Step 1: Replace `_capture_states` in `tools/contact_sheet.py`**

Replace the body of `_capture_states()` (the base-branch fallback) with real screen captures:

```python
def _capture_states():
    """Render one frame of each restyled screen for the contact sheet."""
    import menu
    pygame.font.init()
    frames = []

    s = pygame.Surface((WIDTH, HEIGHT))
    menu._render_main_menu(s, selected=0)
    frames.append(("menu", s))

    s = pygame.Surface((WIDTH, HEIGHT))
    menu._render_initials(s, letters=[9, 0, 12], slot=0)  # "JAM"-ish, slot 0 active
    frames.append(("initials", s))

    s = pygame.Surface((WIDTH, HEIGHT))
    sample = [{"initials": "JAP", "score": 7540}, {"initials": "JEM", "score": 4140},
              {"initials": "ZZZ", "score": 7}]
    menu._render_leaderboard(s, active="week", entries=sample, last_week_initials="ZZZ")
    frames.append(("leaderboard", s))

    s = pygame.Surface((WIDTH, HEIGHT))
    menu._render_game_over(s, score=7540, is_new_best=True, game_won=False, identity_error=False)
    frames.append(("game_over", s))

    return frames
```

- [ ] **Step 2: Generate the sheet**

Run:

```bash
.venv/Scripts/python.exe tools/contact_sheet.py --label brand-match
```

Expected: `wrote .../tools/_contact/brand-match.png` showing the four restyled screens. (Open it to eyeball the look — especially the title glow at the dialed-back radius.)

- [ ] **Step 3: Commit (script only — the PNG is gitignored)**

```bash
git add tools/contact_sheet.py
git commit -m "tools(brand): contact-sheet captures the four restyled screens"
```

---

## Self-Review

**Spec coverage (Brand Match section):**
- Restyle the four `menu.py` screens to the web aesthetic → Tasks 1-4 ✓
- Pixel font + reserved yellow + navy panels + scanlines via `theme.py` → all tasks (`_draw_backdrop` + `glow_text` + `pixel_font`) ✓
- Gameplay untouched (golden traces safe) → `game.py` never in any task's file list ✓
- Verbatim copy strings preserved → carried verbatim in `_render_leaderboard`/`_render_game_over`/`_render_initials` ✓
- Comparison artifact → Task 5 contact sheet ✓
- pygame_gui → **deliberately not used** (deviation noted at top; pending sign-off)

**Placeholder scan:** none. Every render function is shown in full; no "similar to Task N".

**Type consistency:** `_render_main_menu(screen, selected, banner_text=None)`, `_render_initials(screen, letters, slot)`, `_render_leaderboard(screen, active, entries, last_week_initials)`, `_render_game_over(screen, score, is_new_best, game_won, identity_error=False)`, `_draw_backdrop(screen)`, `_blit_center(screen, surface, center)`, `_show_loading(screen)` — signatures match between their definitions and their callers (the loops in Tasks 1-4 and the contact-sheet consumer in Task 5).

**Open risk (mitigated):** `_has_color` uses a per-channel tolerance (`tol=40`) rather than exact match, so the scanline overlay (alpha 45/255 ≈ 18% darkening on 1-of-3 rows) cannot cause false negatives, regardless of how the 2px sample stride aligns with the 3px scanline pattern. The tolerance is tight enough that white/gray/red/green never read as yellow (their channels differ by ≫40). If a test still flakes, widen the band — do not raise `tol` past ~60.
