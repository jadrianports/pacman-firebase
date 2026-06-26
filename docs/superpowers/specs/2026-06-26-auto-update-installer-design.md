# Auto-Update + Installer Design Spec

**Date:** 2026-06-26
**Status:** Approved design — pending spec review before planning
**Author:** brainstormed with James (research-grounded)

## Problem

The game ships as a PyInstaller `--onedir` build (`dist/pacman/pacman.exe`) handed to friends as loose files. There's no clean install, no Start Menu shortcut, no uninstaller, and no way to push fixes/new versions — every update means re-sending the whole folder and asking people to replace it manually.

## Goal

1. **Auto-update on launch** — the game checks for a newer version, and if found, securely downloads and applies it, then restarts, with no manual file-shuffling. (The core feature.)
2. **Two distribution channels from one build**, both auto-updating:
   - **`pacman.zip`** — the zipped `--onedir` folder; unzip anywhere writable and run `pacman.exe`. Grab-and-go.
   - **`pacman-setup.exe`** — an Inno Setup installer for a polished first-install: installs to `%LOCALAPPDATA%\Pacman`, adds Start Menu + desktop shortcuts, registers an uninstaller.
3. Reuse the existing **Firebase Hosting** to serve updates (no new infra/cost).

Both channels run the identical `pacman.exe` with the same tufup updater; the installer is convenience around the same binary, not a separate capability.

## Non-Goals

- Code-signing / SmartScreen bypass (accept the one-time "More info → Run anyway" — EV certs no longer auto-bypass and aren't worth it for a friends-level audience; revisit later).
- macOS/Linux packaging (Windows only for now).
- Delta/patch updates (tufup supports them; start with full-bundle updates, add patches later if downloads feel large).
- In-game "what's new" UI beyond a minimal updating notice.

## Toolset (research-grounded)

- **Updater: `tufup==0.10.0`** — TUF-based, actively maintained, built specifically for PyInstaller `--onedir` self-update. It solves the hard part (you can't overwrite a running `.exe` on Windows) with a wait-for-exit → swap → relaunch helper, and verifies updates via **signed metadata** so a compromised host can't push players malware. Template: `dennisvang/tufup-example`.
- **Installer: Inno Setup** — compiles one `.iss` into `pacman-setup.exe`.
- **Repo host: Firebase Hosting** — the TUF repo is just static files (metadata JSON + target archives); host under a path on the existing site.

## Hard Constraints

1. **Install to `%LOCALAPPDATA%\Pacman`, not Program Files.** Self-update must write its own files; Program Files needs admin every time. LocalAppData install → `PrivilegesRequired=lowest`, no UAC, friction-free silent updates. (Consistent with `paths.py:data_path()`, already user-writable.)
2. **Updater is frozen-only and best-effort.** It runs only when `getattr(sys, "frozen", False)` is true (never in dev). Any failure (offline, host down, verification error) is caught and the game launches normally — exactly the graceful-degrade pattern the leaderboard already uses. The update check must never block or crash startup.
3. **`root.json` is the trust anchor** — bundled into the build via the PyInstaller `.spec`/`--add-data`. The **root private key is kept offline and backed up**; losing it can permanently break the update chain. Key handling is documented in a `RELEASE.md`.
4. **Determinism/tests untouched.** The updater is startup-only, outside the game loop and the deterministic frame-hash/golden path. No change to `game.py` rendering.
5. **No secrets in the repo.** TUF private keys live outside git (gitignored, like `hmac_secret.local`).

## Design

### Versioning
- Add a single source of truth: `settings.APP_VERSION = "1.0.0"` (PEP440). tufup compares the bundled version against the signed `targets` metadata to decide if an update exists.

### In-app client (`updater.py`, new)
- `updater.check_and_apply(on_status)` — frozen-only; constructs a `tufup.client.Client` with:
  - `app_name="Pacman"`, `current_version=settings.APP_VERSION`
  - `metadata_dir` / `target_dir` = cache under `%LOCALAPPDATA%\Pacman\update-cache`
  - `metadata_base_url` / `target_base_url` = the Firebase Hosting update path (e.g. `https://pacman-firebase.web.app/updates/metadata/` and `/updates/targets/`)
  - the bundled trusted `root.json` copied into the metadata cache on first run (bootstrap)
- Flow: `client.check_for_updates()` → if an update is found, call `on_status("Updating…")`, then `client.download_and_apply_update(skip_confirmation=True)` which downloads (TUF-verified), swaps via the Windows helper, and relaunches. Everything wrapped in `try/except Exception` → on any failure, log and return so the game continues.
- Called once in `main.main()` right after `pygame.init()` + window/icon setup, BEFORE the menu loop, behind the frozen guard. A minimal `on_status` renders a centered "Updating…" frame via `theme.pixel_font` so the user sees why the window paused.

### Release tooling (`release.py`, new — dev/operator only)
- One command to cut a release: read `APP_VERSION`, run `build.py` (produces `dist/pacman/`), then:
  - **zip** `dist/pacman/` → `dist/pacman.zip` (the grab-and-go channel),
  - use `tufup.repo.Repository` to `add_bundle(dist/pacman)` + `publish_changes(private_key_dirs=...)`, writing the updated metadata + target archive into a local `repo/` tree (the auto-update channel).
- Operator then: deploys `repo/` to Firebase Hosting under `/updates/`; compiles `installer/pacman.iss` → `pacman-setup.exe`; and publishes `pacman.zip` + `pacman-setup.exe` (e.g. GitHub Releases) for first-time download. Auto-update thereafter is automatic via the TUF repo.
- First-ever run also does the one-time `Repository` init: generate the four role keypairs (`root`, `targets`, `snapshot`, `timestamp`), emit the initial `root.json` to bundle, and print the key-backup reminder.

### Installer (`installer/pacman.iss`, new)
- `[Setup]`: fixed `AppId` GUID (never change), `AppName=Pac-Man`, `AppVersion={#AppVersion}`, `DefaultDirName={localappdata}\Pacman`, `PrivilegesRequired=lowest`, `WizardStyle=modern`, `UninstallDisplayIcon={app}\pacman.exe`, `SetupIconFile=assets\icon.ico`, `OutputBaseFilename=pacman-setup`.
- `[Files]`: `Source: "dist\pacman\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion` (includes the bundled `root.json`).
- `[Icons]`: Start Menu + (opt-in) desktop shortcut to `{app}\pacman.exe`.
- `[Run]`: optional launch-after-install.
- Operator compiles with the Inno Setup compiler (`iscc pacman.iss`) → `pacman-setup.exe`.

### Build changes (`build.py`)
- Add `--add-data` for the trusted `root.json` so the client can bootstrap trust on first install.
- (`--icon=assets/icon.ico` already added.)

### Firebase Hosting
- Serve the TUF repo as static files under `/updates/` (metadata + targets). Either a path in the existing hosting `public` dir or a second hosting target. The web leaderboard page is unaffected.

## What's code vs. operator

- **Code (in this repo, can be built/tested):** `settings.APP_VERSION`, `updater.py` (+ its frozen-guard + graceful-degrade test), `release.py`, `installer/pacman.iss`, `build.py` `--add-data root.json`, `firebase.json` `/updates/` route, `RELEASE.md`.
- **Operator-only (one-time / per-release, documented in `RELEASE.md`):** install Inno Setup; generate + **back up** the TUF keys; run `release.py`; deploy `repo/` to Firebase Hosting; compile the `.iss`; distribute `pacman-setup.exe`. (Same shape as the existing manual `firebase deploy` + `hmac_secret.local` operator steps.)

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| **Root key lost / mismanaged** → update chain bricked | Generate once, store offline + backed up; document rotation in `RELEASE.md`; the bundled `root.json` is committed-as-public (only the private key is secret) |
| Update check hangs/breaks startup | Frozen-only + `try/except` + short timeout; offline/host-down → game launches normally |
| Can't overwrite running `.exe` | Handled by tufup's Windows swap-and-restart helper (the reason we chose tufup over rolling our own) |
| Installing to Program Files breaks self-update | Install to `%LOCALAPPDATA%\Pacman`, `PrivilegesRequired=lowest` |
| SmartScreen warning on unsigned setup | Accepted for now; documented "More info → Run anyway"; revisit signing if audience grows |
| Tampered update from a compromised host | TUF signed metadata — client rejects anything not signed by the trusted roles |
| First version has no `root.json` baked in | Installer ships v1 with `root.json`; tufup only handles updates *after* the initial install |

## Open Questions

None blocking. Exact Firebase Hosting layout for `/updates/` (path vs. second target) and whether to keep a thin `/version` Cloud Function as a secondary signal are minor implementation choices resolved during planning.
