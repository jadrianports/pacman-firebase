---
phase: 03-box-bug-fix-hygiene
verified: 2026-06-12T00:00:00Z
status: passed
score: 10/10 must-haves verified
overrides_applied: 0
resolution: "Re-bless completed 2026-06-12 in a Linux python:3.12 container (canonical bless authority, matches CI) — commit 7c120e5. All 9 masters re-recorded; every scenario's first divergence is frame 340 (verified via host git diff); only the 9 trace.jsonl files changed; full suite green on Linux (61 passed, 9 skipped). human_needed condition resolved."
human_verification:
  - test: "Linux golden re-bless — RESOLVED 2026-06-12 (commit 7c120e5; Linux container; 61 passed on Linux)"
    expected: "All 9 trace.jsonl masters re-recorded; every bless diff rooted at the frame-340 in-ring inky flip (400,358); pytest 0 failed after re-bless — CONFIRMED"
    why_human: "Was a Linux-CI-only operation (Windows float drift forbidden). Completed via local Linux container, the canonical bless authority."
  - test: "Human before/after GIF gate (D-08) — watch the canonical before/after playthrough GIF"
    expected: "Only difference is box-region behavior for eaten/returning ghosts in the ring; nothing else moved; no soft-lock, oscillation, wall-clip, or eaten-eyes glitch"
    why_human: "Visual/play-feel confirmation cannot be automated; GIF review requires human judgment"
  - test: "PyInstaller .exe smoke-run (D-14) — launch dist/pacman/pacman.exe and play a few frames"
    expected: "Ghost and Pac-Man sprites render correctly from bundled assets/ghosts/ and assets/pacman/; no missing-image crash"
    why_human: "Already completed per 03-01-SUMMARY.md (APPROVED), but is recorded here for completeness as a mandatory pre-merge gate that CI cannot perform"
---

# Phase 3: Box-Bug-Fix + Hygiene Verification Report

**Phase Goal:** "Unify the ghost-box bounds (the one sanctioned, isolated behavior change) and finish dependency/repo/doc/asset cleanup."
**Verified:** 2026-06-12T00:00:00Z
**Status:** passed
**Re-verification:** Yes — re-bless completed 2026-06-12 in Linux container (commit 7c120e5); full suite green on Linux (61 passed, 9 skipped). All 10 must-haves verified.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Client deps pygame and pyinstaller are pinned with == in requirements.txt; backend cloud_functions pins untouched | VERIFIED | `requirements.txt` contains exactly `pygame==2.6.1` and `pyinstaller==6.20.0`; no cloud_functions file modified |
| 2 | .claude/settings.local.json is no longer tracked by git; .gitignore has a single /.claude line and no CLAUDE.md line | VERIFIED | `git ls-files .claude/settings.local.json` returns empty; .gitignore has exactly 1 `/.claude` line and 0 `CLAUDE.md` lines |
| 3 | CLAUDE.md is tracked by git and its Ghost Box Exit prose reads ~0.5 s / ~1 s for Pinky/Clyde | VERIFIED | `git ls-files CLAUDE.md` returns `CLAUDE.md`; prose reads "Pinky after ~0.5 sec, Clyde after ~1 sec" |
| 4 | menu.py:run_main_menu docstring no longer references 'Change Initials' | VERIFIED | `grep -c 'Change Initials' menu.py` returns 0 |
| 5 | assets/ghost_images/ and assets/player_images/ no longer exist; live assets/ghosts/ + assets/pacman/ intact | VERIFIED | Both dead folders absent; live folders confirmed present; no live-code references to *_images |
| 6 | geometry.py exposes a single GHOST_BOX_BOUNDS = (350, 550, 360, 480); the two old constants are gone | VERIFIED | Line 24: `GHOST_BOX_BOUNDS = (350, 550, 360, 480)`; grep confirms zero `GHOST_BOX_BOUNDS_TARGET` or `GHOST_BOX_BOUNDS_COLLISION` in any .py file |
| 7 | game.py:get_targets and ghost.py:check_collisions both import and use GHOST_BOX_BOUNDS (no old names remain anywhere) | VERIFIED | game.py has 9 refs (import line 18 + 8 call sites lines 240/249/258/267/275/282/289/296); ghost.py has 2 refs (import line 4 + call site line 384) |
| 8 | The oracle proves isolation: 18,496 get_targets comparisons, 1,728 divergences 100% in-ring, 0 out-of-ring; belt-check byte-identical; teeth-check RED-then-green; oracle deleted | VERIFIED | Documented in 03-02-SUMMARY.md with commit a40ce4c (oracle) and f45a712 (unify + delete); `test ! -f tests/test_box_bounds_oracle.py` passes; 03-REVIEW.md confirms 0 critical / 0 warning |
| 9 | 15 micro-tests stay green untouched | VERIFIED | `pytest -q tests/test_ghost_micro.py` — 15 passed in 0.05s |
| 10 | Golden traces re-blessed in Linux CI; pytest exits 0 after re-bless | HUMAN NEEDED | On Windows: 10 failed / 5 passed — exactly the 9 baseline golden replay tests + test_claude_session_replays_green. This is BY DESIGN: re-bless is a Linux-CI-only operation (forbidden on Windows to prevent float-drift corruption). The differential oracle is the authoritative isolation proof; re-bless is corroborating confirmation pending Linux CI. |

**Score:** 9/10 truths verified (10th is a Linux-CI human gate, not an implementation gap)

### Deviation from Plan: ALL 9 Golden Traces Diverge (Broader than D-06 Assumed)

The plan (D-06) expected ONLY box_edge + box_exit traces to move. In reality ALL 9 golden scenarios diverge — but every one is rooted at the SAME single in-ring decision: frame 340, inky at (400, 358), inside TARGET (340,560,340,500) but outside COLLISION (350,550,360,480) (y=358 falls in the 2px ring band between COLLISION y_lo=360 and TARGET y_lo=340). The unified tighter box flips inky from aim-at-gate to chase-player one frame sooner, and deterministic replay amplifies that one legitimate in-ring flip across all 9 traces.

**Impact on correctness:** None. The oracle independently proves no out-of-ring change is possible (zero out-of-ring divergences across 18,496 comparisons). Isolation holds at the CODE level. The broader trace footprint is deterministic cascade, not new out-of-ring behavior.

**Impact on re-bless scope:** The Linux re-bless must re-record ALL 9 trace.jsonl files (not just 2). Every bless diff must be rooted at the frame-340 inky flip.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `requirements.txt` | Pinned pygame== and pyinstaller== | VERIFIED | `pygame==2.6.1`, `pyinstaller==6.20.0` |
| `.gitignore` | Single /.claude, no CLAUDE.md line | VERIFIED | 1x `/.claude`, 0x `CLAUDE.md` |
| `CLAUDE.md` | Tracked; box-exit prose ~0.5 s / ~1 s | VERIFIED | Tracked + prose correct |
| `menu.py` | Docstring drops 'Change Initials' | VERIFIED | 0 matches for 'Change Initials' |
| `geometry.py` | GHOST_BOX_BOUNDS = (350, 550, 360, 480); old constants gone | VERIFIED | Present at line 24; no old names in any .py |
| `game.py` | Import + 8 call sites use GHOST_BOX_BOUNDS | VERIFIED | 9 total references confirmed |
| `ghost.py` | Import + line 384 use GHOST_BOX_BOUNDS | VERIFIED | 2 references confirmed; value unchanged from _COLLISION |
| `tests/test_box_bounds_oracle.py` | Absent (transient by design, deleted in fix commit) | VERIFIED | File does not exist — correct |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| game.py:get_targets (8 call sites) | geometry.GHOST_BOX_BOUNDS | in_box(ghost_x, ghost_y, GHOST_BOX_BOUNDS) | WIRED | Lines 240, 249, 258, 267, 275, 282, 289, 296 all confirmed |
| ghost.py:check_collisions | geometry.GHOST_BOX_BOUNDS | in_box(self.x_pos, self.y_pos, GHOST_BOX_BOUNDS) | WIRED | Line 384 confirmed; value identical to old _COLLISION |
| CLAUDE.md Ghost Box Exit prose | settings.py BOX_EXIT_DELAY_PINKY=30 / CLYDE=60 | Doc reconciliation (60fps → seconds) | WIRED | Prose reads ~0.5 s / ~1 s; constants read 30 / 60 — correct |
| geometry.py docstring | Historical divergence guard | Comment noting old (340,560,340,500) vs (350,550,360,480) | WIRED | Comment present; "Do NOT merge these" prose gone (0 matches) |

### Data-Flow Trace (Level 4)

Not applicable — this phase modifies game-logic constants and documentation, not data-rendering components with dynamic state/props.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| 15 ghost micro-tests green | `pytest -q tests/test_ghost_micro.py` | 15 passed in 0.05s | PASS |
| All non-golden tests pass | `pytest -q --ignore=tests/test_golden_traces.py` | 46 passed, 9 skipped | PASS |
| Golden traces fail on Windows (by design) | `pytest -q tests/test_golden_traces.py` | 10 failed, 5 passed | EXPECTED — Windows-only; re-bless is Linux-CI gate |
| GHOST_BOX_BOUNDS unified constant present | `grep -c 'GHOST_BOX_BOUNDS = (350, 550, 360, 480)' geometry.py` | 1 | PASS |
| Old constant names absent | `grep -rc 'GHOST_BOX_BOUNDS_TARGET\|GHOST_BOX_BOUNDS_COLLISION' *.py` | 0 matches | PASS |
| Oracle file deleted | `test ! -f tests/test_box_bounds_oracle.py` | not found | PASS |

### Probe Execution

No probe scripts declared or applicable for this phase.

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| BUG-01 | 03-02-PLAN.md | Unified GHOST_BOX_BOUNDS; behavior change provably isolated to box region | SATISFIED (impl complete) | geometry.py line 24; game.py 9 refs; ghost.py 2 refs; oracle proof in 03-02-SUMMARY.md; 0 out-of-ring divergences; Linux re-bless pending |
| HYG-01 | 03-01-PLAN.md | Client dependencies pinned in requirements.txt | SATISFIED | pygame==2.6.1; pyinstaller==6.20.0 confirmed |
| HYG-02 | 03-01-PLAN.md | settings.local.json untracked; .gitignore reconciled | SATISFIED | git ls-files returns empty; single /.claude; no CLAUDE.md line |
| HYG-03 | 03-01-PLAN.md | Doc drift fixed (box-exit timing; dead Change Initials docstring) | SATISFIED | CLAUDE.md prose correct; menu.py 0 matches |
| HYG-04 | 03-01-PLAN.md | Dead duplicate asset folders removed | SATISFIED | ghost_images/ + player_images/ absent; ghosts/ + pacman/ present; no live-code refs |

All 5 requirement IDs from PLAN frontmatter are accounted for. No orphaned phase-3 requirements found in REQUIREMENTS.md.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| None | — | — | — | No TBD/FIXME/XXX/TODO/HACK/PLACEHOLDER markers found in any phase-modified file |

No debt markers, no stubs, no placeholder returns found in geometry.py, game.py, ghost.py, menu.py, requirements.txt, or CLAUDE.md.

### Human Verification Required

#### 1. Linux CI Golden Re-Bless (REQUIRED BEFORE MERGE — BLOCKER for CI-green)

**Test:** On Linux/WSL/CI only, run: `pytest tests/test_golden_traces.py --bless`
**Expected:** All 9 trace.jsonl masters re-recorded; pytest then exits 0 with 0 failed. Every bless diff must be rooted at frame 340, inky at (400, 358) — the single in-ring flip from aim-at-gate to chase-player. The bless must be committed (folded onto f45a712 or as a follow-up commit in the same PR) so CI stays green.
**Why human:** Windows float drift corrupts the Linux-authored golden masters. Re-bless on Windows is explicitly FORBIDDEN by the phase design. This is the one remaining gate before the Phase-3 PR can merge CI-green.

Note on current Windows test state: `10 failed, 5 passed` on `test_golden_traces.py` — exactly the 9 scenario replays + `test_claude_session_replays_green`. This is by design and matches the documented expectation. The 5 that pass (invariant checks + capture smoke) are unaffected.

#### 2. Before/After GIF Gate (D-08)

**Test:** Watch the before/after canonical-playthrough GIF produced by the Claude adversarial playtest (stored in tests/artifacts/, gitignored).
**Expected:** The only visible difference is the box-region behavior for eaten/returning ghosts in the ~10px x / ~20px y ring between the two old rectangles (switching aim-at-gate to chase-player a touch sooner). Nothing else moved. No soft-lock, pen-mouth oscillation, wall-clip, or eaten-eyes glitch.
**Why human:** Visual/play-feel confirmation of an intentional AI behavior change requires human judgment. Claude's own playtest (D-07) found no issues; the GIF is the final human sign-off.

Per 03-02-SUMMARY.md, this gate was APPROVED: "the human confirmed nothing is broken or glitchy (the change is so surgical the playthroughs look essentially identical)."

#### 3. PyInstaller .exe Smoke-Run (D-14)

**Test:** Run `python build.py` and launch `dist/pacman/pacman.exe` (NOT build/pacman/pacman.exe — that is PyInstaller's working dir).
**Expected:** Bundle produces dist/pacman/pacman.exe; sprites render from bundled assets/ghosts/ and assets/pacman/; no missing-image crash.
**Why human:** PyInstaller bundling and sprite rendering cannot be verified headlessly in CI.

Per 03-01-SUMMARY.md, this gate was APPROVED.

### Gaps Summary

No implementation gaps found. All code-level work is complete and verified:

- BUG-01: GHOST_BOX_BOUNDS unified, importers repointed, isolation proven by oracle (18,496 comparisons, 1,728 in-ring, 0 out-of-ring), oracle deleted, 15 micro-tests green.
- HYG-01..04: requirements.txt pinned, settings.local.json untracked, .gitignore reconciled, CLAUDE.md tracked + corrected, menu.py docstring cleaned, dead asset folders deleted.

The only remaining gate is the Linux CI golden re-bless of all 9 trace.jsonl files, which is a required human/CI operation (forbidden on Windows). This is correctly classified as a human_verification item, not an implementation gap. Both D-08 (GIF gate) and D-14 (.exe smoke-run) were approved during execution per their respective SUMMARYs.

---

_Verified: 2026-06-12T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
