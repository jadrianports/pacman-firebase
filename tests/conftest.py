"""Repo-wide pytest configuration — the project's first conftest.

Responsibilities:
- Put the repo root on sys.path so tests import project modules by name
  (`import api_service`, `import game`, ...) — the house layout, no src/ dir.
- Force the SDL dummy drivers before any test imports pygame (belt-and-braces
  with harness.headless; pygame reads SDL_* at import time).
- Register the `--bless` flag the golden-master tests (Plan 04) use to re-record.
- Provide firebase-mocked importers for the cloud-function modules so importing
  them under test never reaches real Firestore (their module bodies call
  `initialize_app()` and `firestore.client()` at import time).
"""
import importlib
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

# Repo root on sys.path[0] so `import api_service` / `import game` resolve by name.
_REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# SDL dummy drivers before any test imports pygame. setdefault so an explicit
# outer env (e.g. CI) still wins, but a bare `pytest` run is headless by default.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")


def pytest_addoption(parser):
    """Register --bless; Plan 04 reads it via request.config.getoption('--bless')."""
    parser.addoption(
        "--bless",
        action="store_true",
        default=False,
        help="Re-record golden-master traces instead of asserting against them.",
    )


# Golden-master registry helpers (Plan 04). The committed scenario registry lives at
# tests/golden/manifest.json; these expose it to tests without each test re-deriving
# the path. test_golden_traces.py parametrizes over load_golden_manifest() directly at
# import time; the fixture is provided for any test that prefers fixture injection.
_GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")


def load_golden_manifest():
    """Return the list of scenario entries from tests/golden/manifest.json."""
    import json

    with open(os.path.join(_GOLDEN_DIR, "manifest.json"), "r", encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def golden_manifest():
    """The golden-master scenario registry (tests/golden/manifest.json) as a list."""
    return load_golden_manifest()


@pytest.fixture
def golden_dir():
    """Absolute path to the committed golden-master directory (tests/golden/)."""
    return _GOLDEN_DIR


def _import_cloud_fn(dotted, mock_client):
    """Import a cloud-function module under firebase mocks.

    Patches initialize_app (no-op), forces firebase_admin._apps empty, and makes
    firestore.client() return `mock_client`, then (re)imports the module so its
    import-time `db = firestore.client()` binds the mock. Returns the module with
    the mock exposed as `module._mock_client` for tests to drive.
    """
    sys.modules.pop(dotted, None)  # drop any cached copy so the import re-runs under patches
    with patch("firebase_admin.initialize_app"), \
         patch("firebase_admin._apps", new=[]), \
         patch("firebase_admin.firestore.client", return_value=mock_client):
        module = importlib.import_module(dotted)
    module._mock_client = mock_client
    return module


@pytest.fixture
def submit_module():
    """cloud_functions.submit_score.main imported with a mocked Firestore client."""
    mock_client = MagicMock()
    module = _import_cloud_fn("cloud_functions.submit_score.main", mock_client)
    yield module
    sys.modules.pop("cloud_functions.submit_score.main", None)


@pytest.fixture
def leaderboard_module():
    """cloud_functions.get_leaderboard.main imported with a mocked Firestore client."""
    mock_client = MagicMock()
    module = _import_cloud_fn("cloud_functions.get_leaderboard.main", mock_client)
    yield module
    sys.modules.pop("cloud_functions.get_leaderboard.main", None)
