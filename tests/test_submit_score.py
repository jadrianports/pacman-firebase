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
import hashlib
import hmac
import json

from werkzeug.test import EnvironBuilder
from flask import Request


def _sign(machine_id, initials, score, secret="test-key"):
    """Compute the expected HMAC hexdigest exactly as leaderboard_crypto does, so
    the valid-signature tests are self-consistent (no hardcoded digest)."""
    msg = json.dumps(
        {"machine_id": machine_id, "initials": initials, "score": score},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()


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
    """score above MAX_SCORE (50000) -> 400 'Invalid score' (D-01 sanity ceiling)."""
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 50001})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid score"}


def test_score_at_max_accepted(submit_module):
    """score exactly at MAX_SCORE (50000) -> accepted 200 (boundary is inclusive)."""
    _stub_existing_doc(submit_module, stored_score=4000)
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 50000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body["success"] is True


# --- D-02 HMAC grace-period matrix (COMP-01) ----------------------------------------


def test_unsigned_accepted_when_grace(submit_module, monkeypatch):
    """No signature + REQUIRE_SIGNATURE unset/false -> accepted 200 (grace period)."""
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", "test-key")
    monkeypatch.delenv("REQUIRE_SIGNATURE", raising=False)
    _stub_existing_doc(submit_module, stored_score=4000)
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body["success"] is True


def test_unsigned_rejected_when_required(submit_module, monkeypatch):
    """No signature + REQUIRE_SIGNATURE=true -> rejected 401."""
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", "test-key")
    monkeypatch.setenv("REQUIRE_SIGNATURE", "true")
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert status in (401, 403)
    assert body["success"] is False


def test_invalid_signature_rejected_when_grace(submit_module, monkeypatch):
    """Forged signature + REQUIRE_SIGNATURE false -> rejected even in grace (invalid always 401)."""
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", "test-key")
    monkeypatch.setenv("REQUIRE_SIGNATURE", "false")
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000,
                        "signature": "deadbeef"})
    body, status, _ = submit_module.submit_score(req)
    assert status in (401, 403)
    assert body["success"] is False


def test_invalid_signature_rejected_when_required(submit_module, monkeypatch):
    """Forged signature + REQUIRE_SIGNATURE=true -> rejected 401."""
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", "test-key")
    monkeypatch.setenv("REQUIRE_SIGNATURE", "true")
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000,
                        "signature": "deadbeef"})
    body, status, _ = submit_module.submit_score(req)
    assert status in (401, 403)
    assert body["success"] is False


def test_valid_signature_accepted(submit_module, monkeypatch):
    """A correct HMAC over the test key -> accepted 200, even with enforcement on."""
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", "test-key")
    monkeypatch.setenv("REQUIRE_SIGNATURE", "true")
    _stub_existing_doc(submit_module, stored_score=4000)
    sig = _sign("m1", "ABC", 5000)
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000,
                        "signature": sig})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body["success"] is True


def test_non_int_score_returns_400(submit_module):
    """score that is a str (not isinstance int) -> 400 'Invalid score'."""
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": "100"})
    body, status, _ = submit_module.submit_score(req)
    assert status == 400
    assert body == {"success": False, "error": "Invalid score"}


def test_bool_score_returns_400(submit_module):
    """WR-01: score that is a JSON bool (true/false) -> 400 'Invalid score'.

    bool subclasses int, so isinstance(True, int) is True; the validator must
    reject bool explicitly so `"score": true` is not stored as a 1-point score.
    """
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": True})
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


# --- D-05 permanent initials + BOARD-01 weekly write (multi-doc transaction) --------


def _wire_multi_doc(submit_module, all_time=None, weekly=None):
    """Drive db.collection() per collection name so the all-time ('leaderboard') and
    weekly ('weekly') docs are distinct mocks with independent snapshots.

    `all_time` / `weekly` are the dicts to return from each doc's snapshot to_dict(),
    or None to mean the doc does not exist. Returns (all_time_doc_ref, weekly_doc_ref,
    weekly_doc_id_holder) so tests can inspect transaction.set / .delete call args. The
    weekly doc id is captured via the .document() call args.
    """
    from unittest.mock import MagicMock

    db = submit_module._mock_client

    def _make_collection(stored):
        coll = MagicMock()
        doc_ref = MagicMock()
        snap = doc_ref.get.return_value
        snap.exists = stored is not None
        snap.to_dict.return_value = stored or {}
        coll.document.return_value = doc_ref
        return coll, doc_ref

    leaderboard_coll, all_time_ref = _make_collection(all_time)
    weekly_coll, weekly_ref = _make_collection(weekly)

    def collection_side_effect(name):
        if name == "weekly":
            return weekly_coll
        return leaderboard_coll

    db.collection.side_effect = collection_side_effect
    return all_time_ref, weekly_ref, weekly_coll


def _all_time_set_calls(submit_module, all_time_ref):
    """Return the list of dicts written to the all-time doc via transaction.set."""
    db = submit_module._mock_client
    transaction = db.transaction.return_value
    return [
        call.args[1]
        for call in transaction.set.call_args_list
        if call.args and call.args[0] is all_time_ref
    ]


def test_keep_original_initials_on_later_submission(submit_module):
    """Existing all-time {BOB,4000}; submit {EVE,9000} -> store BOB (not EVE), score 9000."""
    all_time_ref, _weekly_ref, _ = _wire_multi_doc(
        submit_module,
        all_time={"initials": "BOB", "score": 4000},
        weekly={"initials": "BOB", "score": 4000},
    )
    req = make_request({"machine_id": "m1", "initials": "EVE", "score": 9000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body == {"success": True, "is_new_best": True}

    writes = _all_time_set_calls(submit_module, all_time_ref)
    assert writes, "expected an all-time transaction.set write"
    written = writes[-1]
    assert written["initials"] == "BOB"  # original kept (D-05)
    assert written["initials"] != "EVE"  # new initials never written
    assert written["score"] == 9000  # score still updates


def test_first_submission_locks_initials(submit_module):
    """No existing all-time doc; submit {ABC,1} -> initials written as ABC (lock)."""
    all_time_ref, _weekly_ref, _ = _wire_multi_doc(
        submit_module, all_time=None, weekly=None
    )
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 1})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body == {"success": True, "is_new_best": True}

    writes = _all_time_set_calls(submit_module, all_time_ref)
    assert writes, "expected an all-time transaction.set write"
    assert writes[-1]["initials"] == "ABC"


def test_weekly_doc_written_with_machine_week_id(submit_module):
    """A successful submit writes a weekly doc id '{machine_id}_{week_id}' carrying the
    locked initials, score, machine_id, and the week_id field."""
    import re as _re

    all_time_ref, weekly_ref, weekly_coll = _wire_multi_doc(
        submit_module, all_time=None, weekly=None
    )
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    body, status, _ = submit_module.submit_score(req)
    assert status == 200
    assert body["success"] is True

    # weekly doc id is built from machine_id + a Monday-date week_id (YYYY-MM-DD).
    doc_ids = [c.args[0] for c in weekly_coll.document.call_args_list if c.args]
    weekly_ids = [d for d in doc_ids if _re.match(r"^m1_\d{4}-\d{2}-\d{2}$", str(d))]
    assert weekly_ids, f"expected a weekly doc id like 'm1_YYYY-MM-DD', got {doc_ids}"

    # the weekly write carries the expected fields.
    db = submit_module._mock_client
    transaction = db.transaction.return_value
    weekly_writes = [
        c.args[1]
        for c in transaction.set.call_args_list
        if c.args and c.args[0] is weekly_ref
    ]
    assert weekly_writes, "expected a weekly transaction.set write"
    w = weekly_writes[-1]
    assert w["initials"] == "ABC"
    assert w["score"] == 5000
    assert w["machine_id"] == "m1"
    assert _re.match(r"^\d{4}-\d{2}-\d{2}$", str(w["week_id"]))


def test_lazy_prune_deletes_two_weeks_back(submit_module):
    """A successful submit issues a delete of the weekly doc two weeks back ({mid}_{week-2})."""
    import re as _re

    _all_time_ref, _weekly_ref, weekly_coll = _wire_multi_doc(
        submit_module, all_time=None, weekly=None
    )
    req = make_request({"machine_id": "m1", "initials": "ABC", "score": 5000})
    _body, status, _ = submit_module.submit_score(req)
    assert status == 200

    db = submit_module._mock_client
    transaction = db.transaction.return_value
    # at least one transaction.delete was issued (the lazy prune)
    assert transaction.delete.call_count >= 1, "expected a lazy-prune delete"
    # and a weekly doc id for a *different* (older) week than the current one was addressed
    doc_ids = [str(c.args[0]) for c in weekly_coll.document.call_args_list if c.args]
    week_ids = sorted({d for d in doc_ids if _re.match(r"^m1_\d{4}-\d{2}-\d{2}$", d)})
    assert len(week_ids) >= 2, f"expected current + stale week doc ids, got {week_ids}"
