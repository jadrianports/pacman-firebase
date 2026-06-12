"""Determinism guard (D-12, T-04-T2).

A static, plain-pytest check (NO pygame import, NO game execution) that HARD-FAILS CI if
any randomness or wall-clock token enters game.py / ghost.py / player.py. The entire
golden-master safety net depends on the game being deterministic (integer pixel math +
frame-counter timers, zero `random`, zero wall-clock) — record/replay is only
frame-perfect because of that property. This test locks the property in: the moment a
`random` / `time.time` / `get_ticks` / `datetime` call lands in the game logic, the net
silently stops meaning anything, so we fail loudly instead.

Comment-only lines are stripped before scanning so header prose (this docstring's twin
in a source file, or an inline note mentioning randomness) does not self-invalidate the
gate.
"""
import os

import pytest

_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))

# Files whose source must stay free of nondeterminism (D-12).
GUARDED_FILES = ["game.py", "ghost.py", "player.py"]

# Forbidden tokens: randomness + wall-clock. Scanned as substrings on code lines.
FORBIDDEN_TOKENS = ["random", "randint", "shuffle", "time.time", "get_ticks", "datetime"]


def _scan_source(text):
    """Return a list of (line_number, token) hits for any forbidden token appearing on a
    NON-comment line of `text`. A line whose stripped form starts with '#' is treated as
    a comment and skipped. Line numbers are 1-based."""
    hits = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue  # comment-only line — prose may mention 'random' harmlessly
        for token in FORBIDDEN_TOKENS:
            if token in line:
                hits.append((lineno, token))
    return hits


@pytest.mark.parametrize("filename", GUARDED_FILES)
def test_no_forbidden_tokens(filename):
    """game.py / ghost.py / player.py contain none of the forbidden nondeterminism
    tokens on any code line (D-12). Each file is read exactly once."""
    path = os.path.join(_REPO_ROOT, filename)
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    hits = _scan_source(text)
    assert not hits, (
        f"determinism guard tripped in {filename}: "
        + ", ".join(f"line {ln} -> '{tok}'" for ln, tok in hits)
    )


def test_scanner_ignores_comment_lines():
    """A forbidden word in a comment-only line does NOT trip the guard."""
    src = "x = 1\n# this comment mentions random and time.time harmlessly\ny = 2\n"
    assert _scan_source(src) == []


def test_scanner_detects_code_line():
    """A forbidden token on a real code line IS detected and reported with its name."""
    src = "import os\nstamp = time.time()\n"
    hits = _scan_source(src)
    assert (2, "time.time") in hits
    # an inline comment after code still counts as a code line if the token is in code
    src2 = "val = random.randint(0, 9)  # pick one\n"
    tokens = {tok for _, tok in _scan_source(src2)}
    assert "random" in tokens and "randint" in tokens
