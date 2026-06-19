---
status: partial
phase: 06-in-game-weekly-boards-got-passed-banner
source: 06-VERIFICATION.md
started: 2026-06-20T00:00:00Z
updated: 2026-06-20T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. In-game tab toggle visual
expected: In the leaderboard screen, LEFT/RIGHT arrows switch between This Week and All Time; the selected tab is highlighted; All Time loads lazily on first switch (brief load, then renders).
result: [pending]

### 2. Live BOARD-04 "Last week:" subtitle
expected: After the operator redeploys the `get_leaderboard` Cloud Function, the This Week view shows a "Last week: <INITIALS> <score>" champion subtitle. (In-repo gate is the validator tests; live behavior depends on the manual redeploy per the api-refactor spec.)
result: [pending]

### 3. Cold-start / offline launch graceful degrade
expected: With no network (or a corrupt/missing marker), the main menu is reached within ~2s and no got-passed banner appears — no crash, no hang. (See CR-01 in 06-REVIEW.md: the launch compute should not break startup.)
result: [pending]

### 4. Full RIVAL-01 end-to-end
expected: After a second player passes your tracked this-week best, the launch banner names them on the next launch; opening the board clears the banner and re-baselines the marker so they are not re-reported.
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
