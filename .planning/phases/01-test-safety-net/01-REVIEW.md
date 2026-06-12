---
phase: 01-test-safety-net
reviewed: 2026-06-11T00:00:00Z
depth: deep
files_reviewed: 13
files_reviewed_list:
  - game.py
  - harness/headless.py
  - harness/trace.py
  - harness/replay.py
  - harness/capture.py
  - harness/play_loop.py
  - tests/conftest.py
  - tests/test_ghost_micro.py
  - tests/test_submit_score.py
  - tests/test_get_leaderboard.py
  - tests/test_golden_traces.py
  - tests/test_determinism_guard.py
  - .github/workflows/ci.yml
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-06-11
**Depth:** deep
**Files Reviewed:** 13
**Status:** issues_found

## Summary

The `tick()` extraction in game.py is a clean verbatim lift — the diff confirms byte-identical logic, correct `for-else` soft-lock backstop in `run_scenario`, and proper `return_to_menu` handling (checked at the top of `run()`'s loop, so the refactor does not change when it fires). The test harness is well-structured. The main findings are in `submit_score/main.py`: one security gap (no format check on `machine_id` before it becomes a Firestore document ID), one type-strictness gap in the score validator (`bool` passes `isinstance(score, int)`), and two minor CI/test issues.

## Warnings

### WR-01: `machine_id` accepted as Firestore document ID without format validation

**File:** `cloud_functions/submit_score/main.py:47-48`
**Issue:** The only guard on `machine_id` is `if not machine_id` (non-empty). A value containing `/` is passed directly to `db.collection("leaderboard").document(machine_id)`. The Firebase Python SDK interprets a `/`-delimited path as a subcollection reference, so `machine_id = "abc/def"` writes to `leaderboard/abc/def` (a subcollection) rather than `leaderboard/abc`. A crafted `machine_id` can scatter writes into arbitrary subcollections of `leaderboard`, bypassing the one-document-per-machine model and polluting the collection tree.

This is exploitable by any caller that constructs the POST body directly (the function is unauthenticated).

**Fix:**
```python
import uuid

def _is_valid_machine_id(value: str) -> bool:
    """Accept only UUID4 strings (the format local_storage.py generates)."""
    try:
        uuid.UUID(value, version=4)
        return True
    except (ValueError, AttributeError):
        return False

# In submit_score(), replace the bare non-empty check:
if not machine_id or not _is_valid_machine_id(machine_id):
    return ({"success": False, "error": "Missing machine_id"}, 400, headers)
```

Alternatively, a simple regex: `re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$', machine_id, re.I)` pins the format to UUID4 without a new import.

---

### WR-02: `bool` values pass the `score` type guard (`isinstance(True, int)` is `True` in Python)

**File:** `cloud_functions/submit_score/main.py:51`
**Issue:** `isinstance(score, int)` returns `True` for Python `bool` values because `bool` is a subclass of `int`. A JSON payload with `"score": true` deserializes to Python `True` (value 1) and passes the range check `0 <= 1 <= 500_000`. The score is then written to Firestore as the Python boolean `True`, not the integer `1`. Firestore stores booleans and integers as distinct types, so a later `doc.to_dict().get("score", 0)` comparison (`score <= existing`) may behave unexpectedly when comparing an integer submission against a stored boolean.

**Fix:**
```python
# Replace line 51:
if not isinstance(score, int) or isinstance(score, bool) or score < 0 or score > MAX_SCORE:
    return ({"success": False, "error": "Invalid score"}, 400, headers)
```

The `isinstance(score, bool)` short-circuit explicitly rejects `True`/`False` before the range check.

---

## Info

### IN-01: `build_gif` has no guard against an empty `png_paths` list

**File:** `harness/capture.py:71`
**Issue:** `frames = [Image.open(p) for p in png_paths]` followed by `frames[0].save(...)` raises `IndexError` if `png_paths` is empty. The current callers (only the capture smoke test) guard with `assert len(png_paths) >= 2` before calling, so no test breaks today. But `build_gif` is a public API any future caller could invoke with an empty list, and the error message would be opaque (`list index out of range` with no context).

**Fix:**
```python
def build_gif(png_paths, out_path, duration_ms=33, loop=0):
    if not png_paths:
        raise ValueError("build_gif requires at least one PNG path")
    ...
```

---

### IN-02: CI installs `pyinstaller` (a build tool) on every test run

**File:** `.github/workflows/ci.yml:21`
**Issue:** `pip install -r requirements.txt` installs `pyinstaller` (a large native-dependency package) in the CI test job. `pyinstaller` is only needed for the `python build.py` exe-packaging step, not for running `pytest`. This adds unnecessary install time to every CI run and pulls in a large dependency tree that can cause version conflicts.

**Fix:** Split `requirements.txt` into a runtime (`requirements.txt`) and build-only (`requirements-build.txt`) manifest, or add a `[tool.pytest]` marker and exclude `pyinstaller` from the test step. At minimum, the CI job could install only `requirements-dev.txt` since it already re-pins `pygame`.

---

_Reviewed: 2026-06-11_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: deep_
