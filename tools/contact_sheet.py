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

    Captures 5 frames:
    1. Juiced gameplay (Bold reinvention): Game with juice=True, ~80 frames
    2. Main menu (glowing yellow title with pulse, selected Play)
    3. Initials entry (slot 1 with initials J, A, P)
    4. Leaderboard (This Week, with sample data)
    5. Game Over (score, new best indicator)
    """
    pygame.font.init()
    pygame.mixer.init()
    frames = []

    # Import here to avoid circular deps and ensure pygame is initialized
    import menu
    from game import Game
    from harness.replay import install_frame_driven_sound

    # 1. Juiced gameplay frame (pre-CRT, juice colors visible)
    game_surface = pygame.Surface((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    g = Game(game_surface, clock)
    g.juice = True
    install_frame_driven_sound(g)
    for _ in range(80):
        g.tick()
    frames.append(("gameplay (juiced)", g.screen.copy()))

    # 2. Main menu (glowing title with pulse at frame=30)
    menu_surface = pygame.Surface((WIDTH, HEIGHT))
    menu._render_main_menu(menu_surface, 0, None, 30)
    frames.append(("menu (main)", menu_surface.copy()))

    # 3. Initials entry (slot 1, letters J-A-P → [9,0,15])
    initials_surface = pygame.Surface((WIDTH, HEIGHT))
    menu._render_initials(initials_surface, [9, 0, 15], 1)
    frames.append(("initials entry", initials_surface.copy()))

    # 4. Leaderboard (This Week, with sample entries)
    board_surface = pygame.Surface((WIDTH, HEIGHT))
    sample_entries = [
        {"initials": "JAP", "score": 7540},
        {"initials": "JEM", "score": 4140},
        {"initials": "ZZZ", "score": 7}
    ]
    menu._render_leaderboard(board_surface, "week", sample_entries, "JAP")
    frames.append(("leaderboard (week)", board_surface.copy()))

    # 5. Game Over (new best, loss)
    gameover_surface = pygame.Surface((WIDTH, HEIGHT))
    menu._render_game_over(gameover_surface, 7540, True, False, False)
    frames.append(("game over", gameover_surface.copy()))

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
