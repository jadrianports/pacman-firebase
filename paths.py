import sys
import os

from settings import IDENTITY_DIR_NAME


def user_data_dir():
    """Get the per-user identity storage directory, creating it if missing.

    On Windows this is ``%LOCALAPPDATA%\\PacMan\\`` (D-01) — per-user, local (not
    roaming), and deliberately OFF the desktop and NOT next to the exe. On a
    non-Windows host (no LOCALAPPDATA, e.g. a dev machine) it falls back to
    ``~/.pacman`` so dev runs still work. The folder is created with
    ``exist_ok=True`` before returning, so callers can write immediately; repeat
    calls are idempotent.

    The folder name comes from ``settings.IDENTITY_DIR_NAME`` — not hardcoded here.
    ``data_path``/``resource_path`` are unaffected (migration still needs the
    legacy next-to-exe path).
    """
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        target = os.path.join(local_app_data, IDENTITY_DIR_NAME)
    else:
        target = os.path.join(os.path.expanduser("~"), ".pacman")
    os.makedirs(target, exist_ok=True)
    return target


def user_data_path(relative_path):
    """Join ``relative_path`` (e.g. the identity blob filename) onto user_data_dir()."""
    return os.path.join(user_data_dir(), relative_path)


def resource_path(relative_path):
    """Get path to bundled resource. Works for dev and PyInstaller."""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def data_path(relative_path):
    """Get path for user data files (next to exe, or project root in dev)."""
    if getattr(sys, 'frozen', False):
        base_path = os.path.dirname(sys.executable)
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)
