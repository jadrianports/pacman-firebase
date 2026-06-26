---
phase: 04-server-hardening-weekly-data-model
plan: 04
subsystem: infra
tags: [cloud-run, secret-manager, firestore, deploy, hmac, leaderboard, gcloud]

# Dependency graph
requires:
  - phase: 04-01
    provides: HMAC verify path + leaderboard_crypto (secret read at call time, canonical JSON contract)
  - phase: 04-02
    provides: MAX_SCORE 50k ceiling, HMAC grace gate, weekly doc model, permanent initials
  - phase: 04-03
    provides: scope-aware get_leaderboard (week|all) whose weekly path needs the composite index
provides:
  - cloud_functions/DEPLOY.md operational deploy/secret/index/max-instances checklist
  - Live deploy of both Cloud Run services (pacman = submit_score, get-leaderboard) from the hardened source
  - Secret Manager secret leaderboard-hmac-secret referenced as env var LEADERBOARD_HMAC_SECRET on both services
  - REQUIRE_SIGNATURE=false grace flag live on submit_score (P4->P5 window)
  - max-instances=5 flood cap on both services (D-11)
  - Firestore composite index on weekly (week_id ASC, score DESC) Enabled and serving
affects: [05-client-identity-hardening, 06-in-game-weekly-boards, 07-web-leaderboard-page]

# Tech tracking
tech-stack:
  added:
    - "Google Secret Manager (leaderboard-hmac-secret) referenced into both Cloud Run runtimes"
    - "Firestore composite index on weekly (week_id ASC, score DESC)"
  patterns:
    - "Deploy seam: gcloud run deploy <svc> --source --function=<entrypoint> from Cloud Shell (these are Cloud Run services, not GCF API objects)"
    - "Secret lives in Secret Manager + a safe operator copy for Phase 5; never in git, never in config surface, never logged"
    - "Grace flag REQUIRE_SIGNATURE=false until the Phase 5 signed client ships (D-02)"

key-files:
  created:
    - cloud_functions/DEPLOY.md
  modified: []

key-decisions:
  - "Deploy-model correction: the two functions are Cloud Run services (pacman, get-leaderboard), deployed via `gcloud run deploy --source --function=<entrypoint>` in Cloud Shell — NOT GCF API objects and NOT a Console click-path. DEPLOY.md's Console steps map to the equivalent gcloud run-deploy operations."
  - "REQUIRE_SIGNATURE=false on submit_score (pacman) for the P4->P5 grace window; flipped to true only after Phase 5 signed client ships (D-02)"
  - "max-instances=5 on both services (D-11 flood cap; chosen at the top of the 3-5 band)"
  - "HMAC secret value kept out of git — only the procedure is documented; operator holds a safe copy for the Phase 5 shared-secret seam"

patterns-established:
  - "Cloud Run via gcloud from Cloud Shell is the real, faster deploy path; the Console click-path in DEPLOY.md is the equivalent fallback"
  - "Live smoke checks against the deployed URLs are the acceptance gate for COMP-01 / BOARD-01 / BOARD-02 enforcement"

requirements-completed: [COMP-01, COMP-02, COMP-03, BOARD-01, BOARD-02]

# Metrics
duration: 1 day (operator-paced; live deploy deferred 2026-06-19, completed 2026-06-19)
completed: 2026-06-19
---

# Phase 4 Plan 04: Manual Deploy & Live Hardening Summary

**Both Cloud Run services (pacman + get-leaderboard) redeployed from the hardened source with the HMAC secret referenced from Secret Manager, REQUIRE_SIGNATURE=false grace flag, max-instances=5, and an Enabled weekly composite index — live smoke checks confirm COMP-01 rejection and the index-backed weekly board.**

## Performance

- **Duration:** Operator-paced (live deploy deferred at the human-verify checkpoints on 2026-06-19, completed same day)
- **Completed:** 2026-06-19
- **Tasks:** 3 (1 auto + 2 human-verify checkpoints, all complete)
- **Files modified:** 1 (cloud_functions/DEPLOY.md, authored in Task 1)

## Accomplishments

- **Task 1 (auto):** Authored `cloud_functions/DEPLOY.md` — the full ordered deploy/secret/index/max-instances/redeploy checklist with the secret value kept out of git and the Phase 5 shared-secret seam noted. Committed `80480b8`.
- **Task 2 (human-verify):** Secret Manager secret `leaderboard-hmac-secret` (created 2026-06-18) confirmed; `roles/secretmanager.secretAccessor` granted to the runtime SA `991339031546-compute@developer.gserviceaccount.com` on both services; both services deployed referencing the secret as env var `LEADERBOARD_HMAC_SECRET=leaderboard-hmac-secret:latest`, with `REQUIRE_SIGNATURE=false` on `pacman` (submit_score).
- **Task 3 (human-verify):** `--max-instances=5` set on both services (D-11); Firestore composite index on `weekly` (`week_id ASC, score DESC`, index id `CICAgOjXh4EK`) created and Enabled; both services redeployed in `asia-southeast1` (new revisions `pacman-00005-7rk` and `get-leaderboard-00003-fzk`, each serving 100% traffic).
- **The hardened code (Plans 01-03) is now LIVE and enforcing** — the server is the enforcement boundary for COMP-01/COMP-02/COMP-03 and serves the index-backed weekly board (BOARD-01/BOARD-02).

## Deploy-Model Correction (worth recording)

The two functions are **Cloud Run services**, not Cloud Functions API objects:

| Service | Code (entrypoint) | Role |
|---------|-------------------|------|
| `pacman` | `submit_score` | score submission + HMAC verification + grace gate |
| `get-leaderboard` | `get_leaderboard` | scope-aware reader (week|all) |

The actual deploy used `gcloud run deploy` from **Cloud Shell**, not the Console click-path DEPLOY.md describes (equivalent outcome). The real, faster path for a future operator:

```bash
gcloud run deploy <svc> --source=<dir> --function=<entrypoint> --allow-unauthenticated \
  --max-instances=5 --update-secrets=LEADERBOARD_HMAC_SECRET=leaderboard-hmac-secret:latest \
  [--update-env-vars=REQUIRE_SIGNATURE=false]   # the env-var only on pacman/submit_score
```

A short "Actual deploy path used (Cloud Run via gcloud)" note was appended to `cloud_functions/DEPLOY.md` so the faster path is recorded alongside the Console fallback (existing content preserved).

## Live Smoke Checks (PASSED, run against the live URLs)

1. **COMP-01 enforcement live** — `POST` to submit_score (`pacman`) with a **bogus** `signature` → **HTTP 401** `{"success":false,"error":"Invalid signature"}`. Invalid signatures are always rejected, even during the grace window.
2. **BOARD-01/BOARD-02 + composite index serving** — param-less `GET` to get_leaderboard (weekly default) → **HTTP 200** `{"entries":[]}`. A `200` (not a `500` missing-index error) confirms the `weekly` composite index is Enabled and serving the default-week path.
3. **All-time retained + D-10 projection** — `GET get_leaderboard?scope=all` → **HTTP 200** `{"entries":[{"initials":"JAP","score":7540},{"initials":"JEM","score":4140}]}`. All-time board retained, `{initials, score}`-only projection (no `machine_id`/`week_id`), and existing scores are well under the new 50k cap.

## Requirement Coverage

| Requirement | How it is now live |
|-------------|--------------------|
| COMP-01 (server verifies HMAC) | Invalid-signature POST → 401 against live `pacman`; secret injected from Secret Manager |
| COMP-02 (score sanity ceiling) | MAX_SCORE=50k code (Plan 04-02) deployed and serving; existing scores well under cap |
| COMP-03 (permanent initials, grace gate) | Hardened submit_score deployed; `REQUIRE_SIGNATURE=false` grace flag live on `pacman` (unsigned accepted, invalid rejected) |
| BOARD-01 (weekly write/read) | Weekly read path index-backed; param-less GET → 200 weekly board |
| BOARD-02 (all-time retained) | `?scope=all` → 200 with retained all-time entries |

## Files Created/Modified

- `cloud_functions/DEPLOY.md` — operational deploy/secret/index/max-instances/redeploy checklist (Task 1); short "Actual deploy path used (Cloud Run via gcloud)" note appended in this continuation. No cloud_functions code changed in this plan.

## Decisions Made

- **Deploy model is Cloud Run via gcloud, not GCF Console clicks** — recorded so future operators use the faster, real path. Console steps remain as an equivalent fallback in DEPLOY.md.
- **max-instances=5** chosen at the top of the documented 3-5 band for both services (D-11).
- **REQUIRE_SIGNATURE=false** held on submit_score (`pacman`) until the Phase 5 signed client ships (D-02) — flipping early would 401 every already-shipped unsigned exe.
- **HMAC secret value stays out of git** — only the procedure is documented; the operator holds a safe copy for the Phase 5 shared-secret seam.

## Deviations from Plan

None - plan executed as written. The only refinement is operational: the live deploy used `gcloud run deploy` from Cloud Shell rather than the Console click-path DEPLOY.md describes (the two services are Cloud Run, not GCF API objects). The outcome is equivalent and the faster path is now recorded in DEPLOY.md. The DEPLOY.md content authored in Task 1 was not removed or rewritten.

## Authentication / Human Gates

Tasks 2 and 3 were `checkpoint:human-verify` gates (Console/Cloud Shell operations only an operator can perform — secret creation, IAM grant, index creation, redeploy). Both were completed by the operator and verified via the three live smoke checks above. This is the expected human-in-the-loop flow for a manual-deploy model, not a deviation.

## Issues Encountered

None during this continuation. The earlier deferral (operator paused at the Task 2 checkpoint on 2026-06-19) was an expected human-gated pause, now resolved.

## User Setup Required

Completed by the operator during Tasks 2-3 (Secret Manager secret + IAM grant + env-var reference + grace flag + max-instances + composite index + redeploy). No further setup is required for Phase 4. The HMAC secret value must be retained safely for the Phase 5 client build (shared-secret seam).

## Next Phase Readiness

- The hardened server is **live and enforcing** — Phase 5 (client identity hardening) can now build the signing half against a known, verifying server.
- **Phase 5 must embed the identical HMAC secret string** (operator's safe copy) so client signatures verify; once the signed client ships and friends update, flip `REQUIRE_SIGNATURE` to `true` on `pacman` (D-02).
- Weekly board is index-backed and serving — Phases 6/7 (in-game boards, web page) can consume the scope-aware API.

## Self-Check: PASSED

- `cloud_functions/DEPLOY.md` exists (Task 1, committed `80480b8`).
- Task 1 commit `80480b8` confirmed in `git log`.
- Tasks 2-3 verified live: revisions `pacman-00005-7rk` / `get-leaderboard-00003-fzk` serving 100%; three smoke checks passed (401 on bogus signature; 200 `{"entries":[]}` weekly; 200 all-time with `{initials,score}` projection).

---
*Phase: 04-server-hardening-weekly-data-model*
*Completed: 2026-06-19*
