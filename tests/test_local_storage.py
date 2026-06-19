"""Tests for the Phase 5 consolidated identity blob store.

The legacy plaintext model (get_machine_id/get_initials/save_initials(initials, path))
is gone — identity is now one obfuscated + HMAC-signed blob. These tests cover the
blob round-trip, the fail-closed tamper/corrupt paths (D-05), missing-file fresh mint
(D-04), and migrate-then-remove with a verify-before-delete safety gate (D-04).
"""
import json
import os

import pytest

from local_storage import (
    _read_identity_blob,
    _write_identity_blob,
    load_identity,
    save_initials,
    IDENTITY_STATUS_OK,
    IDENTITY_STATUS_TAMPERED,
    IDENTITY_STATUS_NO_SECRET,
)

SECRET = "test-secret-key"


@pytest.fixture
def blob_path(tmp_path):
    return str(tmp_path / "identity.dat")


@pytest.fixture
def legacy_paths(tmp_path):
    return (
        str(tmp_path / "machine_id.txt"),
        str(tmp_path / "player_data.json"),
    )


# --- Round-trip ------------------------------------------------------------------


def test_blob_round_trip_returns_ok(blob_path):
    _write_identity_blob("m1", "BOB", SECRET, blob_path)
    machine_id, initials, status = _read_identity_blob(SECRET, blob_path)
    assert (machine_id, initials, status) == ("m1", "BOB", IDENTITY_STATUS_OK)


def test_blob_on_disk_is_not_human_readable(blob_path):
    _write_identity_blob("m1", "BOB", SECRET, blob_path)
    raw = open(blob_path, "rb").read()
    assert b"BOB" not in raw
    assert b"machine_id" not in raw


def test_save_initials_round_trip(blob_path):
    save_initials("CAT", SECRET, blob_path=blob_path)
    machine_id, initials, status = _read_identity_blob(SECRET, blob_path)
    assert status == IDENTITY_STATUS_OK
    assert initials == "CAT"
    assert machine_id  # fresh uuid4 minted on first save


def test_save_initials_preserves_machine_id(blob_path):
    save_initials("CAT", SECRET, blob_path=blob_path)
    first_mid = _read_identity_blob(SECRET, blob_path)[0]
    save_initials("DOG", SECRET, blob_path=blob_path)
    second_mid, second_ini, _ = _read_identity_blob(SECRET, blob_path)
    assert second_mid == first_mid
    assert second_ini == "DOG"


# --- Tamper / corrupt (D-05: one fail-closed path, never regenerate) -------------


def test_tampered_blob_returns_tampered(blob_path):
    _write_identity_blob("m1", "BOB", SECRET, blob_path)
    raw = bytearray(open(blob_path, "rb").read())
    raw[len(raw) // 2] ^= 0x01
    open(blob_path, "wb").write(bytes(raw))
    machine_id, initials, status = _read_identity_blob(SECRET, blob_path)
    assert status == IDENTITY_STATUS_TAMPERED
    # Must NOT regenerate a fresh identity.
    assert machine_id is None
    assert initials is None


def test_garbage_blob_returns_tampered_same_path(blob_path):
    open(blob_path, "wb").write(b"garbage-not-a-blob")
    machine_id, initials, status = _read_identity_blob(SECRET, blob_path)
    assert status == IDENTITY_STATUS_TAMPERED
    assert (machine_id, initials) == (None, None)


def test_wrong_secret_returns_tampered(blob_path):
    _write_identity_blob("m1", "BOB", SECRET, blob_path)
    _, _, status = _read_identity_blob("a-different-secret", blob_path)
    assert status == IDENTITY_STATUS_TAMPERED


# --- load_identity: missing → fresh mint -----------------------------------------


def test_load_identity_missing_mints_fresh(blob_path, legacy_paths):
    legacy_mid, legacy_pd = legacy_paths
    result = load_identity(
        SECRET,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["status"] == IDENTITY_STATUS_OK
    assert result["initials"] is None
    assert len(result["machine_id"]) == 36  # uuid4
    # The fresh blob is persisted.
    assert os.path.exists(blob_path)


def test_load_identity_tampered_blob_does_not_regenerate(blob_path, legacy_paths):
    legacy_mid, legacy_pd = legacy_paths
    _write_identity_blob("m1", "BOB", SECRET, blob_path)
    raw = bytearray(open(blob_path, "rb").read())
    raw[len(raw) // 2] ^= 0x01
    open(blob_path, "wb").write(bytes(raw))
    # Leave a legacy file lying around; tampered path must NOT touch it.
    open(legacy_mid, "w").write("legacy-mid")
    result = load_identity(
        SECRET,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["status"] == IDENTITY_STATUS_TAMPERED
    assert result["machine_id"] is None
    assert os.path.exists(legacy_mid)  # legacy untouched


# --- load_identity: migration ----------------------------------------------------


def test_load_identity_migrates_then_removes_legacy(blob_path, legacy_paths):
    legacy_mid, legacy_pd = legacy_paths
    open(legacy_mid, "w").write("legacy-machine-id")
    json.dump({"initials": "JAM"}, open(legacy_pd, "w"))

    result = load_identity(
        SECRET,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )

    # Migrated values returned with OK status.
    assert result["status"] == IDENTITY_STATUS_OK
    assert result["machine_id"] == "legacy-machine-id"
    assert result["initials"] == "JAM"

    # New blob exists and reads back equal.
    assert os.path.exists(blob_path)
    rb_mid, rb_ini, rb_status = _read_identity_blob(SECRET, blob_path)
    assert (rb_mid, rb_ini, rb_status) == (
        "legacy-machine-id",
        "JAM",
        IDENTITY_STATUS_OK,
    )

    # BOTH legacy files deleted after a successful read-back.
    assert not os.path.exists(legacy_mid)
    assert not os.path.exists(legacy_pd)


def test_migration_verifies_read_back_before_deleting_legacy(
    blob_path, legacy_paths, monkeypatch
):
    """The verify-read-back gate must run BEFORE legacy deletion (D-04 safety)."""
    legacy_mid, legacy_pd = legacy_paths
    open(legacy_mid, "w").write("legacy-machine-id")
    json.dump({"initials": "JAM"}, open(legacy_pd, "w"))

    import local_storage

    # Force the read-back to report TAMPERED so the equality gate fails.
    def fake_read(secret, path):
        if path == blob_path and os.path.exists(blob_path):
            return (None, None, IDENTITY_STATUS_TAMPERED)
        return (None, None, "missing")

    monkeypatch.setattr(local_storage, "_read_identity_blob", fake_read)

    result = local_storage.load_identity(
        SECRET,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )

    # Identity is not lost — migrated values still returned.
    assert result["machine_id"] == "legacy-machine-id"
    # Read-back failed → legacy files must SURVIVE (not deleted).
    assert os.path.exists(legacy_mid)
    assert os.path.exists(legacy_pd)


def test_load_identity_partial_legacy_machine_id_only(blob_path, legacy_paths):
    legacy_mid, legacy_pd = legacy_paths
    open(legacy_mid, "w").write("only-machine-id")
    # No player_data.json present.
    result = load_identity(
        SECRET,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["machine_id"] == "only-machine-id"
    assert result["initials"] is None  # prompt later
    assert result["status"] == IDENTITY_STATUS_OK


def test_load_identity_invalid_legacy_initials_become_none(blob_path, legacy_paths):
    legacy_mid, legacy_pd = legacy_paths
    open(legacy_mid, "w").write("mid-2")
    json.dump({"initials": "lowercase"}, open(legacy_pd, "w"))  # fails ^[A-Z]{3}$
    result = load_identity(
        SECRET,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["machine_id"] == "mid-2"
    assert result["initials"] is None
    assert result["status"] == IDENTITY_STATUS_OK


# --- No-secret graceful degrade (CR-01/CR-02 regression) -------------------------
# When _load_hmac_secret() returns None (dev with no hmac_secret.local, or a shipped
# exe where the baked-secret import failed), identity loading must NOT crash and must
# NOT misreport a valid blob as TAMPERED. It degrades to status NO_SECRET (play
# offline, do not submit) and never writes an unsigned blob.


def test_load_identity_no_secret_fresh_launch_does_not_crash(blob_path, legacy_paths):
    """CR-01: fresh launch with secret=None returns a usable identity, no crash."""
    legacy_mid, legacy_pd = legacy_paths
    result = load_identity(
        None,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["status"] == IDENTITY_STATUS_NO_SECRET
    assert result["initials"] is None
    assert len(result["machine_id"]) == 36  # in-session uuid4
    # No key to sign with → no unsigned blob written (would later read as TAMPERED).
    assert not os.path.exists(blob_path)


def test_load_identity_no_secret_existing_valid_blob_not_tampered(blob_path, legacy_paths):
    """CR-02: an existing valid blob read with secret=None is NOT a tamper accusation."""
    legacy_mid, legacy_pd = legacy_paths
    _write_identity_blob("m1", "BOB", SECRET, blob_path)
    result = load_identity(
        None,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["status"] == IDENTITY_STATUS_NO_SECRET
    assert result["machine_id"] == "m1"
    assert result["initials"] == "BOB"


def test_load_identity_no_secret_reads_legacy_without_deleting(blob_path, legacy_paths):
    legacy_mid, legacy_pd = legacy_paths
    open(legacy_mid, "w").write("legacy-machine-id")
    json.dump({"initials": "JAM"}, open(legacy_pd, "w"))
    result = load_identity(
        None,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["status"] == IDENTITY_STATUS_NO_SECRET
    assert result["machine_id"] == "legacy-machine-id"
    assert result["initials"] == "JAM"
    # Cannot sign a migrated blob without the secret → legacy files survive, no blob.
    assert os.path.exists(legacy_mid)
    assert os.path.exists(legacy_pd)
    assert not os.path.exists(blob_path)


def test_load_identity_no_secret_unreadable_blob_falls_back(blob_path, legacy_paths):
    """A corrupt blob with no secret degrades to a fresh in-session id, not a crash."""
    legacy_mid, legacy_pd = legacy_paths
    open(blob_path, "w").write("{ not valid json")
    result = load_identity(
        None,
        blob_path=blob_path,
        legacy_machine_id_path=legacy_mid,
        legacy_player_data_path=legacy_pd,
    )
    assert result["status"] == IDENTITY_STATUS_NO_SECRET
    assert len(result["machine_id"]) == 36


def test_save_initials_no_secret_is_noop(blob_path):
    """save_initials(initials, None) must not crash and must not write a blob."""
    save_initials("CAT", None, blob_path=blob_path)
    assert not os.path.exists(blob_path)
