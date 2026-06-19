---
phase: 05-client-identity-hardening
plan: 01
subsystem: testing
tags: [hmac, sha256, crypto, obfuscation, base64, domain-separation, leaderboard, anti-cheat]

# Dependency graph
requires:
  - phase: 04-leaderboard-backend-hardening
    provides: "Server canonical_message + verify_signature wire contract (the oracle this plan signs against)"
provides:
  - "Client leaderboard_crypto.py — canonical_message (byte-for-byte server mirror) + sign_submission"
  - "Reversible non-human-readable obfuscation (obfuscate/de_obfuscate, base64-over-XOR)"
  - "Domain-separated, constant-time, fail-closed file-integrity HMAC (sign_identity_blob/verify_identity_blob)"
  - "Loop-closing oracle test: client signature accepted by the real server verify_signature in-test"
affects: [05-02-identity-storage, 05-03-submission-signing, local_storage, api_service, build]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Client/server crypto mirror: one canonical_message reproduced byte-for-byte, proven by an in-test oracle"
    - "HMAC domain separation: one secret, two framings (submission canonical vs IDENTITY_FILE_PREFIX + blob)"
    - "Light obfuscation = base64-over-XOR with a non-secret module key (D-10) — not encryption"

key-files:
  created:
    - leaderboard_crypto.py
    - tests/test_client_crypto.py
  modified:
    - cloud_functions/submit_score/main.py
    - cloud_functions/get_leaderboard/main.py

key-decisions:
  - "Client sign_submission takes the secret as an explicit arg (caller supplies build-baked secret) rather than reading os.environ like the server"
  - "Obfuscation key (OBFUSCATION_XOR_KEY) is a committed non-secret constant — obfuscation defeats casual reading only; the HMAC is the real control"
  - "Cloud-fn import seam switched from try/except ModuleNotFoundError to __package__ test, so the new repo-root client module no longer shadows the server copy under the test harness"

patterns-established:
  - "Oracle test (success criterion 4): client crypto signs, the real Phase 4 server verify_signature accepts it — no live deploy needed"
  - "Fail-closed verify (CR-01 mirror): non-string/non-ASCII sig returns False, never raises"

requirements-completed: [IDENT-02, IDENT-03]

# Metrics
duration: 18min
completed: 2026-06-19
---

# Phase 5 Plan 01: Client Crypto Module Summary

**Client `leaderboard_crypto.py` whose signature over a known submission is accepted by the real Phase 4 server `verify_signature` in-test, plus reversible obfuscation and a domain-separated file-integrity HMAC — all stdlib-only.**

## Performance

- **Duration:** 18 min
- **Started:** 2026-06-19
- **Completed:** 2026-06-19
- **Tasks:** 3 (all TDD)
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments
- **Loop closed (success criterion 4):** a CLIENT `sign_submission("m1","BOB",5000,"test-key")` passes the REAL server `verify_signature` in-test, proving the client wire-format mirrors the server byte-for-byte without a live deploy.
- **canonical_message byte-identical** to the server's (`b'{"initials":"BOB","machine_id":"m1","score":5000}'`) — locked json.dumps kwargs (D-07); `score` stays an int.
- **Reversible obfuscation (IDENT-02 / D-10):** `obfuscate`/`de_obfuscate` round-trips and the obfuscated form contains neither `b"BOB"` nor `b"machine_id"` (not greppable).
- **File-integrity HMAC (IDENT-03 / D-08):** `sign_identity_blob`/`verify_identity_blob` over `IDENTITY_FILE_PREFIX + blob`, constant-time and fail-closed; a file sig and a submission sig are not interchangeable (domain separation, tested).

## Task Commits

Each task was committed atomically (TDD: RED test → GREEN impl):

1. **Task 1 + 2 + 3 RED: failing client-crypto tests** - `2f53338` (test)
2. **Task 1 + 2 GREEN: client leaderboard_crypto module** - `af1166b` (feat)
3. **Deviation fix: cloud-fn import seam** - `66c6cc2` (fix)

_Tasks 1-2 both populate the single `leaderboard_crypto.py` module, committed once as the GREEN gate. Task 3 is the test file, committed as the RED gate. The fix commit resolves a namespace collision the new module introduced (see Deviations)._

## TDD Gate Compliance
- RED gate present: `2f53338` (`test(05-01): ...`) — test file written and run failing (ModuleNotFoundError) before the module existed.
- GREEN gate present: `af1166b` (`feat(05-01): ...`) — module added, all 15 client tests pass.
- REFACTOR gate: not needed (implementation was clean on first pass).

## Files Created/Modified
- `leaderboard_crypto.py` (NEW, repo-root CLIENT copy) - canonical_message, sign_submission, obfuscate/de_obfuscate, OBFUSCATION_XOR_KEY, IDENTITY_FILE_PREFIX, sign_identity_blob, verify_identity_blob. Stdlib only (hashlib, hmac, json, base64). No real secret literal.
- `tests/test_client_crypto.py` (NEW) - 15 tests: oracle (client sig → server verify), canonical byte-equality, machine_id binding, int-vs-str score, obfuscation round-trip + not-human-readable, domain separation, fail-closed verify_identity_blob (non-string/non-ASCII/tampered).
- `cloud_functions/submit_score/main.py` (MODIFIED) - import seam fix only (see Deviations).
- `cloud_functions/get_leaderboard/main.py` (MODIFIED) - import seam fix only (see Deviations).

## Decisions Made
- **Client takes `secret` as an explicit parameter** (server reads os.environ) — the Plan 03 caller will supply the build-baked secret.
- **`OBFUSCATION_XOR_KEY` is a committed non-secret constant** — obfuscation is not encryption; the HMAC is the integrity control (D-10 altitude, T-05-04 accepted residual).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Cloud-fn `import leaderboard_crypto` shadowed by the new repo-root client module**
- **Found during:** Task 3 (full-suite verification)
- **Issue:** `cloud_functions/*/main.py` used `try: import leaderboard_crypto / except ModuleNotFoundError: from . import leaderboard_crypto`. Before this plan there was no repo-root `leaderboard_crypto`, so the bare import raised ModuleNotFoundError under the test harness and fell through to the correct co-located server copy. Adding the repo-root CLIENT `leaderboard_crypto.py` (which has no `verify_signature`) made the bare import succeed and bind the wrong module — breaking 20 server tests (`test_submit_score.py`, `test_get_leaderboard.py`) with `AttributeError: module 'leaderboard_crypto' has no attribute 'verify_signature'`.
- **Fix:** Replaced the try/except seam with an `if __package__:` test. Under the test harness the module is loaded as `cloud_functions.submit_score.main` (non-empty `__package__`) → use the package-relative import, which pins the co-located server copy regardless of sys.path shadowing. At deploy time the function dir is the import root and the module loads top-level (`__package__ == ""`) → the bare import resolves the co-located copy as before. Deploy behavior and the wire contract are unchanged; both server copies remain byte-identical (drift guard `test_function_dir_copies_are_byte_identical` green).
- **Files modified:** cloud_functions/submit_score/main.py, cloud_functions/get_leaderboard/main.py
- **Verification:** Full suite `107 passed, 9 skipped, 0 failed`; deploy-path simulation confirmed the bare import still resolves the server copy with `verify_signature`.
- **Committed in:** `66c6cc2`

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** The fix was required for correctness — the new client module is the whole point of the plan, and it could not coexist with the server tests without resolving the namespace collision. No scope creep: the change is import-resolution only, no behavior or wire-contract change. Both server copies stay byte-identical.

## Issues Encountered
- The `leaderboard_crypto` top-level name collision (above) was the one issue; resolved via the import-seam fix. No other problems.

## User Setup Required
None - no external service configuration required. Client crypto is stdlib-only (no package installs).

## Known Stubs
None - all functions are fully implemented and exercised by the test suite.

## Next Phase Readiness
- The crypto contract is established and tested first (interface-first ordering). Plan 02 (identity storage) consumes `obfuscate`/`de_obfuscate` + `sign_identity_blob`/`verify_identity_blob`; Plan 03 (submission signing) consumes `sign_submission` + `canonical_message`.
- The build-baked secret mechanism (D-09) is NOT in this plan — it lands in Plan 03 (`build.py` + a gitignored `hmac_secret.local`). Consumers in Plans 02/03 must supply `secret` explicitly.

## Self-Check: PASSED
- FOUND: leaderboard_crypto.py
- FOUND: tests/test_client_crypto.py
- FOUND: cloud_functions/submit_score/main.py
- FOUND: cloud_functions/get_leaderboard/main.py
- FOUND commit: 2f53338 (RED), af1166b (GREEN), 66c6cc2 (fix)

---
*Phase: 05-client-identity-hardening*
*Completed: 2026-06-19*
