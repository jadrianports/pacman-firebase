"""TST-03 / BOARD-02 — get_leaderboard scope-aware read characterization tests.

Pins the leaderboard read path against the WORKING-TREE
cloud_functions/get_leaderboard/main.py (D-16), with firebase-admin mocked before
import via the conftest `leaderboard_module` fixture (D-15). No Firestore emulator
is ever stood up.

House style mirrors tests/test_api_service.py / tests/test_submit_score.py: build the
request, call the entrypoint, and assert on the returned (body, status, headers) tuple.

Mock seam: the conftest patches `firestore.client` with `return_value=mock_client` and
exposes that same object as `module._mock_client`, so `leaderboard_module._mock_client`
IS `db` directly. The source now branches on `?scope=`:
  - scope=all  -> db.collection("leaderboard").order_by().limit(10).stream()
  - scope=week -> db.collection("weekly").where("week_id","==",cur).order_by().limit(10).stream()
    (default + unknown scope falls back to week)
We drive each chain by walking the matching MagicMock attribute path to an iterable of
mocked docs (each with `.to_dict.return_value`).
"""
from werkzeug.test import EnvironBuilder
from flask import Request


def make_request(method="GET", query_string=None):
    """Build a real flask.Request (the type functions-framework hands the entrypoint)."""
    builder = EnvironBuilder(method=method, query_string=query_string)
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
    """Wire the WEEKLY (default) chain: collection().where().order_by().limit().stream().

    The param-less / scope=week path queries the weekly collection with a where filter,
    so the default tests drive this chain.
    """
    db = leaderboard_module._mock_client
    chain = (
        db.collection.return_value
        .where.return_value
        .order_by.return_value
        .limit.return_value
    )
    chain.stream.return_value = docs


def _stub_all_stream(leaderboard_module, docs):
    """Wire the ALL-TIME chain: collection().order_by().limit().stream() (scope=all)."""
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


def test_options_preflight_returns_204_get(leaderboard_module):
    """OPTIONS preflight is unchanged: 204 + Access-Control-Allow-Methods: GET."""
    body, status, headers = leaderboard_module.get_leaderboard(make_request(method="OPTIONS"))
    assert status == 204
    assert headers["Access-Control-Allow-Methods"] == "GET"


def test_scope_all_queries_leaderboard(leaderboard_module):
    """?scope=all exercises the all-time leaderboard collection chain (D-08 retained)."""
    _stub_all_stream(leaderboard_module, [_make_doc("JAM", 8000)])
    body, status, _ = leaderboard_module.get_leaderboard(
        make_request(query_string="scope=all")
    )
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}
    # the all-time path queries the leaderboard collection, not weekly
    leaderboard_module._mock_client.collection.assert_called_with("leaderboard")


def test_scope_week_queries_weekly(leaderboard_module):
    """?scope=week exercises the weekly collection with a where('week_id',==,cur) filter."""
    from cloud_functions.get_leaderboard import leaderboard_crypto

    _stub_stream(leaderboard_module, [_make_doc("JAM", 8000)])
    body, status, _ = leaderboard_module.get_leaderboard(
        make_request(query_string="scope=week")
    )
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}
    db = leaderboard_module._mock_client
    db.collection.assert_called_with("weekly")
    # the where filter pins the current server-time week id
    db.collection.return_value.where.assert_called_with(
        "week_id", "==", leaderboard_crypto.current_week_id()
    )


def test_default_scope_is_week(leaderboard_module):
    """No scope param defaults to the weekly collection (confirmed decision: default week)."""
    _stub_stream(leaderboard_module, [_make_doc("JAM", 8000)])
    body, status, _ = leaderboard_module.get_leaderboard(make_request())
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}
    leaderboard_module._mock_client.collection.assert_called_with("weekly")


def test_garbage_scope_falls_back_to_week(leaderboard_module):
    """An unknown/garbage scope falls back to weekly without a 400."""
    _stub_stream(leaderboard_module, [_make_doc("JAM", 8000)])
    body, status, _ = leaderboard_module.get_leaderboard(
        make_request(query_string="scope=garbage")
    )
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}
    leaderboard_module._mock_client.collection.assert_called_with("weekly")


def test_weekly_path_projects_only_initials_and_score(leaderboard_module):
    """D-10: the weekly path also drops machine_id/week_id/updated_at — only initials+score ship."""
    _stub_stream(leaderboard_module, [
        _make_doc("JAM", 8000, extra={
            "machine_id": "m1", "week_id": "2026-06-15", "updated_at": "ts",
        }),
    ])
    body, status, _ = leaderboard_module.get_leaderboard(
        make_request(query_string="scope=week")
    )
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}


def test_scope_last_week_queries_weekly_with_previous_week(leaderboard_module):
    """BOARD-04: ?scope=last_week queries weekly filtered to previous_week_id(current_week_id())."""
    from cloud_functions.get_leaderboard import leaderboard_crypto

    _stub_stream(leaderboard_module, [_make_doc("JAM", 8000)])
    body, status, _ = leaderboard_module.get_leaderboard(
        make_request(query_string="scope=last_week")
    )
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}
    db = leaderboard_module._mock_client
    db.collection.assert_called_with("weekly")
    # the where filter pins the PREVIOUS server-time week id (last week's champ)
    db.collection.return_value.where.assert_called_with(
        "week_id", "==",
        leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id()),
    )


def test_scope_last_week_projects_only_initials_and_score(leaderboard_module):
    """D-10: the last_week path also drops machine_id/week_id/updated_at — only initials+score ship."""
    _stub_stream(leaderboard_module, [
        _make_doc("JAM", 8000, extra={
            "machine_id": "m1", "week_id": "2026-06-08", "updated_at": "ts",
        }),
    ])
    body, status, _ = leaderboard_module.get_leaderboard(
        make_request(query_string="scope=last_week")
    )
    assert status == 200
    assert body == {"entries": [{"initials": "JAM", "score": 8000}]}
