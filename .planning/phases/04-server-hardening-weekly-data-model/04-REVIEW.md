---
phase: 04-server-hardening-weekly-data-model
reviewed: 2026-06-19T00:00:00Z
depth: standard
files_reviewed: 8
files_reviewed_list:
  - cloud_functions/submit_score/main.py
  - cloud_functions/submit_score/leaderboard_crypto.py
  - cloud_functions/get_leaderboard/main.py
  - cloud_functions/get_leaderboard/leaderboard_crypto.py
  - tests/test_leaderboard_crypto.py
  - tests/test_submit_score.py
  - tests/test_get_leaderboard.py
  - cloud_functions/DEPLOY.md
findings:
  critical: 1
  warning: 5
  info: 3
  total: 9
status: issues_found
---

# Phase 4: Code Review Report

**Reviewed:** 2026-06-19T00:00:00Z
**Depth:** standard
**Files Reviewed:** 8
**Status:** issues_found

## Summary

Reviewed the Phase 4 server-hardening work: the HMAC grace-period gate and weekly
data-model changes in `submit_score`, the scope-aware read in `get_leaderboard`, the
shared `leaderboard_crypto` helper (byte-identical in both function dirs — confirmed
via `cmp`, no drift), and the three new test modules plus the deploy doc.

The reads-before-writes transaction invariant, the D-05 locked-initials behavior, the
projection-to-`{initials, score}` privacy boundary, the constant-time compare, the
call-time secret read, and the grace matrix are all implemented as described and are
backed by tests. No real secret is committed in `DEPLOY.md`.

The dominant concern is a cluster of **uncaught-exception paths in the signature gate
that run OUTSIDE the entrypoint's `try` block** (`submit_score/main.py` lines 120-128,
`try` starts at line 130). Three independently reachable, attacker-controlled inputs
turn an intended `401 Invalid signature` into an unhandled `500`: a non-string
`signature` value, a non-ASCII string `signature`, and a missing secret env var. These
are remotely triggerable from the public unauthenticated endpoint. There is also a
validation gap (JSON `true`/`false` accepted as `score`) and a single-bad-doc failure
mode in `get_leaderboard`.

## Critical Issues

### CR-01: Signature verification crashes (uncaught 500) on attacker-controlled input, outside the try block

**File:** `cloud_functions/submit_score/main.py:127` and `cloud_functions/submit_score/leaderboard_crypto.py:48-50`

**Issue:** The signature gate at lines 120-128 runs **before** the `try:` at line 130, so any exception it raises is unhandled by the entrypoint and surfaces as an opaque framework `500` (and the intended `401 Invalid signature` never happens). Three reachable inputs on the public, `--allow-unauthenticated` endpoint trigger this — all verified empirically:

1. **Non-string `signature`.** `provided_sig or ""` returns the value unchanged when it is a non-empty non-string (e.g. `"signature": ["x"]`, `123`, `{"a":1}`, or `true`). `hmac.compare_digest(expected, ["x"])` then raises `TypeError: unsupported operand types ... 'str' and 'list'`.
2. **Non-ASCII string `signature`.** `hmac.compare_digest("…hex…", "naïve")` raises `TypeError: comparing strings with non-ASCII characters is not supported`.
3. **Missing secret.** `os.environ["LEADERBOARD_HMAC_SECRET"]` (subscript, not `.get`) raises `KeyError` whenever a `signature` IS supplied but the env var is unset/misconfigured. A misconfigured deploy turns every signed request into a 500 instead of failing closed with a clear signal.

Net effect: a forged/malformed signature that should deterministically yield `401` instead yields `500`, and a single crafted request is a trivial DoS / fingerprinting vector against the anti-cheat path. Because it is uncaught, behavior also depends on functions_framework's default error rendering (risk of stack-trace exposure).

**Fix:** Make `verify_signature` total — coerce/validate the provided signature to a string and treat a missing or wrong-typed secret as a hard failure-closed, and keep the gate inside a guard so any residual error becomes a 401, never a 500:

```python
# leaderboard_crypto.py
def verify_signature(machine_id, initials, score, provided_sig):
    if not isinstance(provided_sig, str):
        return False  # non-string sig can never match a hex digest
    try:
        secret = os.environ["LEADERBOARD_HMAC_SECRET"].encode("utf-8")
    except KeyError:
        return False  # fail closed: no secret -> no valid signature
    expected = hmac.new(
        secret, canonical_message(machine_id, initials, score), hashlib.sha256
    ).hexdigest()
    try:
        return hmac.compare_digest(expected, provided_sig)
    except TypeError:
        return False  # non-ASCII / non-comparable sig
```

(The two copies must stay byte-identical — update both, then the drift-guard test still passes.) Optionally also wrap the signature branch in `submit_score` so any future helper bug degrades to 401, not 500.

## Warnings

### WR-01: JSON booleans accepted as `score` (validation bypass of the int type check)

**File:** `cloud_functions/submit_score/main.py:107`

**Issue:** `isinstance(score, int)` is `True` for `bool`, so `"score": true` passes validation (`0 <= True <= 50000`). It is then written to Firestore as `True` and signed as `true` in the canonical message. A client can submit a "score" of `true` (== 1) and it is accepted as a legitimate integer score, polluting the data model with a boolean.

**Fix:** Exclude `bool` explicitly:
```python
if isinstance(score, bool) or not isinstance(score, int) or score < 0 or score > MAX_SCORE:
    return ({"success": False, "error": "Invalid score"}, 400, headers)
```

### WR-02: One malformed leaderboard doc fails the entire response

**File:** `cloud_functions/get_leaderboard/main.py:63`

**Issue:** `data["initials"]` / `data["score"]` use direct subscript inside the per-doc loop. Any single stored doc missing `initials` or `score` (e.g. a partially-written or legacy row) raises `KeyError`, which the outer `except` turns into a blanket `500` with an empty `entries` list — one bad row takes down the whole board for every reader.

**Fix:** Project defensively and skip incomplete rows:
```python
for d in docs:
    data = d.to_dict()
    if "initials" in data and "score" in data:
        entries.append({"initials": data["initials"], "score": data["score"]})
```

### WR-03: `machine_id` accepted with no format/length validation

**File:** `cloud_functions/submit_score/main.py:99,103-104,137-139`

**Issue:** `machine_id` is only checked for truthiness, then concatenated into Firestore document IDs (`f"{machine_id}_{week_id}"`) and stored as a field. An attacker controls this value entirely. While Firestore document IDs are not SQL, unvalidated values can contain `/` (path segment injection into the document path), be excessively long (Firestore 1500-byte key limit → uncaught 500 in the transaction), or collide with the `{machine_id}_{week_id}` weekly-key scheme by embedding `_YYYY-MM-DD` to forge/overwrite another machine's weekly doc id. Since `machine_id` also keys the all-time board and the locked initials, this is an identity/anti-cheat surface that currently has zero input constraints.

**Fix:** Validate `machine_id` against an expected shape before use, e.g. a UUID/hex pattern:
```python
if not re.match(r"^[A-Za-z0-9-]{8,64}$", machine_id):
    return ({"success": False, "error": "Invalid machine_id"}, 400, headers)
```

### WR-04: CORS `Access-Control-Allow-Origin: *` on a state-mutating, soon-to-be-authenticated endpoint

**File:** `cloud_functions/submit_score/main.py:88,93` and `cloud_functions/get_leaderboard/main.py:24,29`

**Issue:** Both endpoints return a wildcard `Access-Control-Allow-Origin: *`. For the read endpoint this is acceptable. For `submit_score` — a write endpoint that the HMAC scheme is specifically meant to protect — a wildcard origin lets any web page POST scores cross-origin. The HMAC secret is the real gate, but during the documented grace window (`REQUIRE_SIGNATURE=false`) unsigned writes are accepted, so wildcard CORS plus grace means any origin can write unsigned scores from a browser. Worth an explicit decision rather than a default.

**Fix:** If browser clients are not a target (this is a PyGame/exe client), drop the CORS headers on `submit_score` entirely, or restrict `Allow-Origin` to known origins. At minimum, document that wildcard CORS on the write path is intentional for the grace window.

### WR-05: `get_leaderboard` parses but never uses `scope` errors; weekly index dependency is a silent hard failure

**File:** `cloud_functions/get_leaderboard/main.py:51-57,65-67`

**Issue:** The weekly query requires the composite index `week_id ASC, score DESC` (documented in DEPLOY.md Step 5). If the index is missing or still building, `query.stream()` raises and the `except` returns a generic `{"entries": [], "error": "Failed to fetch leaderboard"}` `500`. Because `scope=week` is the **default**, every param-less reader silently gets an empty board with an opaque error until an operator notices — there is no distinction between "no scores this week" (empty list, 200) and "index not ready" (should be a distinguishable server error). The blanket `except Exception` masks the specific failure class.

**Fix:** Let the caught exception's message be logged (already done) but consider distinguishing the missing-index/`FailedPrecondition` case in logs, and ensure monitoring/alerting covers the 500 path so a not-yet-`Enabled` index does not silently degrade the default board.

## Info

### IN-01: Misleading docstring — `verify_signature` "a missing signature compares against '' and fails"

**File:** `cloud_functions/submit_score/leaderboard_crypto.py:46` (and identical copy)

**Issue:** The docstring claims a missing signature "compares against `''` and fails" implying robustness, but as shown in CR-01 the `provided_sig or ""` guard only handles `None`/falsy values — a non-string truthy signature bypasses it and raises. Update the docstring when fixing CR-01 so the contract matches behavior.

**Fix:** After the CR-01 fix, document the actual contract: "non-string, non-ASCII, or missing-secret inputs all fail closed (return False)."

### IN-02: `previous_week_id` is called but never validated against malformed `week_id`

**File:** `cloud_functions/submit_score/main.py:132-135`, `leaderboard_crypto.py:67-70`

**Issue:** `previous_week_id` does `datetime.strptime(week_id, "%Y-%m-%d")`. The input always comes from `current_week_id()` (server-generated, well-formed), so this is safe today. It is flagged only as a latent foot-gun: if a future caller ever passes a client-derived week id, `strptime` raises `ValueError`. Not exploitable as written.

**Fix:** No change required now; note the precondition in the docstring ("`week_id` must be a server-generated `%Y-%m-%d` string").

### IN-03: Duplicated `_sign` helper across two test modules (acceptable, noted for drift)

**File:** `tests/test_leaderboard_crypto.py:28-37` and `tests/test_submit_score.py:32-41`

**Issue:** The HMAC `_sign` helper is copy-pasted into both test files with the same hardcoded `secret="test-key"`. This mirrors the intentional source-level duplication of `leaderboard_crypto.py`, so it is consistent with the project's Gen2 constraint, but the test helpers have no drift guard (unlike the source, which has `test_function_dir_copies_are_byte_identical`). If the canonical-message kwargs ever change, one copy could be updated and the other missed.

**Fix:** Optional — extract `_sign` to a shared test util, or accept the duplication as deliberate. Low priority.

---

_Reviewed: 2026-06-19T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
