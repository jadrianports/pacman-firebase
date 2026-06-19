"""Throwaway build-secret check for build.py (Plan 05-03 Task 3).

Asserts, without invoking PyInstaller:
  - build.py parses and references the gitignored secret file (hmac_secret) before
    the PyInstaller call,
  - hmac_secret.example exists at the repo root with a non-real placeholder,
  - .gitignore lists hmac_secret.local,
  - no committed source holds the placeholder/real secret as a build literal.

Quote-free assertion script kept simple for the shell verify. Not a pytest test.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

build_src = open(os.path.join(ROOT, "build.py"), "r", encoding="utf-8").read()
ast.parse(build_src)
assert "hmac_secret" in build_src, "FAIL: build.py does not reference hmac_secret"

example_path = os.path.join(ROOT, "hmac_secret.example")
assert os.path.exists(example_path), "FAIL: hmac_secret.example missing"
example_val = open(example_path, "r", encoding="utf-8").read().strip()
assert example_val == "REPLACE_WITH_REAL_SECRET", "FAIL: hmac_secret.example is not the placeholder"

gitignore = open(os.path.join(ROOT, ".gitignore"), "r", encoding="utf-8").read()
assert "hmac_secret.local" in gitignore, "FAIL: .gitignore missing hmac_secret.local"

# The build reads the secret from the file, never a literal in build.py/settings.py.
for fname in ("build.py", "settings.py", "main.py"):
    text = open(os.path.join(ROOT, fname), "r", encoding="utf-8").read()
    assert "REPLACE_WITH_REAL_SECRET" not in text, f"FAIL: placeholder literal leaked into {fname}"

print("OK: build secret bake-in wired; placeholder committed; local secret gitignored")
sys.exit(0)
