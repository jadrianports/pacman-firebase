---
phase: 01-test-safety-net
plan: 07
subsystem: infra
tags: [github-actions, ci, pytest, headless, branch-protection]

# Dependency graph
requires:
  - phase: 01-02..01-06
    provides: the full headless pytest suite (goldens, ghost micro, determinism, cloud-fn) that CI runs
provides:
  - .github/workflows/ci.yml — headless pytest on ubuntu-latest / py3.12, push-any-branch + PR-to-main
  - Branch protection on main requiring the 'test' status check (the merge-gate)
  - A conftest bootstrap that makes the suite runnable on any clean checkout (font asset)
affects: [phase-02, phase-03]

# Tech tracking
tech-stack:
  added: [GitHub Actions CI]
  patterns: [headless-pytest-ci, required-status-check-merge-gate, test-env-asset-bootstrap]

key-files:
  created: [.github/workflows/ci.yml]
  modified: [tests/conftest.py]

key-decisions:
  - "CI runs on push to any branch AND PRs to main (D-09); ubuntu-latest / py3.12 / SDL dummy (D-08)"
  - "Branch protection: require 'test' check, strict=true, enforce_admins=false (owner can override)"
  - "freesansbold.ttf gap fixed in conftest (test env), NOT game.py (Cardinal Rule)"

patterns-established:
  - "CI: actions pinned to majors (checkout@v4, setup-python@v5); pip install requirements.txt + requirements-dev.txt; pytest -q"
  - "conftest restores pygame's bundled freesansbold.ttf when missing so a clean checkout can construct Game()"

requirements-completed: [TST-04]

# Metrics
duration: ~30min
completed: 2026-06-11
---

# Phase 1 · Plan 01-07: Continuous Safety Net (CI) Summary

**A pinned headless-pytest GitHub Actions workflow that runs the full 61-test suite green on ubuntu-latest, with branch protection on `main` requiring the `test` check — the safety net is now continuously enforced and merge-gating.**

## Performance

- **Duration:** ~30 min (incl. a real CI-failure diagnose/fix cycle)
- **Completed:** 2026-06-11
- **Tasks:** 2 (1 auto + 1 blocking-human checkpoint)

## Accomplishments
- `.github/workflows/ci.yml`: triggers on push to any branch + PR to `main` (D-09); single `test` job on `ubuntu-latest` with `SDL_VIDEODRIVER/SDL_AUDIODRIVER=dummy`, `python-version: '3.12'` (D-08); installs `requirements.txt` + `requirements-dev.txt`; runs `pytest -q`. Action majors pinned.
- **CI verified green on a real push** — run `27331943685`, 61 tests, 1m14s on ubuntu-latest.
- **Branch protection on `main`** set via `gh api`: requires the `test` status check (strict), `enforce_admins=false`, force-push/deletion disabled. A red CI run now blocks merges to `main`.

## Task Commits
1. **Task 1: Author the headless CI workflow** — `6768aa0` (ci); full local suite green headless before relying on CI.
2. **CI clean-checkout fix (see Deviations)** — `a395d52` (fix)
3. **Task 2: Verify CI green + enable branch protection** — human checkpoint; CI run `27331943685` green; branch protection applied to `main` (attested + executed via gh api with user authorization).

## Files Created/Modified
- `.github/workflows/ci.yml` — the repo's first CI workflow
- `tests/conftest.py` — added `_ensure_default_font()` clean-checkout bootstrap

## Deviations from Plan

### 1. [Blocking — CI environment] First CI run failed: `freesansbold.ttf` missing
- **Found during:** Task 2 (first push → CI red)
- **Issue:** `game.py:22` loads `resource_path('freesansbold.ttf')`, but that font is **gitignored** (`.gitignore`), so a clean CI checkout lacked it and every `Game()`-constructing test raised `FileNotFoundError` before any logic ran. (Local runs passed only because the file sits in the dev working dir.)
- **Fix:** `tests/conftest.py` now copies pygame's **byte-identical** bundled `freesansbold.ttf` into the `resource_path` target when missing — test-environment setup only, **no game.py / game-behavior change** (Cardinal Rule honored). Proven by simulating a clean checkout locally (font removed → suite restored it → 61 passed). Committed as `a395d52`; second CI run green.
- **Verification:** CI run `27331943685` = success.

### 2. [Orchestrator prep] CI-coherence commits (outside 01-07's files_modified)
Before authoring CI, two prerequisite commits made the *committed* tree match what the suite asserts (user-approved):
- `d62670e` — tracked the pre-existing untracked tests (`test_api_service.py`, `test_local_storage.py`, `tests/__init__.py`); CI checks out only tracked files.
- `38417e5` — committed the working-tree cloud-fn improvements (MAX_SCORE cap + transactional best-score upsert) that 01-06's TST-03 tests assert against.

## Issues Encountered
- CI red on first push (font) — diagnosed from the Actions log and fixed (above).

## Known follow-ups (not Phase 1 scope)
- **Game-from-fresh-clone:** the same gitignored `freesansbold.ttf` means `python main.py` would crash on a clean clone. The proper fix (commit the asset, or have `game.py` use pygame's default font) is a **game change → Phase 3 hygiene**, deliberately not done here.
- **Actions Node 20 deprecation:** GitHub flagged `checkout@v4`/`setup-python@v5` (Node 20, deprecating ~2026-06-16). CI still passes; a version bump is a future nicety.

## Branch / merge note
All Phase 1 work lives on `gsd/phase-01-test-safety-net` (per user request to test before integrating). `solid-foundation` was rewound to pre-execution; merge the branch into `solid-foundation` when satisfied.

## Next Phase Readiness
- The full safety net is continuous and merge-gating. Phase 2 (byte-identical refactor) can now refactor against the frozen goldens + micro tests with CI catching any regression on every push/PR.

---
*Phase: 01-test-safety-net*
*Completed: 2026-06-11*
