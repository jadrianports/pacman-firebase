---
status: passed
phase: 04-server-hardening-weekly-data-model
source: [04-VERIFICATION.md]
started: 2026-06-19
updated: 2026-06-19
---

## Current Test

[complete — all items passed live on revisions pacman-00006-ltj / get-leaderboard-00004-rfr]

## Tests

### 1. Valid-format invalid-key HMAC rejection
expected: HTTP 401 {"success": false, "error": "Invalid signature"} when a well-formed HMAC
computed under the WRONG key is submitted — exercises the constant-time compare path, not just
the non-string type-check fast path.
result: passed — well-formed wrong-key sig (471ac9f9…) → HTTP 401 {"error":"Invalid signature","success":false}

### 2. Weekly board populated end-to-end
expected: after an unsigned (grace-window) submit, the param-less GET to get_leaderboard returns
that score in `entries` with `{initials, score}` only (no machine_id / week_id leak), HTTP 200.
result: passed — unsigned submit ZZZ/7 → HTTP 200; param-less GET → 200 {"entries":[{"initials":"ZZZ","score":7}]} (no machine_id/week_id)

### 3. CR-01 fix is live (post-redeploy)
expected: after redeploying both services from the fixed source, a POST with a malformed
`signature` (e.g. a JSON list `["x"]` or a non-ASCII string) returns HTTP 401 (NOT 500).
result: passed — list sig ["x"] → HTTP 401; non-ASCII sig → HTTP 401 (both were 500 pre-fix)

## Summary

total: 3
passed: 3
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

None. All items confirmed live 2026-06-19 against revisions pacman-00006-ltj /
get-leaderboard-00004-rfr (the CR-01-fixed source).

Cleanup note: the end-to-end check wrote a throwaway row `machine_id="smoketest"` (initials ZZZ,
score 7). Delete `leaderboard/smoketest` and `weekly/smoketest_<current-week-Monday>` in the
Firestore console if you don't want it on the board.
