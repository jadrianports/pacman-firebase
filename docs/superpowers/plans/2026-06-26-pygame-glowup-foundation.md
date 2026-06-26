# PyGame Glow-Up — Foundation Implementation Plan (1 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the shared base both redesign branches fork from — migrate to pygame-ce, add the Press Start 2P pixel font, build a reusable `theme.py` primitives module, and stand up the side-by-side comparison tooling.

**Architecture:** Create a `redesign/base` branch off `main`. Swap the `pygame` dependency for the drop-in `pygame-ce`, vendor the pixel font as a bundled asset, and add a focused `theme.py` module exposing a cached pixel-font loader, glow-text and scanline-overlay helpers (built on pygame-ce's `gaussian_blur`). Add a headless contact-sheet capture script. The two visual branches (Brand Match, Bold Reinvention) will each `git worktree` off `redesign/base`.

**Tech Stack:** Python 3.12, pygame-ce 2.5.7, Pillow 11, PyInstaller 6.20, pytest.

## Global Constraints

- **pygame dependency:** `pygame-ce==2.5.7` (replaces `pygame==2.6.1`). Same `import pygame` namespace — no import changes.
- **Determinism is sacred:** the full suite must stay green — `146 passed, 9 skipped` (the 9 are Linux-only golden traces, skipped on Windows). Run via `.venv/Scripts/python.exe -m pytest`.
- **Pixel font:** Press Start 2P, vendored at `assets/fonts/PressStart2P-Regular.ttf`, loaded only through `paths.resource_path()`.
- **No gameplay-logic changes:** this plan touches dependencies, assets, a new module, and tooling only — never ghost/player/board/game simulation code.
- **`.exe` must still build and launch** via `python build.py`; new assets bundled through `--add-data`.
- **Python env:** the real interpreter is `.venv/Scripts/python.exe` (the global Python312 is bare). Run all tests/builds through it.

---

### Task 1: Migrate the dependency to pygame-ce

**Files:**
- Modify: `requirements.txt:1`
- Test: (verification via existing suite — no new test file)

**Interfaces:**
- Consumes: nothing.
- Produces: a working game running on pygame-ce; `pygame.transform.gaussian_blur` and `Surface.fblits` now available to later tasks.

- [ ] **Step 1: Create the base branch off main**

```bash
git switch main
git switch -c redesign/base
```

- [ ] **Step 2: Edit requirements.txt**

Change line 1 from:

```
pygame==2.6.1
```

to:

```
pygame-ce==2.5.7
```

- [ ] **Step 3: Replace pygame with pygame-ce in the real venv**

Run:

```bash
.venv/Scripts/python.exe -m pip uninstall -y pygame
.venv/Scripts/python.exe -m pip install pygame-ce==2.5.7
```

Expected: `Successfully installed pygame-ce-2.5.7`. (pygame and pygame-ce must never be installed together — uninstall first.)

- [ ] **Step 4: Verify the flavor and the new primitives exist**

Run:

```bash
.venv/Scripts/python.exe -c "import pygame; print(pygame.version.ver, 'CE' if getattr(pygame,'IS_CE',False) else 'classic'); print(hasattr(pygame.transform,'gaussian_blur'), hasattr(pygame.Surface((1,1)),'fblits'))"
```

Expected: `2.5.7 CE` then `True True`.

- [ ] **Step 5: Run the full suite to prove the migration is byte-clean**

Run:

```bash
.venv/Scripts/python.exe -m pytest -q
```

Expected: `146 passed, 9 skipped`. The simulation-integrity tests (`test_frame_hash`, `test_ghost_micro`) passing here is the proof the deterministic core is unchanged under CE's newer SDL.

- [ ] **Step 6: Commit**

```bash
git add requirements.txt
git commit -m "build: migrate pygame -> pygame-ce 2.5.7 (drop-in)"
```

---

### Task 2: Vendor the Press Start 2P pixel font

**Files:**
- Create: `assets/fonts/PressStart2P-Regular.ttf` (copied from `web/public/fonts/`)
- Modify: `build.py:77-80` (PyInstaller `--add-data` list)
- Test: `tests/test_theme.py` (created here, asserts the asset resolves)

**Interfaces:**
- Consumes: `paths.resource_path` (existing).
- Produces: the font file resolvable at `resource_path("assets/fonts/PressStart2P-Regular.ttf")` in both dev and frozen builds.

- [ ] **Step 1: Copy the font into the assets tree**

```bash
mkdir -p assets/fonts
cp web/public/fonts/PressStart2P-Regular.ttf assets/fonts/PressStart2P-Regular.ttf
```

- [ ] **Step 2: Write the failing test**

Create `tests/test_theme.py`:

```python
import os
from paths import resource_path


def test_pixel_font_asset_present():
    path = resource_path("assets/fonts/PressStart2P-Regular.ttf")
    assert os.path.isfile(path), f"pixel font missing at {path}"
    assert os.path.getsize(path) > 10_000  # a real TTF, not an empty stub
```

- [ ] **Step 3: Run it to verify it passes (asset already copied)**

Run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_theme.py::test_pixel_font_asset_present -v
```

Expected: PASS. (If FAIL, the copy in Step 1 did not land — re-copy.)

- [ ] **Step 4: Bundle the font in the exe build**

In `build.py`, the `PyInstaller.__main__.run([...])` list currently includes (around line 77-80):

```python
        "--add-data=assets;assets",
        "--add-data=freesansbold.ttf;.",
```

`--add-data=assets;assets` already recursively includes `assets/fonts/`, so no new line is strictly required. Add an explicit belt-and-suspenders entry immediately after the `assets` line for clarity:

```python
        "--add-data=assets;assets",
        "--add-data=assets/fonts/PressStart2P-Regular.ttf;assets/fonts",
        "--add-data=freesansbold.ttf;.",
```

- [ ] **Step 5: Commit**

```bash
git add assets/fonts/PressStart2P-Regular.ttf build.py tests/test_theme.py
git commit -m "assets: vendor Press Start 2P pixel font + bundle in build"
```

---

### Task 3: `theme.py` — cached pixel-font loader + named sizes

**Files:**
- Create: `theme.py`
- Test: `tests/test_theme.py` (append)

**Interfaces:**
- Consumes: `paths.resource_path`; `settings.COLOR_*`.
- Produces:
  - `theme.PIXEL_FONT = "assets/fonts/PressStart2P-Regular.ttf"`
  - `theme.SIZE_TITLE=48, SIZE_HEADING=28, SIZE_MENU=18, SIZE_BODY=12, SIZE_SMALL=9` (ints)
  - `theme.pixel_font(size: int) -> pygame.font.Font` (cached per size)

- [ ] **Step 1: Write the failing test (append to tests/test_theme.py)**

```python
import pygame
import theme


def test_pixel_font_is_cached_and_sized(tmp_path):
    pygame.font.init()
    f1 = theme.pixel_font(theme.SIZE_MENU)
    f2 = theme.pixel_font(theme.SIZE_MENU)
    assert f1 is f2  # same size returns the cached instance
    assert isinstance(f1, pygame.font.Font)
    # a known glyph renders to a non-empty surface
    surf = f1.render("A", True, (255, 255, 0))
    assert surf.get_width() > 0 and surf.get_height() > 0
```

- [ ] **Step 2: Run it to verify it fails**

Run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_theme.py::test_pixel_font_is_cached_and_sized -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'theme'`.

- [ ] **Step 3: Write the minimal implementation**

Create `theme.py`:

```python
"""Shared visual primitives for the redesigned UI: the pixel font, named sizes,
and small render helpers. Imported by menu.py and game.py on the redesign branches.
Colors live in settings.py; this module reuses them rather than redefining."""
import pygame
from paths import resource_path

PIXEL_FONT = "assets/fonts/PressStart2P-Regular.ttf"

# Named pixel-font sizes (px). Press Start 2P reads best at integer sizes.
SIZE_TITLE = 48
SIZE_HEADING = 28
SIZE_MENU = 18
SIZE_BODY = 12
SIZE_SMALL = 9

_font_cache = {}


def pixel_font(size):
    """Return a cached Press Start 2P Font at ``size`` px (loaded once per size)."""
    if size not in _font_cache:
        _font_cache[size] = pygame.font.Font(resource_path(PIXEL_FONT), size)
    return _font_cache[size]
```

- [ ] **Step 4: Run it to verify it passes**

Run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_theme.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add theme.py tests/test_theme.py
git commit -m "feat(theme): cached Press Start 2P loader + named sizes"
```

---

### Task 4: `theme.py` — glow-text helper (pygame-ce gaussian_blur)

**Files:**
- Modify: `theme.py` (append `glow_text`)
- Test: `tests/test_theme.py` (append)

**Interfaces:**
- Consumes: `theme.pixel_font`; `pygame.transform.gaussian_blur` (pygame-ce).
- Produces: `theme.glow_text(text: str, font: pygame.font.Font, color, glow_color=None, radius: int = 6) -> pygame.Surface` — a per-pixel-alpha Surface, larger than the bare text by `2*radius` on each axis, with the crisp text centered over an additive blurred glow.

- [ ] **Step 1: Write the failing test (append)**

```python
def test_glow_text_returns_padded_alpha_surface():
    pygame.font.init()
    font = theme.pixel_font(theme.SIZE_MENU)
    bare = font.render("PLAY", True, (255, 255, 0))
    glow = theme.glow_text("PLAY", font, (255, 255, 0), radius=6)
    # padded by 2*radius on each axis
    assert glow.get_width() == bare.get_width() + 12
    assert glow.get_height() == bare.get_height() + 12
    assert glow.get_flags() & pygame.SRCALPHA
    # there is lit-up glow outside the crisp glyph box (top-left padding pixel)
    assert glow.get_at((1, 1))[3] > 0  # non-zero alpha in the glow margin
```

- [ ] **Step 2: Run it to verify it fails**

Run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_theme.py::test_glow_text_returns_padded_alpha_surface -v
```

Expected: FAIL with `AttributeError: module 'theme' has no attribute 'glow_text'`.

- [ ] **Step 3: Write the minimal implementation (append to theme.py)**

```python
def glow_text(text, font, color, glow_color=None, radius=6):
    """Render ``text`` with a soft additive glow behind the crisp glyphs.

    Returns a SRCALPHA Surface padded by ``radius`` px on every side. The glow is a
    blurred bright copy (pygame-ce ``gaussian_blur``) additively blitted under the
    sharp text. ``glow_color`` defaults to ``color``."""
    glow_color = glow_color or color
    sharp = font.render(text, True, color)
    w, h = sharp.get_width() + 2 * radius, sharp.get_height() + 2 * radius

    out = pygame.Surface((w, h), pygame.SRCALPHA)
    blur_src = pygame.Surface((w, h), pygame.SRCALPHA)
    tinted = font.render(text, True, glow_color)
    blur_src.blit(tinted, (radius, radius))
    blurred = pygame.transform.gaussian_blur(blur_src, radius)
    out.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    out.blit(blurred, (0, 0), special_flags=pygame.BLEND_RGB_ADD)  # double for intensity
    out.blit(sharp, (radius, radius))
    return out
```

- [ ] **Step 4: Run it to verify it passes**

Run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_theme.py::test_glow_text_returns_padded_alpha_surface -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add theme.py tests/test_theme.py
git commit -m "feat(theme): glow_text helper via pygame-ce gaussian_blur"
```

---

### Task 5: `theme.py` — scanline overlay builder

**Files:**
- Modify: `theme.py` (append `scanline_overlay`)
- Test: `tests/test_theme.py` (append)

**Interfaces:**
- Consumes: `pygame`.
- Produces: `theme.scanline_overlay(size: tuple[int,int], spacing: int = 4, alpha: int = 70) -> pygame.Surface` — a cached SRCALPHA overlay of horizontal dark lines, blittable over any screen each frame.

- [ ] **Step 1: Write the failing test (append)**

```python
def test_scanline_overlay_is_striped_alpha():
    pygame.font.init()
    surf = theme.scanline_overlay((40, 40), spacing=4, alpha=70)
    assert surf.get_size() == (40, 40)
    assert surf.get_flags() & pygame.SRCALPHA
    # dark line rows carry alpha; gap rows are transparent
    line_alpha = surf.get_at((0, 0))[3]
    gap_alpha = surf.get_at((0, 2))[3]
    assert line_alpha == 70
    assert gap_alpha == 0
    # cached: same args return the same object
    assert theme.scanline_overlay((40, 40), spacing=4, alpha=70) is surf
```

- [ ] **Step 2: Run it to verify it fails**

Run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_theme.py::test_scanline_overlay_is_striped_alpha -v
```

Expected: FAIL with `AttributeError: module 'theme' has no attribute 'scanline_overlay'`.

- [ ] **Step 3: Write the minimal implementation (append to theme.py)**

Add near the top, after `_font_cache = {}`:

```python
_scanline_cache = {}
```

Then append the function:

```python
def scanline_overlay(size, spacing=4, alpha=70):
    """Return a cached SRCALPHA overlay: a dark horizontal line every ``spacing`` px.

    Blit over the whole screen each frame for a subtle CRT scanline. ``alpha`` is the
    per-line darkness (0-255). Cached by (size, spacing, alpha)."""
    key = (size, spacing, alpha)
    if key not in _scanline_cache:
        w, h = size
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        line = (0, 0, 0, alpha)
        for y in range(0, h, spacing):
            pygame.draw.line(surf, line, (0, y), (w, y))
        _scanline_cache[key] = surf
    return _scanline_cache[key]
```

- [ ] **Step 4: Run it to verify it passes**

Run:

```bash
.venv/Scripts/python.exe -m pytest tests/test_theme.py -v
```

Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add theme.py tests/test_theme.py
git commit -m "feat(theme): cached scanline overlay builder"
```

---

### Task 6: Headless contact-sheet capture script

**Files:**
- Create: `tools/contact_sheet.py`
- Test: manual run (produces an image; verified by inspecting output)

**Interfaces:**
- Consumes: `paths.resource_path`, Pillow (`PIL.Image`), pygame (dummy video driver).
- Produces: `tools/contact_sheet.py` writing a montage PNG of every screen state for the current branch. Run once per worktree; filenames carry the branch so the two can be combined.

- [ ] **Step 1: Write the script**

Create `tools/contact_sheet.py`:

```python
"""Headless screen-capture montage for visual comparison across branches.

Boots pygame with the dummy video driver, renders each menu screen and a
representative gameplay frame to off-screen surfaces, and montages them into a
single PNG. Run once per branch worktree:

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy \\
        .venv/Scripts/python.exe tools/contact_sheet.py --label brand-match

Output: tools/_contact/<label>.png
"""
import argparse
import os
import sys

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from settings import WIDTH, HEIGHT
import theme  # noqa: F401  (ensures the redesign theme imports on this branch)

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_contact")


def _surface_to_pil(surface):
    raw = pygame.image.tostring(surface, "RGB")
    return Image.frombytes("RGB", surface.get_size(), raw)


def _capture_states():
    """Return a list of (title, Surface). One static frame per screen state.

    NOTE: this renders each screen's *first frame* by calling its draw path with a
    synthetic event that immediately exits. Branch-specific: the brand/bold branches
    each implement ``render_once(screen, state)`` in menu.py / game.py for capture.
    Until those exist, fall back to a single filled frame so the tool runs on base."""
    pygame.font.init()
    frames = []
    surf = pygame.Surface((WIDTH, HEIGHT))
    surf.fill("black")
    title = theme.pixel_font(theme.SIZE_TITLE).render("PAC-MAN", True, (255, 255, 0))
    surf.blit(title, title.get_rect(center=(WIDTH // 2, 150)))
    frames.append(("title", surf))
    return frames


def _montage(frames, label):
    os.makedirs(OUT_DIR, exist_ok=True)
    thumbs = []
    for name, surf in frames:
        img = _surface_to_pil(surf)
        img.thumbnail((300, 320))
        thumbs.append((name, img))
    cols = max(1, len(thumbs))
    cell_w = max(t.width for _, t in thumbs) + 16
    cell_h = max(t.height for _, t in thumbs) + 16
    sheet = Image.new("RGB", (cell_w * cols, cell_h), (10, 10, 20))
    for i, (_, img) in enumerate(thumbs):
        sheet.paste(img, (i * cell_w + 8, 8))
    out = os.path.join(OUT_DIR, f"{label}.png")
    sheet.save(out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--label", required=True, help="branch label for the output filename")
    args = ap.parse_args()
    pygame.display.set_mode((WIDTH, HEIGHT))
    out = _montage(_capture_states(), args.label)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run it on the base branch**

Run:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy .venv/Scripts/python.exe tools/contact_sheet.py --label base
```

Expected: `wrote .../tools/_contact/base.png` and the PNG shows the pixel-font `PAC-MAN`. (The per-screen `render_once` hooks are added in the branch plans; base proves the tooling runs.)

- [ ] **Step 3: Ignore the capture output dir**

Append to `.gitignore`:

```
# Contact-sheet capture output (regenerated)
tools/_contact/
```

- [ ] **Step 4: Commit**

```bash
git add tools/contact_sheet.py .gitignore
git commit -m "tools: headless contact-sheet capture for branch comparison"
```

---

### Task 7: Document the worktree comparison workflow

**Files:**
- Create: `docs/superpowers/plans/REDESIGN-COMPARE.md`
- Test: none (documentation)

**Interfaces:**
- Consumes: the `redesign/base` branch from Task 1.
- Produces: the exact commands to stand up both branches side by side and generate the combined contact sheet.

- [ ] **Step 1: Write the workflow doc**

Create `docs/superpowers/plans/REDESIGN-COMPARE.md`:

````markdown
# Redesign Comparison Workflow

Both visual branches fork from `redesign/base` and are checked out as sibling
worktrees so they can run side by side.

## Create the worktrees (after the two branch plans are executed)

```bash
git worktree add ../pacman-brand-match redesign/brand-match
git worktree add ../pacman-bold-reinvention redesign/bold-reinvention
```

Each worktree needs its own venv (deps differ — pygame_gui on both; zengl on Bold):

```bash
# in each worktree dir
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

## Run both at once

Open two terminals:

```bash
# terminal 1
cd ../pacman-brand-match && .venv/Scripts/python.exe main.py
# terminal 2
cd ../pacman-bold-reinvention && .venv/Scripts/python.exe main.py
```

## Generate the combined contact sheet

```bash
# from each worktree
SDL_VIDEODRIVER=dummy .venv/Scripts/python.exe tools/contact_sheet.py --label brand-match
SDL_VIDEODRIVER=dummy .venv/Scripts/python.exe tools/contact_sheet.py --label bold-reinvention
```

Then montage `brand-match.png` + `bold-reinvention.png` into a single before/after.

## Ship the winner

```bash
git switch main
git merge --no-ff redesign/<winner>
git worktree remove ../pacman-brand-match
git worktree remove ../pacman-bold-reinvention
git branch -D redesign/<loser>
```
````

- [ ] **Step 2: Commit**

```bash
git add docs/superpowers/plans/REDESIGN-COMPARE.md
git commit -m "docs: redesign branch comparison workflow"
```

---

## Self-Review

**Spec coverage (Foundation section of the spec):**
- Migrate pygame → pygame-ce → Task 1 ✓
- Press Start 2P bundled asset via resource_path → Task 2 ✓
- `theme.py` (font loader, sizes, color tokens, glow + scanline helpers) → Tasks 3-5 ✓ (color tokens are reused from `settings` directly per the module docstring; no redefinition needed)
- Comparison: worktrees + contact sheet → Tasks 6-7 ✓
- Determinism untouched → enforced by Task 1 Step 5 (full suite green) ✓

**Out of scope here (covered by plans 2 and 3):** the `juice` flag + firewall, pygame_gui menu restyle, gameplay glow-up, zengl CRT, ghost-eye preservation. These land in the Brand-Match (plan 2) and Bold-Reinvention (plan 3) plans, written against this concrete `theme.py` API.

**Placeholder scan:** none. The `render_once` per-screen capture hooks are explicitly deferred to the branch plans with a working base fallback (not a placeholder — a stated staging boundary).

**Type consistency:** `pixel_font(size)`, `glow_text(text, font, color, glow_color, radius)`, `scanline_overlay(size, spacing, alpha)` — signatures match between their definition tasks and the contact-sheet consumer.
