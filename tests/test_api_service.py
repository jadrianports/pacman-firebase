import json
from unittest.mock import patch, MagicMock
import pytest
from api_service import ApiService


@pytest.fixture
def service():
    return ApiService("https://fake-submit.run.app", "https://fake-leaderboard.run.app")


def _mock_response(data, status=200):
    mock = MagicMock()
    mock.status = status
    mock.read.return_value = json.dumps(data).encode()
    mock.__enter__ = lambda s: s
    mock.__exit__ = MagicMock(return_value=False)
    return mock


def test_submit_score_new_best(service):
    response = _mock_response({"success": True, "is_new_best": True})
    with patch("api_service.urlopen", return_value=response):
        result = service.submit_score("machine-1", "JAM", 5000, signature="abc123")
    assert result == {"success": True, "is_new_best": True}


def test_submit_score_not_new_best(service):
    response = _mock_response({"success": True, "is_new_best": False})
    with patch("api_service.urlopen", return_value=response):
        result = service.submit_score("machine-1", "JAM", 5000, signature="abc123")
    assert result == {"success": True, "is_new_best": False}


def test_submit_score_network_error(service):
    with patch("api_service.urlopen", side_effect=Exception("timeout")):
        result = service.submit_score("machine-1", "JAM", 5000, signature="abc123")
    assert result is None


def test_submit_score_sends_signature_field(service):
    """The POST body carries the signature in the locked "signature" field, and
    score stays an int (the signature was computed over the int)."""
    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode())
        return _mock_response({"success": True, "is_new_best": False})

    with patch("api_service.urlopen", side_effect=_fake_urlopen):
        service.submit_score("machine-1", "JAM", 5000, signature="deadbeef")

    body = captured["body"]
    assert body["signature"] == "deadbeef"
    assert body["machine_id"] == "machine-1"
    assert body["initials"] == "JAM"
    assert body["score"] == 5000
    assert isinstance(body["score"], int)


def test_submit_score_signature_defaults_to_none(service):
    """Without a signature the body sends null (server grace-accepts during the
    grace period)."""
    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["body"] = json.loads(req.data.decode())
        return _mock_response({"success": True, "is_new_best": False})

    with patch("api_service.urlopen", side_effect=_fake_urlopen):
        service.submit_score("machine-1", "JAM", 5000)

    assert captured["body"]["signature"] is None


def test_get_leaderboard_success(service):
    entries = [{"initials": "JAM", "score": 8000}, {"initials": "BOB", "score": 5000}]
    response = _mock_response({"entries": entries})
    with patch("api_service.urlopen", return_value=response):
        result = service.get_leaderboard()
    assert result == entries


def test_get_leaderboard_empty(service):
    response = _mock_response({"entries": []})
    with patch("api_service.urlopen", return_value=response):
        result = service.get_leaderboard()
    assert result == []


def test_get_leaderboard_network_error(service):
    with patch("api_service.urlopen", side_effect=Exception("timeout")):
        result = service.get_leaderboard()
    assert result is None


def test_get_leaderboard_sends_scope_param(service):
    """A truthy scope is urlencode'd into the query string (escaped, not
    hand-concatenated), so the server returns that specific board."""
    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["url"] = req.get_full_url()
        return _mock_response({"entries": []})

    with patch("api_service.urlopen", side_effect=_fake_urlopen):
        service.get_leaderboard(scope="last_week")
    assert "scope=last_week" in captured["url"]

    with patch("api_service.urlopen", side_effect=_fake_urlopen):
        service.get_leaderboard(scope="all")
    assert "scope=all" in captured["url"]


def test_get_leaderboard_no_scope_omits_param(service):
    """No scope → no query param → URL is the bare base so the server defaults
    to the current week."""
    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["url"] = req.get_full_url()
        return _mock_response({"entries": []})

    with patch("api_service.urlopen", side_effect=_fake_urlopen):
        service.get_leaderboard()
    assert captured["url"] == service.leaderboard_url
    assert "scope" not in captured["url"]


def test_get_leaderboard_passes_timeout(service):
    """The timeout kwarg threads into urlopen; default stays 10, the launch
    banner can pass a short value."""
    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured["timeout"] = timeout
        return _mock_response({"entries": []})

    with patch("api_service.urlopen", side_effect=_fake_urlopen):
        service.get_leaderboard(timeout=2)
    assert captured["timeout"] == 2

    with patch("api_service.urlopen", side_effect=_fake_urlopen):
        service.get_leaderboard()
    assert captured["timeout"] == 10
