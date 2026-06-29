---
phase: 08
slug: fairness-pass
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-06-29
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.
> Seeded from `08-RESEARCH.md` § Validation Architecture (lines 301-329).

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (CI: Python 3.12, pygame 2.6.1, `SDL_*=dummy`) |
| **Config file** | `tests/conftest.py` (registers `--bless`); CI `.github/workflows/ci.yml` |
| **Quick run command** | `.venv/Scripts/python.exe -m pytest tests/test_ghost_micro.py tests/test_determinism_guard.py -q` |
| **Full suite command** | `.venv/Scripts/python.exe -m pytest -q` (frame-hash asserts only in pinned CI/Linux env) |
| **Estimated runtime** | quick ~3s · full suite ~20-40s |

---

## Sampling Rate

- **After every task commit:** Run `.venv/Scripts/python.exe -m pytest tests/test_ghost_micro.py tests/test_determinism_guard.py -q` — fast guard that the byte-identical (ghost decision logic) and determinism invariants still hold.
- **After every plan wave:** Run the full suite — golden net skips frame-hash off-CI but asserts the state traces.
- **Before `/gsd-verify-work`:** Full suite green in the pinned CI/Linux env **after** the single re-bless; ghost micro-tests + determinism guard green **without** the re-bless (the byte-identical proof artifact).
- **Max feedback latency:** ~3 seconds (quick guard).

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | FAIR-01/02/03 | — | N/A (local game constants) | source-assert | `grep -E "GHOST_CATCH_DISTANCE|GHOST_CHASE_SPEED_NUM|GHOST_CHASE_SPEED_DEN|PLAYER_TURN_WINDOW_MARGIN" settings.py` | ✅ | ⬜ pending |
| 08-01-02 | 01 | 1 | FAIR-03 | — | N/A | unit (xfail-strict) | `.venv/Scripts/python.exe -m pytest tests/test_player_micro.py -q` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | FAIR-01/02 | — | N/A | unit (xfail-strict) | `.venv/Scripts/python.exe -m pytest tests/test_fairness_unit.py -q` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | FAIR-01 | — | N/A | unit + golden | `.venv/Scripts/python.exe -m pytest tests/test_fairness_unit.py -k catch -q` | ✅ (after W0) | ⬜ pending |
| 08-02-02 | 02 | 2 | FAIR-02 | — | N/A | unit + golden | `.venv/Scripts/python.exe -m pytest tests/test_fairness_unit.py -k accumulator -q` | ✅ (after W0) | ⬜ pending |
| 08-03-01 | 03 | 2 | FAIR-03 | — | N/A | unit + golden | `.venv/Scripts/python.exe -m pytest tests/test_player_micro.py -q` | ✅ (after W0) | ⬜ pending |
| 08-04-01 | 04 | 3 | FAIR-01/02/03 | — | N/A | manual (human-verify) | D-10 Windows playtest sign-off — see Manual-Only | n/a | ⬜ pending |
| 08-04-02 | 04 | 3 | FAIR-01/02/03 | — | N/A | golden re-bless | `docker run python:3.12` → `pytest --bless` + terminal-scenario verify | ✅ (Linux/Docker only) | ⬜ pending |
| 08-04-03 | 04 | 3 | FAIR-01/02/03 (byte-identical guard) | — | N/A | characterization | `.venv/Scripts/python.exe -m pytest tests/test_ghost_micro.py tests/test_determinism_guard.py -q` + `git diff --stat ghost.py` == 0 | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

**Threat Ref:** all tasks `—` (no new attack surface — offline single-player local simulation math; see `08-RESEARCH.md` § Security Domain, `security_block_on: high` not reached).

---

## Wave 0 Requirements

- [ ] `tests/test_player_micro.py` — characterization for the new cornering window: assert `Player.check_position` yields the widened `turns_allowed` at a crafted junction with `PLAYER_TURN_WINDOW_MARGIN`, plus a default-margin baseline. **No player-level characterization test exists today** (verified), so FAIR-03 is otherwise guarded only by golden traces. (Authored RED via `@pytest.mark.xfail(strict=True)` in 08-01.)
- [ ] `tests/test_fairness_unit.py` — (a) FAIR-02 accumulator: feed N frames, assert the produced integer step sequence and that the running average converges to `GHOST_CHASE_SPEED_NUM/DEN`; (b) FAIR-01 catch helper: corner-kiss (diagonal one-tile) → not caught, same-tile overlap → caught, using crafted `center_*` values. Pure-Python, no pygame. (Authored RED via `xfail(strict=True)` in 08-01.)
- [ ] Existing `tests/conftest.py` already provides `--bless` + headless fixtures — no new conftest needed.

*xfail-strict bridge: Wave 1 authors these tests asserting post-change behavior wrapped in `@pytest.mark.xfail(strict=True)` so the suite stays green at wave merge; Wave 2 removes each marker as its test turns green.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| The game *feels* fair/escapable; final dial-in of the four tunables | FAIR-01/02/03 (D-10) | "Feels right" is a human playtest judgement; tunables are starting points within CONTEXT ranges | Run `python main.py` on Windows; play several rounds; adjust `GHOST_CATCH_DISTANCE` (~15), `GHOST_CHASE_SPEED_NUM/DEN` (~1.85), `PLAYER_TURN_WINDOW_MARGIN` (~6) until corner-kisses read safe, you can pull away on a straight, and early turns land; then sign off. (Plan 08-04 Task 1, blocking checkpoint.) |
| Frame-hash golden manifests re-bless | FAIR-01/02/03 (re-bless) | Frame-hash pixels are platform-pinned — must be blessed in the Linux `python:3.12` env, never Windows (Pitfall 3) | After sign-off: `docker run --rm -v "$PWD":/app -w /app python:3.12` → install deps → `pytest --bless`; first confirm `death`/`ghost_eat` still reach their scripted terminal (re-author `input.jsonl` if not). One re-bless covers all three FAIR changes. (Plan 08-04 Task 2.) |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies (08-04-01 is the single sanctioned human checkpoint per D-10)
- [x] Sampling continuity: no 3 consecutive tasks without automated verify (quick guard runs at every commit)
- [x] Wave 0 covers all MISSING references (`test_player_micro.py`, `test_fairness_unit.py`)
- [x] No watch-mode flags
- [x] Feedback latency < 3s (quick guard)
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-06-29
