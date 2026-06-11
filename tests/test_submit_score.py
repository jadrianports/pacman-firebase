"""TST-03 — submit_score validator + best-score-upsert characterization tests.

Pins the EXISTING input validators (the V5 Input Validation control surface) and the
`is_new_best` upsert decision against the WORKING-TREE cloud_functions/submit_score/main.py
(D-16), with firebase-admin mocked before import via the conftest `submit_module` fixture
(D-15). No Firestore emulator is ever stood up.

House style mirrors tests/test_api_service.py: build the request, call the entrypoint, and
assert on the returned (body, status, headers) tuple.

@firestore.transactional spike (A2 / Pitfall 2) RESOLVED — decorator-works path:
A 30-min spike confirmed that, under the conftest firebase mock, the real
`@firestore.transactional` decorator drives the MagicMock transaction cleanly:
`db.transaction()` yields a MagicMock and `_update_score(transaction, doc_ref, ...)` runs,
with `doc_ref.get(transaction=...)` returning the mocked snapshot and `is_new_best`
reflecting the score comparison. So `cloud_functions.submit_score.main.firestore.transactional`
is NOT patched to a pass-through — the decorator is exercised as-shipped.

Note on the mock seam: the conftest patches `firestore.client` with
`return_value=mock_client` and exposes that same object as `module._mock_client`, so
`submit_module._mock_client` IS `db` directly (drive `.collection.return_value...`, not
`.return_value.collection...`).
"""
from werkzeug.test import EnvironBuilder
from flask import Request


def make_request(body, method="POST"):
    """Build a real flask.Request (the type functions-framework hands the entrypoint).

    `json=body` makes request.get_json(silent=True) return `body`; pass body=None for the
    Invalid-JSON path. functions-framework brings Flask/werkzeug transitively.
    """
    builder = EnvironBuilder(method=method, json=body)
    return Request(builder.get_environ())


# --- Validator 400 rejections (V5 Input Validation control surface) ---------------


def test_bad_initials_returns_400(submit_module):
    """initials not matching ^[A-Z]{3}$ -> 400 'Invalid initials'."""
    req = make_request({"machine_id": "m1", "initials": "ab", "score": 100})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid initials"}


def test_score_over_max_returns_400(submit_module):
    """score above MAX_SCORE (500000) -> 400 'Invalid score' (overflow guard)."""
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 500001})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid score"}


def test_non_int_score_returns_400(submit_module):
    """score that is a str (not isinstance int) -> 400 'Invalid score'."""
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": "100"})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid score"}


def test_negative_score_returns_400(submit_module):
    """score below 0 -> 400 'Invalid score' (lower-bound of the range guard)."""
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": -1})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid score"}


def test_missing_machine_id_returns_400(submit_module):
    """absent machine_id -> 400 'Missing machine_id' (checked before initials/score)."""
    req = make_request({"initials": "ABC", "score": 100})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Missing machine_id"}


def test_invalid_json_returns_400(submit_module):
    """empty/None body -> get_json(silent=True) is falsy -> 400 'Invalid JSON'."""
    req = make_request(None)
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid JSON"}


def test_valid_submission_sets_cors_header(submit_module):
    """A 400 still carries the permissive CORS header the entrypoint always sets."""
    req = make_request({"machine_id": "m1", "initials": "ab", "score": 100})
    _, _, headers = submit_module.submit_score(req)
    assert headers == {"Access-Control-Allow-Origin": "*"}


# --- is_new_best best-score upsert decision (mocked transaction/doc) ---------------


def _stub_existing_doc(submit_module, stored_score):
    """Wire db.collection().document().get() to return a snapshot with an existing score."""
    db = submit_module._mock_client
    snap = db.collection.return_value.document.return_value.get.return_value
    snap.exists = True
    snap.to_dict.return_value = {"score": stored_score}
    return snap


def test_is_new_best_true_when_higher(submit_module):
    """Submitted score strictly greater than the stored best -> is_new_best True, 200."""
    _stub_existing_doc(submit_module, stored_score=4000)
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body == {"success": True, "is_new_best": True}


def test_not_new_best_when_lower(submit_module):
    """Submitted score below the stored best -> is_new_best False, 200."""
    _stub_existing_doc(submit_module, stored_score=9000)
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body == {"success": True, "is_new_best": False}


def test_not_new_best_when_equal(submit_module):
    """Submitted score equal to the stored best -> is_new_best False (score <= stored)."""
    _stub_existing_doc(submit_module, stored_score=5000)
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body == {"success": True, "is_new_best": False}


def test_is_new_best_true_when_no_existing_doc(submit_module):
    """No existing doc (doc.exists False) -> always a new best, is_new_best True, 200."""
    db = submit_module._mock_client
    snap = db.collection.return_value.document.return_value.get.return_value
    snap.exists = False
    snap.to_dict.return_value = {}
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 1})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body == {"success": True, "is_new_best": True}
