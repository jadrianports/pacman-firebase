"""Tests for the client-side leaderboard_crypto module (Phase 5 Plan 01).

This is the loop-closing test suite: the client signs a submission and the REAL
Phase 4 server `verify_signature` (used here as an in-test oracle) accepts it,
proving the client wire-format mirrors the server byte-for-byte without a live
deploy (success criterion 4). It also covers the two new client primitives:
reversible obfuscation (IDENT-02 / D-10) and the domain-separated file-integrity
HMAC (IDENT-03 / D-08).

Env note: tests/conftest.py does NOT patch environment variables, so the oracle
tests set LEADERBOARD_HMAC_SECRET via monkeypatch.setenv (the server's
verify_signature reads the secret from os.environ at call time).
"""

# CLIENT module under test (repo-root copy created by this plan).
from leaderboard_crypto import (
    canonical_message,
    de_obfuscate,
    obfuscate,
    sign_identity_blob,
    sign_submission,
    verify_identity_blob,
)

# SERVER oracle (the real Phase 4 verifier + its canonical_message).
from cloud_functions.submit_score.leaderboard_crypto import (
    canonical_message as server_canonical_message,
    verify_signature as server_verify_signature,
)

TEST_SECRET = "test-key"

# The locked wire bytes (from tests/test_leaderboard_crypto.py:44).
LOCKED_BYTES = b'{"initials":"BOB","machine_id":"m1","score":5000}'


# --- canonical_message (server-contract mirror) ------------------------------

def test_client_canonical_matches_server():
    """Client canonical bytes == server canonical bytes == the locked literal."""
    client = canonical_message("m1", "BOB", 5000)
    server = server_canonical_message("m1", "BOB", 5000)
    assert client == server == LOCKED_BYTES


def test_canonical_message_returns_bytes():
    assert isinstance(canonical_message("m1", "BOB", 5000), bytes)


def test_canonical_message_score_int_vs_str_differ():
    """Passing the score as a string yields a different canonical message than
    passing the int (proves the int-stays-int contract -- D-07)."""
    assert canonical_message("m1", "BOB", 5000) != canonical_message("m1", "BOB", "5000")


# --- sign_submission: THE loop-closing oracle test ---------------------------

def test_client_signature_passes_server_verifier(monkeypatch):
    """Success criterion 4: a CLIENT signature over a known submission is accepted
    by the REAL server verify_signature with the shared test secret."""
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", TEST_SECRET)
    sig = sign_submission("m1", "BOB", 5000, TEST_SECRET)
    assert server_verify_signature("m1", "BOB", 5000, sig) is True


def test_lifted_submission_sig_rejected_for_other_machine(monkeypatch):
    """machine_id binding (D-03/D-07): a client sig for m1 must NOT verify for m2."""
    monkeypatch.setenv("LEADERBOARD_HMAC_SECRET", TEST_SECRET)
    sig_for_m1 = sign_submission("m1", "BOB", 5000, TEST_SECRET)
    assert server_verify_signature("m2", "BOB", 5000, sig_for_m1) is False


def test_sign_submission_int_vs_str_score_differ():
    """A submission signed over the int 5000 differs from one over the str "5000"."""
    assert sign_submission("m1", "BOB", 5000, TEST_SECRET) != sign_submission(
        "m1", "BOB", "5000", TEST_SECRET
    )


# --- obfuscation (IDENT-02 / D-10) -------------------------------------------

def test_obfuscation_round_trip():
    payload = b'{"machine_id":"m1","initials":"BOB"}'
    assert de_obfuscate(obfuscate(payload)) == payload


def test_obfuscated_not_human_readable():
    """The obfuscated form must not contain the plaintext substrings (not greppable)."""
    payload = b'{"machine_id":"m1","initials":"BOB"}'
    blob = obfuscate(payload)
    assert b"BOB" not in blob
    assert b"machine_id" not in blob


def test_obfuscation_round_trip_empty():
    assert de_obfuscate(obfuscate(b"")) == b""


# --- file-integrity HMAC (IDENT-03 / D-08) -----------------------------------

def test_file_sig_not_interchangeable_with_submission_sig():
    """Domain separation (D-08): a file-integrity sig and a submission sig over the
    same conceptual bytes are NOT equal -- their message spaces are disjoint."""
    canonical = canonical_message("m1", "BOB", 5000)
    file_sig = sign_identity_blob(canonical, TEST_SECRET)
    submission_sig = sign_submission("m1", "BOB", 5000, TEST_SECRET)
    assert file_sig != submission_sig


def test_verify_identity_blob_valid():
    blob = b'{"machine_id":"m1","initials":"BOB"}'
    sig = sign_identity_blob(blob, TEST_SECRET)
    assert verify_identity_blob(blob, sig, TEST_SECRET) is True


def test_verify_identity_blob_tampered_sig():
    blob = b'{"machine_id":"m1","initials":"BOB"}'
    assert verify_identity_blob(blob, "deadbeef", TEST_SECRET) is False


def test_verify_identity_blob_non_string_sig_returns_false():
    """Fail-closed: a non-string sig returns False, never raises (mirrors CR-01)."""
    blob = b'{"machine_id":"m1","initials":"BOB"}'
    for bad_sig in (123, ["x"], True, {"a": 1}, None):
        assert verify_identity_blob(blob, bad_sig, TEST_SECRET) is False


def test_verify_identity_blob_non_ascii_sig_returns_false():
    """Fail-closed: a non-ASCII string sig returns False, never raises."""
    blob = b'{"machine_id":"m1","initials":"BOB"}'
    assert verify_identity_blob(blob, "naïve", TEST_SECRET) is False


def test_verify_identity_blob_tampered_blob():
    """A signature over the original blob must not verify a mutated blob."""
    blob = b'{"machine_id":"m1","initials":"BOB"}'
    sig = sign_identity_blob(blob, TEST_SECRET)
    tampered = b'{"machine_id":"m1","initials":"EVE"}'
    assert verify_identity_blob(tampered, sig, TEST_SECRET) is False
