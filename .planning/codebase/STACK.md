---
type: codebase-map
focus: tech
doc: STACK
generated: 2026-06-01
last_mapped_commit: 5e8d4b1773c03b4d3953200a764d658a431911de
---

# Technology Stack

Pac-Man clone: a desktop PyGame client with a serverless (Google Cloud Functions + Firestore) online leaderboard backend. The game is fully playable offline; the leaderboard degrades gracefully when the network is unavailable.

## Languages & Runtime

| Area | Language | Runtime | Notes |
|------|----------|---------|-------|
| Game client | Python 3 (CPython) | Desktop (Windows-first) | No version pin; syntax floor is **3.6+** (f-strings, numeric underscores like `500_000`). No 3.10+ features (`match`) used. |
| Backend | Python 3 | Google Cloud Functions (2nd gen / Cloud Run) | Region `asia-southeast1`. Runtime selected at deploy time (not pinned in repo). |
| Build | Python 3 | PyInstaller | Produces a Windows `.exe` bundle. |

There is no compiled language, no JS/TS, and no web frontend — the "frontend" is the PyGame window.

## Client Dependencies

Declared in `requirements.txt` (repo root):

```text
pygame
pyinstaller
```

- **pygame** — windowing, rendering (`pygame.draw`, `blit`, `transform`), input events, audio (`pygame.mixer.Sound`/`Channel`), clock/FPS. Core of the entire client.
- **pyinstaller** — packaging only (build-time, not a runtime dependency).
- **Standard library only** for everything else: `json`, `urllib.request` (HTTP — see `api_service.py`), `uuid` (machine id), `os`, `sys`, `copy`, `math`, `re`.

> Versions are **unpinned** in the client `requirements.txt`. No `pyproject.toml`, `setup.py`, `Pipfile`, or lockfile exists.

## Backend Dependencies

Each Cloud Function has its own `requirements.txt`, both identical:

`cloud_functions/submit_score/requirements.txt` and `cloud_functions/get_leaderboard/requirements.txt`:

```text
functions-framework==3.*
firebase-admin==6.*
```

- **functions-framework** (`3.*`) — Google's HTTP function runtime adapter (`@functions_framework.http`).
- **firebase-admin** (`6.*`) — Firestore Admin SDK (`firestore.client()`, transactions, server timestamps).

> Backend deps pin **major versions** (`3.*`, `6.*`) — looser than exact pins but stricter than the client.

## Build & Packaging

Two overlapping PyInstaller paths exist:

1. **`build.py`** (the documented path — `python build.py`):
   ```python
   PyInstaller.__main__.run([
       "main.py", "--name=pacman", "--onedir", "--windowed",
       "--add-data=assets;assets", "--add-data=freesansbold.ttf;.",
   ])
   ```
   Output: `dist/pacman/pacman.exe`.

2. **`pacman.spec`** — a generated PyInstaller spec describing the same bundle (assets + `freesansbold.ttf`, `console=False`, `upx=True`). `*.spec` is git-ignored.

The `--add-data` / `datas` entries use the Windows `;` path separator, confirming a Windows build target.

## Configuration

- **`settings.py`** — single source for client constants: window dimensions (`WIDTH=900`, `HEIGHT=950`), `FPS=60`, speeds, start positions/directions for player and four ghosts, box-exit delays, menu colors, font sizes, and the two backend URLs:
  ```python
  API_SUBMIT_SCORE_URL = "https://pacman-991339031546.asia-southeast1.run.app"
  API_LEADERBOARD_URL  = "https://get-leaderboard-991339031546.asia-southeast1.run.app"
  ```
- **No environment variables** are read anywhere. All configuration is hardcoded in `settings.py`.
- **`firebase-key.json`** — a Google service-account key present locally for backend/dev use. It is git-ignored (`.gitignore:19`) and has never been committed. The client never reads it (the client only talks to the public Cloud Function URLs).

## Asset & Data Path Handling

`paths.py` abstracts dev-vs-frozen (PyInstaller) paths:
- `resource_path(rel)` — bundled, read-only assets. Uses `sys._MEIPASS` when frozen.
- `data_path(rel)` — writable user-data files next to the exe (or repo root in dev).

Bundled assets: `freesansbold.ttf` (font), `assets/audio/*.wav`, `assets/ghosts/*.png`, `assets/pacman/*.png`.

## Dev Environment

- `.venv/` — local virtualenv (git-ignored).
- `.vscode/settings.json` — `"python-envs.defaultEnvManager": "ms-python.python:system"`.
- `.idea/` present (JetBrains) but git-ignored.
- `pytest` is the test runner (see `TESTING.md`), but `pytest` is **not** listed in any `requirements.txt` — it must be installed separately.

## Quick Reference — How to Run

```bash
python main.py                       # run the game
pytest                               # run tests (pytest must be installed)
python build.py                      # build dist/pacman/pacman.exe (needs pyinstaller)
```
