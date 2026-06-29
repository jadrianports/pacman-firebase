---
phase: 9
slug: arcade-juice
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-06-30
---

# Phase 9 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Derived from
> `09-RESEARCH.md` → Validation Architecture. The phase success signal is **full `pytest`
> green with NO `--bless`** (golden state traces + frame-hash manifest unchanged).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (repo-root `tests/conftest.py`; SDL dummy video+audio drivers forced) |
| **Config file** | `tests/conftest.py` (no `pytest.ini`; registers the `--bless` flag) |
| **Quick run command** | `.venv/Scripts/python.exe -m pytest tests/test_juice_firewall.py tests/test_determinism_guard.py -q` |
| **Full suite command** | `.venv/Scripts/python.exe -m pytest -q` |
| **Golden subset** | `.venv/Scripts/python.exe -m pytest tests/test_golden_traces.py tests/test_frame_hash.py -q` |
| **Estimated runtime** | ~30 seconds (full suite, local) |

> Note: local `.venv` is **pygame-ce 2.5.7** and SKIPS the frame-hash assertion on Windows;
> the Linux CI run (vanilla pygame 2.6.1) is the frame-hash authority. Restrict new juice
> visuals/tests to dual-edition-safe primitives (`draw.polygon`/`circle`, `Surface.fill` +
> `BLEND_RGB_ADD`). Do NOT use `gaussian_blur` (pygame-ce only).

---

## Sampling Rate

- **After every task commit:** Run the quick command (firewall + determinism guard) — catches the two highest-risk regressions fast.
- **After every plan wave:** Run the golden subset (`test_golden_traces` + `test_frame_hash`) plus the new feature tests.
- **Before `/gsd-verify-work`:** Full suite must be green.
- **Phase gate:** full `pytest` green **with no `--bless`**, and the Linux CI run green (frame-hash asserts only there). NO re-bless is the success signal.
- **Max feedback latency:** ~10 seconds (quick command).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-W0 | Wave 0 | 0 | FEEL-01/03/04 | — | N/A | unit (stubs) | `.venv/Scripts/python.exe -m pytest tests/test_death_anim.py tests/test_eat_ghost_sound.py tests/test_fright_flash.py -q` | ❌ W0 | ⬜ pending |
| FEEL-01 | death | 1 | FEEL-01 | — | wedge draws only under `dying and juice`; `juice=False` dying unchanged | unit + firewall | `.venv/Scripts/python.exe -m pytest tests/test_death_anim.py -x` | ❌ W0 | ⬜ pending |
| FEEL-01b | death | 1 | FEEL-01 | — | a dying frame under `juice=True` raises nothing (`player_circle` safe) | unit | `.venv/Scripts/python.exe -m pytest tests/test_death_anim.py::test_dying_juice_frame_ok -x` | ❌ W0 | ⬜ pending |
| FEEL-03 | sound | 1 | FEEL-03 | T-asset (license) | `play_eat_ghost` uses Channel(2), no-raise headless; called on bite | unit | `.venv/Scripts/python.exe -m pytest tests/test_eat_ghost_sound.py -x` | ❌ W0 | ⬜ pending |
| FEEL-04 | flash | 1 | FEEL-04 | — | `Ghost.draw` blits white when `blink_white`, spooked otherwise | unit (pixel) | `.venv/Scripts/python.exe -m pytest tests/test_fright_flash.py -x` | ❌ W0 | ⬜ pending |
| FEEL-04b | flash | 1 | FEEL-04 | — | `create_ghosts` computes `blink_white=False` whenever `juice=False` | unit | `.venv/Scripts/python.exe -m pytest tests/test_fright_flash.py::test_blink_off_under_juice_false -x` | ❌ W0 | ⬜ pending |
| SC5-traces | all | * | SC5 (golden) | — | `juice=False` golden state traces byte-identical | regression | `.venv/Scripts/python.exe -m pytest tests/test_golden_traces.py -q` | ✅ | ⬜ pending |
| SC5-hash | all | * | SC5 (golden) | — | `juice=False` frame-hash manifest unchanged (Linux CI authority) | regression | `.venv/Scripts/python.exe -m pytest tests/test_frame_hash.py -q` (CI) | ✅ | ⬜ pending |
| SC5-firewall | all | * | SC5 (golden) | — | two `juice=False` games render byte-identical | regression | `.venv/Scripts/python.exe -m pytest tests/test_juice_firewall.py -q` | ✅ | ⬜ pending |
| determinism | all | * | SC5 (golden) | — | no `random`/wall-clock in game.py/ghost.py/player.py | static | `.venv/Scripts/python.exe -m pytest tests/test_determinism_guard.py -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_death_anim.py` — FEEL-01: juice-gated wedge; `juice=False` dying unchanged; no-raise dying frame.
- [ ] `tests/test_eat_ghost_sound.py` — FEEL-03: `play_eat_ghost` channel + headless no-raise; spy that the eat branch calls it.
- [ ] `tests/test_fright_flash.py` — FEEL-04: white-vs-spooked blit; `blink_white` off under `juice=False`.
- [ ] `settings.py` constants (with failing tests referencing them, phase-8 pattern): `DEATH_ANIM_FRAMES`, `FRIGHT_FLASH_START`, `FRIGHT_FLASH_INTERVAL`.
- [ ] Optional belt-and-braces: extend a firewall-style test to replay the `death`/`power_chase` scenarios under `juice=False` twice and assert identical frame hashes (before CI).

*Existing infrastructure (`test_golden_traces`, `test_frame_hash`, `test_juice_firewall`, `test_determinism_guard`, `harness/replay.install_frame_driven_sound`) covers all SC5 regression requirements — reused unchanged.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Eat-ghost `.wav` feel + licensing | FEEL-03 | Subjective audio feel; license must be human-verified (D-10) | Play a session, eat a frightened ghost, confirm the bite is audible over the paused siren and "feels" retro; confirm the chosen `.wav` is CC0/permissive or self-authored and record source+author+license in a NOTICE line. |
| Death wedge cadence vs `death.wav` | FEEL-01 | "End together" timing (D-04) is tuned by ear | Die in-game with `juice=True`; confirm the wedge collapse finishes about when `death.wav` ends; dial `DEATH_ANIM_FRAMES` in `settings.py` if off. |
| Frightened blink readability | FEEL-04 | Discretionary look/cadence (D-07) judged visually | Trigger a power pellet, watch the last ~2s; confirm the white blink clearly signals "no longer safe"; adjust `FRIGHT_FLASH_INTERVAL`/tint if it reads poorly. |
| New `.wav` ships in exe | FEEL-03 | PyInstaller asset bundling (A4) | Build with `python build.py`; confirm the new `assets/audio/*.wav` is present in `dist/pacman/` and the eat sound plays in the built exe. |

---

## Validation Sign-Off

- [ ] All tasks have an automated verify or a Wave 0 dependency
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s (quick command)
- [ ] Golden state traces + frame-hash manifest green with NO `--bless`
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
