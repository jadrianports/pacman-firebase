# Auto-Update + Installer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `tufup` auto-update-on-launch (best-effort, frozen-only) plus the release tooling and Inno Setup installer, producing two auto-updating distribution channels (`pacman.zip` + `pacman-setup.exe`) from one build.

**Architecture:** A new `updater.py` runs a `tufup` client once at startup behind a `frozen`-only guard, swallowing all errors so it never blocks the game. A new `release.py` (dev tool) builds, zips, and publishes a tufup bundle. `build.py` bundles the trusted `root.json`. An `installer/pacman.iss` wraps the build for a polished install to `%LOCALAPPDATA%\Pacman`. `RELEASE.md` documents the operator-only steps (key generation, Inno Setup, Firebase deploy).

**Tech Stack:** Python 3.12, `tufup==0.10.0`, PyInstaller 6.20, Inno Setup (operator), Firebase Hosting, pytest.

## Global Constraints

- **Updater is frozen-only + best-effort.** Active only when `getattr(sys, "frozen", False)`. Any failure (offline, host down, bad metadata) is caught — the game ALWAYS launches. Never raises out of `check_and_apply`.
- **Install/run location must be user-writable** (`%LOCALAPPDATA%\Pacman` or any writable extract dir) so in-place self-update needs no admin.
- **`root.json` is public** (committed/bundled); the four TUF **private keys are gitignored** (like `hmac_secret.local`) and operator-managed.
- **No change to the game loop or determinism path.** Updater is startup-only. Suite stays green (`168 passed, 9 skipped`).
- **`tufup` added to `requirements.txt`** and bundled by PyInstaller (hidden imports for `tuf` if needed).
- **Python env:** run tests via `.venv/Scripts/python.exe`.

---

### Task 1: Version constant + dependency

**Files:**
- Modify: `settings.py` (add `APP_VERSION`), `requirements.txt` (add tufup)
- Test: `tests/test_version.py`

**Interfaces:**
- Produces: `settings.APP_VERSION` (PEP440 string, e.g. `"1.0.0"`).

- [ ] **Step 1: Write the failing test**

Create `tests/test_version.py`:

```python
import re
import settings


def test_app_version_is_pep440_string():
    assert isinstance(settings.APP_VERSION, str)
    # simple major.minor.patch (PEP440 subset we use)
    assert re.fullmatch(r"\d+\.\d+\.\d+", settings.APP_VERSION), settings.APP_VERSION
```

- [ ] **Step 2: Run it → FAIL** (`AttributeError: APP_VERSION`)

Run: `.venv/Scripts/python.exe -m pytest tests/test_version.py -v`

- [ ] **Step 3: Add the constant**

In `settings.py`, near the top (after the imports), add:

```python
# Shipped app version (PEP440). tufup compares this to the signed update metadata
# to decide whether a newer build is available. Bump on every release.
APP_VERSION = "1.0.0"
```

- [ ] **Step 4: Add tufup to requirements.txt**

Append:

```
tufup==0.10.0
```

(Do NOT pip-install in CI here; the import is exercised only in `release.py`/frozen builds. The updater test mocks it.)

- [ ] **Step 5: Run the test → PASS**, then full suite → green.

Run: `.venv/Scripts/python.exe -m pytest tests/test_version.py -v` then `.venv/Scripts/python.exe -m pytest -q`

- [ ] **Step 6: Commit**

```bash
git add settings.py requirements.txt tests/test_version.py
git commit -m "feat(update): APP_VERSION constant + tufup dependency"
```

---

### Task 2: `updater.py` — frozen-only, graceful-degrade client

**Files:**
- Create: `updater.py`
- Test: `tests/test_updater.py`

**Interfaces:**
- Produces:
  - `updater.is_active() -> bool` — true only in a frozen build.
  - `updater.check_and_apply(on_status=None) -> bool` — returns True if an update was applied (the helper then restarts the app), False otherwise. NEVER raises.
  - `updater._run_update(on_status)` — the real tufup flow, isolated so the test can monkeypatch it without tufup installed.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_updater.py`:

```python
import sys
import updater


def test_is_active_false_in_dev():
    # pytest runs unfrozen
    assert updater.is_active() is False


def test_check_and_apply_noop_when_not_frozen(monkeypatch):
    called = {"ran": False}
    monkeypatch.setattr(updater, "_run_update", lambda on_status: called.__setitem__("ran", True))
    monkeypatch.setattr(updater, "is_active", lambda: False)
    assert updater.check_and_apply() is False
    assert called["ran"] is False          # never even attempts the update when unfrozen


def test_check_and_apply_swallows_errors(monkeypatch):
    monkeypatch.setattr(updater, "is_active", lambda: True)
    def boom(on_status):
        raise RuntimeError("network down / bad metadata")
    monkeypatch.setattr(updater, "_run_update", boom)
    # must NOT raise — the game has to launch regardless
    assert updater.check_and_apply() is False


def test_check_and_apply_returns_true_when_update_applied(monkeypatch):
    monkeypatch.setattr(updater, "is_active", lambda: True)
    monkeypatch.setattr(updater, "_run_update", lambda on_status: True)
    assert updater.check_and_apply() is True
```

- [ ] **Step 2: Run → FAIL** (`ModuleNotFoundError: updater`)

Run: `.venv/Scripts/python.exe -m pytest tests/test_updater.py -v`

- [ ] **Step 3: Implement `updater.py`**

```python
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
        on_status("Updating…")
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
```

- [ ] **Step 4: Run → PASS**, then full suite green.

Run: `.venv/Scripts/python.exe -m pytest tests/test_updater.py -v` then `.venv/Scripts/python.exe -m pytest -q`

- [ ] **Step 5: Commit**

```bash
git add updater.py tests/test_updater.py
git commit -m "feat(update): frozen-only graceful-degrade tufup client"
```

---

### Task 3: Wire the updater into `main.py` startup

**Files:**
- Modify: `main.py` (call `updater.check_and_apply` after init, before the menu loop)
- Test: covered by `tests/test_updater.py` (main.py's `main()` isn't unit-tested; the guard makes the call a no-op in dev)

**Interfaces:**
- Consumes: `updater.check_and_apply`, `theme.pixel_font`.

- [ ] **Step 1: Add the startup hook**

In `main.py`, `import updater` at the top. After `pygame.init()` + the icon `set_icon` + `set_mode` + `set_caption` (so there's a window to draw the notice on), add the update check before the identity/menu logic:

```python
    # Best-effort auto-update (frozen builds only; never blocks startup).
    def _update_notice(msg):
        screen.fill((6, 6, 18))
        surf = theme.pixel_font(theme.SIZE_HEADING).render(msg, True, (255, 255, 0))
        screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()

    updater.check_and_apply(on_status=_update_notice)
```

Add `import theme` to `main.py` if not already imported.

(When an update IS applied, tufup's helper relaunches the process, so control does not return here. When not, execution continues to the menu as normal.)

- [ ] **Step 2: Sanity-check main.py imports + the suite**

Run: `.venv/Scripts/python.exe -c "import ast; ast.parse(open('main.py').read()); print('main.py parses')"`
Run: `.venv/Scripts/python.exe -m pytest -q`
Expected: parses; `170 passed, 9 skipped` (version + updater tests added).

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat(update): run best-effort updater at startup with on-screen notice"
```

---

### Task 4: Bundle `root.json` in the build + tufup hidden imports

**Files:**
- Modify: `build.py`
- Test: manual (build is an operator step; this task only wires the flags)

**Interfaces:**
- Produces: a build that includes `assets/tuf/root.json` and the tufup/tuf modules.

- [ ] **Step 1: Add the data + hidden imports**

In `build.py`'s PyInstaller arg list, add (after the existing `--add-data` lines):

```python
        "--add-data=assets/tuf/root.json;assets/tuf",
        "--collect-submodules=tuf",
        "--collect-submodules=tufup",
        "--collect-submodules=securesystemslib",
```

Add a guard near the top of `build.py`'s `main()` (after `_read_secret`) so a build without the published trust anchor fails loudly rather than shipping an un-updatable app:

```python
    root_json = os.path.join(ROOT, "assets", "tuf", "root.json")
    if not os.path.exists(root_json):
        raise SystemExit(
            "ERROR: assets/tuf/root.json missing. Run `python release.py --init` once to "
            "generate the TUF keys + root.json before the first build (see RELEASE.md)."
        )
```

- [ ] **Step 2: Verify build.py still parses**

Run: `.venv/Scripts/python.exe -c "import ast; ast.parse(open('build.py').read()); print('build.py parses')"`

- [ ] **Step 3: Commit**

```bash
git add build.py
git commit -m "build(update): bundle root.json + collect tufup/tuf submodules"
```

---

### Task 5: `release.py` — build, zip, publish the tufup bundle (dev tool)

**Files:**
- Create: `release.py`
- Test: `tests/test_release_smoke.py` (imports + arg parsing only — running it needs keys)

**Interfaces:**
- Produces: `release.py` with `--init` (one-time key/repo setup) and default (cut a release) modes.

- [ ] **Step 1: Write a smoke test (import + CLI shape only)**

Create `tests/test_release_smoke.py`:

```python
import importlib
import sys


def test_release_module_imports_and_has_cli():
    # release.py must import without side effects and expose main() + an arg parser.
    mod = importlib.import_module("release")
    assert hasattr(mod, "main")
    assert hasattr(mod, "build_parser")
    p = mod.build_parser()
    ns = p.parse_args(["--init"])
    assert ns.init is True
```

- [ ] **Step 2: Run → FAIL** (`ModuleNotFoundError: release`)

- [ ] **Step 3: Implement `release.py`**

```python
"""Developer release tool (NOT shipped). Cuts an auto-updatable release:

  python release.py --init     # one-time: generate TUF keys + root.json, init repo
  python release.py            # build + zip + add signed bundle to the TUF repo

Operator then deploys ./repo to Firebase Hosting /updates and compiles the installer.
See RELEASE.md. tufup + its keys are imported/used only here, never in the game."""
import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.join(ROOT, "repo")
KEYS_DIR = os.path.join(ROOT, "tuf-keys")          # gitignored — private keys
DIST_APP = os.path.join(ROOT, "dist", "pacman")
ROOT_JSON_DEST = os.path.join(ROOT, "assets", "tuf", "root.json")
APP_NAME = "Pacman"


def build_parser():
    p = argparse.ArgumentParser(description="Cut an auto-updatable Pac-Man release.")
    p.add_argument("--init", action="store_true",
                   help="one-time: generate TUF keys + root.json and initialise the repo")
    return p


def _app_version():
    sys.path.insert(0, ROOT)
    import settings
    return settings.APP_VERSION


def init_repo():
    """One-time TUF setup: keypairs for the four roles, initial metadata, and the
    public root.json copied into assets/tuf so the build can bundle it."""
    from tufup.repo import Repository
    os.makedirs(KEYS_DIR, exist_ok=True)
    repo = Repository(
        app_name=APP_NAME,
        repo_dir=REPO_DIR,
        keys_dir=KEYS_DIR,
    )
    repo.initialize()  # generates keys + root/targets/snapshot/timestamp metadata
    os.makedirs(os.path.dirname(ROOT_JSON_DEST), exist_ok=True)
    shutil.copyfile(os.path.join(REPO_DIR, "metadata", "root.json"), ROOT_JSON_DEST)
    print(f"TUF repo initialised. PUBLIC root.json -> {ROOT_JSON_DEST} (commit it).")
    print(f"PRIVATE keys -> {KEYS_DIR} (gitignored). BACK THESE UP. Do NOT lose root key.")


def cut_release():
    version = _app_version()
    print(f"Building Pac-Man {version} ...")
    subprocess.check_call([sys.executable, os.path.join(ROOT, "build.py")])

    zip_base = os.path.join(ROOT, "dist", "pacman")
    shutil.make_archive(zip_base, "zip", DIST_APP)   # dist/pacman.zip (grab-and-go)
    print(f"Zipped -> {zip_base}.zip")

    from tufup.repo import Repository
    repo = Repository(app_name=APP_NAME, repo_dir=REPO_DIR, keys_dir=KEYS_DIR)
    repo.add_bundle(new_bundle_dir=DIST_APP, new_version=version)
    repo.publish_changes(private_key_dirs=[KEYS_DIR])
    print(f"Published {version} to TUF repo {REPO_DIR}.")
    print("Next (operator): deploy ./repo to Firebase /updates, compile installer/pacman.iss,")
    print("publish dist/pacman.zip + pacman-setup.exe. See RELEASE.md.")


def main(argv=None):
    args = build_parser().parse_args(argv)
    if args.init:
        init_repo()
    else:
        cut_release()


if __name__ == "__main__":
    main()
```

(The exact `tufup.repo.Repository` method names/signatures are pinned to `tufup==0.10.0`; the operator verifies the first `--init` + release run live — running it is gated on having keys, so it can't be unit-tested here.)

- [ ] **Step 4: Gitignore the private keys**

Append to `.gitignore`:

```
# TUF private keys (never commit) + build repo output
tuf-keys/
repo/
```

- [ ] **Step 5: Run the smoke test → PASS**, full suite green.

Run: `.venv/Scripts/python.exe -m pytest tests/test_release_smoke.py -v` then `.venv/Scripts/python.exe -m pytest -q`
(`release.py` imports stdlib + argparse at module load; tufup is imported only inside the functions, so the smoke test passes without tufup installed.)

- [ ] **Step 6: Commit**

```bash
git add release.py tests/test_release_smoke.py .gitignore
git commit -m "feat(update): release.py — build, zip, publish tufup bundle"
```

---

### Task 6: Inno Setup script + Firebase `/updates/` route + RELEASE.md

**Files:**
- Create: `installer/pacman.iss`, `RELEASE.md`
- Modify: `firebase.json` (serve `/updates/` if hosting the repo there)
- Test: none (config + docs; operator-compiled/-deployed)

**Interfaces:**
- Produces: the installer script, the operator runbook, and the hosting route.

- [ ] **Step 1: Write `installer/pacman.iss`**

```ini
; Inno Setup script for Pac-Man. Compile with: iscc installer\pacman.iss
; Installs to a USER-WRITABLE dir so the in-place auto-updater needs no admin.
#define AppVersion "1.0.0"   ; keep in sync with settings.APP_VERSION

[Setup]
AppId={{8F2C9A41-7B3D-4E6A-9C12-PACMAN000001}
AppName=Pac-Man
AppVersion={#AppVersion}
AppPublisher=jadrianports
DefaultDirName={localappdata}\Pacman
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputBaseFilename=pacman-setup
SetupIconFile=..\assets\icon.ico
UninstallDisplayIcon={app}\pacman.exe
WizardStyle=modern
Compression=lzma2
SolidCompression=yes

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"

[Files]
Source: "..\dist\pacman\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Pac-Man"; Filename: "{app}\pacman.exe"
Name: "{autodesktop}\Pac-Man"; Filename: "{app}\pacman.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\pacman.exe"; Description: "Launch Pac-Man"; Flags: nowait postinstall skipifsilent
```

- [ ] **Step 2: Add the `/updates/` hosting note to `firebase.json`**

If hosting the TUF repo on the existing site, the operator copies `repo/` into the hosting public dir under `updates/`. Document this in RELEASE.md (Step 3); no `firebase.json` rewrite is needed since static files under `public/updates/` are served directly. (Add a comment block to RELEASE.md rather than changing `firebase.json` ignore rules — the repo files are deploy-time, not committed.)

- [ ] **Step 3: Write `RELEASE.md`** (operator runbook)

```markdown
# Release Runbook (operator)

Prereqs: `pip install tufup==0.10.0`, Inno Setup installed (`iscc` on PATH),
`hmac_secret.local` present, Firebase CLI authenticated.

## One-time setup
1. `python release.py --init` — generates TUF keys in `tuf-keys/` (GITIGNORED) and the
   public `assets/tuf/root.json` (COMMIT this). **Back up `tuf-keys/` securely — losing
   the root key permanently breaks auto-update for installed players.**
2. `git add assets/tuf/root.json && git commit` — the trust anchor must ship in builds.

## Each release
1. Bump `settings.APP_VERSION` (and `#define AppVersion` in `installer/pacman.iss`).
2. `python release.py` — builds the exe, makes `dist/pacman.zip`, and publishes a signed
   bundle into `repo/`.
3. Deploy the TUF repo so clients can reach it at `https://pacman-firebase.web.app/updates/`:
   copy `repo/metadata` and `repo/targets` into the Firebase hosting public dir under
   `updates/`, then `firebase deploy --only hosting`.
4. `iscc installer\pacman.iss` → `installer\Output\pacman-setup.exe`.
5. Publish `dist/pacman.zip` + `pacman-setup.exe` (e.g. a GitHub Release) for first-time
   downloads. Installed players auto-update on next launch.

## Notes
- Install/extract location must be user-writable (the installer uses `%LOCALAPPDATA%\Pacman`).
- Unsigned builds trigger a one-time SmartScreen "More info -> Run anyway".
```

- [ ] **Step 4: Commit**

```bash
git add installer/pacman.iss RELEASE.md
git commit -m "feat(update): Inno Setup installer + operator release runbook"
```

---

## Self-Review

**Spec coverage:** auto-update client (frozen-only, graceful) → Tasks 2-3 ✓; version + dep → Task 1 ✓; root.json bundling → Task 4 ✓; release tooling (build+zip+tufup) → Task 5 ✓; installer + operator runbook + hosting → Task 6 ✓; both distribution channels (zip in Task 5, installer in Task 6) ✓; LocalAppData/writable install → Task 6 `.iss` + Task 2 `_install_dir`/`_cache_dir` ✓; keys gitignored → Task 5 ✓.

**Placeholder scan:** none. The two not-unit-testable pieces (the live tufup repo flow in `release.py`, the Inno/Firebase steps) are explicitly operator-verified with exact commands in `RELEASE.md`, not vague TODOs — same pattern as the existing manual `firebase deploy`.

**Type consistency:** `updater.is_active()`, `updater.check_and_apply(on_status)`, `updater._run_update(on_status)`, `settings.APP_VERSION`, `release.build_parser()`/`release.main()` — consistent across definitions, tests, and `main.py`'s call site.

**Open risk:** `tufup==0.10.0`'s exact `Repository`/`Client` method signatures are pinned but only operator-verified on the first real `--init`/release (no keys/network in CI). If a signature differs, it surfaces on the operator's first run with a clear error, not in players' hands — and `updater.check_and_apply` swallows any client-side mismatch so the shipped game is never bricked by it.
