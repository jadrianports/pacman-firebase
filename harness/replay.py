"""Record/replay driver for the headless game (HRN-02, TST-01, D-18/D-19).

`run_scenario` injects sparse `{frame, key}` events into the REAL input path via
`pygame.event.post` (so `handle_events()`'s KEYDOWN/KEYUP logic is exercised — D-18),
steps `game.tick()` once per frame, captures the per-frame trace, terminates on the
natural game end (`game_over`/`game_won` — D-19), and raises loudly if a scenario
runs past `frame_cap` without terminating (the soft-lock backstop — D-19/T-02-D).

Also provides `install_frame_driven_sound`, a harness-only shim required because the
SDL **dummy** audio driver reports a played Sound as "playing" forever — which would
soft-lock the game in its `starting` phase. The shim makes
`is_start_playing()`/`is_death_playing()` advance by frame count (sound length * FPS),
reproducing interactive behavior deterministically with NO change to game.py.
"""
import json

from settings import FPS


def load_events(input_path):
    """Parse a sparse JSONL input file into a {frame: [event, ...]} dict.

    Each record is `{"frame": int, "key": str, "type": "down"|"up"}` where `type`
    defaults to "down" (a held arrow) when omitted.
    """
    by_frame = {}
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                ev = json.loads(line)
                by_frame.setdefault(ev["frame"], []).append(ev)
    return by_frame


# Logical key name -> pygame K_* attribute name.
KEYMAP = {
    "RIGHT": "K_RIGHT",
    "LEFT": "K_LEFT",
    "UP": "K_UP",
    "DOWN": "K_DOWN",
    "SPACE": "K_SPACE",
}


def install_frame_driven_sound(game):
    """Make game.sound's playback queries advance by frame count (headless determinism).

    Under SDL dummy audio, a played Sound reports `get_num_channels() > 0` forever, so
    `is_start_playing()` would never become False and the game would never leave the
    `starting` phase. This shim records the frame each sound was played on (via the
    driver-maintained `game._frame`) and reports the sound "playing" only until its
    real length in frames has elapsed. No game.py change.

    Used identically by the baseline capture and the tick() replay so the byte-for-byte
    comparison still detects any statement reorder in the extraction.
    """
    sm = game.sound

    start_frames = int(sm.start_sound.get_length() * FPS) if sm.start_sound else 0
    death_frames = int(sm.death_sound.get_length() * FPS) if sm.death_sound else 0

    state = {"start_at": None, "death_at": None}

    real_play_start = sm.play_start
    real_play_death = sm.play_death

    def play_start():
        state["start_at"] = getattr(game, "_frame", 0)
        real_play_start()

    def play_death():
        state["death_at"] = getattr(game, "_frame", 0)
        real_play_death()

    def is_start_playing():
        if state["start_at"] is None:
            return False
        return (getattr(game, "_frame", 0) - state["start_at"]) < start_frames

    def is_death_playing():
        if state["death_at"] is None:
            return False
        return (getattr(game, "_frame", 0) - state["death_at"]) < death_frames

    sm.play_start = play_start
    sm.play_death = play_death
    sm.is_start_playing = is_start_playing
    sm.is_death_playing = is_death_playing
    return game


def run_scenario(game, pygame, input_path, frame_cap, capture_state, on_frame=None):
    """Replay a scenario deterministically and return the per-frame trace.

    For each frame in `range(frame_cap)`:
      - set `game._frame = frame` (the trace's frame field; never added to game.py),
      - post every event scheduled at this frame via `pygame.event.post` (D-18),
      - step one frame with `game.tick()`,
      - append `capture_state(game)` to the trace,
      - call `on_frame(frame, game)` if provided (Plan 03 saves PNGs here),
      - break on `game.game_over or game.game_won` (D-19 natural terminal).

    If the loop exhausts `frame_cap` without terminating, the `else` clause raises an
    AssertionError naming the cap — the loud soft-lock backstop (D-19, T-02-D).
    """
    events = load_events(input_path)
    trace = []
    for frame in range(frame_cap):
        game._frame = frame
        for ev in events.get(frame, []):
            etype = pygame.KEYDOWN if ev.get("type", "down") == "down" else pygame.KEYUP
            key = getattr(pygame, KEYMAP[ev["key"]])
            pygame.event.post(pygame.event.Event(etype, key=key))
        game.tick()
        trace.append(capture_state(game))
        if on_frame is not None:
            on_frame(frame, game)
        if game.game_over or game.game_won:
            break
    else:
        raise AssertionError(
            f"scenario hit frame_cap={frame_cap} without terminating (soft-lock?)"
        )
    return trace
