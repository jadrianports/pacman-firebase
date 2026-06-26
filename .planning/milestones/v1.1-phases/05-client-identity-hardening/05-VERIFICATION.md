---
phase: 05-client-identity-hardening
verified: 2026-06-19T02:00:00Z
status: passed
score: 4/4 must-haves verified
overrides_applied: 0
re_verification:
  previous_status: gaps_found
  previous_score: 3/4
  gaps_closed:
    - "When no HMAC secret is available (secret=None), dev/exe gracefully degrades — the game stays fully playable, leaderboard features degrade, no crash"
  gaps_remaining: []
  regressions: []
---

# Phase 5: Client Identity Hardening — Verification Report

**Phase Goal:** The player's identity is stored safely outside the game folder and signed, so the client both detects local tampering and produces submissions the hardened server accepts.
**Verified:** 2026-06-19
**Status:** passed
**Re-verification:** Yes — after gap closure (commit fad716e)

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| SC-1 | Identity stored in per-user location outside the game/exe folder | VERIFIED | `paths.user_data_dir()` targets `%LOCALAPPDATA%\PacMan\` on Windows, `~/.pacman` dev fallback. `settings.IDENTITY_DIR_NAME = "PacMan"`, `IDENTITY_FILE_NAME = "identity.dat"`. Test `test_load_identity_missing_mints_fresh` confirms blob written under tmp path, not next to exe. |
| SC-2 | Stored identity is obfuscated, not human-readable plaintext | VERIFIED | `_write_identity_blob` calls `obfuscate(payload)` (XOR+base64) before storing. On-disk JSON envelope `{sig, blob}` where blob is base64-ASCII. `test_blob_on_disk_is_not_human_readable` asserts `b"BOB"` and `b"machine_id"` absent from raw file bytes. Behavioral spot-check confirmed. |
| SC-3 | Out-of-band alteration detected on load; tampered identity refuses to submit | VERIFIED | HMAC mismatch path: `_read_identity_blob` calls `verify_identity_blob`; a failed verify returns `IDENTITY_STATUS_TAMPERED`; `main.py:88` gates `identity_tampered` and skips `api.submit_score`, shows "Score not saved — identity error". Tests `test_tampered_blob_returns_tampered`, `test_garbage_blob_returns_tampered_same_path`, `test_load_identity_tampered_blob_does_not_regenerate` all pass. No-secret path now returns `IDENTITY_STATUS_NO_SECRET` (never `TAMPERED`) — previously-broken edge case fixed. |
| SC-4 | Normally-played score carries valid HMAC signature accepted by Phase 4 server | VERIFIED | `test_client_signature_passes_server_verifier` passes: `sign_submission("m1","BOB",5000,"test-key")` accepted by `server_verify_signature`. `main.py:98` computes `signature = sign_submission(machine_id, initials, score, secret) if secret else None` and passes to `api.submit_score(..., signature)`. `test_submit_score_sends_signature_field` asserts "signature" key present in POST body. |

**Score:** 4/4 truths verified

---

### Gap Closure Evidence — CR-01 and CR-02

**CR-01 closed: fresh launch with secret=None no longer crashes.**

`load_identity(secret=None, ...)` now short-circuits immediately into `_load_identity_no_secret` (local_storage.py line 168-171). That path mints an in-session uuid4, returns `IDENTITY_STATUS_NO_SECRET`, and never calls `sign_identity_blob` or `_write_identity_blob`. Direct behavioral spot-check confirmed:

```
CR-01 PASS: fresh launch with secret=None returns NO_SECRET, no crash, no blob written
```

**CR-02 closed: valid blob read with secret=None no longer returns TAMPERED.**

`_load_identity_no_secret` reads the blob directly by decoding the obfuscated payload with `de_obfuscate` (which uses only the public `OBFUSCATION_XOR_KEY`, not the secret), skips `verify_identity_blob` entirely, and returns `IDENTITY_STATUS_NO_SECRET` with the recovered `machine_id` and `initials`. Direct behavioral spot-check confirmed:

```
CR-02 PASS: valid blob read with secret=None returns NO_SECRET, machine_id=m1, initials=BOB
```

**Graceful-degrade contract (CLAUDE.md: "Game is fully playable offline — leaderboard features gracefully degrade") now upheld.**

`IDENTITY_STATUS_NO_SECRET != IDENTITY_STATUS_TAMPERED`, so `identity_tampered` is `False` in `main.py` line 61. The game proceeds normally. Score submission is skipped at line 98 (`if secret else None`), which was already correct. The player sees no error notice and the game is fully playable.

---

### Must-Haves from PLAN Frontmatter

#### Plan 01 Must-Haves (IDENT-02, IDENT-03)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Client signature over known submission passes server verify_signature | VERIFIED | `test_client_signature_passes_server_verifier` passes. Regression spot-check: `canonical_message` byte equality confirmed. |
| 2 | canonical_message produces byte-identical output to server | VERIFIED | `test_client_canonical_matches_server` asserts equality with `LOCKED_BYTES = b'{"initials":"BOB","machine_id":"m1","score":5000}'`. |
| 3 | Identity blob can be obfuscated and de-obfuscated round-trip; obfuscated form not human-readable | VERIFIED | `test_obfuscation_round_trip` and `test_obfuscated_not_human_readable` pass. Spot-check confirmed. |
| 4 | File-integrity sig and submission sig over same bytes are NOT equal (domain separation) | VERIFIED | `test_file_sig_not_interchangeable_with_submission_sig` passes. `IDENTITY_FILE_PREFIX = b"identity-file-v1:"` present in module. |

#### Plan 02 Must-Haves (IDENT-01, IDENT-02, IDENT-03)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Identity stored in `%LOCALAPPDATA%\PacMan\` on Windows | VERIFIED | `paths.user_data_dir()` uses `os.environ.get("LOCALAPPDATA")` + `IDENTITY_DIR_NAME`. |
| 2 | Single identity blob holds {machine_id, initials} obfuscated under one HMAC signature | VERIFIED | On-disk format `{sig, blob}` where blob = `obfuscate(json({machine_id, initials}))`. Both `b"BOB"` and `b"machine_id"` absent from raw bytes. |
| 3 | On first launch with legacy files present, new blob written, verified, legacy deleted | VERIFIED | `test_load_identity_migrates_then_removes_legacy` and `test_migration_verifies_read_back_before_deleting_legacy` both pass. |
| 4 | Missing file mints fresh identity; present-but-invalid returns TAMPERED sentinel that blocks submit | VERIFIED | Missing-file fresh mint: VERIFIED (`test_load_identity_missing_mints_fresh`). Present-but-invalid TAMPERED: VERIFIED for real tampering. No-secret path: now correctly returns NO_SECRET (never crashes, never false-TAMPERED) — CR-01/CR-02 resolved. |

#### Plan 03 Must-Haves (IDENT-01, IDENT-03)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Normally-played score submitted with valid HMAC signature, accepted by Phase 4 server | VERIFIED | Oracle test passes; `main.py:98` signs with `sign_submission` and passes `signature` to `api.submit_score`. |
| 2 | Tampered/invalid identity: client skips submission, shows "Score not saved", game fully playable | VERIFIED | `main.py:88-94` gates on `identity_tampered`; `menu.py:211-214` renders gray notice. Tests pass. No-secret path no longer triggers false TAMPERED — player sees no error notice with NO_SECRET. |
| 3 | Real HMAC secret never committed: build.py reads gitignored hmac_secret.local; repo ships placeholder only | VERIFIED | `hmac_secret.example` exists with `REPLACE_WITH_REAL_SECRET`. `git check-ignore hmac_secret.local` exits 0. `git check-ignore _baked_secret.py` exits 0. `build.py` calls `_read_secret()` which raises `SystemExit` if file absent. No real secret literal in committed source. |
| 4 | Identity load/migrate runs at startup before initials entry; migrated identities not re-prompted | VERIFIED | `main.py:58` calls `load_identity(secret)` before `run_initials_entry` at line 64-69. Prompt gated on `not identity_tampered and initials is None`. With NO_SECRET status, `identity_tampered` is False — initials prompt still runs correctly if initials is None. |

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `leaderboard_crypto.py` | canonical_message, sign_submission, obfuscate, de_obfuscate, sign_identity_blob, verify_identity_blob | VERIFIED | All 7 exported symbols present. Stdlib only (hashlib, hmac, json, base64). 125 lines. `sign_identity_blob` still calls `secret.encode()` without a None guard, but this is now unreachable with None — the guard lives in `load_identity` before any call reaches here. |
| `tests/test_client_crypto.py` | Oracle test + canonical/obfuscation/domain-separation tests | VERIFIED | 15 tests, all pass. |
| `paths.py` | `user_data_dir()` / `user_data_path()` targeting `%LOCALAPPDATA%\PacMan\` | VERIFIED | `user_data_dir()` uses `LOCALAPPDATA` env var with `IDENTITY_DIR_NAME` from settings. Dev fallback `~/.pacman`. Auto-creates dir. |
| `local_storage.py` | `load_identity()` + `_write_identity_blob` + `_read_identity_blob` + tamper sentinel + migration + no-secret path | VERIFIED | All functions present. New: `IDENTITY_STATUS_NO_SECRET` sentinel, `_load_identity_no_secret()` helper, `load_identity` short-circuit on `secret is None`, `save_initials` no-op on `secret is None`. CR-01/CR-02 resolved. |
| `settings.py` | `IDENTITY_DIR_NAME`, `IDENTITY_FILE_NAME`, `HMAC_SECRET_FILE_NAME` constants | VERIFIED | All three present at lines 83-89. |
| `api_service.py` | `submit_score(machine_id, initials, score, signature=None)` — sends "signature" field | VERIFIED | `signature=None` parameter present; `"signature": signature` in body dict; `test_submit_score_sends_signature_field` passes. |
| `main.py` | Startup `load_identity` wiring, signed submit, tamper gate, notice flag | VERIFIED | All four elements present. `load_identity(secret)` now safe with `secret=None` (short-circuits to no-secret path). Submit guard `if secret else None` at line 98 unchanged. |
| `menu.py` | `run_game_over_screen(..., identity_error=False)` renders "Score not saved" notice | VERIFIED | `identity_error` parameter. Gray render branch at lines 211-214. |
| `build.py` | Reads `hmac_secret.local`, bakes non-literally, fails loudly if absent | VERIFIED | `_read_secret()` raises `SystemExit` if file absent. `_write_baked_module()` emits `_baked_secret.py` with obfuscated string. |
| `hmac_secret.example` | Committed placeholder (not real secret) | VERIFIED | Contains `REPLACE_WITH_REAL_SECRET`. |
| `tests/test_local_storage.py` | Round-trip, tamper, corrupt, missing, migration, partial-legacy, no-secret tests | VERIFIED | 18 tests, all pass. 5 new no-secret tests cover CR-01, CR-02, legacy-no-delete, corrupt-blob-fallback, and save_initials-noop. |
| `tests/test_api_service.py` | Signature field assertion | VERIFIED | `test_submit_score_sends_signature_field` decodes POST body and asserts `"signature"` key and int `score`. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `leaderboard_crypto.py sign_submission` | Server `verify_signature` | Identical HMAC-SHA256 over identical canonical_message | WIRED | Oracle test confirms: `sign_submission("m1","BOB",5000,"test-key")` accepted by `server_verify_signature`. |
| `local_storage.py` | `leaderboard_crypto.py` (obfuscate/sign/verify) | `from leaderboard_crypto import ...` at line 29 | WIRED | Import confirmed. Functions called in `_write_identity_blob` and `_read_identity_blob`. `_load_identity_no_secret` calls only `de_obfuscate` (not `sign/verify`). |
| `local_storage.load_identity` | `_load_identity_no_secret` | `if secret is None:` guard at line 168 | WIRED | Short-circuit in place; unreachable by `sign_identity_blob(None)` path. |
| `local_storage.py` | `paths.py user_data_path` | `from paths import data_path, user_data_path` at line 35 | WIRED | `IDENTITY_FILE = user_data_path(IDENTITY_FILE_NAME)` at line 45. |
| `local_storage.py migration` | `paths.py data_path (legacy)` | `MACHINE_ID_FILE = data_path("machine_id.txt")` | WIRED | Legacy paths defined at lines 41-42. |
| `main.py` | `leaderboard_crypto.sign_submission + api_service.submit_score` | `sign_submission(...)` at line 98, passed as `signature` | WIRED | `signature = sign_submission(machine_id, initials, score, secret) if secret else None` then `api.submit_score(..., signature)`. |
| `main.py submit gate` | `IDENTITY_STATUS_TAMPERED` | `identity_tampered = identity["status"] == IDENTITY_STATUS_TAMPERED` at line 61 | WIRED | `IDENTITY_STATUS_NO_SECRET != IDENTITY_STATUS_TAMPERED` — confirmed; no-secret path does not trigger the submit block. |
| `build.py` | `hmac_secret.local` (gitignored) | `_read_secret()` reads `HMAC_SECRET_FILE_NAME` | WIRED | `SECRET_PATH = os.path.join(ROOT, HMAC_SECRET_FILE_NAME)`. Fails loudly if absent. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `menu.py run_game_over_screen` | `identity_error` | `main.py:88-94` — set from `identity_tampered` | Yes (from `load_identity` status; NO_SECRET does not set this flag) | FLOWING |
| `api_service.py submit_score` | `signature` | `main.py:98` — `sign_submission(...)` with build-baked secret, or `None` when no secret | Yes (HMAC-SHA256 hexdigest, or omitted gracefully) | FLOWING |
| `local_storage._read_identity_blob` | `machine_id, initials` | JSON de-obfuscate from on-disk blob | Yes (from obfuscated+signed file) | FLOWING |
| `local_storage._load_identity_no_secret` | `machine_id, initials` | `de_obfuscate(blob)` (XOR key only, no HMAC), or legacy read, or fresh uuid4 | Yes (real data or fresh in-session id) | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| canonical_message byte equality | `.venv/Scripts/python.exe -c "from leaderboard_crypto import canonical_message; assert canonical_message('m1','BOB',5000)==b'{\"initials\":\"BOB\",\"machine_id\":\"m1\",\"score\":5000}'"` | Exits 0 | PASS |
| Obfuscation round-trip | `.venv/Scripts/python.exe -c "from leaderboard_crypto import obfuscate, de_obfuscate; p=b'test'; assert de_obfuscate(obfuscate(p))==p"` | Exits 0 | PASS |
| CR-01: Fresh launch, secret=None (no blob, no legacy) | `load_identity(None, ...)` direct execution | Returns `{status: NO_SECRET, machine_id: <uuid4>, initials: None}`, no blob written | PASS |
| CR-02: Valid blob, secret=None | `load_identity(None, ...)` with pre-written signed blob | Returns `{status: NO_SECRET, machine_id: m1, initials: BOB}` — never TAMPERED | PASS |
| main.py tamper gate with NO_SECRET | `IDENTITY_STATUS_NO_SECRET == IDENTITY_STATUS_TAMPERED` | False — identity_tampered remains False, game fully playable | PASS |
| Full test suite | `.venv/Scripts/python.exe -m pytest -q` | 122 passed, 9 skipped | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| IDENT-01 | 05-02, 05-03 | Identity stored outside game folder | SATISFIED | `paths.user_data_dir()` targets `%LOCALAPPDATA%\PacMan\`; `user_data_path("identity.dat")` used as default blob path. |
| IDENT-02 | 05-01, 05-02 | Identity files stored obfuscated, not human-readable | SATISFIED | `obfuscate()` XOR+base64 applied; on-disk blob has no plaintext machine_id or initials; test asserts `b"BOB"` absent. |
| IDENT-03 | 05-01, 05-02 | Identity files carry HMAC; tampering detected on load, refuses to submit | SATISFIED | Real tamper detection: fully working. No-secret path: now returns `IDENTITY_STATUS_NO_SECRET` (never false-TAMPERED). CR-01/CR-02 both resolved. Graceful degrade contract upheld. |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `leaderboard_crypto.py` | 103-106 | `secret.encode("utf-8")` in `sign_identity_blob` with no None guard | INFO (residual) | Previously BLOCKER; now INFO only. The None path is fully blocked at `load_identity` entry (line 168) before `sign_identity_blob` is ever reached. No reachable None path remains. |
| `local_storage.py` | 204-206 (original save_initials) | `save_initials` was a no-op for TAMPERED blobs but could mint fresh uuid (WR-05 from review) | INFO | `save_initials(initials, None)` is now explicitly a no-op (lines 268-269). The TAMPERED-does-not-regenerate invariant holds via `main.py`'s gate on `not identity_tampered` before calling `save_initials`. |
| `leaderboard_crypto.py` | 78-86 | `obfuscate` docstring says "not greppable"; XOR key is a committed public constant (WR-03) | WARNING | Overstates protection; the baked secret is fully recoverable by any user with the binary and the public key. Accepted residual per Phase 4 ceiling, but documentation is misleading. |
| `leaderboard_crypto.py` | 92 | `base64.b64decode` without `validate=True` (WR-04) | WARNING | Non-alphabet chars silently discarded, weakening the exact-round-trip assumption. Low impact post-HMAC-verify gate but a correctness gap. |
| `menu.py` | 147-157 | Unbounded leaderboard render loop; negative dot count possible (WR-01) | WARNING | If server returns more than ~14 rows, entries render off-screen. `dots` multiplication on a negative count is a silent formatting bug. |

---

### Human Verification Required

None — all must-haves are verifiable programmatically. The identified gaps were code defects confirmed and now resolved by direct execution.

---

### Re-verification Summary

**Items closed since initial verification (2026-06-19 gaps_found):**

1. **CR-01 resolved.** `load_identity(None)` on a fresh launch no longer crashes. The new `IDENTITY_STATUS_NO_SECRET` sentinel and `_load_identity_no_secret()` helper short-circuit the path before any call to `sign_identity_blob`. An in-session uuid4 is returned; no unsigned blob is written to disk.

2. **CR-02 resolved.** `load_identity(None)` with an existing valid blob no longer returns `IDENTITY_STATUS_TAMPERED`. `_load_identity_no_secret` reads the blob payload using only `de_obfuscate` (which uses the public `OBFUSCATION_XOR_KEY`, not the HMAC secret), skips `verify_identity_blob` entirely, and returns `IDENTITY_STATUS_NO_SECRET` with the correct `machine_id` and `initials`.

3. **Graceful-degrade contract (CLAUDE.md) now upheld.** `IDENTITY_STATUS_NO_SECRET` does not trigger `identity_tampered` in `main.py`. The game is fully playable. Score submission is skipped via the existing `if secret else None` guard at line 98. No player-visible error is shown.

4. **5 new regression tests added** in `tests/test_local_storage.py` (18 total, up from 13): `test_load_identity_no_secret_fresh_launch_does_not_crash`, `test_load_identity_no_secret_existing_valid_blob_not_tampered`, `test_load_identity_no_secret_reads_legacy_without_deleting`, `test_load_identity_no_secret_unreadable_blob_falls_back`, `test_save_initials_no_secret_is_noop`. All pass.

5. **No regressions detected.** All 3 previously-passing must-haves (IDENT-01 location, IDENT-02 obfuscation, SC-4 server-oracle) verified unchanged. Full suite: 122 passed, 9 skipped.

---

_Verified: 2026-06-19_
_Verifier: Claude (gsd-verifier)_
