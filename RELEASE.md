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
