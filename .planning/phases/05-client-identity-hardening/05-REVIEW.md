---
phase: 05-client-identity-hardening
reviewed: 2026-06-19T00:00:00Z
depth: standard
files_reviewed: 17
files_reviewed_list:
  - .gitignore
  - api_service.py
  - build.py
  - cloud_functions/get_leaderboard/main.py
  - cloud_functions/submit_score/main.py
  - hmac_secret.example
  - leaderboard_crypto.py
  - local_storage.py
  - main.py
  - menu.py
  - paths.py
  - settings.py
  - tests/check_build_secret.py
  - tests/check_main_wiring.py
  - tests/test_api_service.py
  - tests/test_client_crypto.py
  - tests/test_local_storage.py
findings:
  critical: 2
  warning: 5
  info: 4
  total: 11
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-06-19
**Depth:** standard
**Files Reviewed:** 17
**Status:** issues_found

## Summary

Phase 5 hardens client identity: a consolidated obfuscated + HMAC-signed identity blob,
domain-separated file-integrity HMAC, fail-closed tamper detection, and a build-time
secret bake-in. The crypto primitives in `leaderboard_crypto.py` are well-constructed —
constant-time comparison via `hmac.compare_digest`, correct fail-closed guards on
non-string/non-ASCII signatures, byte-for-byte canonical-message parity with the server
verifier (test-proven), and correct domain separation between file and submission
signatures. The migration verify-before-delete ordering is correct, and `.gitignore`
correctly excludes the real secret and the baked module.

However, the `None`-secret path — which `main._load_hmac_secret` is **explicitly
documented to produce and support** ("dev runs without it still play") — is broken in two
directions and is the dominant concern. On a fresh launch with `secret=None`, the game
crashes at startup with an uncaught `AttributeError`; on a launch where a blob already
exists but `secret` resolves to `None`, the valid blob reads as permanently TAMPERED and
blocks all submission with no recovery. This is not a theoretical path: a shipped exe
whose `_baked_secret` import fails returns `None` from `_load_hmac_secret`, so both
failures are reachable in the production artifact. These are BLOCKERs against the phase's
own stated "graceful degrade / fully playable offline" contract.

The remaining findings are robustness and consistency issues: an unbounded leaderboard
render loop, an unhandled-KeyError leaderboard path, an obfuscation-key claim that is
weaker than advertised, and a couple of consistency gaps with the server contract.

## Critical Issues

### CR-01: `None` secret crashes the game at startup on fresh launch (fail-open contract broken)

**File:** `main.py:53-58`, `local_storage.py:165,184,207`, `leaderboard_crypto.py:103-107`
**Issue:** `_load_hmac_secret()` is documented to return `None` when no secret is
available ("Returns ``None`` if no secret is available — dev runs without it still play",
`main.py:23-24`). `main()` then calls `load_identity(secret)` with that `None`. On a
genuine first launch (no blob, no legacy files), `load_identity` reaches
`_write_identity_blob(fresh_machine_id, None, secret, blob_path)` (`local_storage.py:184`),
which calls `sign_identity_blob(obfuscated, None)`, which executes
`secret.encode("utf-8")` (`leaderboard_crypto.py:106`) on `None`. This raises an uncaught
`AttributeError: 'NoneType' object has no attribute 'encode'` and the game crashes before
the menu renders. Verified by direct execution:

```
$ load_identity(None, ...)  -> UNCAUGHT: AttributeError 'NoneType' object has no attribute 'encode'
```

This is reachable in the **shipped exe**, not just dev: per `_load_hmac_secret`, a frozen
build whose `import _baked_secret` fails (corrupt/missing baked module, PyInstaller
bundling miss) hits `except Exception: return None` (`main.py:30-31`) and returns `None`.
The result is a product that crashes on launch with no diagnostic.

**Fix:** Decide the `None`-secret contract and enforce it in one place. Either (a) make
the blob path tolerate `None` by deriving a deterministic local-only fallback key when no
HMAC secret exists (degrading signing, not crashing), or (b) make signing total against
`None`:

```python
# leaderboard_crypto.py
def sign_identity_blob(blob_bytes, secret):
    if secret is None:
        raise ValueError("sign_identity_blob requires a non-None secret")
    ...
```

and have `load_identity` / `save_initials` catch the missing-secret case explicitly and
return a defined degraded status rather than letting it bubble out of `main()`. Whichever
is chosen, add a test that `load_identity(None, ...)` does not raise.

### CR-02: Existing valid identity reads as permanently TAMPERED when secret resolves to `None` (unrecoverable submit lockout)

**File:** `local_storage.py:94-95`, `main.py:53,58-61,88-94`
**Issue:** `_read_identity_blob` calls `verify_identity_blob(obfuscated, sig, secret)`.
When `secret is None`, `verify_identity_blob` computes `sign_identity_blob(blob, None)`,
which raises inside the `try` only at `.encode` — but that call is *outside* the `try`
(`leaderboard_crypto.py:120` runs before the `try` at 121), so the `AttributeError`
propagates out of `verify_identity_blob`, is caught by the broad `except Exception` in
`_read_identity_blob` (`local_storage.py:99`), and is reported as `TAMPERED`. Verified:

```
read existing valid blob with None secret -> (None, None, 'tampered')
```

Consequently, any run where the secret legitimately resolves to `None` while a previously
valid blob exists (shipped exe loses `_baked_secret`; a dev deletes `hmac_secret.local`
between runs; env var unset) flips the player's good identity to TAMPERED. Per the
fail-closed model (D-05), a TAMPERED blob is **never auto-regenerated** and **blocks all
submission** (`main.py:88-94`) — so this is a permanent, unrecoverable lockout from the
leaderboard caused purely by a missing secret rather than actual tampering. This directly
contradicts the phase contract that the game "gracefully degrades" without a secret.

**Fix:** Treat "no secret available" as a distinct, recoverable state — not as tampering.
Short-circuit before verification:

```python
def _read_identity_blob(secret, path):
    if not os.path.exists(path):
        return (None, None, _STATUS_MISSING)
    if not secret:
        return (None, None, _STATUS_NO_SECRET)  # degraded, not tamper; do not block/regen
    ...
```

and handle `_STATUS_NO_SECRET` in `main()` as "play offline, do not submit, do not show a
tamper accusation." Add tests for both the existing-blob and fresh-launch `None`-secret
cases.

## Warnings

### WR-01: Unbounded leaderboard render loop can crash or overflow the screen

**File:** `menu.py:147-157`
**Issue:** `run_leaderboard` renders every entry returned by the API:
`for i, entry in enumerate(entries)` with `y = 180 + i * 50`. The client never slices to a
known cap. The server query uses `.limit(10)` (`cloud_functions/get_leaderboard/main.py:48,60`),
but the client trusts that bound implicitly. If the API ever returns more than ~14 rows
(misconfig, future change, or a malicious/compromised endpoint), entries render off-screen
or overlap unboundedly. Additionally, `dots = "." * (30 - len(rank) - len(initials) - len(score))`
(`menu.py:152`) can go negative when `initials`/`score` are long, producing an empty string
silently — minor, but the multiplication on a negative count is a latent formatting bug.

**Fix:** Clamp client-side: `for i, entry in enumerate(entries[:10])` and guard the dot
count with `max(0, ...)`.

### WR-02: Leaderboard entry access can `KeyError` on a malformed/hostile response

**File:** `menu.py:150-151`, `api_service.py:29-36`
**Issue:** `get_leaderboard` returns whatever `data.get("entries")` yields with no shape
validation. `run_leaderboard` then does `entry["initials"]` and `entry["score"]` directly
(`menu.py:150-151`). If the endpoint returns entries missing those keys (server bug,
partial outage returning the 500-shape `{"entries": [], "error": ...}` is fine, but any
non-conforming proxy is not), this raises `KeyError` inside the render loop, which is not
caught — crashing the menu. The offline path is handled (`entries is None`), but the
malformed-but-present path is not.

**Fix:** Use `.get` with defaults and skip malformed rows:

```python
initials = entry.get("initials")
score = entry.get("score")
if initials is None or score is None:
    continue
```

### WR-03: Obfuscation docstring/comment overstates protection ("not greppable")

**File:** `leaderboard_crypto.py:37,78-86`, `build.py:53-57`
**Issue:** Comments repeatedly claim the base64-over-XOR scheme makes the secret/identity
"not greppable" and that a "plain strings/grep of the artifact never surfaces the raw
secret." This is misleading: the XOR key is a committed module constant
(`OBFUSCATION_XOR_KEY`), so anyone with the (public) client source can trivially reverse
the baked secret from the artifact — it is encoding, not protection. The code itself is
honest in places ("NOT encryption", "only defeats casual reading"), but `build.py`'s
framing ("not a committed literal, and not greppable in the artifact") implies a security
property the design does not provide. A reviewer or future maintainer may rely on this and
ship the shared HMAC secret believing it is meaningfully protected in the exe, when in
fact the shared secret is fully recoverable by any user. This is a design-documentation
defect that affects threat-model decisions.

**Fix:** Correct the comments to state plainly that the baked secret is recoverable by any
user with the client binary, and that the obfuscation only stops casual `strings`. If the
threat model requires that the secret not be user-recoverable, the shared-HMAC-in-client
approach must be reconsidered (e.g., per-device keys / server-issued tokens) — but at
minimum the docs must not claim a guarantee the scheme cannot keep.

### WR-04: `de_obfuscate` accepts arbitrary attacker-controlled base64 without length/validation guard

**File:** `leaderboard_crypto.py:89-93`, `local_storage.py:96-97`
**Issue:** `de_obfuscate` does `base64.b64decode(blob_bytes)` with no `validate=True`. The
input here is only reached *after* a successful HMAC verify in `_read_identity_blob`
(`local_storage.py:94` gates `de_obfuscate` at line 96), so an attacker cannot reach it
without forging a signature — which mitigates the security impact. However,
`base64.b64decode` without `validate=True` silently discards non-alphabet characters,
which weakens the "exact round-trip" assumption the obfuscation contract relies on and can
mask corruption that should have been caught. Given the file-integrity HMAC is the real
control, this is a robustness/correctness concern rather than a vuln.

**Fix:** Use `base64.b64decode(blob_bytes, validate=True)` so malformed input raises
(caught and reported TAMPERED) instead of being silently coerced.

### WR-05: `save_initials` silently mints a NEW machine_id when the existing blob is TAMPERED

**File:** `local_storage.py:204-207`
**Issue:** `save_initials` reads the current blob and, if `status != IDENTITY_STATUS_OK or
not machine_id`, generates a fresh uuid4. This means: if the on-disk blob is TAMPERED,
`save_initials` does not refuse — it silently discards the (blocked) identity and writes a
brand-new valid identity with new initials. That is exactly the "auto-regen lets tampering
force a fresh slot" behavior the module docstring (`local_storage.py:9-12`) says the design
forbids. In normal flow `main()` never calls `save_initials` on a tampered identity
(the `initials is None` entry is gated behind `not identity_tampered`, `main.py:64`), so
this is not currently exploitable — but the helper itself violates its own stated
invariant and is a trap for any future caller.

**Fix:** Have `save_initials` refuse to overwrite a TAMPERED blob (raise or return a status)
rather than minting a fresh machine_id, mirroring the fail-closed contract:

```python
machine_id, _ini, status = _read_identity_blob(secret, blob_path)
if status == IDENTITY_STATUS_TAMPERED:
    return  # do not regenerate over a tampered blob (D-05)
if status != IDENTITY_STATUS_OK or not machine_id:
    machine_id = str(uuid.uuid4())
```

## Info

### IN-01: Migration adopts unvalidated legacy machine_id

**File:** `local_storage.py:162-180`
**Issue:** `_read_legacy_machine_id` returns any non-empty stripped string as the
machine_id and migration adopts it as-is. A hand-edited legacy `machine_id.txt` (the legacy
files were plaintext and user-writable, which is the whole reason for Phase 5) is migrated
verbatim into the new signed blob, laundering a user-chosen machine_id into a "valid"
signed identity. Low impact (machine_id is not a secret and the server keys on it), but
worth noting that migration trusts pre-Phase-5 plaintext.
**Fix:** Optionally validate the legacy machine_id shape (e.g., uuid4) before adopting, or
document that legacy machine_ids are trusted by design.

### IN-02: `api_service` swallows all exceptions into `None`, masking diagnostics

**File:** `api_service.py:26-27,35-36`
**Issue:** Both methods use `except Exception: return None`, which is correct for graceful
offline degradation but discards every failure cause (DNS, TLS, 4xx/5xx, JSON decode),
making field diagnosis impossible. Consider logging the exception (without leaking the URL
secret/secrets) at minimum.
**Fix:** `except Exception as e: print(f"leaderboard request failed: {type(e).__name__}")`
or route to a logger.

### IN-03: `de_obfuscate` import in `main.py` is only used for the baked secret path

**File:** `main.py:10,29`
**Issue:** `de_obfuscate` is imported at module top but used only inside the frozen branch.
Harmless, but a reader may expect it on the dev path too. Minor clarity note.
**Fix:** None required; optionally move usage comment to the import.

### IN-04: `build.py` does not clean up the generated `_baked_secret.py` after build

**File:** `build.py:68-81`
**Issue:** `_write_baked_module` writes `_baked_secret.py` (the obfuscated secret) next to
`main.py` and never removes it. It is gitignored, so it will not be committed, but it
persists on the operator's disk after every build, leaving a recoverable copy of the shared
secret (obfuscation is reversible — see WR-03) sitting in the working tree indefinitely.
**Fix:** Remove `_baked_secret.py` in a `finally` after the PyInstaller run, or document
that the operator must clean it up.

---

_Reviewed: 2026-06-19_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
