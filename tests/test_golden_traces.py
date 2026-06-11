"""Golden-master replay tests (TST-01, HRN-02/03/04, D-05/D-07/D-11).

Every scenario in tests/golden/manifest.json is replayed against the REAL headless game
and compared byte-for-byte to its committed golden trace (D-05). Standing per-frame
invariants (D-11) run on EVERY frame of EVERY replay. `pytest --bless` re-records the
goldens and prints a human-readable per-frame/field diff instead of asserting (D-07).
A capture smoke test proves PNG/montage/GIF are produced (HRN-03).

This is the safety net Phase 2's "byte-identical" and Phase 3's "isolated to the box
edges" proofs read. The box_edge and tunnel_wrap scenarios are authored to catch those
changes at the exact frame.

Replay model:
  - terminal == "game_over"/"game_won": driven via harness.replay.run_scenario, which
    breaks on the natural terminal (D-19) and raises loudly on a frame_cap soft-lock.
  - terminal == "fixed_frames": a bounded window (the scenario exercises a behavior but
    never reaches game_over/game_won), replayed via the SAME per-frame body without the
    soft-lock backstop, frozen at exactly frame_cap frames.
"""
import json
import os

import pytest

from harness.headless import init_headless
from harness.replay import KEYMAP, install_frame_driven_sound, load_events, run_scenario
from harness.trace import capture_state, diff_traces, read_jsonl, traces_equal, write_jsonl

# Headless pygame once for the whole module (SDL dummy; conftest also forces the env).
pygame, _screen, _clock = init_headless()
from game import Game  # noqa: E402  (import after headless init)

_HERE = os.path.dirname(__file__)
_REPO_ROOT = os.path.dirname(_HERE)
_MANIFEST_PATH = os.path.join(_HERE, "golden", "manifest.json")

# Board tile codes that count as a wall/gate for the wall-clip invariant (D-11).
# 0=empty, 1=dot, 2=big dot are walkable; 3/4=walls, 5-8=corners, 9=gate are NOT.
WALL_CODES = {3, 4, 5, 6, 7, 8, 9}
# Tile-size math — IDENTICAL to game.py (num1=(HEIGHT-50)//32, num2=WIDTH//30).
NUM1 = (950 - 50) // 32  # 28
NUM2 = 900 // 30         # 30
MAX_SCORE = 500000


def _load_manifest():
    with open(_MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


MANIFEST = _load_manifest()


def _abs_input(entry):
    return os.path.join(_REPO_ROOT, entry["input"])


def _trace_path(entry):
    return os.path.join(_HERE, "golden", entry["name"], "trace.jsonl")


def _new_game():
    g = Game(_screen, _clock)
    install_frame_driven_sound(g)  # headless sound-gating shim (Plan 02)
    return g


def _replay_fixed(game, input_path, frame_cap):
    """Bounded replay for fixed_frames scenarios — the run_scenario body WITHOUT the
    soft-lock `else` raise. Returns exactly `frame_cap` frames (or fewer if a natural
    terminal is hit early). Mirrors run_scenario exactly so a terminal scenario and a
    fixed scenario capture identical per-frame state."""
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
        if game.game_over or game.game_won:
            break
    return trace


def replay_scenario(entry):
    """Replay one manifest scenario and return its per-frame trace (today's behavior)."""
    game = _new_game()
    input_path = _abs_input(entry)
    if entry["terminal"] in ("game_over", "game_won"):
        return run_scenario(game, pygame, input_path, entry["frame_cap"], capture_state)
    return _replay_fixed(game, input_path, entry["frame_cap"])


# --------------------------------------------------------------------------------------
# Standing per-frame invariants (D-11) — run on EVERY frame of EVERY replay.
# --------------------------------------------------------------------------------------

def pacman_tile_code(snapshot, level):
    """Map Pac-Man's CENTER to a board tile using the game's exact tile-size math."""
    px, py = snapshot["pacman"]["x"], snapshot["pacman"]["y"]
    center_x, center_y = px + 23, py + 24
    row = center_y // NUM1
    col = center_x // NUM2
    # Clamp to board bounds (tunnel wrap can push the center just past an edge).
    row = max(0, min(len(level) - 1, row))
    col = max(0, min(len(level[0]) - 1, col))
    return level[row][col]


def assert_score_in_range(snapshot):
    score = snapshot["score"]
    assert 0 <= score <= MAX_SCORE, (
        f"frame {snapshot['frame']}: score {score} outside [0, {MAX_SCORE}]"
    )


def assert_not_in_wall(snapshot, level):
    code = pacman_tile_code(snapshot, level)
    assert code not in WALL_CODES, (
        f"frame {snapshot['frame']}: Pac-Man center on wall tile (code {code}) "
        f"at {snapshot['pacman']}"
    )


class _SoftlockTracker:
    """No-soft-lock guard (D-11): fail if Pac-Man stays stationary AND score/dots do not
    advance for more than `softlock_n` consecutive frames. Legitimate pauses
    (starting/dying/eat_freeze) are far shorter than `softlock_n` (calibrated > the
    longest legit pause), so a trip means a genuine permanent soft-lock — not a real
    pause. D-04 forbids reading the pause flags, so the guard infers a pause from the
    absence of position/score/dots change combined with the calibrated threshold."""

    def __init__(self, softlock_n):
        self.softlock_n = softlock_n
        self.stuck = 0
        self.prev_pos = None
        self.prev_score = None
        self.prev_dots = None

    def update(self, snapshot):
        pos = (snapshot["pacman"]["x"], snapshot["pacman"]["y"])
        score = snapshot["score"]
        dots = snapshot["dots_remaining"]
        if (self.prev_pos is not None and pos == self.prev_pos
                and score == self.prev_score and dots == self.prev_dots):
            self.stuck += 1
        else:
            self.stuck = 0
        assert self.stuck <= self.softlock_n, (
            f"frame {snapshot['frame']}: soft-lock — no progress (pos/score/dots) "
            f"for {self.stuck} > softlock_n={self.softlock_n} frames"
        )
        self.prev_pos, self.prev_score, self.prev_dots = pos, score, dots


def assert_invariants(trace, entry):
    """Run all standing per-frame invariants (D-11) over a full trace + the manifest
    terminal expectation."""
    level = Game(_screen, _clock).level  # a fresh, full board for wall-tile lookup
    tracker = _SoftlockTracker(entry.get("softlock_n", 720))
    for snapshot in trace:
        assert_score_in_range(snapshot)
        assert_not_in_wall(snapshot, level)
        tracker.update(snapshot)
    # Terminal expectation (D-19): a natural terminal must actually be reached; a
    # fixed_frames scenario must run the full declared window (not end early).
    last = trace[-1]
    if entry["terminal"] == "game_over":
        assert last["game_over"] is True, f"{entry['name']} did not reach game_over"
    elif entry["terminal"] == "game_won":
        assert last["game_won"] is True, f"{entry['name']} did not reach game_won"
    else:  # fixed_frames
        assert len(trace) == entry["frame_cap"], (
            f"{entry['name']} fixed_frames expected {entry['frame_cap']} frames, "
            f"got {len(trace)} (ended early — terminal hit?)"
        )


# --------------------------------------------------------------------------------------
# The parametrized golden-trace test (D-05) + --bless re-bless with diff (D-07).
# Test id contains "baseline" so `pytest -k baseline` selects the replay-vs-golden family.
# --------------------------------------------------------------------------------------

@pytest.mark.parametrize("entry", MANIFEST, ids=[e["name"] for e in MANIFEST])
def test_baseline_golden(entry, request):
    """Replay the scenario and assert byte-identical to its committed golden (D-05);
    under --bless, re-record the golden and print the per-frame/field diff (D-07)."""
    replayed = replay_scenario(entry)
    assert_invariants(replayed, entry)

    trace_path = _trace_path(entry)
    if request.config.getoption("--bless"):
        old = read_jsonl(trace_path) if os.path.exists(trace_path) else []
        write_jsonl(replayed, trace_path)
        diff = diff_traces(old, replayed)
        print(f"\n=== BLESS DIFF [{entry['name']}] ({len(replayed)} frames) ===")
        print(diff if diff else "(no change — golden already matched)")
        return  # do NOT assert in bless mode — we just re-recorded

    assert os.path.exists(trace_path), (
        f"missing committed golden {trace_path} — run `pytest --bless` to record it"
    )
    golden = read_jsonl(trace_path)
    if not traces_equal(replayed, golden):
        # Surface a readable diff on failure so a regression is debuggable.
        pytest.fail(
            f"{entry['name']} trace diverged from committed golden:\n"
            + diff_traces(golden, replayed)
        )


def test_claude_session_replays_green(request):
    """HRN-04: the recorded Claude session replays deterministically (named so
    `pytest -k claude_session` selects it)."""
    entry = next(e for e in MANIFEST if e["name"] == "claude_session_01")
    replayed = replay_scenario(entry)
    assert_invariants(replayed, entry)
    if request.config.getoption("--bless"):
        pytest.skip("bless mode — golden re-recorded by test_baseline_golden")
    golden = read_jsonl(_trace_path(entry))
    assert traces_equal(replayed, golden), diff_traces(golden, replayed)


# --------------------------------------------------------------------------------------
# Determinism: re-running a scenario twice yields the identical trace.
# --------------------------------------------------------------------------------------

def test_replay_is_deterministic():
    """A scenario replayed twice produces byte-identical traces (the property the whole
    net depends on)."""
    entry = next(e for e in MANIFEST if e["name"] == "ghost_eat")
    a = replay_scenario(entry)
    b = replay_scenario(entry)
    assert traces_equal(a, b), diff_traces(a, b)


# --------------------------------------------------------------------------------------
# Invariant self-tests — prove the invariants actually catch corruption (T-04-T).
# --------------------------------------------------------------------------------------

def _crafted_snapshot(score=0, pacman=(450, 663)):
    return {
        "frame": 0,
        "pacman": {"x": pacman[0], "y": pacman[1], "dir": 0},
        "ghosts": [],
        "score": score,
        "lives": 3,
        "powerup": False,
        "dots_remaining": 0,
        "game_over": False,
        "game_won": False,
    }


def test_score_invariant_catches_overflow():
    with pytest.raises(AssertionError):
        assert_score_in_range(_crafted_snapshot(score=MAX_SCORE + 1))
    with pytest.raises(AssertionError):
        assert_score_in_range(_crafted_snapshot(score=-1))
    # a valid score does NOT raise
    assert_score_in_range(_crafted_snapshot(score=12345))


def test_wall_clip_invariant_catches_wall():
    level = Game(_screen, _clock).level
    # Tile (0,0) is a corner wall code (6) — place Pac-Man center there.
    # center maps to tile via (cy//28, cx//30); pick coords landing in row 0 col 0.
    wall_snap = _crafted_snapshot(pacman=(-23, -24))  # center (0,0) -> tile (0,0)
    with pytest.raises(AssertionError):
        assert_not_in_wall(wall_snap, level)
    # The real start position is a walkable corridor — must NOT raise.
    assert_not_in_wall(_crafted_snapshot(pacman=(450, 663)), level)


def test_softlock_invariant_catches_permanent_stall():
    tracker = _SoftlockTracker(softlock_n=5)
    snap = _crafted_snapshot()
    # First update establishes baseline; then 5 identical frames are allowed, the 6th trips.
    with pytest.raises(AssertionError):
        for f in range(20):
            s = _crafted_snapshot()
            s["frame"] = f
            tracker.update(s)


# --------------------------------------------------------------------------------------
# Capture smoke (HRN-03) — produce PNG/montage/GIF for ONE short scenario.
# Named so `pytest -k capture` selects it. Writes ONLY under gitignored tests/artifacts/.
# --------------------------------------------------------------------------------------

def test_capture_smoke_png_montage_gif(tmp_path):
    """HRN-03: run one short scenario, save PNGs via an on_frame hook, then assemble a
    montage PNG and a GIF; assert the artifact files exist. No pixel comparison (D-06)."""
    from harness.capture import build_gif, build_montage, save_png

    artifacts = os.path.join(_HERE, "artifacts", "capture_smoke")
    os.makedirs(artifacts, exist_ok=True)

    game = _new_game()
    png_paths = []
    surfaces = []

    def on_frame(frame, g):
        # Sample a few frames spread across the starting + first-move window.
        if frame % 80 == 0 and len(png_paths) < 6:
            p = os.path.join(artifacts, f"frame_{frame:05d}.png")
            save_png(pygame, g.screen, p)
            png_paths.append(p)
            surfaces.append(g.screen.copy())

    entry = next(e for e in MANIFEST if e["name"] == "box_exit")
    _replay_fixed_with_hook(game, _abs_input(entry), entry["frame_cap"], on_frame)

    assert len(png_paths) >= 2, "expected several PNG stills captured"
    montage = build_montage(pygame, surfaces, cols=3)
    montage_path = os.path.join(artifacts, "montage.png")
    save_png(pygame, montage, montage_path)
    gif_path = os.path.join(artifacts, "playback.gif")
    build_gif(png_paths, gif_path, duration_ms=120)

    assert os.path.exists(montage_path) and os.path.getsize(montage_path) > 0
    assert os.path.exists(gif_path) and os.path.getsize(gif_path) > 0


def _replay_fixed_with_hook(game, input_path, frame_cap, on_frame):
    """Bounded replay that invokes on_frame(frame, game) each frame (capture smoke)."""
    events = load_events(input_path)
    for frame in range(frame_cap):
        game._frame = frame
        for ev in events.get(frame, []):
            etype = pygame.KEYDOWN if ev.get("type", "down") == "down" else pygame.KEYUP
            pygame.event.post(pygame.event.Event(etype, key=getattr(pygame, KEYMAP[ev["key"]])))
        game.tick()
        on_frame(frame, game)
        if game.game_over or game.game_won:
            break
