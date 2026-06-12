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
        result = service.submit_score("machine-1", "JAM", 5000)
    assert result == {"success": True, "is_new_best": True}


def test_submit_score_not_new_best(service):
    response = _mock_response({"success": True, "is_new_best": False})
    with patch("api_service.urlopen", return_value=response):
        result = service.submit_score("machine-1", "JAM", 5000)
    assert result == {"success": True, "is_new_best": False}


def test_submit_score_network_error(service):
    with patch("api_service.urlopen", side_effect=Exception("timeout")):
        result = service.submit_score("machine-1", "JAM", 5000)
    assert result is None


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
