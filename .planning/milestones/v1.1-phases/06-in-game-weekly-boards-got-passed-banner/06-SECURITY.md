---
phase: 06
slug: in-game-weekly-boards-got-passed-banner
status: verified
threats_open: 0
asvs_level: 1
created: 2026-06-20
---

# Phase 6 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.
> Verifies the Phase-06 threat register (authored across 4 plans) against the implemented code.
> Implementation files are READ-ONLY; this audit confirms each declared mitigation is present.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| client → get_leaderboard (HTTP) | Public read endpoint; untrusted `?scope=` query string crosses here | `scope` string (client-chosen) |
| get_leaderboard → Firestore | Server-controlled query; `week_id` computed server-side, never from client | week_id (server-derived) |
| network → client (response parse) | Untrusted JSON leaderboard response parsed by `json.loads` | `{initials, score}` entries |
| public board response → got-passed banner | Untrusted initials/scores displayed in a cosmetic banner; no trust beyond display | initials (public) |
| local disk → game client | Unsigned, user-writable marker file (D-13); a player can edit it | tracked_best, initials_above, week_id |
| in-memory state → marker file | Best-effort write; a failure must not affect gameplay | marker JSON |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation / Evidence | Status |
|-----------|----------|-----------|-------------|-----------------------|--------|
| T-06-01 | Tampering | `?scope=` query param | mitigate | Tolerant allow-list: `cloud_functions/get_leaderboard/main.py:38-41` — `scope = (request.args.get("scope") or "week").lower()` then `if scope not in ("week","all","last_week"): scope = "week"`. No client value reaches Firestore except via the closed allow-list (never 400). Test: `tests/test_get_leaderboard.py::test_garbage_scope_falls_back_to_week` (pass). | closed |
| T-06-02 | Information disclosure | last_week response projection | mitigate | Projection loop `cloud_functions/get_leaderboard/main.py:80-90` emits only `{"initials","score"}`; machine_id/week_id/updated_at never leave server. Test: `tests/test_get_leaderboard.py::test_scope_last_week_projects_only_initials_and_score` (pass). | closed |
| T-06-03 | Spoofing | forged week selection | mitigate | Queried week = `leaderboard_crypto.previous_week_id(leaderboard_crypto.current_week_id())` (`main.py:60-62`) / `current_week_id()` (`main.py:74`), both from server time only — `current_week_id` uses `datetime.now(timezone.utc)` (`leaderboard_crypto.py:73`). No client week_id path. Test: `test_scope_last_week_queries_weekly_with_previous_week` (pass). | closed |
| T-06-04 | Denial of service | request flooding on read endpoint | accept | Public read of `{initials,score}` top-10 only; `--max-instances=5` cap live on the service (`cloud_functions/DEPLOY.md:164,171`; STATE.md live revision `get-leaderboard-00003-fzk`). No new attack surface vs existing `week`/`all`. See Accepted Risks Log. | closed |
| T-06-05 | Tampering | scope query-string assembly | mitigate | `api_service.py:34` — `url += f"?{urlencode({'scope': scope})}"` (safe escaping, not string concat). Server independently allow-lists (T-06-01). Test: `tests/test_api_service.py::test_get_leaderboard_sends_scope_param` (pass). | closed |
| T-06-06 | Tampering/Spoofing | forged/malformed leaderboard response (MITM/hostile endpoint) | mitigate | `api_service.py:31-40` — fetch+parse wrapped in `try/except Exception: return None`; malformed body → None → UI "Could not connect." Display is read-only `{initials,score}`; your-best tracked locally. Test: `tests/test_api_service.py::test_get_leaderboard_network_error` (pass). | closed |
| T-06-07 | Denial of service | hung/slow endpoint blocking client | mitigate | `api_service.py:36` — `urlopen(req, timeout=timeout)`; default 10s (`api_service.py:30`); launch passes `BANNER_FETCH_TIMEOUT_SECONDS`. Test: `tests/test_api_service.py::test_get_leaderboard_passes_timeout` (pass, asserts 2 and default 10). | closed |
| T-06-08 | Tampering | unsigned marker file | accept | `marker.py` is plain JSON, no HMAC/obfuscation (D-13). A wrong/edited marker only changes a cosmetic banner; controls no score/submission/server state. Verified no signing seam: `tests/test_marker.py::test_marker_module_has_no_signing_imports` (pass). See Accepted Risks Log. | closed |
| T-06-09 | Denial of service | marker IO crashing startup | mitigate | `marker.py:52-64` (write try/except → `pass`) and `marker.py:76-85` (read try/except → None). Tests: `test_write_marker_never_raises_on_dump_failure`, `test_write_marker_never_raises_on_open_failure` (pass). | closed |
| T-06-10 | Tampering | malformed/corrupt marker on load | mitigate | `marker.py:76-81` — `except Exception: return None` (cold start / corrupt / unreadable → re-baseline); stale-week → None at `marker.py:83-84`. Test: `tests/test_marker.py::test_read_marker_malformed_json_returns_none` (pass). | closed |
| T-06-11 | Information disclosure | marker contents | accept | `marker.py:54-62` stores only `{week_id, tracked_best, initials_above}` — player's own best + already-public initials. No PII, no HMAC secret (D-09), local-only. See Accepted Risks Log. | closed |
| T-06-12 | Spoofing | spoofed got-passed rival data (forged/MITM board) | accept | Banner is cosmetic — built from board `initials` only (`main.py:107`); player tracks own best locally (`main.py:151`) and never trusts board to identify self (machine_id stripped server-side, T-06-02). Cannot alter score/submission/server state. See Accepted Risks Log. | closed |
| T-06-13 | Denial of service | hung/dead network blocking startup before menu | mitigate | `main.py:105` — `api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)`; single blocking call BEFORE the menu loop (`main.py:101-109` precede `while True` at `main.py:112`), no threading, no retry. `BANNER_FETCH_TIMEOUT_SECONDS = 2` (`settings.py:104`). None → banner skipped (`main.py:106`). | closed |
| T-06-14 | Information disclosure | banner/board leaking private data | mitigate | Banner built from `e["initials"]` only (`main.py:107`; `menu.py:44-47` renders the string). Board projection is `{initials,score}` (T-06-02) — no machine_id, no PII. | closed |
| T-06-15 | Tampering | marker baseline manipulation to fake/suppress banner | accept | Same control posture as T-06-08 — marker unsigned by design (D-13); editing only changes a cosmetic banner. See Accepted Risks Log. | closed |
| T-06-16 | Denial of service | marker write crashing on submit or board-open | mitigate | `marker.write_marker` best-effort (`marker.py:52-64`, try/except → silent); called in submit path (`main.py:152`) and board-open path (`main.py:167`); launch read guarded (`main.py:101`). A write failure cannot break submit or board exit. | closed |
| T-06-SC | Tampering | npm/pip/cargo installs | mitigate | No package installs across the phase. `main.py` (stdlib + pygame, already vendored), `api_service.py` (stdlib `urllib`/`json`), `marker.py` (stdlib `json`/`datetime` + local `paths`/`settings`), `get_leaderboard/main.py` (stdlib + already-vendored firebase_admin/functions_framework). | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-06-04 | T-06-04 | Read endpoint flood. Public read of `{initials,score}` top-10 only; `--max-instances=5` flood/cost cap live on the service (D-11, Phase 4; DEPLOY.md:164,171). No per-request rate limit is the accepted residual. No new attack surface vs existing `week`/`all` scopes. | Plan author (Phase 4 D-11 carried forward) | 2026-06-20 |
| AR-06-08 | T-06-08 | Marker file is unsigned/unobfuscated by design (D-13) — the deliberate inverse of the Phase-5 identity blob. A wrong/edited marker is harmless (worst case: a wrong or suppressed cosmetic banner). Controls no score, submission, or server state. Tamper-proofing would be security theater. | Plan author (D-13) | 2026-06-20 |
| AR-06-11 | T-06-11 | Marker stores only the player's own tracked best + initials already public on the board. No PII, no HMAC secret (kept out per D-09), local-only. | Plan author (D-13) | 2026-06-20 |
| AR-06-12 | T-06-12 | Spoofed/MITM rival data can only over/under-name passers in a cosmetic banner; cannot alter score/submission/server state. Player tracks own best locally and never trusts the board to identify self (machine_id stripped server-side). | Plan author (Phase 5 D-03) | 2026-06-20 |
| AR-06-15 | T-06-15 | Marker baseline manipulation = same posture as AR-06-08; editing only changes a cosmetic banner. No security impact. | Plan author (D-13) | 2026-06-20 |

*Accepted risks do not resurface in future audit runs.*

---

## Unregistered Flags

None. No SUMMARY.md (`06-01`..`06-04`) contains a `## Threat Flags` section; `06-04-SUMMARY.md` `## Threat Surface` explicitly states "No new surface beyond the plan's `<threat_model>`." No new attack surface appeared during implementation without a threat mapping.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-06-20 | 16 | 16 | 0 | gsd-security-auditor |

Cited test evidence executed during audit: `tests/test_get_leaderboard.py`, `tests/test_api_service.py`, `tests/test_marker.py` → 34 passed (`.venv` Python).

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-06-20
