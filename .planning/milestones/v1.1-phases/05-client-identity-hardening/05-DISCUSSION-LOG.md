# Phase 5: Client Identity Hardening - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-19
**Phase:** 5-client-identity-hardening
**Areas discussed:** Storage location, Identity migration, Tamper response, Secret & obfuscation, Tamper notice surfacing, One file vs two, File-HMAC key separation, Store extensibility

---

## Storage location — base directory

| Option | Description | Selected |
|--------|-------------|----------|
| %LOCALAPPDATA%\PacMan | Per-user, local (does not roam) — matches machine-bound machine_id | ✓ |
| %APPDATA%\PacMan (roaming) | Roams across PCs — would carry machine_id to a second machine | |
| Documents\PacMan | Visible/discoverable — cuts against IDENT-01 | |

**User's choice:** %LOCALAPPDATA%\PacMan (local, not roaming)
**Notes:** Local-not-roaming chosen because machine_id identifies this PC's leaderboard slot; roaming would blur the one-machine-one-slot model.

## Storage location — folder name

| Option | Description | Selected |
|--------|-------------|----------|
| PacMan | Clean and obvious; small collision risk | ✓ |
| JadPacMan | Namespaced to author; ~zero collision risk | |
| pacman-firebase | Matches repo; leaks "firebase" backend detail in a user path | |

**User's choice:** PacMan
**Notes:** —

## Identity migration

| Option | Description | Selected |
|--------|-------------|----------|
| Migrate, then remove old | Carry machine_id + locked initials to new store, delete old plaintext | ✓ |
| Migrate, leave old in place | Same carry-over, keep old files as fallback (leaves discoverable plaintext) | |
| Fresh start, no migration | Everyone becomes a new player; orphaned old board rows | |

**User's choice:** Migrate, then remove old
**Notes:** Seamless upgrade — friends keep board slot + locked initials. Absent files = normal fresh start. Planner to write+verify the new store before deleting old (no data loss on mid-migration failure).

## Tamper response — broken HMAC on load

| Option | Description | Selected |
|--------|-------------|----------|
| Block submit + brief notice | Game playable, scores not submitted this session, one-time notice; non-destructive | ✓ |
| Block submit, stay silent | Same, but no message — reads like a bug | |
| Auto-regenerate fresh identity | Treat broken HMAC like corrupt; silently mint new identity | |

**User's choice:** Block submit + brief notice
**Notes:** Non-destructive; recovery is deleting the file → fresh identity. Auto-regenerate rejected (lets tampering force-reset someone; silently changes board slot).

## Tamper response — corrupt vs tampered

| Option | Description | Selected |
|--------|-------------|----------|
| Same: any invalid file blocks submit | One rule — won't-decode OR HMAC-mismatch → block submit; no silent identity changes | ✓ |
| Corrupt → fresh, tamper → block | Auto-recover undecodable files; only decodable-but-wrong blocks | |

**User's choice:** Same — any present-but-invalid file blocks submit
**Notes:** Single code path; missing file (not present) remains the fresh-identity path.

## Secret & obfuscation — secret source

| Option | Description | Selected |
|--------|-------------|----------|
| Gitignored local file, baked at build | Real secret in gitignored file; build.py bakes it; repo ships placeholder | ✓ |
| Build-time environment variable | build.py reads from env var; nothing secret on disk in repo | |
| Hardcoded in a source file | Committed to git in plaintext — rejected | |

**User's choice:** Gitignored local file, baked at build
**Notes:** Mirrors the settings.local.json handling from Phase 3.

## Secret & obfuscation — obfuscation altitude

| Option | Description | Selected |
|--------|-------------|----------|
| Light but real — stop casual snooping | Files obfuscated (not hand-editable) + secret stored non-literally to survive `strings` | ✓ |
| Bare minimum — base64 only | Files base64'd; secret left as recoverable literal | |
| Obfuscate files, leave secret as-is | File obfuscation only; embedded secret untouched | |

**User's choice:** Light but real
**Notes:** Matches the locked "light secret obfuscation is worth it" call from Phase 4; full obfuscation (PyArmor) remains out of scope. Accepts the secret-is-extractable ceiling.

## Tamper notice surfacing

| Option | Description | Selected |
|--------|-------------|----------|
| Game-over screen | Show at the moment a submit would happen; reuses new-best feedback seam | ✓ |
| Main menu line | Persistent line; sets expectation before playing | |
| Both menu + game-over | Most visible; more UI; borders Phase 6 board UI | |

**User's choice:** Game-over screen
**Notes:** Minimal and contextual; consistent with the existing graceful-offline degrade message.

## One file vs two

| Option | Description | Selected |
|--------|-------------|----------|
| One signed identity blob | Single file holding {machine_id, initials} + one HMAC | ✓ |
| Two files, each signed | Mirrors today's layout; two signatures, one-valid-one-not edge case | |

**User's choice:** One signed identity blob
**Notes:** Simplest load path; legacy split doesn't constrain since we migrate off it.

## File-HMAC key separation

| Option | Description | Selected |
|--------|-------------|----------|
| Shared secret + domain separation | Reuse embedded secret with distinct message framing (e.g. identity-file-v1: prefix) | ✓ |
| Shared secret, no separation | Same secret, no framing — tiny cross-protocol confusion risk | |
| Separate/derived local key | Independent/HKDF-derived local key — buys little, more moving parts | |

**User's choice:** Shared secret + domain separation
**Notes:** One secret to ship; standard practice; file and submission signatures non-interchangeable.

## Store extensibility

| Option | Description | Selected |
|--------|-------------|----------|
| Identity-only; directory is the seam | Build only the signed blob; Phase 6 marker is a separate unsigned file in the same dir | ✓ |
| Build a general local-store module now | Reusable abstraction now — risks over-fitting Phase 6 (YAGNI) | |

**User's choice:** Identity-only; directory is the seam
**Notes:** Last-viewed marker deliberately not in the signed blob and not tamper-protected (harmless if edited).

---

## Claude's Discretion

- Exact obfuscation algorithm (identity blob + non-literal embedded secret) — stdlib-only, no new deps.
- The domain-separation prefix/framing string for the file-integrity HMAC.
- A client `leaderboard_crypto`-style module mirroring `canonical_message` + a sign function; the server's `verify_signature` reused as a test oracle.
- Cross-platform / dev fallback for the storage directory (Windows is the only requirement).
- Migration edge cases (only one legacy file present; malformed legacy initials; unreadable files).
- The `build.py` secret-injection mechanism.

## Deferred Ideas

- Phase 6 last-viewed-board marker (RIVAL-01) — separate, unsigned file in the same %LOCALAPPDATA%\PacMan directory; designed-for, not built here.
- Flipping `REQUIRE_SIGNATURE=true` server-side — operator follow-up after the signed client ships (Phase 4 D-02).
- Stronger local protection (real encryption, PyArmor, HKDF-derived/separate local key) — rejected as theater for an extractable-secret client.
