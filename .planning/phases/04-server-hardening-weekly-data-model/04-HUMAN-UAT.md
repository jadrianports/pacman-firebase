---
status: partial
phase: 04-server-hardening-weekly-data-model
source: [04-VERIFICATION.md]
started: 2026-06-19
updated: 2026-06-19
---

## Current Test

[awaiting human testing — requires redeploy of the CR-01 fix first]

## Tests

### 1. Valid-format invalid-key HMAC rejection
expected: HTTP 401 {"success": false, "error": "Invalid signature"} when a well-formed HMAC
computed under the WRONG key is submitted — exercises the constant-time compare path, not just
the non-string type-check fast path.
result: [pending]

### 2. Weekly board populated end-to-end
expected: after an unsigned (grace-window) submit, the param-less GET to get_leaderboard returns
that score in `entries` with `{initials, score}` only (no machine_id / week_id leak), HTTP 200.
result: [pending]

### 3. CR-01 fix is live (post-redeploy)
expected: after redeploying both services from the fixed source, a POST with a malformed
`signature` (e.g. a JSON list `["x"]` or a non-ASCII string) returns HTTP 401 (NOT 500).
result: [pending]

## Summary

total: 3
passed: 0
issues: 0
pending: 3
skipped: 0
blocked: 0

## Gaps

- The hardened+fixed code (HEAD) is committed and green locally, but the LIVE Cloud Run
  revisions still run the pre-fix code. Redeploy both services (same `gcloud run deploy --source`
  commands as the initial deploy) before running tests 1-3. After redeploy, the orchestrator can
  run all three checks via curl (test 2 writes a throwaway row — clean up `leaderboard/smoketest`
  + `weekly/smoketest_<week>` afterward if desired).
