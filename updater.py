"""Best-effort auto-update via tufup. Runs ONLY in a frozen build, once at startup,
and swallows every error so it can never block or crash the game — exactly the
graceful-degrade contract the leaderboard uses. The real tufup flow lives in
``_run_update`` so it can be tested in isolation (and so tufup is imported lazily,
only when actually updating)."""
import os
import sys

from settings import APP_VERSION

APP_NAME = "Pacman"
# Firebase Hosting paths for the TUF repo (static files). Trailing slashes required.
METADATA_BASE_URL = "https://pacman-firebase.web.app/updates/metadata/"
TARGET_BASE_URL = "https://pacman-firebase.web.app/updates/targets/"


def is_active():
    """True only in a PyInstaller-frozen build (never in dev / tests)."""
    return bool(getattr(sys, "frozen", False))


def _install_dir():
    """Directory of the running exe (what tufup swaps in place)."""
    return os.path.dirname(sys.executable)


def _cache_dir():
    """User-writable cache for downloaded metadata/targets (never the install dir)."""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, APP_NAME, "update-cache")
    os.makedirs(d, exist_ok=True)
    return d


def _run_update(on_status):
    """The real tufup client flow. Imported lazily; raises on any failure (caught by
    the caller). Returns True if an update was downloaded+applied (the platform helper
    then restarts the app), else False.

    NOTE: bootstrapping the trusted root.json into the metadata cache on first run is
    done here (copy the bundled assets/tuf/root.json if the cache has none)."""
    import shutil
    from tufup.client import Client

    metadata_dir = os.path.join(_cache_dir(), "metadata")
    target_dir = os.path.join(_cache_dir(), "targets")
    os.makedirs(metadata_dir, exist_ok=True)
    os.makedirs(target_dir, exist_ok=True)

    # Bootstrap trust anchor on first run.
    trusted_root = os.path.join(metadata_dir, "root.json")
    if not os.path.exists(trusted_root):
        from paths import resource_path
        shutil.copyfile(resource_path("assets/tuf/root.json"), trusted_root)

    client = Client(
        app_name=APP_NAME,
        app_install_dir=_install_dir(),
        current_version=APP_VERSION,
        metadata_dir=metadata_dir,
        metadata_base_url=METADATA_BASE_URL,
        target_dir=target_dir,
        target_base_url=TARGET_BASE_URL,
    )
    if not client.check_for_updates():
        return False
    if on_status:
        on_status("Updating...")  # ASCII dots — the pixel font has no … glyph
    client.download_and_apply_update(skip_confirmation=True)
    return True


def check_and_apply(on_status=None):
    """If frozen and an update exists, apply it (process is then replaced by the helper).
    Best-effort: returns False and lets the game continue on ANY problem. Never raises."""
    if not is_active():
        return False
    try:
        return bool(_run_update(on_status))
    except Exception:
        # Updates are a convenience; a failure must never stop the game launching.
        return False
