---
phase: 05-client-identity-hardening
plan: 03
subsystem: api
tags: [hmac, pyinstaller, leaderboard, identity, signing, obfuscation, pygame]

# Dependency graph
requires:
  - phase: 05-client-identity-hardening (Plan 01)
    provides: leaderboard_crypto.sign_submission / obfuscate / de_obfuscate (client crypto primitives)
  - phase: 05-client-identity-hardening (Plan 02)
    provides: local_storage.load_identity / save_identity, IDENTITY_STATUS_TAMPERED fail-closed sentinel
  - phase: 04 (server)
    provides: cloud_functions/submit_score verify_signature + REQUIRE_SIGNATURE grace gate
provides:
  - "api_service.submit_score sends the score signature in the locked \"signature\" body field"
  - "main.py loads/migrates identity at startup, signs valid submissions, gates tampered ones"
  - "run_game_over_screen renders a 'Score not saved — identity error' notice on tamper"
  - "build.py bakes the gitignored shared HMAC secret into the bundle non-literally"
  - "repo ships hmac_secret.example placeholder; real secret gitignored, never committed"
affects: [phase-04 ops follow-up (REQUIRE_SIGNATURE flip), future leaderboard/build phases]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Build-baked obfuscated secret (generated _baked_secret.py) de-obfuscated at runtime — no literal in committed source"
    - "Gitignored-local-secret + committed-example file convention (hmac_secret.local / hmac_secret.example)"
    - "Frozen-vs-dev secret resolution mirroring paths.py frozen branch"

key-files:
  created:
    - hmac_secret.example
    - tests/check_main_wiring.py
    - tests/check_build_secret.py
  modified:
    - api_service.py
    - main.py
    - menu.py
    - build.py
    - settings.py
    - .gitignore
    - tests/test_api_service.py

key-decisions:
  - "Bake the secret as a generated gitignored _baked_secret.py carrying base64-over-XOR obfuscated bytes, bundled via --add-data + hidden-import; runtime de_obfuscate is the exact counterpart"
  - "main._load_hmac_secret resolves frozen (baked module) -> dev hmac_secret.local -> LEADERBOARD_HMAC_SECRET env, returning None so dev runs without a secret still play"
  - "Added HMAC_SECRET_FILE_NAME to settings.py during Task 2 (Rule 3 blocking) since main.py imports it; Task 3's 'add if not already present' was satisfied early"
  - "build.py fails loudly (SystemExit) when hmac_secret.local is missing — no silent placeholder ship"

patterns-established:
  - "Reversible obfuscation (Plan 01 obfuscate/de_obfuscate) reused for the build secret embedding, not just the identity blob"
  - "Throwaway quote-free check scripts (check_main_wiring.py / check_build_secret.py) for ast-parse + token assertions that keep shell verify commands simple"

requirements-completed: [IDENT-01, IDENT-03]

# Metrics
duration: ~22min
completed: 2026-06-19
---

# Phase 5 Plan 03: Wire signed submissions, tamper gate, and build secret bake-in Summary

**Closed the end-to-end loop: valid runs are HMAC-signed and POSTed in the `"signature"` field, tampered identities are blocked with a game-over notice, and the build bakes the gitignored shared secret in non-literally.**

## Performance

- **Duration:** ~22 min
- **Started:** 2026-06-19T11:59:xxZ
- **Completed:** 2026-06-19T12:21:48Z
- **Tasks:** 3
- **Files modified:** 7 (3 new)

## Accomplishments
- `api_service.submit_score(..., signature=None)` adds the locked `"signature"` field to the POST body; `score` stays an int so the server can recompute and accept the signature (D-07).
- `main.py` reworked: `_load_hmac_secret()` resolves the secret (frozen baked module / dev local file / env); startup `load_identity(secret)` runs before the initials prompt so migrated identities are not re-prompted (D-04); valid runs sign via `sign_submission` and submit the signature; `IDENTITY_STATUS_TAMPERED` skips submit and shows the notice (D-05/D-06).
- `run_game_over_screen(..., identity_error=False)` renders a gray "Score not saved — identity error" line, mirroring the existing graceful-degrade tone; the game stays fully playable (D-06).
- `build.py` reads the gitignored `hmac_secret.local`, obfuscates it (base64-over-XOR), emits a gitignored `_baked_secret.py`, and bundles it via `--add-data` + `--hidden-import`; it fails loudly when the secret is missing (D-09/D-10).
- Repo ships only the `hmac_secret.example` placeholder; `hmac_secret.local` and `_baked_secret.py` are gitignored; no real secret literal lives in any committed source.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): failing tests for submit_score signature field** - `d8f00d8` (test)
2. **Task 1 (GREEN): signature field + game-over notice** - `87a4102` (feat)
3. **Task 2: main.py wiring (load/migrate, signed submit, tamper gate, notice)** - `beb077a` (feat)
4. **Task 3: build.py secret bake-in + gitignored secret + placeholder** - `9524867` (feat)

_Task 1 followed the TDD RED→GREEN cycle (no refactor commit needed)._

## Files Created/Modified
- `api_service.py` - `submit_score` accepts `signature=None` and sends it in the body (`score` stays int; graceful-degrade + stdlib `urllib` preserved).
- `main.py` - `_load_hmac_secret()` helper, startup `load_identity` wiring, signed submission, `IDENTITY_STATUS_TAMPERED` gate, `identity_error` notice flag.
- `menu.py` - `run_game_over_screen(..., identity_error=False)` + the gray "Score not saved — identity error" render branch.
- `build.py` - reads `hmac_secret.local`, obfuscates + emits `_baked_secret.py`, bundles it, fails loudly if the secret is absent.
- `settings.py` - `HMAC_SECRET_FILE_NAME = "hmac_secret.local"`.
- `.gitignore` - `hmac_secret.local` and `_baked_secret.py` entries.
- `hmac_secret.example` - committed placeholder (`REPLACE_WITH_REAL_SECRET`).
- `tests/test_api_service.py` - call sites pass `signature`; new tests assert the `"signature"` body field (int `score`) and the `None` default.
- `tests/check_main_wiring.py`, `tests/check_build_secret.py` - throwaway ast-parse + token assertion scripts backing the plan's verify commands.

## Decisions Made
- Embedded the secret as a generated, gitignored `_baked_secret.py` (obfuscated string) bundled via `--add-data` + `--hidden-import`, reusing the Plan 01 `obfuscate`/`de_obfuscate` scheme as the reversible counterpart. Verified the build→runtime round-trip programmatically.
- `_load_hmac_secret()` returns `None` when no secret is available so dev runs without the secret still play (submissions just won't verify) — matches the graceful-degrade ethos.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Added `HMAC_SECRET_FILE_NAME` to settings.py during Task 2**
- **Found during:** Task 2 (main.py wiring)
- **Issue:** `main.py` imports `HMAC_SECRET_FILE_NAME` from `settings`, but the constant was scheduled for creation in Task 3 — importing `settings`/`main` would break before Task 3 ran.
- **Fix:** Added the constant in Task 2. Task 3's action ("add ... if not already present") was satisfied early; Task 3 verified it remained present.
- **Files modified:** settings.py
- **Verification:** `import settings` smoke test prints the value; `check_build_secret.py` and the full suite pass.
- **Committed in:** beb077a (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Necessary to keep the import graph valid across the task ordering. No scope creep — the constant was always part of this plan; only its commit moved one task earlier.

## Issues Encountered
- The worktree has no local `.venv` (gitignored, lives in the main repo). Resolved by invoking the main repo's `.venv/Scripts/python.exe` against the worktree source — tests and check scripts run correctly against the worktree's code.

## User Setup Required
**External service requires manual configuration.** Before running `build.py`, the operator must place the real `leaderboard-hmac-secret` value (identical to the deployed Cloud Run secret) into a gitignored `hmac_secret.local` at the repo root, created from `hmac_secret.example`. The repo ships only the placeholder. Flipping server-side `REQUIRE_SIGNATURE=true` is a post-ship ops follow-up (Phase 4 D-02), not part of this plan.

## Next Phase Readiness
- End-to-end signed submission loop is live in the app; the shipped exe carries the secret safely once `hmac_secret.local` is supplied at build time.
- Server-side `REQUIRE_SIGNATURE` flip remains an operator ops step after the signed client ships and friends update — recorded as carry-forward, not a build task.

## Threat Surface
- T-05-09 (sign valid submissions): mitigated — `sign_submission` over the locked canonical message, signature sent in `"signature"`.
- T-05-10 (tamper gate): mitigated — TAMPERED identity skips submit + shows notice; game stays playable.
- T-05-11 (secret extraction): accepted to ceiling — baked non-literally (base64-over-XOR), not surfaced by strings/grep; reverse-engineering residual is the inherited Phase 4 ceiling.
- T-05-12 (secret in git): mitigated — `hmac_secret.local`/`_baked_secret.py` gitignored, build fails loudly if missing; `git check-ignore` confirmed.

No new threat surface beyond the plan's `<threat_model>`.

## Self-Check: PASSED
- api_service.py, main.py, menu.py, build.py, settings.py, hmac_secret.example present (verified).
- tests/check_main_wiring.py, tests/check_build_secret.py present (verified).
- Commits d8f00d8, 87a4102, beb077a, 9524867 exist in git log (verified).
- Full suite: 117 passed, 9 skipped (golden net intact). Wiring + build check scripts pass. `git check-ignore hmac_secret.local` exits 0. No real secret literal in committed source.

---
*Phase: 05-client-identity-hardening*
*Completed: 2026-06-19*
