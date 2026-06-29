# Phase 9: Arcade Juice - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-30
**Phase:** 9-Arcade Juice
**Areas discussed:** Death animation (FEEL-01), Frightened-end flash (FEEL-04), Eat-ghost sound (FEEL-03)

---

## Area selection

Scouting revealed the juice firewall + `juice.py`/`theme.py` and FEEL-02 (eat popup/freeze) + FEEL-05
("READY!") already shipped via the earlier "Bold" UI redesign. Offered 4 areas; user selected the
three **unbuilt** items and skipped "Confirm done items (FEEL-02/05)" → accepted as-is.

| Area offered | Selected |
|--------------|----------|
| Death animation (FEEL-01) | ✓ |
| Eat-ghost sound (FEEL-03) | ✓ |
| Frightened-end flash (FEEL-04) | ✓ |
| Confirm done items (FEEL-02/05) | — (accepted as-is) |

---

## Death animation (FEEL-01)

### Style

| Option | Description | Selected |
|--------|-------------|----------|
| Classic wedge spin | Mouth opens wider, wedge rotates and shrinks to a point, then vanishes. pygame arcs. | ✓ |
| Particle disintegrate | Bursts into glowing sparks via juice.Particles. | |
| Both — spin then burst | Wedge-spin collapse + spark burst at the end. | |

**User's choice:** Classic wedge spin (arcade-faithful).

### Timing vs death.wav

| Option | Description | Selected |
|--------|-------------|----------|
| Fill the death.wav window | Plays across the existing `dying` phase (waits for death.wav), then +60-frame pause + reset. | ✓ |
| Fixed ~1s, then hold | Fixed ~60 frames, hold until death.wav finishes. | |
| You decide | Planner picks. | |

**User's choice:** Fill the death.wav window.
**Notes:** Renders only under `juice=True`; `juice=False` keeps today's held-sprite behavior (death terminal untouched).

---

## Frightened-end flash (FEEL-04)

### Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Last ~2s (≈120 frames) | Blink in the final ~2s of the 600-frame power window (`power_counter > ~480`). Arcade-faithful. | ✓ |
| Last ~3s (≈180 frames) | More lead time. | |
| Named tunable, default ~2s | Settings constant, default ~2s. | |

**User's choice:** Last ~2s (≈120 frames). *(Captured in CONTEXT as a named `settings.py` tunable defaulting to ~2s — best of both.)*

### Look

| Option | Description | Selected |
|--------|-------------|----------|
| Blue ↔ white alternate | Alternate spooked-blue with a white-tinted sprite. | |
| Blue ↔ original color | Alternate spooked-blue with the ghost's normal colored sprite. | |
| You decide | Planner picks (likely white tint of spooked_img). | ✓ |

**User's choice:** You decide.

---

## Eat-ghost sound (FEEL-03)

### Source

| Option | Description | Selected |
|--------|-------------|----------|
| You'll drop in a .wav | User provides the asset. | |
| I find a CC0/free .wav | Claude sources a freely-licensed retro eat-ghost .wav, adds to assets/audio/. | ✓ |
| Pitch an existing sound | Derive from an existing .wav, no new asset. | |

**User's choice:** I find a CC0/free .wav. **Notes:** Runtime synthesis ruled out — numpy/sndarray not installed (would add a client dep). User verifies licensing/feel during playtest.

### Mix vs powerup siren

| Option | Description | Selected |
|--------|-------------|----------|
| Play over freeze, keep current mix | Bite fires while siren is paused for the freeze, then siren resumes. | |
| You decide | Planner picks channel/timing. | ✓ |

**User's choice:** You decide. **Notes:** Sound is exempt from the juice firewall (audio doesn't touch hashed paths).

---

## Claude's Discretion

- FEEL-04 blink look/cadence and exact white/tint mechanism.
- FEEL-03 sound channel/timing mix vs the siren.
- Exact death-wedge geometry/arc math and frame cadence within the death.wav window.

## Deferred Ideas

None — discussion stayed within phase scope. FEEL-02 (eat popup/freeze) and FEEL-05 ("READY!")
reviewed and accepted as-is.
