---
phase: 09-arcade-juice
plan: 04
subsystem: audio
tags: [pygame, sound, channel, tdd, juice-firewall, golden-safe, feel-03]

# Dependency graph
requires:
  - phase: 09-arcade-juice
    provides: "09-01 RED test net (tests/test_eat_ghost_sound.py) targeting play_eat_ghost on Channel(2) + eat-branch spy"
  - phase: 09-arcade-juice
    provides: "09-03 fright-flash (wave dependency); existing SoundManager dedicated-channel pattern (waka ch0, siren ch1)"
provides:
  - "SoundManager.play_eat_ghost() — one-shot bite cue on dedicated pygame.mixer.Channel(2), None-guarded degraded path"
  - "Ungated (D-02) eat-ghost trigger in Game.check_ghost_collisions eat branch"
affects: [09-05-asset-playtest]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Dedicated mixer channel per controlled sound (eat-ghost -> Channel(2), beside waka ch0 / powerup ch1) so the bite cue is never stolen (Pitfall 6)"
    - "None-guarded one-shot play: _load_sound returns None when the .wav is absent -> method degrades silently until the asset ships (09-05)"
    - "Audio is firewall-exempt (D-02): the trigger is ungated and never touches the hashed pixel path, so goldens stay green with no --bless"

key-files:
  created: []
  modified:
    - sound.py
    - game.py

key-decisions:
  - "play_eat_ghost is a ONE-SHOT (no loops=-1), unlike play_powerup's looping siren — a single bite blip per eat"
  - "Call placed immediately after pause_powerup() in the eat branch and BEFORE break, ungated (D-02) — FEEL-02 eat-freeze state left byte-identical"
  - "Channel(2) needs no set_num_channels call — pygame's default 8 channels already cover it (Pitfall 6)"

patterns-established:
  - "New controlled sound = _load_sound(volume) beside the others + dedicated Channel(N) + None-guarded play method mirroring play_powerup but one-shot"

requirements-completed: [FEEL-03]

# Metrics
duration: 2min
completed: 2026-06-30
---

# Phase 9 Plan 04: Eat-Ghost Sound Summary

**Wired a distinct ungated eat-ghost bite cue — `SoundManager.play_eat_ghost()` on a dedicated `pygame.mixer.Channel(2)`, fired in the `check_ghost_collisions` eat branch — turning the 09-01 RED tests GREEN while golden traces, firewall, and determinism stay green with no re-bless.**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-06-29T23:33:34Z
- **Completed:** 2026-06-29T23:35:52Z
- **Tasks:** 2
- **Files modified:** 2 (sound.py, game.py)

## Accomplishments
- Added `self.eat_ghost_sound = self._load_sound('eat_ghost.wav', volume=0.5)` and `self._eat_channel = pygame.mixer.Channel(2)` to `SoundManager.__init__`, beside the existing death-sound load and dedicated channels.
- Added `play_eat_ghost()` — a None-guarded ONE-SHOT play on Channel(2) (mirrors `play_powerup` shape but no `loops=-1`), no-raise headless / when the .wav is absent.
- Wired one ungated `self.sound.play_eat_ghost()` call after `self.sound.pause_powerup()` in the `check_ghost_collisions` eat branch (game.py:524), before `break`.
- Confirmed the cross-plan TDD cycle closes: both 09-01 RED tests (`test_play_eat_ghost_exists_on_dedicated_channel_no_raise`, `test_eat_branch_calls_play_eat_ghost`) now GREEN.
- Golden state traces + frame-hash + juice firewall + determinism guard + FEEL regression all green with NO `--bless` (SC5 honored).

## Task Commits

1. **Task 1: SoundManager loader + Channel(2) + play_eat_ghost()** - `8dab8e0` (feat)
2. **Task 2: Fire play_eat_ghost on the bite (ungated)** - `cc03ae2` (feat)

## Files Created/Modified
- `sound.py` - eat_ghost.wav loader, `_eat_channel = pygame.mixer.Channel(2)`, one-shot None-guarded `play_eat_ghost()`.
- `game.py` - one ungated `self.sound.play_eat_ghost()` after `pause_powerup()` in the eat branch; FEEL-02 eat-freeze state untouched.

## Decisions Made
- None beyond the plan — implemented exactly as specified (one-shot, Channel(2), ungated, post-pause_powerup placement).

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
- Git emitted an LF→CRLF normalization warning when staging `sound.py` (repo `core.autocrlf`). Harmless — does not affect pytest collection/execution; the CRLF caveat applies to PLAN.md must_haves parsing, not source files.

## Known Stubs
- `assets/audio/eat_ghost.wav` does **not** exist yet — this is intentional and planned. The `_load_sound` None-guard means `play_eat_ghost()` degrades silently (no-raise, no sound) until the real human-sourced CC0/self-authored asset + license NOTICE lands in **09-05** (D-09/D-10). No placeholder/synthetic .wav was invented here. The code ships and the game stays fully playable in the meantime.

## Threat Flags

None — no new trust boundary, network, auth, persistence, or crypto surface. Audio playback only, on a dedicated channel, touching no captured/hashed state.

## Verification
- `.venv/Scripts/python.exe -m pytest tests/test_eat_ghost_sound.py tests/test_golden_traces.py tests/test_juice_firewall.py tests/test_determinism_guard.py tests/test_feel_regression.py tests/test_frame_hash.py -q` → **28 passed, 9 skipped** (frame_hash skips local Windows; asserts on Linux CI). NO `--bless`.
- Acceptance one-liner (`SDL_AUDIODRIVER=dummy ... SoundManager().play_eat_ghost()`) exits 0 — no-raise degraded path confirmed.

## Next Phase Readiness
- 09-05 sources and human-verifies the real `assets/audio/eat_ghost.wav` (+ license NOTICE). Once the file exists, `_load_sound` will pick it up automatically — no further code change required; the bite will be audible.

## Self-Check: PASSED

---
*Phase: 09-arcade-juice*
*Completed: 2026-06-30*
