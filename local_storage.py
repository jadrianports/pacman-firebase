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
