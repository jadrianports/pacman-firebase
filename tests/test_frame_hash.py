"""Deterministic frame-hash (pixel) check for the geometry centralization (D-08/D-09).

The golden state-trace (test_golden_traces.py) records ghost/Pac-Man positions + score, but
NOT pixels. ``draw_board`` uses the SAME tile-math (was ``num1=(HEIGHT-50)//32`` /
``num2=WIDTH//30``) that Plan 02-01 centralized into ``TILE_HEIGHT`` / ``TILE_WIDTH`` — so a
geometry bug (e.g. an off-by-one tile dim) could shift every drawn wall/dot pixel while the
state trace stays byte-identical. This check closes that gap: it hashes the rendered frame
bytes and asserts they match a committed manifest.

ALGORITHM (research FOCUS-5): ``hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()``.
Format "RGB" (the screen is opaque — ``screen.fill('black')`` each frame, alpha carries no
information); stdlib ``hashlib`` (zero new dependency — do NOT add numpy/Pillow for hashing).

SAMPLING (research A1): hash every 20th frame + the terminal frame per scenario, to keep the
manifest small for the 4200-frame ``death`` scenario. A geometry bug shifts ALL frames globally,
so any sampled frame catches it.

PLATFORM-STABILITY CONTRACT (D-09 / Pitfall 4):
  The frame-hash is byte-stable ONLY in the Linux pinned bless env (the project CI:
  ``.github/workflows/ci.yml`` — ubuntu-latest, Python 3.12, pygame 2.6.1, ``SDL_*=dummy``).
  ``freesansbold.ttf`` rasterization (the HUD score text) differs across SDL builds, so the
  COMMITTED manifest is the Linux-blessed truth and CI is the assertion authority.

  - Under ``--bless``: (re)write each scenario's ``frame_hashes.txt`` and return WITHOUT asserting
    (mirrors test_golden_traces.py's bless branch). Re-bless in CI to mint the true Linux baseline.
  - On a non-pinned dev machine (e.g. Windows authoring): ``pytest.skip(...)`` so a local run does
    NOT false-red on legitimate cross-platform font rasterization differences.
  - In the pinned CI env (``CI`` or ``GSD_FRAME_HASH_ENV`` set): assert every sampled replayed
    frame hash equals the committed hash. If the manifest is missing, skip with a "re-bless in CI"
    message rather than fail (the first CI run after an off-platform authoring commit must re-bless).

LIFECYCLE: PERMANENT (unlike the one-shot oracle in test_check_collisions_oracle.py). The text
manifest is tiny and is the cheap rendering regression guard going forward.
"""
import hashlib
import os

import pytest

from harness.headless import init_headless
from harness.replay import KEYMAP, install_frame_driven_sound, load_events, run_scenario

# Headless pygame once for the whole module (SDL dummy; conftest also forces the env).
pygame, _screen, _clock = init_headless()
from game import Game  # noqa: E402  (import after headless init)

from tests.test_golden_traces import MANIFEST, _abs_input  # reuse the scenario registry

_HERE = os.path.dirname(__file__)

# Sample cadence: hash every Nth frame plus the terminal frame (research A1 / FOCUS-5).
_SAMPLE_EVERY = 20


def frame_hash(pygame, surface):
    """sha256 over the raw RGB pixel bytes of a surface (research FOCUS-5)."""
    return hashlib.sha256(pygame.image.tobytes(surface, "RGB")).hexdigest()


def _manifest_path(entry):
    return os.path.join(_HERE, "golden", entry["name"], "frame_hashes.txt")


def _in_pinned_env():
    """True only in the Linux pinned bless/CI env (D-09). Honors CI or GSD_FRAME_HASH_ENV."""
    return bool(os.environ.get("CI") or os.environ.get("GSD_FRAME_HASH_ENV"))


def _new_game():
    g = Game(_screen, _clock)
    install_frame_driven_sound(g)  # headless sound-gating shim
    return g


def _sampled(frame, frame_cap, is_terminal):
    """Sample every _SAMPLE_EVERY-th frame, plus the terminal/last frame."""
    return frame % _SAMPLE_EVERY == 0 or is_terminal


def _replay_frame_hashes(entry):
    """Replay one scenario and return [(frame_index, sha256hex), ...] for sampled frames.

    Mirrors test_golden_traces._replay_fixed / run_scenario per-frame body, but captures a
    frame-hash of ``game.screen`` instead of the state snapshot.
    """
    game = _new_game()
    input_path = _abs_input(entry)
    events = load_events(input_path)
    frame_cap = entry["frame_cap"]
    natural_terminal = entry["terminal"] in ("game_over", "game_won")

    hashes = []
    last_frame = -1
    for frame in range(frame_cap):
        game._frame = frame
        for ev in events.get(frame, []):
            etype = pygame.KEYDOWN if ev.get("type", "down") == "down" else pygame.KEYUP
            key = getattr(pygame, KEYMAP[ev["key"]])
            pygame.event.post(pygame.event.Event(etype, key=key))
        game.tick()
        last_frame = frame
        ended = game.game_over or game.game_won
        is_terminal = ended or frame == frame_cap - 1
        if _sampled(frame, frame_cap, is_terminal):
            hashes.append((frame, frame_hash(pygame, game.screen)))
        if natural_terminal and ended:
            break

    # Guarantee the genuine last replayed frame is always recorded (terminal coverage).
    if hashes and hashes[-1][0] != last_frame:
        hashes.append((last_frame, frame_hash(pygame, game.screen)))
    return hashes


def _read_manifest(path):
    """Read a committed ``frame_hashes.txt`` -> [(frame_index, sha256hex), ...]."""
    out = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            idx, digest = line.split()
            out.append((int(idx), digest))
    return out


def _write_manifest(path, hashes):
    """Write [(frame_index, sha256hex), ...] as committed ``<int> <64-hex>`` text lines."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(
            "# frame-hash manifest (D-09): sha256(pygame.image.tobytes(surface,'RGB')).\n"
            "# Linux-pinned-CI-blessed truth; re-bless in CI via `pytest --bless`.\n"
        )
        for idx, digest in hashes:
            fh.write(f"{idx} {digest}\n")


@pytest.mark.parametrize("entry", MANIFEST, ids=[e["name"] for e in MANIFEST])
def test_frame_hash_matches_manifest(entry, request):
    """Replay the scenario and assert sampled rendered frames match the committed manifest.

    Under ``--bless`` re-writes the manifest and returns (no assert). On non-pinned dev,
    skips clean (font rasterization is platform-bound — D-09). In the pinned CI env, asserts.
    """
    manifest_path = _manifest_path(entry)

    if request.config.getoption("--bless"):
        hashes = _replay_frame_hashes(entry)
        _write_manifest(manifest_path, hashes)
        print(f"\n=== BLESS FRAME-HASH [{entry['name']}] ({len(hashes)} sampled frames) ===")
        return  # do NOT assert in bless mode — we just re-recorded

    if not _in_pinned_env():
        pytest.skip(
            "frame-hash asserted only in the Linux pinned bless env (D-09); "
            "regenerate locally via `pytest --bless`"
        )

    if not os.path.exists(manifest_path):
        pytest.skip(
            f"no committed frame-hash manifest for {entry['name']} — re-bless in the pinned "
            f"CI env via `pytest --bless` to mint the Linux baseline (D-09)"
        )

    committed = _read_manifest(manifest_path)
    replayed = _replay_frame_hashes(entry)

    assert replayed == committed, (
        f"{entry['name']}: rendered frames diverged from committed frame-hash manifest "
        f"(geometry/rendering byte-shift?). "
        f"committed {len(committed)} sampled frames, replayed {len(replayed)}. "
        f"First divergence: "
        + next(
            (
                f"frame {r[0]}: committed={c[1][:12]}… replayed={r[1][:12]}…"
                for c, r in zip(committed, replayed)
                if c != r
            ),
            "(length mismatch only)",
        )
    )
