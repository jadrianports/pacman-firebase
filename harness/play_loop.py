"""Claude play-loop driver — observe -> decide -> act (HRN-04, D-10/D-18).

`play_turn` lets Claude (or any pluggable `decide_fn`) drive the headless game one
turn at a time:

  - OBSERVE: optionally save a PNG of the current frame (Claude's eyes) and read the
             numeric `capture_state` snapshot.
  - DECIDE:  call `decide_fn(state, png_path)` -> a logical direction
             ("RIGHT"/"LEFT"/"UP"/"DOWN"/"SPACE") or None. This is where Claude is in
             the loop; the callback MUST be pure (no randomness / no wall-clock) so a
             recorded session replays deterministically.
  - ACT:     inject the chosen key via `pygame.event.post` through the REAL input path
             (D-18) — never by mutating `player.direction_command` directly.
  - STEP:    advance exactly one `game.tick()`.

`serialize_inputs` writes the injected `{frame, key, type}` events as the SAME sparse
JSONL that `harness.replay.load_events` parses, so a Claude-played session becomes a
deterministic, CI-replayable golden (the D-10 capture half). The hunt side stays a
manual phase-verification gate, not a committed file.

KEYMAP is imported from `harness.replay` — there is intentionally NO second mapping.
"""
import json

from harness.capture import save_png
from harness.replay import KEYMAP


def play_turn(game, pygame, capture_state, decide_fn, png_path=None):
    """Run one observe -> decide -> act -> step turn; return the post-tick snapshot.

    If `png_path` is given, the current `game.screen` is saved as a PNG before deciding
    (OBSERVE). `decide_fn(state, png_path)` returns a logical key name or None; a
    returned key is injected via `pygame.event.post(KEYDOWN)` (ACT, D-18). The game is
    then advanced one frame with `game.tick()`. Returns `capture_state(game)` after the
    tick so the caller can record the per-frame trace.
    """
    if png_path is not None:
        save_png(pygame, game.screen, png_path)          # OBSERVE (montage frame)
    state = capture_state(game)                           # OBSERVE (numeric snapshot)
    key = decide_fn(state, png_path)                      # DECIDE (Claude in the loop)
    if key:
        pygame.event.post(                                # ACT — real input path (D-18)
            pygame.event.Event(pygame.KEYDOWN, key=getattr(pygame, KEYMAP[key]))
        )
    game.tick()                                           # STEP one frame
    return capture_state(game)


def serialize_inputs(events, path):
    """Write injected `{frame, key, type}` events as sparse JSONL for replay.

    `events` is an iterable of dicts shaped `{"frame": int, "key": str, "type": str}`
    (the same shape `harness.replay.load_events` parses, where `type` defaults to
    "down"). Records are written one JSON object per line, sorted by frame, so a
    recorded session round-trips byte-for-byte through `run_scenario`. Returns `path`.
    """
    ordered = sorted(events, key=lambda e: e["frame"])
    with open(path, "w", encoding="utf-8") as f:
        for ev in ordered:
            record = {"frame": ev["frame"], "key": ev["key"], "type": ev.get("type", "down")}
            f.write(json.dumps(record, sort_keys=True))
            f.write("\n")
    return path
