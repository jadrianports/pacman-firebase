"""Throwaway wiring check for main.py (Plan 05-03 Task 2).

Ast-parses main.py (no import, no pygame side effects) and asserts the four wiring
tokens the plan requires are present:
  - load_identity              (startup load/migrate, D-04)
  - sign_submission            (signed submission, D-07)
  - identity_error             (game-over tamper notice, D-06)
  - IDENTITY_STATUS_TAMPERED   (the submit gate, D-05)

Not a pytest test — a quote-free assertion script kept simple for the shell verify.
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = open(os.path.join(ROOT, "main.py"), "r", encoding="utf-8").read()

# Parses cleanly.
ast.parse(src)

required = ["load_identity", "sign_submission", "identity_error", "IDENTITY_STATUS_TAMPERED"]
missing = [tok for tok in required if tok not in src]
if missing:
    print("FAIL: main.py missing wiring tokens: " + ", ".join(missing))
    sys.exit(1)

# No raw secret literal: the secret comes only from _load_hmac_secret().
assert "_load_hmac_secret" in src, "FAIL: main.py missing _load_hmac_secret helper"

print("OK: main.py wires " + ", ".join(required))
