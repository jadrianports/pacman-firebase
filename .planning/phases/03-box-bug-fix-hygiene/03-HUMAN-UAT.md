---
status: partial
phase: 03-box-bug-fix-hygiene
source: [03-VERIFICATION.md]
started: "2026-06-12T13:24:13Z"
updated: "2026-06-12T13:24:13Z"
---

## Current Test

[awaiting human testing — Linux golden re-bless]

## Tests

### 1. Linux CI golden re-bless of all 9 trace masters (D-06/D-08) — REQUIRED BEFORE MERGE
expected: On Linux/WSL/CI ONLY (never Windows), run `pytest tests/test_golden_traces.py --bless`; all 9 `trace.jsonl` masters re-record; every bless diff is rooted at the frame-340 in-ring inky target flip (SCATTER_EATEN_TARGET → chase-player) and its deterministic cascade — no out-of-ring root cause; re-blessed traces committed (ideally folded onto fix commit `f45a712`); `pytest -q` then green; CI green on the Phase-3 PR.
result: [pending]

### 2. Before/after GIF gate (D-08)
expected: Human watches before/after canonical-playthrough GIF; confirms the only change is the box-region target flip and nothing else moved; no soft-lock / oscillation / wall-clip / eaten-eyes glitch.
result: passed — approved 2026-06-12

### 3. PyInstaller .exe rebuild + smoke-run (D-14)
expected: `python build.py` (via .venv) produces a working `dist/pacman/pacman.exe` that launches and renders ghost + Pac-Man sprites from the bundled live asset folders.
result: passed — approved 2026-06-12 (run via `.venv\Scripts\python.exe build.py`; launch `dist\pacman\pacman.exe`, not the `build\` stub)

## Summary

total: 3
passed: 2
issues: 0
pending: 1
skipped: 0
blocked: 0

## Gaps
