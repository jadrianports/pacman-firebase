# Phase 4: Server Hardening & Weekly Data Model - Context

**Gathered:** 2026-06-14
**Status:** Ready for planning

<domain>
## Phase Boundary

The Cloud Functions become the **real enforcement boundary** and the **single source of weekly +
all-time score data** that every other v1.1 feature consumes. Concretely, this phase:

- Adds **server-side HMAC verification** to `submit_score` (COMP-01) — built and tested here; the
  matching client-side signing lands in Phase 5.
- Tightens the **score sanity ceiling** (COMP-02).
- Enforces **permanent initials server-side** (COMP-03).
- Reshapes the score data model to be **week-bucketed** with an **all-time** view retained, and makes
  `get_leaderboard` **scope-aware** (BOARD-01, BOARD-02).

**In scope:** Cloud Functions (`submit_score`, `get_leaderboard`), the Firestore data model, and the
server-side cloud-function validator tests (TST-03).

**Out of scope (belongs to other phases / milestones):** client-side identity storage, obfuscation,
and signing (Phase 5); in-game weekly UI, This Week/All Time toggle, last-week's-champ display, and
got-passed banner (Phase 6); the web leaderboard page (Phase 7); any ghost-AI decision behavior change
(locked spec — CI golden net stays green); replay-verification, season archives, friend groups (deferred).
</domain>

<decisions>
## Implementation Decisions

### Anti-Cheat / Score Integrity

- **D-01 (COMP-02 — Sanity ceiling value):** Lower `MAX_SCORE` from **500,000 → 50,000**. The board is
  a single, non-repeating maze; the *mathematical perfect run is ~14,620* (242 dots×10 + 4 pellets×50 +
  4 power pellets × up to 3,000 ghost points each). 50,000 is ~3.4× perfect — comfortable headroom
  against any analysis edge or near-term scoring tweak, while being ~10× tighter than today. Raise it
  later if the Fun milestone adds scoring (fruit/levels).

- **D-02 (COMP-01 — HMAC enforcement rollout):** **Grace period + flip.** The Phase 4 server *accepts*
  unsigned submissions during the P4→P5 gap (and should log them), but *rejects any invalid signature*.
  A server-side flag (e.g. `REQUIRE_SIGNATURE`) gates hard enforcement and is flipped to "require" only
  **after** the Phase 5 signed client ships and friends have updated. Rationale: the currently-shipped
  exe posts unsigned data; enforcing immediately would break every friend's live board. This is no
  regression vs. today (curl forgeries already get through), and rejection logic is still fully built
  and **tested** in Phase 4 (success criterion: an unsigned/invalid `curl` post is rejected against the
  known key).

- **D-03 (COMP-01 — HMAC binding scope):** The signature must cover the **full payload: machine_id +
  initials + score**. Binding `machine_id` into the signed material prevents a captured/valid signature
  from being lifted onto a *different* identity or score. (Exact serialization format is a
  research/planning decision — see Claude's Discretion.)

- **D-04 (COMP-01 — Replay protection):** **No replay defense.** Submit is "only-if-higher", so
  re-POSTing a captured valid submission is a no-op or re-submits a score the player already holds —
  near-harmless. Adding a nonce/timestamp + freshness window buys ~zero here and introduces
  clock-skew fragility. Deliberately skipped.

- **D-05 (COMP-03 — Permanent initials):** Initials **lock on a machine's first submission**. On a later
  submission whose initials *differ* from the locked ones, **keep the original initials and still accept
  the score** (if it's a new best). The new initials are silently ignored — no error returned. This
  honors permanence without dropping a legitimate higher score and blocks tag-swapping/impersonation.
  (Note: today's `submit_score` rewrites initials on every new best — this behavior MUST change.)

### Weekly Data Model

- **D-06 (BOARD-01 — Week bucketing):** Scores are bucketed by week with a **Monday 00:00 UTC** reset.
  Buckets are computed from **server time only** — never a client-supplied timestamp — so a client
  cannot lie about its clock to land a score in a different week or fake last-week standings.

- **D-07 (BOARD-01 — Per-player best per week):** "This Week" shows the **best score per player (per
  machine_id) for the current week**, mirroring the existing all-time board's one-row-per-machine shape.

- **D-08 (BOARD-02 — All-time retained):** The all-time board persists untouched across week boundaries;
  `get_leaderboard` becomes **scope-aware** (current week vs. all-time).

- **D-09 (Weekly retention):** Keep **current week + last week only**. Weeks older than last week are
  pruned via **lazy delete-on-write** (opportunistically prune stale buckets when a submission lands) —
  no Cloud Scheduler/cron to deploy or maintain. Stale weeks are harmless clutter until the next write.
  Last week's bucket must survive (Phase 6 surfaces "last week's champ"). Season-archives remain out of
  scope, so there's no need to retain older history.

### Hardening / Ops

- **D-10 (Identity privacy):** `machine_id` MUST stay out of **all** API responses. `get_leaderboard`
  already returns only `initials` + `score` — keep it that way so a machine_id can't be discovered via
  the API and used for impersonation.

- **D-11 (Quota/spam defense):** **Cap the Cloud Functions' `max-instances`** to bound cost/blast-radius
  if someone floods the endpoint; otherwise accept the (low-likelihood) spam risk. No per-request
  rate-limiting state. (A per-machine cooldown was considered and rejected — a secret-holder can mint
  fresh machine_ids, so it's partial protection for more logic.)

### Claude's Discretion (handed to research/planning — design these, don't re-ask the user)

- **Exact HMAC scheme:** the canonical serialization of `machine_id|initials|score`, the hash
  (recommend HMAC-SHA256), and **where the server secret lives** (recommend a Cloud Function
  environment variable / runtime config, NOT in source or git). The same shared secret is consumed by
  the Phase 5 client build.
- **`get_leaderboard` scope-param shape:** e.g. `?scope=week|all`, and the **default scope**
  (recommend defaulting to the current week, since "This Week" is the competitive focus).
- **Week-bucket storage mechanism:** separate weekly collection keyed by `{machine_id}_{week_id}` vs. a
  `week_id` field vs. timestamp-range queries — pick what keeps the all-time path simple and the lazy
  prune cheap.
- **`week_id` format / week math:** ISO-week vs. epoch-week-number; ensure the Monday 00:00 UTC boundary
  is exact and derived from server time.
- **Baseline verification:** confirm the *committed* `cloud_functions/` code is the intended reconciled
  baseline before modifying (see Integration Points — working tree is currently clean).
- **Light secret obfuscation in the client build** is a Phase 5 concern (the secret ships in the exe);
  noted here so the HMAC scheme chosen in Phase 4 doesn't make that harder.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements & Roadmap (authoritative scope)
- `.planning/ROADMAP.md` § "Phase 4: Server Hardening & Weekly Data Model" — goal, dependencies, the 5
  success criteria, and the shared-secret-seam / prerequisite notes.
- `.planning/REQUIREMENTS.md` § "Anti-Cheat / Score Integrity" + "Weekly Boards" — COMP-01, COMP-02,
  COMP-03, BOARD-01, BOARD-02 (the exact requirement wording each decision maps to).

### Current implementation — the REAL baseline (ahead of the stale specs)
- `cloud_functions/submit_score/main.py` — current `submit_score`: already has `MAX_SCORE = 500_000`
  (D-01 lowers it), a `@firestore.transactional` `_update_score`, and rewrites initials on every new
  best (D-05 changes this). This is what gets hardened.
- `cloud_functions/get_leaderboard/main.py` — current `get_leaderboard`: top-10 by score desc, returns
  only `initials`+`score`. Becomes scope-aware (D-08); keep machine_id out (D-10).
- `api_service.py` — client API service; currently POSTs unsigned `{machine_id, initials, score}` via
  `urllib`. Informs the request shape the server must accept during the grace period (D-02).
- `settings.py` — holds `API_SUBMIT_SCORE_URL` and `API_LEADERBOARD_URL` (Cloud Run, asia-southeast1).

### Tests that MUST stay green (TST-03 + CI golden net — success criterion 5)
- `tests/test_submit_score.py` — cloud-function `submit_score` validator tests.
- `tests/test_get_leaderboard.py` — cloud-function `get_leaderboard` validator tests.
- `tests/test_api_service.py` — client API-service tests.
- (CI golden net: `tests/test_golden_traces.py`, `tests/test_ghost_micro.py`,
  `tests/test_frame_hash.py`, `tests/test_determinism_guard.py` — must stay green; this phase touches
  no ghost-AI code, but the merge gate still applies.)

### Design specs — STALE baseline (dated 2026-03-26, pre-HMAC / pre-weekly)
- `docs/superpowers/specs/2026-03-26-leaderboard-design.md` — original Firestore data model
  (`leaderboard/{machine_id}`, one doc per machine, score-desc top-10). Useful for the existing shape;
  does NOT reflect HMAC or week buckets.
- `docs/superpowers/specs/2026-03-26-api-refactor-exe-design.md` — the Cloud-Functions-HTTP-proxy
  architecture (no client credentials), submit/get contracts, PyInstaller build. Useful baseline;
  predates the security work.

### Codebase maps
- `.planning/codebase/INTEGRATIONS.md` — how the client talks to the Cloud Functions / Firestore.
- `.planning/codebase/ARCHITECTURE.md` — overall game + leaderboard architecture.
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`@firestore.transactional _update_score`** in `submit_score/main.py` — the existing transactional
  read-modify-write is the natural seam to extend for permanent-initials (D-05) and week buckets (D-06).
- **`MAX_SCORE` constant** — sanity ceiling already exists; D-01 just changes the value (500_000 → 50_000).
- **CORS preflight handling** — both functions already emit `Access-Control-Allow-Origin: *` and handle
  OPTIONS; the Phase 7 web page depends on this, so preserve it.
- **`api_service.py` (`urllib`, no deps)** — the client request contract to keep compatible during the
  grace period (D-02); the signing half is added in Phase 5.

### Established Patterns
- **Cloud Functions as HTTP API proxy, no client credentials** — the enforcement boundary. All secrets
  (Firestore creds, and now the HMAC secret) live server-side only.
- **"Only-if-higher" idempotent submit** — a write happens only when the new score beats the stored one;
  this is what makes replay near-harmless (D-04).
- **Deterministic, no-`random` game** — scoring is fixed (dots 10, pellets 50, ghosts `(2^n)·100`); the
  ~14,620 perfect-run math behind D-01 is stable.

### Integration Points
- **Prerequisite — `cloud_functions/` working tree is CLEAN** (verified during discussion): the
  "reconcile uncommitted `cloud_functions/*/main.py` changes flagged at v1.0 close" prerequisite appears
  already satisfied. Planner should confirm the committed code is the intended reconciled baseline before
  modifying, so TST-03 targets a known state.
- **Shared-secret seam:** the HMAC secret established here (server-side) is the same secret the Phase 5
  client build consumes to sign submissions. End-to-end "valid signed submission accepted" only fully
  closes once Phase 5 ships; Phase 4 proves rejection of unsigned/invalid against the known key.
- **Deployment is manual** (Google Cloud Console per the api-refactor spec) — full prod verification of
  HMAC/weekly behavior depends on the user deploying; local validator tests are the in-repo gate.
</code_context>

<specifics>
## Specific Ideas

The user explicitly asked to think through the **threat model** for `machine_id` + initials and then
how to **harden** each vector. The resulting analysis (captured as the residual limits + D-03/D-04/
D-06/D-10/D-11) is itself a guiding artifact:

- **Accepted ceiling:** the HMAC secret is extractable from the exe (PyInstaller bundles are easy to
  reverse). HMAC stops raw `curl`, web/JS submissions, and casual local tampering — **not** a determined
  decompiler. This is the deliberately-accepted altitude ("client secrets are extractable; the server is
  the real enforcement boundary" — PROJECT.md). The unforgeable fix (replay-verification) is deferred.
- **Irreducible identity limit:** a user can delete their local identity file → fresh `machine_id` →
  new slot + new initials. The server cannot prevent this without real accounts (out of scope).
  "Permanent initials" therefore means *permanent-per-machine_id*, not *permanent-per-person*; the
  Phase 5 file-HMAC detects *third-party* tampering, not *self-initiated* reset.
- **Hardening that IS worth it (locked above):** bind machine_id into the signature (D-03), bucket by
  server time (D-06), keep machine_id out of API responses (D-10), cap max-instances (D-11), light
  secret obfuscation in the build (Phase 5).
</specifics>

<deferred>
## Deferred Ideas

- **Replay-verification of scores** (re-run inputs server-side) — the unforgeable ceiling; already
  deferred as COMP-F1 in REQUIREMENTS.md. Out of scope.
- **Season-history archives** of past weekly boards (BOARD-F1) — directly informed the "current + last
  week only" retention choice (D-09). Out of scope.
- **Heavier anti-abuse:** per-machine/per-IP rate-limiting beyond the max-instances cap, nonce/timestamp
  replay protection, full code obfuscation (PyArmor) — all considered and rejected as overkill for a
  friends board. Revisit only if abuse actually materializes.
- **Friend groups / private join-code boards** (SOCL-F1) — out of scope for v1.1.

No scope creep occurred — discussion stayed within the server-hardening + weekly-data-model boundary.
</deferred>

---

*Phase: 4-server-hardening-weekly-data-model*
*Context gathered: 2026-06-14*
