"""Frame capture for visual proof (HRN-03, D-06/D-20).

Three dev/test-only helpers, all writing under the gitignored ``tests/artifacts/``
scratch dir (D-06) — never under ``tests/golden/`` (the committed numeric goldens):

  - ``save_png``       — write a pygame Surface to a ``.png`` via ``pygame.image.save``.
  - ``build_montage``  — assemble a grid of scaled stills onto ONE pygame Surface by
                         blitting thumbnails (pure pygame, ZERO new dependency).
  - ``build_gif``      — assemble a GIF from PNG frames using Pillow ONLY (the single
                         new dep, imported INSIDE the function per D-20).

Pixels are for eyes only — this module never hashes pixels for comparison. The stable
golden is the numeric per-frame trace (``harness/trace.py``); PNG/montage/GIF are the
human/Claude-vision channel that is regenerated on demand and gitignored.
"""
import os


def save_png(pygame, screen, path):
    """Write the ``screen`` Surface to ``path`` as a PNG.

    The PNG format is inferred from the ``.png`` extension by ``pygame.image.save``.
    Parent directories (under ``tests/artifacts/``) are created if missing so callers
    need not pre-make the scratch dir.
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    pygame.image.save(screen, path)
    return path


def build_montage(pygame, frame_surfaces, cols, cell=(180, 190), pad=4):
    """Blit scaled thumbnails of ``frame_surfaces`` into a cols-wide grid sheet.

    Returns a single ``pygame.Surface`` (the caller saves it with ``save_png``). Pure
    pygame — ``pygame.transform.scale`` + ``Surface.blit`` — so this adds ZERO new
    dependency (D-20). The sheet width is ``cols * (cell_w + pad) + pad`` so it always
    fits the requested number of columns.
    """
    cell_w, cell_h = cell
    n = len(frame_surfaces)
    cols = max(1, cols)
    rows = (n + cols - 1) // cols
    width = cols * (cell_w + pad) + pad
    height = rows * (cell_h + pad) + pad
    sheet = pygame.Surface((width, height))
    sheet.fill((0, 0, 0))
    for i, surf in enumerate(frame_surfaces):
        thumb = pygame.transform.scale(surf, cell)
        r, c = divmod(i, cols)
        x = pad + c * (cell_w + pad)
        y = pad + r * (cell_h + pad)
        sheet.blit(thumb, (x, y))
    return sheet


def build_gif(png_paths, out_path, duration_ms=33, loop=0):
    """Assemble ``png_paths`` into an animated GIF at ``out_path`` using Pillow ONLY.

    Pillow is the single new dependency and is imported HERE, inside the function, so it
    is used nowhere else in the harness (D-20). Each PNG is opened and the first frame is
    saved with ``save_all=True`` + ``append_images=frames[1:]``; ``duration`` is the
    per-frame delay in milliseconds and ``loop=0`` loops forever.
    """
    from PIL import Image  # Pillow ONLY for GIF (D-20) — imported inside build_gif.

    parent = os.path.dirname(out_path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    frames = [Image.open(p) for p in png_paths]
    frames[0].save(
        out_path,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=loop,
    )
    return out_path
