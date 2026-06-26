# Phase 5: Client Identity Hardening - Context

**Gathered:** 2026-06-19
**Status:** Ready for planning

<domain>
## Phase Boundary

The player's identity (`machine_id` + initials) is stored **outside the game folder**,
**obfuscated**, and **HMAC-signed**, so the client both (a) detects out-of-band tampering on load
and refuses to submit a tampered identity, and (b) signs each score submission so the hardened Phase 4
server accepts it. This **closes the signing↔verification loop** Phase 4 opened (server verifies =
COMP-01; client signs = IDENT-03, same shared secret).

**In scope:** client-side identity storage relocation + obfuscation + HMAC (IDENT-01/02/03); client
score-submission signing (the COMP-01 client half — success criterion 4); one-time migration of the
existing plaintext identity; a minimal "scores not saved" notice on the game-over screen; baking the
shared secret into the build safely. Touches `local_storage.py`, `paths.py`, `api_service.py`,
`main.py`, `build.py`, a new client crypto module, and tests.

**Out of scope (belongs to other phases / milestones):** the in-game This Week/All Time board UI,
last-week's-champ, and got-passed banner (Phase 6); the web leaderboard page (Phase 7); flipping
`REQUIRE_SIGNATURE=true` server-side (ops follow-up after this ships — D-02 from Phase 4); any
local-file encryption beyond obfuscation + HMAC; full code obfuscation / PyArmor; any ghost-AI
decision-behavior change (locked spec — CI golden net stays green).

</domain>

<decisions>
## Implementation Decisions

### Storage Location (IDENT-01)

- **D-01 (Where identity lives):** Relocate to **`%LOCALAPPDATA%\PacMan\`** — per-user, **local
  (NOT roaming)**, off the desktop and not next to the exe. Local-not-roaming is deliberate:
  `machine_id` is machine-bound (it identifies this PC's leaderboard slot), so a roaming profile that
  carried it to a second PC would blur the one-machine-one-slot model. Folder name is exactly
  **`PacMan`**. (Cross-platform / dev fallback for non-Windows is Claude's discretion — Windows is the
  only requirement.)

- **D-02 (One consolidated, signed blob):** Replace the two legacy files (`machine_id.txt` +
  `player_data.json`) with **a single obfuscated, HMAC-signed identity blob** (e.g. `identity.dat`)
  holding `{machine_id, initials}` under **one** signature. One read, one signature, one obfuscation,
  one tamper-check, one file to migrate-and-write. The legacy two-file split does not constrain the new
  store because we migrate off it anyway. Avoids a "one file valid, the other not" edge case.

- **D-03 (Store is identity-only; directory is the extension seam):** Phase 5 builds **only** the signed
  identity blob. The `%LOCALAPPDATA%\PacMan\` directory is the extension point — Phase 6's
  "last-viewed board" marker (RIVAL-01) will be a **separate, unsigned** file dropped alongside it,
  added in Phase 6. The marker is deliberately **not** in the signed blob and **not** tamper-protected
  (re-signing on every board view is pointless friction; a wrong got-passed banner is harmless). No
  general "local store" abstraction is built now (YAGNI — the shared directory already is the seam).

### Migration (continuity)

- **D-04 (Migrate-then-remove on first launch):** On first launch of the Phase 5 build, if the legacy
  plaintext `machine_id.txt` / `player_data.json` exist next to the exe: read them → write the new
  obfuscated+signed blob in `%LOCALAPPDATA%\PacMan\` → **delete the old files**. Friends keep their
  `machine_id`, server-locked initials, and board slot — a seamless upgrade with a clean folder
  afterward. **No legacy files present = a normal genuine first launch** → mint a fresh identity (this
  is the already-sanctioned self-reset path, not an error). The migrated values are adopted as-is and
  treated as already-set (do not re-prompt for initials).
  - *Planner note (safety ordering):* write the new blob and **verify it reads back** before deleting
    the old files, so a mid-migration failure never loses the identity.

### Tamper / Integrity Response (IDENT-03, SC-3)

- **D-05 (Any present-but-invalid file blocks submit, one simple rule):** On load, a file that is
  **present but invalid — whether it won't decode at all (corrupt) OR decodes but the HMAC mismatches
  (tampered)** → **block score submission for this session; the game stays fully playable.** One code
  path, no silent identity changes ever. A **missing** file is different → fresh identity (D-04).
  Recovery is explicit: the player deletes the file → fresh identity next launch. This deliberately
  does NOT auto-regenerate on a broken HMAC (that would let tampering force-reset someone and would
  silently move a bit-rotted identity to a new slot). Consistent with the locked "file-HMAC detects
  third-party tampering, not self-initiated reset."

- **D-06 (Notice on the game-over screen):** Surface the failure as a **small line on the game-over /
  score screen** at the moment a submit would have happened (e.g. "Score not saved — identity error"),
  reusing the existing new-best-feedback seam (`main.py:45-47`, `run_game_over_screen`). Not a menu
  line, not a modal — minimal, contextual, and consistent with the existing graceful-offline
  degrade pattern (`menu.py:140` "Could not connect to leaderboard."). Full board UI is Phase 6.

### Crypto & Build

- **D-07 (Submission wire format is LOCKED by Phase 4 — reproduce byte-for-byte):** The client signs
  score submissions with HMAC-SHA256 over Phase 4's `canonical_message`:
  `json.dumps({"machine_id", "initials", "score"}, sort_keys=True, separators=(",",":"),
  ensure_ascii=False).encode("utf-8")`, hex digest, sent as a **`"signature"`** field added to the
  existing POST body. `score` stays an **int** (stringifying it produces a rejected signature). This
  must match `cloud_functions/.../leaderboard_crypto.py:verify_signature` exactly. **No replay
  protection** (D-04 from Phase 4) — no nonce/timestamp needed.

- **D-08 (File-integrity HMAC: same secret + domain separation):** The local file-integrity HMAC reuses
  the **same embedded shared secret** as submissions, but frames its signed message **distinctly**
  (e.g. a `identity-file-v1:` prefix over the blob) so a file signature and a submission signature are
  **not interchangeable**. One secret to ship, standard domain-separation practice, no extra key
  management. (Exact prefix string is Claude's discretion.)

- **D-09 (Secret stays out of git — gitignored local file, baked at build):** The real
  `leaderboard-hmac-secret` value (the operator's safe copy, identical to the deployed server secret)
  lives in a **gitignored local file** on the build machine (e.g. `hmac_secret.local`); `build.py`
  reads it and bakes it into the bundle. The repo ships only a **placeholder/example + a `.gitignore`
  entry** — the real value is never committed. Mirrors the `settings.local.json` handling from Phase 3.
  The secret MUST NOT be hardcoded into any committed source file.

- **D-10 (Light-but-real obfuscation — for BOTH files and the embedded secret):** Obfuscation altitude
  is "stop casual snooping," not real crypto. Identity blob = an obfuscated (e.g. base64-over-payload /
  XOR) form that is **not human-readable and not hand-editable** (IDENT-02). The **embedded secret** is
  stored **non-literally** (byte array / XOR'd / split-and-reassembled) so a plain `strings`/grep of
  the exe does not surface it. This beats casual eyeballing and trivial dumps while accepting the locked
  ceiling that a determined reverse-engineer extracts it anyway (the server is the real enforcement
  boundary). Full obfuscation (PyArmor) remains rejected/out of scope.

### Claude's Discretion (handed to research/planning — design these, don't re-ask the user)

- **Exact obfuscation algorithm** for the identity blob and for the non-literal embedded secret (D-10) —
  pick a simple, stdlib-only, reversible scheme; avoid new client runtime deps.
- **The domain-separation prefix/framing** for the file-integrity HMAC (D-08).
- **A client `leaderboard_crypto`-style module** that mirrors the server helper's `canonical_message` +
  an HMAC sign function. Note: the server's `verify_signature` is an excellent **test oracle** — a test
  can assert the client's signature passes the real server verifier (with a known test secret), proving
  the loop closes without a live deploy.
- **Cross-platform / dev fallback** for the storage directory on non-Windows (Windows is the only
  requirement; dev runs should still work — e.g. a home-dir fallback).
- **Migration edge cases:** only one legacy file present (machine_id but no initials, or vice versa);
  legacy initials that don't match `^[A-Z]{3}$`; unreadable/locked legacy files. Define sensible
  fallbacks (e.g. partial migration adopts what's valid; invalid legacy initials → treat as not-yet-set
  and prompt).
- **Build-time injection mechanism** in `build.py` (how the gitignored secret is read and embedded).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap (authoritative scope)
- `.planning/ROADMAP.md` § "Phase 5: Client Identity Hardening" — goal, dependency on Phase 4, the 4
  success criteria, and the IDENT-03↔COMP-01 same-secret loop-closing note + the obfuscation+HMAC-only
  scope guard.
- `.planning/REQUIREMENTS.md` § "Identity & Tamper-Resistance (client-side)" — IDENT-01, IDENT-02,
  IDENT-03 (exact requirement wording each decision maps to); § "Out of Scope" row on local-file
  encryption.

### The OTHER half of this mechanism — Phase 4 (server side; the contract the client must satisfy)
- `cloud_functions/submit_score/leaderboard_crypto.py` — **the wire-format contract**:
  `canonical_message` (json.dumps kwargs locked: `sort_keys=True`, `separators=(",",":")`,
  `ensure_ascii=False`; score as int) and `verify_signature` (HMAC-SHA256 hexdigest, secret from
  `LEADERBOARD_HMAC_SECRET`, constant-time compare). The client MUST reproduce `canonical_message`
  byte-for-byte (D-07); `verify_signature` doubles as the client test oracle.
- `cloud_functions/submit_score/main.py:122-130` — the server reads the signature from the
  **`"signature"`** JSON body field and the grace gate (`REQUIRE_SIGNATURE`); informs where the client
  puts the signature and the post-Phase-5 flip.
- `.planning/phases/04-server-hardening-weekly-data-model/04-CONTEXT.md` — Phase 4 decisions that
  constrain this phase: D-02 (grace flip), D-03 (machine_id+initials+score binding), D-04 (no replay),
  and the "Claude's Discretion → light secret obfuscation is a Phase 5 concern" hand-off + the
  threat-model `<specifics>` (accepted-ceiling / irreducible-identity-limit reasoning).

### Current client implementation — the baseline being hardened
- `local_storage.py` — current identity storage: `get_machine_id` (plaintext UUID in
  `machine_id.txt`), `get_initials`/`save_initials` (`player_data.json`). Both via `data_path()`. This
  is what gets relocated, consolidated, obfuscated, and signed.
- `paths.py` — `data_path()` currently returns next-to-exe (frozen) / project-root (dev). A new
  per-user-dir resolver (`%LOCALAPPDATA%\PacMan\`) is added here or alongside (D-01); `resource_path`
  is unaffected.
- `api_service.py` — `ApiService.submit_score` currently POSTs unsigned `{machine_id, initials,
  score}` via `urllib`. Gets the `"signature"` field added (D-07); stays no-new-deps.
- `main.py:15-46` — wires `ApiService` + `get_machine_id`/`get_initials`/`save_initials`, forces
  initials entry on first launch, and submits after a run. The integration seam for migration (D-04),
  the tamper/no-submit gate (D-05), and the game-over notice (D-06).
- `settings.py` — holds `API_SUBMIT_SCORE_URL` / `API_LEADERBOARD_URL`; candidate home for any new
  identity-path / secret-loading constants.
- `build.py` — PyInstaller build; gets the gitignored-secret bake-in step (D-09).

### Tests that MUST stay green (CI merge gate)
- `tests/test_api_service.py` — client API-service tests (submit now includes a signature).
- `tests/test_leaderboard_crypto.py` — server crypto tests; the canonical-format reference + oracle.
- CI golden net (`tests/test_golden_traces.py`, `tests/test_ghost_micro.py`, `tests/test_frame_hash.py`,
  `tests/test_determinism_guard.py`) — this phase touches no ghost-AI code, but the merge gate applies.

### Design specs — STALE baseline (dated 2026-03-26, pre-HMAC / pre-relocation)
- `docs/superpowers/specs/2026-03-26-api-refactor-exe-design.md` — Cloud-Functions-HTTP-proxy +
  PyInstaller build + the existing `data_path()`/next-to-exe identity model. Useful baseline; predates
  the relocation/obfuscation/signing.
- `docs/superpowers/specs/2026-03-26-leaderboard-design.md` — original Firestore/leaderboard shape.
  Predates HMAC. Context only.

### Codebase maps
- `.planning/codebase/INTEGRATIONS.md` — how the client talks to the Cloud Functions.
- `.planning/codebase/ARCHITECTURE.md` — overall game + leaderboard architecture (state machine,
  identity flow).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **Server `leaderboard_crypto.py`** — `canonical_message` is the exact spec to mirror client-side;
  `verify_signature` is reusable as a **test oracle** to prove client signatures pass the real verifier
  without a live deploy.
- **`paths.py` resolver pattern** — `resource_path`/`data_path` already centralize frozen-vs-dev path
  logic; the new per-user-dir resolver slots in naturally here.
- **`local_storage.py` function shape** — `get_machine_id`/`get_initials`/`save_initials` are the API
  surface to preserve (or wrap) so `main.py`'s call sites change minimally.
- **Existing graceful-offline UI** — `menu.py:138-142` ("Could not connect to leaderboard.") and the
  game-over new-best feedback are the established pattern the D-06 notice mirrors.

### Established Patterns
- **`settings.local.json` precedent (Phase 3)** — a gitignored local file + `.gitignore` entry +
  committed example is exactly the model D-09 reuses for the secret.
- **No-new-deps client** — `api_service.py` uses stdlib `urllib`; identity/crypto should stay
  stdlib-only (`hashlib`, `hmac`, `json`, `base64`) per the PROJECT.md "avoid new client runtime deps"
  constraint.
- **Deterministic, offline-resilient game** — leaderboard features degrade gracefully; the tamper
  no-submit state (D-05) is just another graceful-degrade branch.

### Integration Points
- **`main.py` startup + post-game** — load/migrate identity at startup (D-04), gate submit on identity
  validity (D-05), pass the signature through `api.submit_score` (D-07), render the game-over notice
  (D-06).
- **Shared-secret seam (from Phase 4):** the embedded client secret MUST equal the deployed
  `leaderboard-hmac-secret`. After this ships and friends update, the operator flips
  `REQUIRE_SIGNATURE=true` on `pacman` (D-02 from Phase 4).
- **Build pipeline:** `build.py` bakes the gitignored secret (D-09) — the in-repo gate is local tests;
  full end-to-end proof needs a build + (eventually) the server flag flip.

</code_context>

<specifics>
## Specific Ideas

- The signing↔verification loop must be **provable in tests without a live server**: a client-side
  signature over a known `{machine_id, initials, score}` with a known test secret must pass the server's
  `verify_signature`. This is the concrete expression of Phase 5 success criterion 4 and the single
  most important test to write.
- The realistic threat model for "tamper" is the user themselves (or a prankster with PC access)
  editing the file — not a sophisticated remote attacker. The accepted ceiling (secret extractable from
  the exe) is inherited from Phase 4 and deliberately not re-litigated; this phase raises the bar past
  *trivial* (`strings`/grep, hand-editing), nothing more.

</specifics>

<deferred>
## Deferred Ideas

- **Phase 6 last-viewed-board marker (RIVAL-01)** — will live as a separate, unsigned file in the
  `%LOCALAPPDATA%\PacMan\` directory established here (D-03). Designed-for, not built here.
- **Flipping `REQUIRE_SIGNATURE=true`** — operator ops follow-up after the signed client ships and
  friends update (Phase 4 D-02). Not a Phase 5 build task.
- **Stronger local protection** (real file encryption, PyArmor, per-key derivation/HKDF, separate local
  key) — considered and rejected as theater for an extractable-secret client; the server is the
  enforcement boundary. Revisit only if abuse materializes.

None of these are scope creep — discussion stayed within the client-identity-hardening boundary.

</deferred>

---

*Phase: 5-client-identity-hardening*
*Context gathered: 2026-06-19*
