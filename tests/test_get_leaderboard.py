"""TST-03 — get_leaderboard success/empty characterization tests.

Pins the leaderboard read path against the WORKING-TREE
cloud_functions/get_leaderboard/main.py (D-16), with firebase-admin mocked before
import via the conftest `leaderboard_module` fixture (D-15). No Firestore emulator
is ever stood up.

House style mirrors tests/test_api_service.py / tests/test_submit_score.py: build the
request, call the entrypoint, and assert on the returned (body, status, headers) tuple.

Mock seam: the conftest patches `firestore.client` with `return_value=mock_client` and
exposes that same object as `module._mock_client`, so `leaderboard_module._mock_client`
IS `db` directly. The source builds
`db.collection().order_by().limit(10).stream()` and iterates the result, so we drive
`db.collection.return_value.order_by.return_value.limit.return_value.stream.return_value`
to an iterable of mocked docs (each with `.to_dict.return_value`).
"""
from werkzeug.test import EnvironBuilder
from flask import Request


def make_request(method="GET"):
    """Build a real flask.Request (the type functions-framework hands the entrypoint)."""
    builder = EnvironBuilder(method=method)
    return Request(builder.get_environ())


def _make_doc(initials, score, extra=None):
    """A mocked Firestore snapshot whose .to_dict() carries the projected fields."""
    from unittest.mock import MagicMock

    doc = MagicMock()
    data = {"initials": initials, "score": score}
    if extra:
        data.update(extra)
    doc.to_dict.return_value = data
    return doc


def _stub_stream(leaderboard_module, docs):
    """Wire db.collection().order_by().limit().stream() to yield `docs`."""
    db = leaderboard_module._mock_client
    chain = db.collection.return_value.order_by.return_value.limit.return_value
    chain.stream.return_value = docs


def test_leaderboard_success_returns_entries(leaderboard_module):
    """Two docs from stream() -> 200 with entries in stream order, projected to {initials,score}."""
    _stub_stream(leaderboard_module, [
        _make_doc("JAM", 8000),
        _make_doc("BOB", 5000),
    ])
    body, status, _ = leaderboard_module.get_leaderboard(make_request())
    assert status == 200
    assert body == {"entries": [
        {"initials": "JAM", "score": 8000},
        {"initials": "BOB", "score": 5000},
    ]}


def test_leaderboard_projects_only_initials_and_score(leaderboard_module):
    """Extra stored fields (machine_id, updated_at) are dropped — only initials+score ship."""
    _stub_stream(leaderboard_module, [
        _make_doc("JAM", 8000, extra={"machine_id": "m1", "updated_at": "ts"}),
    ])
    body, status, _ = leaderboard_module.get_leaderboard(make_request())
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}


def test_leaderboard_empty_returns_empty_list(leaderboard_module):
    """stream() returns no docs -> 200 with an empty entries list."""
    _stub_stream(leaderboard_module, [])
    body, status, _ = leaderboard_module.get_leaderboard(make_request())
    assert status == 200
    assert body == {"entries": []}


def test_leaderboard_sets_cors_header(leaderboard_module):
    """The 200 response carries the permissive CORS header the entrypoint always sets."""
    _stub_stream(leaderboard_module, [])
    _, _, headers = leaderboard_module.get_leaderboard(make_request())
    assert headers == {"Access-Control-Allow-Origin": "*"}
