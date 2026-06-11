---
phase: 01-test-safety-net
plan: 06
subsystem: leaderboard
tags: [tests, cloud-functions, validators, characterization, security]
requires: ['01-01']
provides:
  - "tests/test_submit_score.py (submit_score validator 400s + is_new_best upsert pinned)"
  - "tests/test_get_leaderboard.py (get_leaderboard success/empty pinned via mocked stream)"
affects:
  - "cloud_functions/submit_score/main.py (READ ONLY — characterized, not modified)"
  - "cloud_functions/get_leaderboard/main.py (READ ONLY — characterized, not modified)"
tech-stack:
  added: []
  patterns:
    - "flask.Request via werkzeug EnvironBuilder, call HTTP entrypoint, assert (body, status, headers) tuple"
    - "firebase-admin mocked pre-import via conftest submit_module / leaderboard_module fixtures; module._mock_client IS db"
key-files:
  created:
    - tests/test_submit_score.py
    - tests/test_get_leaderboard.py
  modified: []
decisions:
  - "@firestore.transactional spike (A2): decorator-works path — the real decorator drives the MagicMock transaction cleanly under the conftest firebase mock; NO passthrough patch of main.firestore.transactional was needed."
  - "Tested the WORKING-TREE cloud_functions/*/main.py as-is (D-16); pre-existing uncommitted source mods left untouched."
metrics:
  duration: ~10m
  completed: 2026-06-11
requirements: [TST-03]
---

# Phase 01 Plan 06: Cloud-Function Validator + Upsert Tests Summary

Froze the submit_score input validators (the V5 Input Validation control surface) and the
is_new_best best-score upsert, plus the get_leaderboard read path, as characterization tests
against the working-tree cloud functions with firebase-admin fully mocked — no Firestore emulator.

## What Was Built

**tests/test_submit_score.py (11 tests)** — pre-existing untracked file, evaluated against the
plan's must_haves and acceptance criteria. It already fully satisfied Task 1, so it was kept as-is
(not rewritten) and committed to bring it under version control. Coverage:
- Validator 400s: bad initials `"ab"` (Invalid initials), score `500001` over MAX_SCORE=500000
  (Invalid score), non-int score `"100"` (Invalid score), negative score `-1` (Invalid score),
  missing machine_id (Missing machine_id), `None` body (Invalid JSON).
- CORS header assertion on a 400 response.
- is_new_best upsert via mocked `db.collection().document().get()`: True when higher, False when
  lower, False when equal, True when no existing doc (`.exists = False`).

**tests/test_get_leaderboard.py (4 tests, NEW)** — created for Task 2:
- Success: two docs from a mocked `query.stream()` -> 200 with entries in stream order.
- Projection: extra stored fields (machine_id, updated_at) dropped; only `{initials, score}` ship.
- Empty: `stream()` returns `[]` -> `({"entries": []}, 200, ...)`.
- CORS header assertion on the 200 response.

## Verification

```
./.venv/Scripts/python.exe -m pytest tests/test_submit_score.py tests/test_get_leaderboard.py -q
-> 15 passed

./.venv/Scripts/python.exe -m pytest -q
-> 41 passed
```

Both exit 0. Tests never reach real Firestore (firebase mocked pre-import in conftest; no
credential/network error).

## Decisions Made

**@firestore.transactional spike (A2 / Pitfall 2) — RESOLVED, decorator-works path.**
Under the conftest firebase mock, the real `@firestore.transactional` decorator drives the
MagicMock transaction cleanly: `db.transaction()` yields a MagicMock, `_update_score` runs,
`doc_ref.get(transaction=...)` returns the mocked snapshot, and `is_new_best` reflects the score
comparison. The decorator is exercised as-shipped — `cloud_functions.submit_score.main.firestore.transactional`
is NOT patched to a pass-through. (Documented in the test module docstring as well.)

**Mock seam note.** The conftest patches `firestore.client(return_value=mock_client)` and exposes
the same object as `module._mock_client`, so `_mock_client` IS `db` directly. Tests drive
`db.collection.return_value...` (not `.return_value.collection...`).

## Deviations from Plan

None affecting behavior. One notable handling detail: the plan's Task 1 expected to author
test_submit_score.py, but it already existed (untracked) and already met every must_have /
acceptance criterion. Per the orchestrator's pre-existing-files instruction, it was READ and
evaluated rather than blindly overwritten, confirmed passing, then committed unchanged. No new
test cases were needed beyond what the file already contained (it is in fact slightly richer than
the minimum — it adds negative-score and equal-score upsert cases).

## Surprises

- The pre-existing test_submit_score.py had already resolved the transactional spike (decorator-works)
  and documented it. Confirmed by running it green under the venv.
- No bugs surfaced in the working-tree cloud-fn source while pinning current behavior; the validators
  and upsert behave exactly as the plan describes.

## Self-Check: PASSED

- tests/test_submit_score.py — FOUND (committed b02f359)
- tests/test_get_leaderboard.py — FOUND (committed 29530ec)
- cloud_functions/submit_score/main.py — unmodified by this plan (only pre-existing mods present)
- cloud_functions/get_leaderboard/main.py — unmodified by this plan (only pre-existing mods present)
