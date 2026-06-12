---
phase: 03-box-bug-fix-hygiene
plan: 01
subsystem: infra
tags: [hygiene, requirements, gitignore, pyinstaller, pygame, assets, docs]

# Dependency graph
requires:
  - phase: 02-byte-identical-refactor
    provides: "Centralized geometry + unified ghost mover proven byte-identical; golden traces + frame-hash manifest as the regression authority this plan keeps green"
provides:
  - "Pinned client dependencies (pygame==2.6.1, pyinstaller==6.20.0) for reproducible runs + .exe builds"
  - "Untracked .claude/settings.local.json + reconciled .gitignore (single /.claude, no CLAUDE.md line); CLAUDE.md now tracked"
  - "CLAUDE.md box-exit prose reconciled to constants (~0.5 s / ~1 s); menu.py docstring drops dead 'Change Initials'"
  - "Dead byte-duplicate asset folders (assets/ghost_images/, assets/player_images/) deleted; live assets/ghosts/ + assets/pacman/ intact"
  - "Human-verified PyInstaller .exe rebuild + smoke-run (D-14) on the cleaned asset tree"
affects: [03-02-box-fix, future-exe-builds, ci]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hygiene-first sequencing at commit granularity (D-09): four ordered, atomic, independently-green commits, each keeping golden traces byte-identical before any behavior change"
    - "Doc reconciliation reconciles prose TO the constants — never edit the constants to match drifted docs"

key-files:
  created:
    - .planning/phases/03-box-bug-fix-hygiene/03-01-SUMMARY.md
  modified:
    - requirements.txt
    - .gitignore
    - CLAUDE.md
    - menu.py
  deleted:
    - assets/ghost_images/ (5 files)
    - assets/player_images/ (5 files)

key-decisions:
  - "Pinned BOTH pygame and pyinstaller (HYG-01) so the .exe bundle stays reproducible; backend cloud_functions/* pins left untouched (client scope only)"
  - "Reconciled CLAUDE.md box-exit prose to ~0.5 s / ~1 s (60fps frame->seconds) by editing the DOC, not settings.py constants — editing constants would have been an unsanctioned behavior change that moves golden traces"
  - "Deleted *_images folders only after grep confirmed the sole references live in design/.planning docs (no live-code path); the real distributable is dist/pacman/pacman.exe, NOT build/pacman/pacman.exe"

patterns-established:
  - "Pattern: behavior-neutral hygiene lands as N atomic commits, each verified green (golden traces byte-identical) before the next"
  - "Pattern: PyInstaller asset hygiene verified by a human .exe rebuild + smoke-run (D-14) — the one check headless CI structurally cannot perform"

requirements-completed: [HYG-01, HYG-02, HYG-03, HYG-04]

# Metrics
duration: ~30min
completed: 2026-06-12
---

# Phase 3 Plan 01: Box-Bug-Fix Hygiene Summary

**Four behavior-neutral hygiene items (deps pin, untrack+gitignore reconcile, doc-drift fix, dead-asset delete) landed as four ordered atomic commits — golden traces byte-identical after each, full suite green, and a human-verified PyInstaller .exe rebuild on the cleaned asset tree.**

## Performance

- **Duration:** ~30 min (incl. blocking human .exe gate)
- **Completed:** 2026-06-12
- **Tasks:** 4 of 4
- **Files modified:** 4 modified, 10 deleted (2 dead folders), 1 SUMMARY created

## Accomplishments

- **HYG-01** — Pinned client deps in `requirements.txt`: `pygame==2.6.1`, `pyinstaller==6.20.0`, sourced from the CI-green env. Backend `cloud_functions/*` pins untouched (client scope only).
- **HYG-02** — `git rm --cached .claude/settings.local.json` (untracked, still on disk); `.gitignore` reconciled to a single `/.claude` line with the `CLAUDE.md` ignore line removed; `CLAUDE.md` now tracked.
- **HYG-03** — Reconciled `CLAUDE.md` "Ghost Box Exit" prose to match constants (Pinky ~0.5 s, Clyde ~1 s at 60 fps); dropped the dead `'Change Initials'` reference from `menu.py:run_main_menu` docstring. `settings.py` constants (`BOX_EXIT_DELAY_PINKY = 30`, `CLYDE = 60`) left UNCHANGED.
- **HYG-04** — Deleted dead byte-duplicate folders `assets/ghost_images/` + `assets/player_images/` (10 files) after grep confirmed no live-code reference; live `assets/ghosts/` + `assets/pacman/` intact.
- **D-14 human gate** — Human ran `.venv\Scripts\python.exe build.py`, producing a complete `dist/pacman/` bundle (python312.dll, VCRUNTIME140.dll, full api-ms-win-crt set, SDL2*.dll, and bundled assets = audio/ghosts/pacman only — no dead *_images). `dist/pacman/pacman.exe` launched and rendered ghost + Pac-Man sprites correctly.

## Task Commits

Each task was committed atomically:

1. **Task 1: Pin client deps (HYG-01)** — `3f827db` (chore)
2. **Task 2: Untrack settings.local.json + reconcile .gitignore + track CLAUDE.md (HYG-02)** — `948fe4d` (chore)
3. **Task 3: Box-exit doc timing + drop dead 'Change Initials' docstring (HYG-03)** — `5e87bf0` (docs)
4. **Task 4: Delete dead duplicate asset folders (HYG-04)** — `70df7d1` (chore) + human-verified .exe rebuild (D-14)

**Plan metadata:** committed separately with this SUMMARY + tracking updates.

## Files Created/Modified

- `requirements.txt` — pinned `pygame==2.6.1`, `pyinstaller==6.20.0` (client deps only)
- `.gitignore` — single `/.claude` line; `CLAUDE.md` ignore line removed
- `CLAUDE.md` — now tracked; box-exit prose reads ~0.5 s / ~1 s
- `menu.py` — `run_main_menu` docstring no longer references 'Change Initials'
- `assets/ghost_images/` (deleted, 5 files) — dead byte-duplicate of `assets/ghosts/`
- `assets/player_images/` (deleted, 5 files) — dead byte-duplicate of `assets/pacman/`

## Verification Evidence

- **Golden traces byte-identical after every hygiene commit:** `tests/test_golden_traces.py` stayed byte-identical after each of Tasks 1-3 (15 passed) — zero behavior change, per D-09 CI-green-at-every-step.
- **Full suite green after Task 4 deletion:** `pytest` reported **61 passed, 9 skipped, 0 failed** after the dead-folder deletion (deleted folders unreferenced by any code path).
- **D-14 human .exe smoke-run: APPROVED.** `build.py` produced a complete `dist/pacman/` bundle; `dist/pacman/pacman.exe` launched and rendered ghost + Pac-Man sprites correctly from bundled `assets/ghosts/` + `assets/pacman/` — proving the deleted `*_images` folders were truly dead and the pyinstaller pin builds a working bundle.

## Decisions Made

- Pinned both pygame and pyinstaller (not just pygame) so the .exe bundle stays reproducible — backend cloud_functions pins deliberately untouched.
- Doc-drift fix edits the PROSE in CLAUDE.md to match `settings.py`, never the constants — editing the delay constants would have been an unsanctioned behavior change that moves golden traces.

## Deviations from Plan

None — plan executed exactly as written. All four tasks landed on their suggested commit messages; golden traces byte-identical after each; constants untouched.

## Notes

- **dist vs build .exe (for the next .exe builder):** During the D-14 gate the human initially launched the stale intermediate `build/pacman/pacman.exe` (PyInstaller's working dir), which caused brief confusion. The real distributable is **`dist/pacman/pacman.exe`** — always smoke-run the `dist/` exe, not the `build/` one.

## Issues Encountered

- Brief D-14 confusion launching the stale `build/pacman/pacman.exe` instead of the distributable `dist/pacman/pacman.exe`; resolved once the human ran the `dist/` exe, which launched and rendered sprites correctly. (Captured above as a note for future .exe builders.)

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Repo hygiene is clean: deps pinned, local settings untracked, docs reconciled, dead assets gone. The Phase-3 PR now reads "everything green and unchanged" ahead of the isolated box fix.
- **03-02 (Wave 2) is next** — BUG-01 (unify ghost-box bounds), the ONE sanctioned behavior change, provably isolated to the box region. This plan touched no gameplay logic, geometry constants, or golden traces, leaving Plan 02's box fix cleanly isolated.

## Self-Check: PASSED

- `requirements.txt` pins present: `pygame==2.6.1`, `pyinstaller==6.20.0` — FOUND
- `assets/ghost_images/` absent, `assets/player_images/` absent — FOUND (deleted)
- `.claude/settings.local.json` untracked (`git ls-files` empty) — FOUND
- Commit `3f827db` (HYG-01) — FOUND
- Commit `948fe4d` (HYG-02) — FOUND
- Commit `5e87bf0` (HYG-03) — FOUND
- Commit `70df7d1` (HYG-04) — FOUND
- `.planning/phases/03-box-bug-fix-hygiene/03-01-SUMMARY.md` — FOUND (this file)

---
*Phase: 03-box-bug-fix-hygiene*
*Completed: 2026-06-12*
