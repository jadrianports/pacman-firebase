"""Client identity storage (Phase 5).

Identity is a SINGLE obfuscated + HMAC-signed blob (D-02) stored under
``%LOCALAPPDATA%\\PacMan\\identity.dat`` (D-01), not the two legacy plaintext files
(``machine_id.txt`` / ``player_data.json``). The blob holds ``{machine_id, initials}``
obfuscated (so it is not human-readable / hand-editable, IDENT-02) under one HMAC
signature (file-integrity, IDENT-03).

Fail-closed tamper model (D-05): a PRESENT-but-invalid blob — corrupt bytes OR an
HMAC mismatch — returns the TAMPERED sentinel via ONE code path; it blocks submit and
is NEVER auto-regenerated (auto-regen would let tampering force a fresh slot). A
MISSING blob is a genuine first launch → mint a fresh identity (D-04).

On-disk format: a small JSON envelope ``{"sig": <hexdigest>, "blob": <ascii>}`` where
``blob`` is ``obfuscate(json({machine_id, initials}))`` (base64-over-XOR ASCII) and
``sig`` is ``sign_identity_blob(obfuscated_bytes, secret)``. The envelope key names are
generic; the identity values live only inside the obfuscated payload, so the raw
initials/machine_id never appear in the file.

The HMAC ``secret`` is supplied explicitly by the caller (the build-baked value,
D-09) — never stored in this module. Stdlib only (``json``, ``uuid``, ``os``, ``re``)
plus the Plan 01 client crypto module.
"""
import json
import os
import re
import uuid

from leaderboard_crypto import (
    obfuscate,
    de_obfuscate,
    sign_identity_blob,
    verify_identity_blob,
)
from paths import data_path, user_data_path
from settings import IDENTITY_FILE_NAME


# Legacy next-to-exe plaintext files (pre-Phase-5). Kept as the migration source so
# load_identity can find and consolidate them, then remove them.
MACHINE_ID_FILE = data_path("machine_id.txt")
PLAYER_DATA_FILE = data_path("player_data.json")

# Default location of the new consolidated blob (%LOCALAPPDATA%\PacMan\identity.dat).
IDENTITY_FILE = user_data_path(IDENTITY_FILE_NAME)

# Load-status sentinels.
IDENTITY_STATUS_OK = "ok"
IDENTITY_STATUS_TAMPERED = "tampered"

# Internal sentinel: the blob file does not exist (genuine first launch, not tamper).
_STATUS_MISSING = "missing"

# Initials are exactly three uppercase letters (server-enforced format mirror).
_INITIALS_RE = re.compile(r"^[A-Z]{3}$")


def _write_identity_blob(machine_id, initials, secret, path):
    """Obfuscate + sign {machine_id, initials} and write the envelope to ``path``.

    The identity dict is serialized to JSON bytes, obfuscated (not human-readable),
    signed over the obfuscated bytes, and stored as a JSON envelope so the raw
    machine_id / initials never appear in the file.
    """
    payload = json.dumps(
        {"machine_id": machine_id, "initials": initials},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    obfuscated = obfuscate(payload)  # base64-ASCII bytes
    sig = sign_identity_blob(obfuscated, secret)
    envelope = {"sig": sig, "blob": obfuscated.decode("ascii")}
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(envelope, f)


def _read_identity_blob(secret, path):
    """Read + verify the identity blob at ``path``.

    Returns ``(machine_id, initials, status)``:
    - status OK with the parsed values on a verified blob,
    - status TAMPERED (values None) if the file is present but corrupt OR the HMAC
      does not match — ONE fail-closed code path (D-05); never regenerates,
    - the internal _STATUS_MISSING (values None) if the file does not exist.
    """
    if not os.path.exists(path):
        return (None, None, _STATUS_MISSING)
    try:
        with open(path, "r") as f:
            envelope = json.load(f)
        sig = envelope["sig"]
        obfuscated = envelope["blob"].encode("ascii")
        if not verify_identity_blob(obfuscated, sig, secret):
            return (None, None, IDENTITY_STATUS_TAMPERED)
        payload = de_obfuscate(obfuscated)
        data = json.loads(payload.decode("utf-8"))
        return (data["machine_id"], data["initials"], IDENTITY_STATUS_OK)
    except Exception:
        # Any decode/parse/structure failure is treated identically to an HMAC
        # mismatch: present-but-invalid → TAMPERED (D-05). Never raises.
        return (None, None, IDENTITY_STATUS_TAMPERED)


def _read_legacy_machine_id(path):
    """Read a legacy plaintext machine_id from ``path``, or None if absent/unreadable."""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            value = f.read().strip()
        return value or None
    except OSError:
        return None


def _read_legacy_initials(path):
    """Read legacy initials from ``path`` (json {"initials": ...}).

    Returns the initials only if they match ^[A-Z]{3}$; any missing/invalid/unreadable
    value is treated as not-yet-set (None) so a fresh prompt happens later.
    """
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r") as f:
            data = json.load(f)
        initials = data.get("initials")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None
    if isinstance(initials, str) and _INITIALS_RE.match(initials):
        return initials
    return None


def load_identity(
    secret,
    *,
    blob_path=IDENTITY_FILE,
    legacy_machine_id_path=MACHINE_ID_FILE,
    legacy_player_data_path=PLAYER_DATA_FILE,
):
    """Resolve the player identity, returning ``{machine_id, initials, status}``.

    Resolution order:
    1. If the new blob exists → return ``_read_identity_blob`` shaped as the dict
       (covers both OK and the fail-closed TAMPERED case; a tampered blob never
       touches legacy files and never regenerates — D-05).
    2. Else if legacy plaintext files exist → migrate (D-04): read legacy machine_id
       (and validated legacy initials), write the new signed blob, VERIFY it reads
       back equal, and ONLY THEN delete both legacy files. If the verify-read-back
       fails, leave the legacy files in place but still return the migrated values
       (never lose the identity). Migrated values are adopted as-is (not re-prompted).
    3. Else (no blob, no legacy) → genuine first launch: mint a fresh uuid4
       machine_id, initials None, write the blob, status OK.
    """
    machine_id, initials, status = _read_identity_blob(secret, blob_path)
    if status != _STATUS_MISSING:
        # Present blob (OK or TAMPERED) — authoritative; do not migrate or regenerate.
        return {"machine_id": machine_id, "initials": initials, "status": status}

    legacy_machine_id = _read_legacy_machine_id(legacy_machine_id_path)
    if legacy_machine_id is not None:
        legacy_initials = _read_legacy_initials(legacy_player_data_path)
        _write_identity_blob(legacy_machine_id, legacy_initials, secret, blob_path)
        rb_mid, rb_ini, rb_status = _read_identity_blob(secret, blob_path)
        if (
            rb_status == IDENTITY_STATUS_OK
            and rb_mid == legacy_machine_id
            and rb_ini == legacy_initials
        ):
            # Verify-before-delete gate (D-04 safety ordering): only remove legacy
            # files after a confirmed equal read-back.
            _safe_remove(legacy_machine_id_path)
            _safe_remove(legacy_player_data_path)
        return {
            "machine_id": legacy_machine_id,
            "initials": legacy_initials,
            "status": IDENTITY_STATUS_OK,
        }

    # Genuine first launch: mint fresh.
    fresh_machine_id = str(uuid.uuid4())
    _write_identity_blob(fresh_machine_id, None, secret, blob_path)
    return {"machine_id": fresh_machine_id, "initials": None, "status": IDENTITY_STATUS_OK}


def _safe_remove(path):
    """Delete ``path`` if present; never raise (best-effort legacy cleanup)."""
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def save_initials(initials, secret, *, blob_path=IDENTITY_FILE):
    """Re-sign and rewrite the identity blob with ``initials`` after first-launch entry.

    Reads the current machine_id from the existing blob (minting a fresh uuid4 if the
    blob is missing), then rewrites the signed blob carrying the new initials. A
    subsequent load returns the saved initials with status OK.
    """
    machine_id, _existing_initials, status = _read_identity_blob(secret, blob_path)
    if status != IDENTITY_STATUS_OK or not machine_id:
        machine_id = str(uuid.uuid4())
    _write_identity_blob(machine_id, initials, secret, blob_path)
