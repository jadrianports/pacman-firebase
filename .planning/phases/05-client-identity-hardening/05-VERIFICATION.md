---
phase: 05-client-identity-hardening
verified: 2026-06-19T00:00:00Z
status: gaps_found
score: 3/4 must-haves verified
overrides_applied: 0
gaps:
  - truth: "When no HMAC secret is available (secret=None), dev/exe gracefully degrades — the game stays fully playable, leaderboard features degrade, no crash"
    status: failed
    reason: >
      CR-01: load_identity(None) on a fresh launch (no blob, no legacy files) crashes with
      AttributeError: 'NoneType' object has no attribute 'encode'. Code path:
      load_identity(None) -> _write_identity_blob(uuid, None, None, path) ->
      sign_identity_blob(obfuscated, None) -> None.encode('utf-8') -> AttributeError (uncaught).
      Reproduced directly against the codebase. This contradicts the documented contract in
      main._load_hmac_secret ('dev runs without it still play').

      CR-02: load_identity(None) when a valid blob already exists permanently misreports
      the identity as TAMPERED. Code path: _read_identity_blob(None, path) ->
      verify_identity_blob(obfuscated, sig, None) -> sign_identity_blob(blob, None) ->
      None.encode('utf-8') -> AttributeError raised outside the try/except TypeError in
      verify_identity_blob, propagates out, is caught by _read_identity_blob's broad
      'except Exception:' and returned as IDENTITY_STATUS_TAMPERED. Result: a player
      whose exe loses its _baked_secret module is permanently locked out of leaderboard
      submission with no recovery path and a misleading 'identity error' message.
      Reproduced directly against the codebase.

      These are the same root cause: sign_identity_blob does not guard against secret=None.
      Both are reachable in the shipped exe (frozen branch catch-all: 'except Exception: return None').
    artifacts:
      - path: "leaderboard_crypto.py"
        issue: "sign_identity_blob(blob_bytes, secret) calls secret.encode('utf-8') with no None guard; raises AttributeError when secret is None"
      - path: "local_storage.py"
        issue: "_write_identity_blob calls sign_identity_blob with whatever secret was passed; no None guard before the call. _read_identity_blob broad except Exception swallows AttributeError from verify_identity_blob and returns IDENTITY_STATUS_TAMPERED instead"
      - path: "main.py"
        issue: "load_identity(secret) called at line 58 with no guard on secret=None; the submission signing at line 98 correctly guards (if secret else None) but startup does not"
    missing:
      - "Guard secret=None before blob write/read. Either: (a) treat None secret as 'unsigned mode' by skipping signing/verifying (no HMAC, just obfuscation, with a status that is distinct from TAMPERED), or (b) add a None check in sign_identity_blob/verify_identity_blob so they handle None gracefully, or (c) short-circuit in _read_identity_blob/_write_identity_blob when secret is None and return a defined 'no-secret' status"
      - "Add tests: load_identity(None, ...) on fresh launch must not raise; load_identity(None, ...) with valid existing blob must not return TAMPERED"
---

# Phase 5: Client Identity Hardening — Verification Report

**Phase Goal:** The player's identity is stored safely outside the game folder and signed, so the client both detects local tampering and produces submissions the hardened server accepts.
**Verified:** 2026-06-19
**Status:** gaps_found
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (Roadmap Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| SC-1 | Identity stored in per-user location outside the game/exe folder | VERIFIED | `paths.user_data_dir()` targets `%LOCALAPPDATA%\PacMan\` on Windows, `~/.pacman` dev fallback. `settings.IDENTITY_DIR_NAME = "PacMan"`, `IDENTITY_FILE_NAME = "identity.dat"`. Test `test_load_identity_missing_mints_fresh` confirms blob written under tmp path, not next to exe. |
| SC-2 | Stored identity is obfuscated, not human-readable plaintext | VERIFIED | `_write_identity_blob` calls `obfuscate(payload)` (XOR+base64) before storing. On-disk JSON envelope `{sig, blob}` where blob is base64-ASCII. `test_blob_on_disk_is_not_human_readable` asserts `b"BOB"` and `b"machine_id"` absent from raw file bytes. |
| SC-3 | Out-of-band alteration detected on load; tampered identity refuses to submit | VERIFIED (conditional) | HMAC mismatch path: `_read_identity_blob` calls `verify_identity_blob`; a failed verify returns `IDENTITY_STATUS_TAMPERED`; `main.py:88` gates `identity_tampered` and skips `api.submit_score`, shows "Score not saved — identity error". Tests `test_tampered_blob_returns_tampered`, `test_garbage_blob_returns_tampered_same_path`, `test_load_identity_tampered_blob_does_not_regenerate` all pass. However: SC-3 is broken for the None-secret case (see gaps below — a missing secret falsely triggers TAMPERED, which is a different failure mode sharing the same user-visible outcome). |
| SC-4 | Normally-played score carries valid HMAC signature accepted by Phase 4 server | VERIFIED | `test_client_signature_passes_server_verifier` passes: `sign_submission("m1","BOB",5000,"test-key")` accepted by `server_verify_signature`. `main.py:98` computes `signature = sign_submission(machine_id, initials, score, secret) if secret else None` and passes to `api.submit_score(..., signature)`. `test_submit_score_sends_signature_field` asserts "signature" key present in POST body. |

**Score:** 3/4 truths verifiably satisfied (SC-3 has a broken edge case — the None-secret path; core tamper detection for the normal case is working).

---

### Must-Haves from PLAN Frontmatter

#### Plan 01 Must-Haves (IDENT-02, IDENT-03)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Client signature over known submission passes server verify_signature | VERIFIED | `test_client_signature_passes_server_verifier` passes. |
| 2 | canonical_message produces byte-identical output to server | VERIFIED | `test_client_canonical_matches_server` asserts equality with `LOCKED_BYTES = b'{"initials":"BOB","machine_id":"m1","score":5000}'`. |
| 3 | Identity blob can be obfuscated and de-obfuscated round-trip; obfuscated form not human-readable | VERIFIED | `test_obfuscation_round_trip` and `test_obfuscated_not_human_readable` pass. |
| 4 | File-integrity sig and submission sig over same bytes are NOT equal (domain separation) | VERIFIED | `test_file_sig_not_interchangeable_with_submission_sig` passes. `IDENTITY_FILE_PREFIX = b"identity-file-v1:"` present in module. |

#### Plan 02 Must-Haves (IDENT-01, IDENT-02, IDENT-03)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Identity stored in `%LOCALAPPDATA%\PacMan\` on Windows | VERIFIED | `paths.user_data_dir()` uses `os.environ.get("LOCALAPPDATA")` + `IDENTITY_DIR_NAME`. |
| 2 | Single identity blob holds {machine_id, initials} obfuscated under one HMAC signature | VERIFIED | On-disk format `{sig, blob}` where blob = `obfuscate(json({machine_id, initials}))`. Both `b"BOB"` and `b"machine_id"` absent from raw bytes. |
| 3 | On first launch with legacy files present, new blob written, verified, legacy deleted | VERIFIED | `test_load_identity_migrates_then_removes_legacy` and `test_migration_verifies_read_back_before_deleting_legacy` both pass. |
| 4 | Missing file mints fresh identity; present-but-invalid returns TAMPERED sentinel that blocks submit | FAILED (partial) | Missing-file fresh mint: VERIFIED (`test_load_identity_missing_mints_fresh`). Present-but-invalid TAMPERED: VERIFIED for real tampering. FAILED for None-secret: `load_identity(None)` with no blob crashes (AttributeError), never reaching the mint branch. `load_identity(None)` with a valid blob falsely returns TAMPERED. |

#### Plan 03 Must-Haves (IDENT-01, IDENT-03)

| # | Truth | Status | Evidence |
|---|-------|--------|---------|
| 1 | Normally-played score submitted with valid HMAC signature, accepted by Phase 4 server | VERIFIED | Oracle test passes; `main.py:98` signs with `sign_submission` and passes `signature` to `api.submit_score`. |
| 2 | Tampered/invalid identity: client skips submission, shows "Score not saved", game fully playable | VERIFIED (for real tamper) | `main.py:88-94` gates on `identity_tampered`; `menu.py:211-214` renders gray notice. Tests pass. CAVEAT: None-secret causes false TAMPERED (CR-02) — game stays playable but player incorrectly sees the notice and is locked out. |
| 3 | Real HMAC secret never committed: build.py reads gitignored hmac_secret.local; repo ships placeholder only | VERIFIED | `hmac_secret.example` exists with `REPLACE_WITH_REAL_SECRET`. `git check-ignore hmac_secret.local` exits 0. `git check-ignore _baked_secret.py` exits 0. `build.py` calls `_read_secret()` which raises `SystemExit` if file absent. No real secret literal in committed source. |
| 4 | Identity load/migrate runs at startup before initials entry; migrated identities not re-prompted | VERIFIED | `main.py:58` calls `load_identity(secret)` before `run_initials_entry` at line 64-69. Prompt gated on `not identity_tampered and initials is None`. |

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `leaderboard_crypto.py` | canonical_message, sign_submission, obfuscate, de_obfuscate, sign_identity_blob, verify_identity_blob | VERIFIED (with defect) | All 7 exported symbols present. Stdlib only (hashlib, hmac, json, base64). 124 lines. Defect: `sign_identity_blob` calls `secret.encode()` with no None guard — crashes on None secret. |
| `tests/test_client_crypto.py` | Oracle test + canonical/obfuscation/domain-separation tests | VERIFIED | 15 tests, all pass. Loop-closing oracle test (`test_client_signature_passes_server_verifier`) passes. |
| `paths.py` | `user_data_dir()` / `user_data_path()` targeting `%LOCALAPPDATA%\PacMan\` | VERIFIED | `user_data_dir()` uses `LOCALAPPDATA` env var with `IDENTITY_DIR_NAME` from settings. Dev fallback `~/.pacman`. Auto-creates dir. `data_path`/`resource_path` unchanged. |
| `local_storage.py` | `load_identity()` + `_write_identity_blob` + `_read_identity_blob` + tamper sentinel + migration | VERIFIED (with defect) | All functions present. Tamper detection, migration, verify-before-delete all correct. Defect: no None-secret guard in write/read paths. |
| `settings.py` | `IDENTITY_DIR_NAME`, `IDENTITY_FILE_NAME`, `HMAC_SECRET_FILE_NAME` constants | VERIFIED | All three present at lines 83-89. No HMAC secret literal. |
| `api_service.py` | `submit_score(machine_id, initials, score, signature=None)` — sends "signature" field | VERIFIED | `signature=None` parameter present; `"signature": signature` in body dict; `test_submit_score_sends_signature_field` passes. |
| `main.py` | Startup `load_identity` wiring, signed submit, tamper gate, notice flag | VERIFIED (with defect) | All four elements present and wired. Defect: `load_identity(secret)` called with no None guard — crashes on fresh launch with None secret. |
| `menu.py` | `run_game_over_screen(..., identity_error=False)` renders "Score not saved" notice | VERIFIED | `identity_error` parameter at line 174. Gray render branch at lines 211-214. String "Score not saved — identity error" confirmed. |
| `build.py` | Reads `hmac_secret.local`, bakes non-literally, fails loudly if absent | VERIFIED | `_read_secret()` raises `SystemExit` if file absent. `_write_baked_module()` emits `_baked_secret.py` with obfuscated string. `--hidden-import=_baked_secret` in PyInstaller args. |
| `hmac_secret.example` | Committed placeholder (not real secret) | VERIFIED | Contains `REPLACE_WITH_REAL_SECRET`. |
| `tests/test_local_storage.py` | Round-trip, tamper, corrupt, missing, migration, partial-legacy tests | VERIFIED | 13 tests, all pass. All branches covered. Does NOT test None-secret case (gap). |
| `tests/test_api_service.py` | Signature field assertion | VERIFIED | `test_submit_score_sends_signature_field` decodes POST body and asserts `"signature"` key and int `score`. |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `leaderboard_crypto.py sign_submission` | Server `verify_signature` | Identical HMAC-SHA256 over identical canonical_message | WIRED | Oracle test confirms: `sign_submission("m1","BOB",5000,"test-key")` accepted by `server_verify_signature`. |
| `local_storage.py` | `leaderboard_crypto.py` (obfuscate/sign/verify) | `from leaderboard_crypto import ...` at line 29 | WIRED | Import confirmed. Functions called in `_write_identity_blob` and `_read_identity_blob`. |
| `local_storage.py` | `paths.py user_data_path` | `from paths import data_path, user_data_path` at line 35 | WIRED | `IDENTITY_FILE = user_data_path(IDENTITY_FILE_NAME)` at line 45. |
| `local_storage.py migration` | `paths.py data_path (legacy)` | `MACHINE_ID_FILE = data_path("machine_id.txt")` | WIRED | Legacy paths defined at lines 41-42. |
| `main.py` | `leaderboard_crypto.sign_submission + api_service.submit_score` | `sign_submission(...)` at line 98, passed as `signature` | WIRED | `signature = sign_submission(machine_id, initials, score, secret) if secret else None` then `api.submit_score(..., signature)`. |
| `main.py submit gate` | `IDENTITY_STATUS_TAMPERED` | `identity_tampered = identity["status"] == IDENTITY_STATUS_TAMPERED` at line 61 | WIRED | Branch at line 88 skips submit, calls `run_game_over_screen(..., identity_error=True)`. |
| `build.py` | `hmac_secret.local` (gitignored) | `_read_secret()` reads `HMAC_SECRET_FILE_NAME` | WIRED | `SECRET_PATH = os.path.join(ROOT, HMAC_SECRET_FILE_NAME)`. Fails loudly if absent. |

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|-------------------|--------|
| `menu.py run_game_over_screen` | `identity_error` | `main.py:88-94` — set from `identity_tampered` | Yes (from `load_identity` status) | FLOWING |
| `api_service.py submit_score` | `signature` | `main.py:98` — `sign_submission(...)` with build-baked secret | Yes (HMAC-SHA256 hexdigest) | FLOWING |
| `local_storage._read_identity_blob` | `machine_id, initials` | JSON de-obfuscate from on-disk blob | Yes (from obfuscated+signed file) | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| canonical_message byte equality | `.venv/Scripts/python.exe -c "from leaderboard_crypto import canonical_message; assert canonical_message('m1','BOB',5000)==b'{\"initials\":\"BOB\",\"machine_id\":\"m1\",\"score\":5000}'"` | Exits 0 | PASS |
| Obfuscation round-trip | `.venv/Scripts/python.exe -c "from leaderboard_crypto import obfuscate, de_obfuscate; p=b'test'; assert de_obfuscate(obfuscate(p))==p"` | Exits 0 | PASS |
| Fresh launch, secret=None | `.venv/Scripts/python.exe -c "from local_storage import load_identity; load_identity(None, ...)"` | AttributeError — CRASH | FAIL |
| Valid blob, secret=None | `.venv/Scripts/python.exe -c "_read_identity_blob(None, path)"` | Returns `(None, None, 'tampered')` — false positive | FAIL |
| Full test suite | `.venv/Scripts/python.exe -m pytest -q` | 117 passed, 9 skipped | PASS |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|---------|
| IDENT-01 | 05-02, 05-03 | Identity stored outside game folder | SATISFIED | `paths.user_data_dir()` targets `%LOCALAPPDATA%\PacMan\`; `user_data_path("identity.dat")` used as default blob path. |
| IDENT-02 | 05-01, 05-02 | Identity files stored obfuscated, not human-readable | SATISFIED | `obfuscate()` XOR+base64 applied; on-disk blob has no plaintext machine_id or initials; test asserts `b"BOB"` absent. |
| IDENT-03 | 05-01, 05-02 | Identity files carry HMAC; tampering detected on load, refuses to submit | PARTIALLY SATISFIED | Real tamper detection: SATISFIED. None-secret path: `_read_identity_blob(None, path)` with a valid blob returns TAMPERED falsely — a missing secret is misreported as tampering, blocking all submission permanently with no recovery. |

---

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `leaderboard_crypto.py` | 103-106 | `secret.encode("utf-8")` in `sign_identity_blob` with no None guard | BLOCKER | Crashes entire game on fresh launch when secret=None (CR-01). Causes false TAMPERED misreport on existing valid blob when secret=None (CR-02). |
| `local_storage.py` | 99 | Broad `except Exception:` swallows AttributeError from None-secret path and reports TAMPERED | BLOCKER | Part of CR-02: the catch-all that converts a programming error (None.encode) into a security state (TAMPERED) without the caller being able to distinguish the two. |
| `local_storage.py` | 204-206 | `save_initials` mints a fresh uuid4 when blob is TAMPERED (WR-05 from review) | WARNING | Violates the stated "never auto-regen over tampered" invariant; not currently exploitable because `main.py:64` gates the prompt on `not identity_tampered`, but is a trap for future callers. |
| `leaderboard_crypto.py` | 78-86 | `obfuscate` docstring says "not greppable"; XOR key is a committed public constant (WR-03) | WARNING | Overstates protection; the baked secret is fully recoverable by any user with the binary and the public key. Accepted residual per Phase 4 ceiling, but documentation is misleading. |
| `leaderboard_crypto.py` | 92 | `base64.b64decode` without `validate=True` (WR-04) | WARNING | Non-alphabet chars silently discarded, weakening the exact-round-trip assumption. Low impact post-HMAC-verify gate but a correctness gap. |
| `menu.py` | 147-157 | Unbounded leaderboard render loop; negative dot count possible (WR-01) | WARNING | If server returns more than ~14 rows, entries render off-screen. `dots` multiplication on a negative count is a silent formatting bug. |

---

### Critical Findings from 05-REVIEW.md — Independent Confirmation

The code review (05-REVIEW.md) flagged two CRITICAL findings. Both have been independently confirmed by direct execution:

**CR-01: Fresh launch with secret=None crashes the game**

Confirmed. Execution trace:

```
main() -> secret = _load_hmac_secret()  # returns None (no hmac_secret.local, no env var)
       -> identity = load_identity(None)
          -> _read_identity_blob(None, path)  # no blob -> _STATUS_MISSING
          -> _write_identity_blob(uuid, None, None, path)
             -> sign_identity_blob(obfuscated, None)
                -> hmac.new(None.encode("utf-8"), ...)
                   -> AttributeError: 'NoneType' object has no attribute 'encode'
```

This is uncaught all the way up through `_write_identity_blob`, `load_identity`, and `main()`. The game crashes before the menu renders.

**Reachable in the shipped exe:** `_load_hmac_secret` frozen branch catches all exceptions from `import _baked_secret` and returns `None`. A corrupt or missing baked module in the bundle produces this crash.

**CR-02: Existing valid blob reads as permanently TAMPERED when secret=None**

Confirmed. Execution trace:

```
_read_identity_blob(None, path)
  -> envelope parsed, sig and obfuscated extracted
  -> verify_identity_blob(obfuscated, sig, None)
     -> isinstance(sig, str) is True  # sig is a hex string, passes
     -> expected = sign_identity_blob(obfuscated, None)
        -> None.encode("utf-8")  # raises AttributeError
        # NOTE: this line is OUTSIDE the try/except TypeError in verify_identity_blob
        # AttributeError propagates out of verify_identity_blob
  -> except Exception:  # caught by _read_identity_blob's broad handler
     -> return (None, None, IDENTITY_STATUS_TAMPERED)  # false positive
```

Direct test result: `_read_identity_blob(None, valid_blob_path)` returns `(None, None, 'tampered')`.

**Consequence:** Any player whose shipped exe fails to load `_baked_secret` (bundling miss, file corruption) gets their valid identity permanently misreported as tampered. Per the fail-closed D-05 design, TAMPERED blobs are never auto-regenerated, blocking all leaderboard submission permanently. The player sees "Score not saved — identity error" with no recovery mechanism. This directly contradicts the documented graceful-degrade contract.

**The graceful-degrade contract (CLAUDE.md: "Game is fully playable offline — leaderboard features gracefully degrade") is NOT upheld** for the None-secret path. Both failures are triggered by the single missing guard in `sign_identity_blob`.

---

### Human Verification Required

None — all must-haves are verifiable programmatically. The identified gaps are code defects confirmed by execution, not UI/UX behaviors requiring human judgment.

---

### Gaps Summary

**One root cause, two observable failure modes — both BLOCKERS:**

The `_load_hmac_secret()` function is explicitly documented to return `None` when no secret is available, with the contract that "dev runs without it still play." However, `sign_identity_blob(blob_bytes, secret)` calls `secret.encode("utf-8")` without guarding against `None`, and this call is outside any protective try/except in `verify_identity_blob`. The result is:

1. **Fresh launch crash (CR-01):** `load_identity(None)` with no existing blob reaches `_write_identity_blob` which calls `sign_identity_blob(obfuscated, None)` and crashes with `AttributeError`. The game cannot start.

2. **Valid blob falsely TAMPERED (CR-02):** `load_identity(None)` with an existing valid blob calls `verify_identity_blob(obfuscated, sig, None)`. The `AttributeError` from `None.encode()` is raised outside the `try/except TypeError`, propagates out of `verify_identity_blob`, and is caught by `_read_identity_blob`'s broad `except Exception:`, returning `IDENTITY_STATUS_TAMPERED`. A player with a valid identity is permanently locked out of submission with no recovery.

The fix requires a None-secret guard at one of: `sign_identity_blob`, `_write_identity_blob`, `_read_identity_blob`, or `load_identity`. The submission signing in `main.py:98` already correctly handles this (`if secret else None`); the identity blob paths do not.

The three non-gap must-haves (identity location, obfuscation, server submission signing) are fully implemented and working. The test suite passes 117/117 (9 skipped) but has no None-secret coverage in `test_local_storage.py`.

---

_Verified: 2026-06-19_
_Verifier: Claude (gsd-verifier)_
