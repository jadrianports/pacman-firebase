import os

USERNAME_FILE = "username.txt"

def get_username():
    """Returns username if saved, otherwise None."""
    if os.path.exists(USERNAME_FILE):
        with open(USERNAME_FILE, "r") as f:
            return f.read().strip()
    return None


def save_username(name):
    """Save username to file."""
    with open(USERNAME_FILE, "w") as f:
        f.write(name.strip())
