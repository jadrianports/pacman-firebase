---
status: partial
phase: 02-safe-refactor
source: [02-VERIFICATION.md]
started: 2026-06-12T00:00:00Z
updated: 2026-06-12T00:00:00Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. D-19 Before/After GIF gate — ghost AI visually indistinguishable
expected: Running `harness/capture.py` `build_gif` on a canonical playthrough produces a before/after montage in which the refactored ghost AI (data-driven `_move` + per-ghost `*_PROFILE`) is visually indistinguishable from the pre-refactor recording. The automated byte-identity proof (384k-case geometry oracle + 138k-case per-ghost mover oracle + 9 golden traces + 15 micro tests + frame-hash net) is already complete; this GIF is the human-readable seal of approval.
result: [pending]

## Summary

total: 1
passed: 0
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
