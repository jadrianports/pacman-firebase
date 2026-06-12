import json
import os
import pytest
from local_storage import get_machine_id, get_initials, save_initials


@pytest.fixture
def temp_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_get_machine_id_creates_file_on_first_call(temp_dir):
    machine_id = get_machine_id(str(temp_dir / "machine_id.txt"))
    assert len(machine_id) == 36  # UUID format: 8-4-4-4-12
    assert os.path.exists(temp_dir / "machine_id.txt")


def test_get_machine_id_returns_same_id_on_second_call(temp_dir):
    path = str(temp_dir / "machine_id.txt")
    first = get_machine_id(path)
    second = get_machine_id(path)
    assert first == second


def test_get_initials_returns_none_when_no_file(temp_dir):
    result = get_initials(str(temp_dir / "player_data.json"))
    assert result is None


def test_save_and_get_initials(temp_dir):
    path = str(temp_dir / "player_data.json")
    save_initials("JAM", path)
    assert get_initials(path) == "JAM"


def test_save_initials_overwrites(temp_dir):
    path = str(temp_dir / "player_data.json")
    save_initials("JAM", path)
    save_initials("BOB", path)
    assert get_initials(path) == "BOB"
