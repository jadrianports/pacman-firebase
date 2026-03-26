import json
import uuid
import os
from paths import data_path


MACHINE_ID_FILE = data_path("machine_id.txt")
PLAYER_DATA_FILE = data_path("player_data.json")


def get_machine_id(path=MACHINE_ID_FILE):
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read().strip()
    machine_id = str(uuid.uuid4())
    with open(path, "w") as f:
        f.write(machine_id)
    return machine_id


def get_initials(path=PLAYER_DATA_FILE):
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        return data.get("initials")
    except (json.JSONDecodeError, KeyError):
        return None


def save_initials(initials, path=PLAYER_DATA_FILE):
    with open(path, "w") as f:
        json.dump({"initials": initials}, f)
