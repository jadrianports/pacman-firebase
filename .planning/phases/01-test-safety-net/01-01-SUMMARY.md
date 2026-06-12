---
phase: 01-test-safety-net
plan: 01
subsystem: testing
tags: [pytest, pygame, firebase-admin, functions-framework, pillow, headless, conftest, venv]

# Dependency graph
requires: []  # foundation plan — depends on nothing
provides:
  - Pinned dev/test/harness dependencies (requirements-dev.txt)
  - Headless pygame bootstrap (harness.headless.init_headless)
  - Repo-first conftest.py — repo-root sys.path, SDL dummy env, --bless flag, firebase-mocked cloud-fn importers
  - tests/artifacts/ gitignored
  - Isolated .venv (Python 3.12.10) with the pinned deps installed
affects: [01-02, 01-03, 01-04, 01-05, 01-06, 01-07]

# Tech tracking
tech-stack:
  added: [pytest==8.4.2, pygame==2.6.1, Pillow==11.0.0, firebase-admin==6.5.0, functions-framework==3.8.1]
  patterns: [set-SDL-dummy-before-import-pygame, conftest-repo-root-syspath, firebase-pre-import-patch-fixtures, flat-but-pinned-requirements-dev]

key-files:
  created: [requirements-dev.txt, harness/__init__.py, harness/headless.py, tests/conftest.py]
  modified: [.gitignore]

key-decisions:
  - "Installed deps into an isolated .venv (user request) rather than the global Python"
  - "Used uv to seed a working pip into the venv because this machine's global ensurepip is corrupt"
  - "No __init__.py added to cloud_functions/ — namespace-package import resolves the dotted path"

patterns-established:
  - "Headless: set SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy BEFORE import pygame (ordering is load-bearing)"
  - "conftest inserts repo root at sys.path[0] so project modules import by name (no src/ layout)"
  - "Cloud-fn tests import the module under patch(initialize_app)/patch(_apps=[])/patch(firestore.client) and drive module._mock_client"

requirements-completed: [HRN-01, TST-03, TST-01]

# Metrics
duration: ~30min
completed: 2026-06-11
---

# Phase 1 · Plan 01-01: Test & Harness Foundation Summary

**Pinned dev deps (human-verified on PyPI), a headless pygame bootstrap, and the repo's first conftest with firebase-mocked cloud-fn importers and a `--bless` flag — all installed into an isolated `.venv`.**

## Performance

- **Duration:** ~30 min
- **Completed:** 2026-06-11
- **Tasks:** 3 (1 human-verify checkpoint + 2 auto)
- **Files created:** 4 · **Files modified:** 1

## Accomplishments
- Human-verified all five pinned dev packages against the PyPI JSON API (canonical projects, real release histories) with `firebase-admin` on major **6** and `functions-framework` on major **3** — matching the deployed `cloud_functions/*/requirements.txt` pins.
- `harness/headless.py::init_headless()` brings up pygame with `SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy` set *before* `import pygame`; returns a real 900×950 surface under the `dummy` driver (matches `settings.py` WIDTH/HEIGHT).
- `tests/conftest.py` (repo-first config): repo-root on `sys.path`, SDL dummy env, `--bless` via `pytest_addoption`, and `submit_module`/`leaderboard_module` fixtures that import each cloud-fn under firebase mocks and expose `module._mock_client`.
- `pytest --collect-only` green (11 existing tests collected) with **no** real Firebase initialization; `--bless` flag registers cleanly.

## Task Commits

1. **Task 1: Human-verify pinned dev dependencies** — checkpoint gate (no commit); all five packages verified on PyPI and authorized by the user.
2. **Task 2: Pin requirements-dev.txt + gitignore test artifacts** — `90b60af` (build)
3. **Task 3: Headless harness + firebase-mocked conftest** — `2397852` (feat)

## Files Created/Modified
- `requirements-dev.txt` — five flat, pinned dev/test deps
- `harness/__init__.py` — package marker
- `harness/headless.py` — `init_headless(size=(900,950))` headless pygame bootstrap
- `tests/conftest.py` — sys.path, SDL env, `--bless`, firebase-mocked cloud-fn fixtures
- `.gitignore` — added `tests/artifacts/` (also carries a pre-existing in-tree correction from a stale Next.js template to a Python `.gitignore`)

## Decisions Made
- **Isolated venv over global install** (user request): deps live in `.venv`, global Python stays clean. All downstream plans must run tests via `.venv\Scripts\python.exe -m pytest`.
- **uv-seeded pip:** see Deviations.
- **No `cloud_functions/__init__.py`:** the dotted-path import works via implicit namespace packages (verified), so the minimal-change rule kept them out.

## Deviations from Plan

### Auto-fixed Issues

**1. [Blocking — Environment] Global `ensurepip` pip is corrupt; seeded a working pip via uv**
- **Found during:** Env setup (before Task 2 install)
- **Issue:** `python -m venv .venv` produced a venv whose bundled pip raised `ImportError: cannot import name '_log' from 'pip._internal.utils' (unknown location)` — the global Python's bundled pip wheels are broken, so every venv it creates inherits a broken pip.
- **Fix:** Recreated the venv with `uv venv --seed --python 3.12 .venv` (uv is on PATH), which seeds a known-good `pip 26.1.2`. Did **not** touch the global Python.
- **Verification:** `.venv\Scripts\python.exe -m pip --version` works; both requirement files installed cleanly.

**2. [Scope — user-directed] Created an isolated virtualenv**
- **Issue:** The plan said "pip install" without specifying an environment; user explicitly asked for an isolated env.
- **Fix:** Created `.venv` (already gitignored) and installed both `requirements.txt` and `requirements-dev.txt` into it.
- **Impact:** No scope creep — same packages, just isolated. Downstream plans/CI unaffected (CI uses a fresh runner with standard pip).

---

**Total deviations:** 2 (1 blocking env fix, 1 user-directed scope). Both necessary; behavior of the deliverables unchanged.

## Issues Encountered
- Corrupt global pip (above) — resolved via uv seed.
- Windows console cp1252 could not print a Unicode checkmark in a verification script — cosmetic; rerun with ASCII output.

## Pre-existing working-tree state (NOT touched by this plan)
The repo had uncommitted/untracked work at phase start that this plan deliberately left alone:
- **Untracked** `tests/test_api_service.py`, `tests/test_local_storage.py`, `tests/__init__.py` (existing tests, never committed).
- **Modified** `cloud_functions/get_leaderboard/main.py`, `cloud_functions/submit_score/main.py` (the working-tree code 01-06's tests target, per STATE.md).
- **Modified** `.claude/settings.local.json`, `.planning/config.json`; **untracked** `docs/superpowers/`.

⚠ **CI implication (for 01-07):** untracked test files are not checked out on a GitHub runner, so they won't run in CI until committed. Recommend committing the existing `tests/` scaffolding (and deciding on the `cloud_functions` edits) before Wave 5.

## Next Phase Readiness
- Wave 2 unblocked: `init_headless()` ready for 01-02's `tick()` extraction; conftest fixtures ready for 01-06's cloud-fn tests (import path already verified); `--bless` ready for 01-04's goldens.
- All downstream test runs must use the venv interpreter.

---
*Phase: 01-test-safety-net*
*Completed: 2026-06-11*
