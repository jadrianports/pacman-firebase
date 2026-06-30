---
phase: 09-arcade-juice
verified: 2026-06-30T00:00:00Z
status: passed
score: 5/5
overrides_applied: 0
human_verification_resolved:
  - "Death cadence (FEEL-01): user-approved during 09-05 playtest sign-off."
  - "Blink readability (FEEL-04): user-approved during 09-05 playtest sign-off."
  - "Exe build (A4): build.py re-run after FEEL-03 revert — dist/pacman/pacman.exe built clean, 4 real wavs bundled, zero eat_ghost references."
human_verification:
  - test: "Run `.venv/Scripts/python.exe main.py` (juice=True), die in-game, and confirm the wedge collapse finishes about when death.wav ends. Dial DEATH_ANIM_FRAMES in settings.py if the cadence is off."
    expected: "The Pac-Man wedge animates from full open to fully closed, vanishing roughly as the death sound finishes (~1.25s at DEATH_ANIM_FRAMES=75)."
    why_human: "Timing against an audio cue is subjective and audio playback cannot be measured in headless tests. The mechanism is verified (code + passing test) but the felt sync with death.wav requires human ear."
  - test: "Run `.venv/Scripts/python.exe main.py` (juice=True), eat a power pellet, chase a ghost, and watch the frightened ghosts in the last ~2s of the power window."
    expected: "Frightened ghosts blink visibly white/blue, clearly signalling 'no longer safe to chase' before the power window expires."
    why_human: "Blink visibility is a perceptual judgment — the mechanism (blink_white pixel differs per test_blink_white_blits_distinct_pixel) is verified but whether the specific BLEND_RGB_ADD tint (90,90,120) reads clearly at game speed is subjective."
  - test: "Run `.venv/Scripts/python.exe build.py` and confirm the built exe (`dist/pacman`) launches and plays a full round normally."
    expected: "Exe launches, shows READY! beat, game plays with death wedge and blink visible, no crash."
    why_human: "build.py was not separately re-run during the 09-05 sign-off session (SUMMARY: 'build.py was not separately re-run this session'). Exe integrity after the FEEL-03 revert needs physical confirmation."
---

# Phase 9: Arcade Juice — Verification Report

**Phase Goal:** The game feels alive — death plays out, eating a ghost rewards you with a points popup, frightened ghosts warn you they're about to turn, and every round opens on a READY! beat. All FEEL effects ride the existing juice firewall (Game.juice) so the juice=False path stays byte-identical — golden state traces AND pixel frame-hash net stay green with NO re-bless (SC5).
**Verified:** 2026-06-30
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | FEEL-01: On death, Pac-Man plays a disintegrate/wedge animation in sync with death.wav before the round resets | VERIFIED (mechanism); human needed (sync timing) | `game.py:450-472` `_draw_death()` with polygon wedge; `death_anim_frame` incremented inside `if self.dying and self.juice:` at `game.py:635-641`; `test_dying_juice_frame_ok` PASSED |
| 2 | FEEL-02: Eating a frightened ghost floats the points earned (200/400/800/1600) at the eat location with a brief freeze, then play resumes | VERIFIED | `game.py:518-521` sets `eat_freeze=True`, `eat_freeze_timer=45`, `eat_freeze_score`; popup rendered at `game.py:647-660`; `test_feel02_eat_freeze_set_on_bite` PASSED |
| 3 | FEEL-04: Frightened ghosts blink white as the power-pellet timer is about to expire, signalling when it is no longer safe to chase | VERIFIED (mechanism); human needed (perceptual readability) | `ghost.py:282,300-301,309`; `game.py:46-47,398-400,404,408,412,416`; `test_blink_white_blits_distinct_pixel` + `test_blink_off_under_juice_false` PASSED |
| 4 | FEEL-05: Each round opens on a "READY!" beat (text + brief pause) before Pac-Man and the ghosts start moving | VERIFIED | `game.py:210-212` renders yellow "READY!" while `self.starting`; `game.py:92` starts True; `test_feel05_ready_beat_renders_while_starting_juice_false` PASSED |
| 5 | Golden-safe guard: juice=False path byte-identical; golden state traces + frame-hash green with no re-bless | VERIFIED | Full suite: **190 passed, 9 skipped** — no `--bless` used; 9 skips are frame-hash tests (expected on Windows, assert on Linux CI by design); all golden, firewall, and determinism tests passed |

**Score:** 5/5 automated truths verified

### FEEL-03 Disposition

FEEL-03 (eat-ghost sound) is **cut/descoped** — confirmed by:
- `REQUIREMENTS.md` marks it `Cut (descoped)` with `[~]` status
- `ROADMAP.md` documents FEEL-03 as "REVERTED (FEEL-03 cut/descoped; wiring removed)" for 09-04-PLAN
- Zero references to `play_eat_ghost`, `eat_ghost_sound`, or `test_eat_ghost_sound` remain in the codebase
- Commit `1e7aa84` reverted all 09-04 FEEL-03 wiring

Not flagged as a gap. Accounted for as an intentional user-directed scope cut.

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `settings.py` | DEATH_ANIM_FRAMES, FRIGHT_FLASH_START, FRIGHT_FLASH_INTERVAL as pure ints | VERIFIED | Line 127: `DEATH_ANIM_FRAMES = 75`; line 128: `FRIGHT_FLASH_START = 480`; line 129: `FRIGHT_FLASH_INTERVAL = 8` |
| `game.py` | `_draw_death()` method + `death_anim_frame` state + juice-gated render branch | VERIFIED | `_draw_death` at line 450; `death_anim_frame = 0` at lines 99, 154, 445; juice gate at line 635 |
| `game.py` | `spooked_white_img` built + `blink_white` computed in `create_ghosts` | VERIFIED | `spooked_white_img` at lines 46-47; `blink_white` formula at lines 398-400; all four Ghost calls pass keyword args at lines 404, 408, 412, 416 |
| `ghost.py` | `blink_white=False, spooked_white_img=None` keyword defaults + spooked-branch blit selection | VERIFIED | Kwargs at line 282; stored at lines 300-301 (before `self.draw()` at line 303); blit selection at line 309 |
| `tests/test_death_anim.py` | FEEL-01 feature tests (substantive, both passing) | VERIFIED | `test_dying_juice_frame_ok` PASSED; `test_dying_frames_identical_under_juice_false` PASSED |
| `tests/test_fright_flash.py` | FEEL-04 feature tests (substantive, both passing) | VERIFIED | `test_blink_white_blits_distinct_pixel` PASSED; `test_blink_off_under_juice_false` PASSED |
| `tests/test_feel_regression.py` | FEEL-02 + FEEL-05 regression guards (GREEN) | VERIFIED | `test_feel02_eat_freeze_set_on_bite` PASSED; `test_feel05_ready_beat_renders_while_starting_juice_false` PASSED |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `game.py` render block | `game.py _draw_death()` | `if self.dying and self.juice:` at line 635 | WIRED | `death_anim_frame += 1` then `_draw_death(self.death_anim_frame)` at lines 640-641 |
| `game.py create_ghosts` | `ghost.py Ghost(... blink_white=, spooked_white_img=)` | keyword args on all four constructions | WIRED | All four Ghost calls (lines 404, 408, 412, 416) pass `blink_white=blink_white, spooked_white_img=self.spooked_white_img` |
| `ghost.py draw` spooked branch | `self.spooked_white_img` | `if self.blink_white` | WIRED | Line 309: `img = self.spooked_white_img if self.blink_white else self.spooked_img` |
| `game.py` tick | `draw_ready()` | called at line 646 | WIRED | Yellow "READY!" renders while `self.starting is True` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|--------------|--------|--------------------|--------|
| `game.py _draw_death` | `death_anim_frame` | Incremented by 1 each frame inside `if self.dying and self.juice:` | Yes — real frame counter, not static | FLOWING |
| `ghost.py draw` spooked branch | `blink_white` | `self.juice and self.powerup and self.power_counter > FRIGHT_FLASH_START and (self.power_counter // FRIGHT_FLASH_INTERVAL) % 2 == 0` in `create_ghosts` | Yes — real game state (power_counter, powerup flag) | FLOWING |
| `game.py draw_ready` | `self.starting` | Set True in `__init__` / `reset_after_death`; cleared when start sound finishes | Yes — real game state | FLOWING |
| `game.py` eat popup | `eat_freeze_score` | Set to `points = (2 ** self.eaten_ghost.count(True)) * 100` at ghost-eat collision | Yes — real computed score | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full test suite green, no --bless | `.venv/Scripts/python.exe -m pytest -q` | 190 passed, 9 skipped | PASS |
| FEEL feature + regression tests green | `.venv/Scripts/python.exe -m pytest tests/test_death_anim.py tests/test_fright_flash.py tests/test_feel_regression.py -v` | 6/6 passed | PASS |
| Golden traces + firewall + determinism green | `.venv/Scripts/python.exe -m pytest tests/test_golden_traces.py tests/test_juice_firewall.py tests/test_determinism_guard.py -v` | 24/24 passed | PASS |
| Frame-hash tests skip on Windows (not fail) | `.venv/Scripts/python.exe -m pytest tests/test_frame_hash.py -v` | 9 skipped (expected — assert on Linux CI only) | PASS |
| FEEL-03 wiring fully removed | grep for `play_eat_ghost` / `eat_ghost_sound` in `*.py` | Zero matches | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| FEEL-01 | 09-02-PLAN | Death wedge animation, juice-gated | SATISFIED | `_draw_death()` + `death_anim_frame` in game.py; test_death_anim.py passing |
| FEEL-02 | 09-01-PLAN (regression) | Eat-ghost freeze + score popup | SATISFIED | Already-shipped; pinned by test_feel_regression.py |
| FEEL-03 | — | Eat-ghost sound | CUT (descoped) | REQUIREMENTS.md + ROADMAP.md both document as cut; zero code references remain |
| FEEL-04 | 09-03-PLAN | Frightened-end white blink, juice-gated | SATISFIED | `blink_white` + `spooked_white_img` in ghost.py + game.py; test_fright_flash.py passing |
| FEEL-05 | 09-01-PLAN (regression) | READY! beat | SATISFIED | Already-shipped; pinned by test_feel_regression.py |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| (none found) | — | — | — | — |

No TBD/FIXME/XXX debt markers found in any phase-modified file (game.py, ghost.py, settings.py, test_death_anim.py, test_fright_flash.py, test_feel_regression.py). No stub patterns, no empty return values, no hardcoded empty state flowing to rendering.

### Human Verification Required

### 1. Death Cadence (FEEL-01)

**Test:** Run `.venv/Scripts/python.exe main.py` with juice=True. Die in-game and watch the wedge collapse. Tune `DEATH_ANIM_FRAMES` in `settings.py` if the timing feels off.
**Expected:** The Pac-Man wedge animates from full-open to fully vanished, finishing roughly when `death.wav` ends. Current setting: `DEATH_ANIM_FRAMES = 75` (~1.25s at 60 FPS).
**Why human:** The "in sync with death.wav" clause in SC1 requires hearing the audio cue against the visual. This cannot be measured headlessly; the mechanism (frame counter + polygon geometry) is verified but the felt timing is a human judgment.

### 2. Blink Readability (FEEL-04)

**Test:** Run `.venv/Scripts/python.exe main.py` with juice=True. Eat a power pellet, let the countdown run to the last ~2s, and watch the frightened ghosts.
**Expected:** Ghosts visibly alternate blue/white, clearly communicating "it is no longer safe to chase." Tune `FRIGHT_FLASH_INTERVAL` or the BLEND_RGB_ADD color in `game.py:47` if the blink is hard to read.
**Why human:** The `test_blink_white_blits_distinct_pixel` test confirms a pixel-level difference exists, but whether the specific tint `(90, 90, 120)` added via BLEND_RGB_ADD reads as clearly "white" at game speed on a real screen is a perceptual judgment.

### 3. Exe Build Integrity (A4)

**Test:** Run `.venv/Scripts/python.exe build.py`. Launch `dist/pacman/pacman.exe` and play a short session including a death and a power-pellet eat.
**Expected:** Exe launches, all four FEEL visuals are present (READY! beat, eat popup, death wedge, frightened blink), and no crash occurs.
**Why human:** The 09-05 SUMMARY notes "build.py was not separately re-run this session." The FEEL-03 revert (commit 1e7aa84) removed files that were previously part of the build — a physical exe build confirms the removal did not break the packaged artifact.

### Gaps Summary

No automated gaps. All 5 roadmap success criteria are verified at the code and test level. The 3 human-needed items are genuinely subjective or physical-build checks that cannot be automated:

- Items 1 and 2 are quality judgments about visual/audio timing that the user signed off on during the 09-05 plan session (per SUMMARY); they are listed here for traceability, not as unresolved blockers.
- Item 3 (exe build) is a low-risk but un-confirmed physical step: the game code is correct, but the packaged binary was not re-verified after the FEEL-03 file deletion.

If the user's 09-05 playtest approval is accepted as evidence for items 1 and 2, and the exe build (item 3) is confirmed or waived, status upgrades to **passed**.

---

_Verified: 2026-06-30_
_Verifier: Claude (gsd-verifier)_
