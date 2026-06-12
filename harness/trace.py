"""Per-frame trace schema (D-03) — a pure reader of existing Game/Ghost state.

`capture_state(game)` snapshots only OBSERVABLE state that already lives on the
`Game` object (flat ghost attrs, `game.targets` set each frame by `get_targets()`,
the player, and counts derived from `game.level`). It adds NO game logic and reads
NO internal counters (D-04: no box-exit timers, no power_counter, no
eat_freeze/starting/dying/flicker/counter). Every captured value is an int or bool,
so comparison is exact and platform-independent (D-05) — no float policy needed.

The serialized form is JSONL: one `json.dumps(..., sort_keys=True)` per frame,
newline-delimited, so goldens diff line-by-line.
"""
import json

# Fixed ghost order for every snapshot (D-03).
GHOST_NAMES = ["blinky", "inky", "pinky", "clyde"]


def capture_state(g):
    """Return the D-03 per-frame snapshot for Game `g` as a plain dict.

    Reads only pre-existing attributes:
      - g._frame            (set by the replay driver, NOT by game.py)
      - g.player.x/y/direction
      - g.{name}_x/_y/_direction/_dead/_box   (flat ghost attrs on Game)
      - g.targets[i]        (set each frame by g.get_targets(), game.py:531)
      - g.score / g.lives / g.powerup / g.game_over / g.game_won
      - g.level             (tile codes 1=dot, 2=big dot → dots_remaining)
    """
    targets = g.targets
    ghosts = []
    for i, name in enumerate(GHOST_NAMES):
        ghosts.append({
            "name": name,
            "x": getattr(g, f"{name}_x"),
            "y": getattr(g, f"{name}_y"),
            "dir": getattr(g, f"{name}_direction"),
            "dead": getattr(g, f"{name}_dead"),
            "box": getattr(g, f"{name}_box"),
            "target": list(targets[i]),
        })
    return {
        "frame": g._frame,
        "pacman": {"x": g.player.x, "y": g.player.y, "dir": g.player.direction},
        "ghosts": ghosts,
        "score": g.score,
        "lives": g.lives,
        "powerup": g.powerup,
        "dots_remaining": sum(row.count(1) + row.count(2) for row in g.level),
        "game_over": g.game_over,
        "game_won": g.game_won,
    }


def write_jsonl(trace, path):
    """Write a list-of-snapshots trace to `path`, one JSON object per line.

    `sort_keys=True` makes the on-disk bytes stable so goldens diff cleanly.
    """
    with open(path, "w", encoding="utf-8") as f:
        for snap in trace:
            f.write(json.dumps(snap, sort_keys=True))
            f.write("\n")


def read_jsonl(path):
    """Read a JSONL trace file back into a list of snapshot dicts."""
    trace = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                trace.append(json.loads(line))
    return trace


def traces_equal(a, b):
    """Exact equality of two traces (list of snapshot dicts), per D-05.

    All values are ints/bools, so plain `==` is a byte-for-byte semantic compare.
    """
    return a == b


def diff_traces(a, b):
    """Return a human-readable per-frame / per-field diff string.

    Empty string means the traces are identical. Used by `pytest --bless` (Plan 04)
    to show what changed when a golden is re-blessed.
    """
    lines = []
    if len(a) != len(b):
        lines.append(f"length differs: baseline={len(a)} frames, other={len(b)} frames")
    n = min(len(a), len(b))
    for i in range(n):
        sa, sb = a[i], b[i]
        if sa == sb:
            continue
        keys = sorted(set(sa) | set(sb))
        for k in keys:
            va = sa.get(k, "<missing>")
            vb = sb.get(k, "<missing>")
            if va != vb:
                lines.append(f"frame {i}: {k}: baseline={va!r} other={vb!r}")
    return "\n".join(lines)
