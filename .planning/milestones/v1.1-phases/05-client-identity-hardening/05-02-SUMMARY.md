---
phase: 05-client-identity-hardening
plan: 02
subsystem: storage
tags: [identity, hmac, obfuscation, migration, local-storage, fail-closed, localappdata]

# Dependency graph
requires:
  - phase: 05-client-identity-hardening
    provides: "Plan 01 leaderboard_crypto.py — obfuscate/de_obfuscate + sign_identity_blob/verify_identity_blob"
provides:
  - "paths.user_data_dir()/user_data_path() — %LOCALAPPDATA%\\PacMan\\ resolver (Windows) with ~/.pacman dev fallback"
  - "local_storage.load_identity(secret, ...) — single entry point returning {machine_id, initials, status}"
  - "Consolidated obfuscated+HMAC-signed identity blob with one fail-closed TAMPERED path (D-05)"
  - "Migrate-then-remove first-launch migration with a verify-before-delete safety gate (D-04)"
  - "save_initials(initials, secret, *, blob_path=...) — re-signs/rewrites the blob"
  - "settings.IDENTITY_DIR_NAME / IDENTITY_FILE_NAME constants"
affects: [05-03-submission-signing, main, api_service]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Single signed blob (D-02): {machine_id, initials} obfuscated under one HMAC, never plaintext on disk"
    - "Fail-closed tamper sentinel (D-05): present-but-invalid (corrupt OR HMAC mismatch) -> ONE TAMPERED path, never auto-regenerate"
    - "Migrate-then-remove (D-04): write new blob -> verify read-back equal -> only then delete legacy files"
    - "Per-user storage resolver reusing the frozen-vs-dev idiom; folder name from settings, never hardcoded in paths"

key-files:
  created: []
  modified:
    - paths.py
    - settings.py
    - local_storage.py
    - tests/test_local_storage.py

key-decisions:
  - "On-disk format is a JSON envelope {sig, blob} where blob = obfuscate(json({machine_id, initials})); raw initials/machine_id never appear in the file"
  - "load_identity treats a present blob (OK or TAMPERED) as authoritative — it never migrates over or regenerates on top of an existing file (D-05)"
  - "Migration verify-before-delete gate asserts read-back equals what was written; on failure legacy files survive and migrated values are still returned (never lose identity)"
  - "Legacy get_machine_id/get_initials removed; main.py rewire is Plan 03's responsibility (no test imports main.py, full suite stays green)"

patterns-established:
  - "Internal _STATUS_MISSING sentinel distinguishes genuine-missing (mint fresh) from present-but-invalid (TAMPERED) inside one reader"
  - "Legacy initials validated against ^[A-Z]{3}$ on migration; invalid/partial -> None (not-yet-set, prompt later)"

requirements-completed: [IDENT-01, IDENT-02, IDENT-03]

# Metrics
duration: ~10min
completed: 2026-06-19
---

# Phase 5 Plan 02: Identity Storage Rework Summary

**Client identity moved out of the game folder into `%LOCALAPPDATA%\PacMan\` as a single obfuscated + HMAC-signed blob, with seamless migrate-then-remove of the two legacy plaintext files and a fail-closed TAMPERED sentinel that blocks submit without ever silently regenerating.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-06-19
- **Completed:** 2026-06-19
- **Tasks:** 3 (all TDD)
- **Files modified:** 4 (0 created, 4 modified)

## Accomplishments
- **Per-user storage (IDENT-01, SC-1):** `paths.user_data_dir()` targets `%LOCALAPPDATA%\PacMan\` on Windows (folder name from `settings.IDENTITY_DIR_NAME`), auto-creates the dir, and falls back to `~/.pacman` on a non-Windows dev host. `data_path`/`resource_path` left byte-for-byte intact so migration can still find the legacy next-to-exe files.
- **Single obfuscated+signed blob (IDENT-02, SC-2, D-02):** identity is `{machine_id, initials}` → JSON → `obfuscate(...)` → stored in a `{sig, blob}` envelope signed via `sign_identity_blob`. The on-disk file contains neither `b"BOB"` nor `b"machine_id"` (not greppable/hand-editable).
- **Fail-closed tamper detection (IDENT-03, SC-3, D-05):** a present-but-invalid blob — a flipped byte (HMAC mismatch) OR un-decodable garbage OR wrong secret — returns `IDENTITY_STATUS_TAMPERED` via ONE code path, returns no machine_id, and never regenerates. A genuinely missing file mints a fresh uuid4 (D-04).
- **Migrate-then-remove (D-04):** `load_identity` reads legacy `machine_id.txt` + validated `player_data.json` initials, writes the new signed blob, VERIFIES it reads back equal, and only then deletes both legacy files. A forced read-back failure leaves legacy files in place and still returns the migrated values (never lose identity).
- **Reworked test suite:** 13 tests covering round-trip, not-human-readable, save_initials machine_id stability, tamper, garbage, wrong-secret, missing-mint, tampered-no-regenerate, full migration, verify-before-delete ordering, and partial/invalid-legacy-initials. Full project suite green: **115 passed, 9 skipped, 0 failed**.

## Task Commits

Each task committed atomically:

1. **Task 1: per-user resolver + path constants** — `22e132e` (feat)
2. **Task 2: consolidated obfuscated+signed blob + tamper sentinel** — `8947ea8` (feat)
3. **Task 3: migrate-then-remove + load_identity + reworked tests** — `cf16671` (feat)

## TDD Gate Compliance
All three tasks are `tdd="true"`. The RED gate was exercised per task by running the task's verification against the not-yet-existing symbols (Task 1: `ImportError` on `user_data_dir`; Task 2: `ImportError` on `_write_identity_blob`; Task 3: the new test file fails before `load_identity` exists), confirmed RED, then implemented to GREEN.

**Note (gate-commit shape):** Tasks 1 and 2 are verified by inline `python -c` assertions (the plan's `<verify>` for those tasks is an assertion, not a test file), so there is no separate test-only RED commit for them — the RED→GREEN cycle was run in-session and each landed as a single `feat` commit. Task 3 introduced the reworked `tests/test_local_storage.py`; per the plan it pairs the test rewrite with the `load_identity` implementation, committed together as one `feat` commit (`cf16671`). The dedicated client-crypto RED/GREEN test commits already exist from Plan 01 (`2f53338`/`af1166b`). No behavior shipped without a passing test asserting it.

## Files Created/Modified
- `paths.py` (MODIFIED) — added `user_data_dir()` / `user_data_path()` (`%LOCALAPPDATA%\PacMan\`, dev fallback, auto-create); imports `IDENTITY_DIR_NAME` from settings; `data_path`/`resource_path` unchanged.
- `settings.py` (MODIFIED) — added `IDENTITY_DIR_NAME = "PacMan"` and `IDENTITY_FILE_NAME = "identity.dat"` near the API URL constants; no HMAC secret literal (D-09).
- `local_storage.py` (MODIFIED, reworked) — single-blob model: `IDENTITY_STATUS_OK`/`IDENTITY_STATUS_TAMPERED`, `_write_identity_blob`/`_read_identity_blob`, `load_identity`, `save_initials(initials, secret, ...)`, legacy-reader helpers, `_safe_remove`. Imports `obfuscate`/`de_obfuscate`/`sign_identity_blob`/`verify_identity_blob` from `leaderboard_crypto` and `user_data_path`/`data_path`. The legacy `get_machine_id`/`get_initials`/`save_initials(initials, path)` are removed.
- `tests/test_local_storage.py` (MODIFIED, rewritten) — 13 blob-model tests replacing the obsolete plaintext tests.

## Decisions Made
- **JSON envelope `{sig, blob}`** for on-disk framing — stdlib-only, keeps the identity values strictly inside the obfuscated payload.
- **Present blob is authoritative** — `load_identity` never migrates over or regenerates on top of an existing file; a TAMPERED present blob short-circuits before the migration/mint branches (D-05).
- **Verify-before-delete** uses a strict equality gate (`read-back == written`); failure preserves legacy files and still returns migrated values.

## Deviations from Plan
None — plan executed as written. The legacy `get_machine_id`/`get_initials` removal is anticipated by the plan ("the legacy ... signatures are replaced by the blob model"); the `main.py` rewire that consumes the new `load_identity`/`save_initials` is explicitly Plan 03's scope, and no test imports `main.py`, so the full suite stays green.

## Issues Encountered
None. All verifications passed on first implementation. (A benign `LF will be replaced by CRLF` git warning appears on commit — the repo's `.gitattributes` governs line endings; no action needed.)

## User Setup Required
None — stdlib-only (`json`, `uuid`, `os`, `re`) plus the Plan 01 client crypto module. No package installs. The build-baked HMAC secret (D-09) lands in Plan 03.

## Known Stubs
None — all functions are fully implemented and exercised by the test suite. `load_identity`/`save_initials` take `secret` as an explicit parameter; Plan 03 wires the build-baked secret and `main.py` startup/submit gate.

## Threat Flags
None — no new security surface beyond the plan's `<threat_model>`. The identity file remains a local trust boundary; the HMAC + fail-closed sentinel (T-05-05), obfuscation (T-05-06), and verify-before-delete (T-05-07) mitigations are all implemented as planned.

## Next Phase Readiness
- Plan 03 (submission signing + wiring) consumes `local_storage.load_identity` and `save_initials(initials, secret)`; it owns the `main.py` rewire (replace the removed `get_machine_id`/`get_initials` calls), the TAMPERED submit-gate, and the build-baked secret (`build.py` + gitignored `hmac_secret.local`, D-09).

## Self-Check: PASSED
- FOUND: paths.py (user_data_dir/user_data_path)
- FOUND: settings.py (IDENTITY_DIR_NAME/IDENTITY_FILE_NAME)
- FOUND: local_storage.py (load_identity/_read_identity_blob/_write_identity_blob/save_initials)
- FOUND: tests/test_local_storage.py (13 tests, green)
- FOUND commit: 22e132e (Task 1), 8947ea8 (Task 2), cf16671 (Task 3)
- Full suite: 115 passed, 9 skipped, 0 failed

---
*Phase: 05-client-identity-hardening*
*Completed: 2026-06-19*
