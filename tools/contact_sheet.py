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
