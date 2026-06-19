"""Client-side crypto for the Pac-Man leaderboard (Phase 5).

This is the CLIENT mirror of the server contract in
`cloud_functions/submit_score/leaderboard_crypto.py`. It is a SEPARATE copy living
at the repo root (NOT inside cloud_functions/) — the client signs, the server
verifies, and the two `canonical_message` implementations MUST stay byte-for-byte
identical so a client-signed submission is recomputable (and accepted) server-side.

Stdlib only (`hashlib`, `hmac`, `json`, `base64`) — no new client runtime deps.

Three concerns live here:
- Submission signing (COMP-01 / D-07): HMAC-SHA256 over the canonical message the
  server recomputes and constant-time compares. The `canonical_message` json.dumps
  kwargs (sort_keys=True, separators=(",", ":"), ensure_ascii=False, utf-8) are the
  LOCKED wire format — they must equal the server's exactly. Do NOT change them.
- Light obfuscation (IDENT-02 / D-10): a reversible base64-over-XOR scheme that makes
  the on-disk identity blob not-human-readable and not hand-editable. This is NOT
  encryption — the XOR key is a non-secret module constant; obfuscation only defeats
  casual `strings`/grep/eyeballing. The HMAC is the real tamper control.
- File-integrity HMAC (IDENT-03 / D-08): sign/verify the identity blob over a
  domain-PREFIXED message so a file signature and a submission signature occupy
  disjoint message spaces and are never interchangeable.

Unlike the server (which reads LEADERBOARD_HMAC_SECRET from os.environ at call time),
the client takes `secret` as an explicit parameter — the caller supplies the
build-baked secret. No real secret literal is stored in this module.
"""
import base64
import hashlib
import hmac
import json

# Non-secret obfuscation key (D-10). Obfuscation is NOT encryption: this key is a
# fixed, committed, repeating XOR pad whose only job is to stop casual reading of
# the on-disk identity blob. The HMAC (sign_identity_blob) is the actual integrity
# control. Do not treat this as a security boundary.
OBFUSCATION_XOR_KEY = b"pacman-identity-obfuscation-v1"

# Domain-separation framing for the file-integrity HMAC (D-08). Prefixing the blob
# with this constant makes the file-signature message space disjoint from the
# submission canonical_message space, so a captured file sig cannot be replayed as a
# submission sig (or vice-versa).
IDENTITY_FILE_PREFIX = b"identity-file-v1:"


def canonical_message(machine_id, initials, score):
    """Return the canonical signed payload as UTF-8 bytes.

    Byte-for-byte mirror of the server's canonical_message
    (cloud_functions/submit_score/leaderboard_crypto.py). LOCKED kwargs (D-07):
    sort_keys=True, separators=(",", ":"), ensure_ascii=False, then .encode("utf-8").
    Keys sort to initials, machine_id, score; `score` stays an int so a client that
    stringifies it produces a different (server-rejected) signature.
    """
    return json.dumps(
        {"machine_id": machine_id, "initials": initials, "score": score},
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sign_submission(machine_id, initials, score, secret):
    """Return the HMAC-SHA256 hexdigest over canonical_message, sent as "signature".

    This is the exact construction the server's verify_signature recomputes
    internally, so the server accepts this hexdigest for the same typed values and
    the same secret. The secret is an explicit parameter (the caller supplies the
    build-baked value) rather than read from os.environ.
    """
    return hmac.new(
        secret.encode("utf-8"),
        canonical_message(machine_id, initials, score),
        hashlib.sha256,
    ).hexdigest()


def obfuscate(payload_bytes):
    """Reversibly obfuscate `payload_bytes` into a not-human-readable form.

    XOR each byte against the cycling OBFUSCATION_XOR_KEY, then base64-encode. The
    result is not greppable for the original plaintext. NOT encryption (D-10).
    """
    key = OBFUSCATION_XOR_KEY
    xored = bytes(b ^ key[i % len(key)] for i, b in enumerate(payload_bytes))
    return base64.b64encode(xored)


def de_obfuscate(blob_bytes):
    """Inverse of obfuscate: base64-decode then XOR back to the original bytes."""
    key = OBFUSCATION_XOR_KEY
    xored = base64.b64decode(blob_bytes)
    return bytes(b ^ key[i % len(key)] for i, b in enumerate(xored))


def sign_identity_blob(blob_bytes, secret):
    """Return the HMAC-SHA256 hexdigest over IDENTITY_FILE_PREFIX + blob_bytes.

    The domain prefix (D-08) makes this message space disjoint from the submission
    canonical_message space, so a file sig and a submission sig are not
    interchangeable. Same secret, distinct framing.
    """
    return hmac.new(
        secret.encode("utf-8"),
        IDENTITY_FILE_PREFIX + blob_bytes,
        hashlib.sha256,
    ).hexdigest()


def verify_identity_blob(blob_bytes, provided_sig, secret):
    """Return True iff provided_sig matches sign_identity_blob(blob_bytes, secret).

    TOTAL / fail-closed (mirrors the server's CR-01 verify_signature): a non-string
    sig returns False, and a non-ASCII / non-comparable sig returns False — never
    raises. Comparison is constant-time (hmac.compare_digest) to avoid a timing
    oracle.
    """
    if not isinstance(provided_sig, str):
        return False  # non-string sig can never match a hex digest
    expected = sign_identity_blob(blob_bytes, secret)
    try:
        return hmac.compare_digest(expected, provided_sig)
    except TypeError:
        return False  # non-ASCII / non-comparable sig
