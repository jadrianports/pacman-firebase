# Phase 8: Fairness Pass - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-29
**Phase:** 8-Fairness Pass
**Areas discussed:** Catch tightness, Escape speed gap, Corner forgiveness, Tuning loop

---

## Catch tightness (FAIR-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Tight (~half tile) | Catch radius ~14px (half a tile); arcade-faithful; kills all corner-kisses | ✓ |
| Moderate (~full tile) | Catch radius ~24px; catches a bit sooner; closer to today | |
| Just-fix-corners | Keep generosity but require both axes close; minimal change | |

**User's choice:** Asked for a recommendation ("what do you suggest tho?"), then confirmed ("okay")
the recommended **Tight / arcade-faithful** option.
**Notes:** Recommendation grounded in: the milestone is about *unfair* catches; tight is what real
Pac-Man does (tile-based collision, sprites bigger than the tile, so visual overlap before a catch is
arcade-authentic); moderate/just-fix-corners leave cheap-feeling catches. Folded in: set value a hair
above pure half-tile (~16px) to avoid pass-through look; lock the *intent* (tight, tunable), not the
exact pixel.

---

## Escape speed gap (FAIR-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Subtle / arcade-faithful | Pac ~5-10% faster (Pac≈2.0, ghost≈1.85); pull away gradually; tense | ✓ |
| Noticeable edge | Pac clearly faster (ghost≈1.6); shake a ghost on a short straight; less arcade | |
| You decide | Lean subtle/arcade-faithful, tunable | |

**User's choice:** **Subtle / arcade-faithful.**
**Notes:** Claude surfaced the diagnosis that Pac and ghosts are both speed 2 (equal) today → no
escape possible; the "unbeatable" feeling is equal-speed, not a literal ×2 chase tier. Captured
implementation lean: keep PLAYER_SPEED=2 (hands feel identical), slow chasing ghosts; leave
eyes-return speed (4) alone; flagged sub-pixel/determinism handling for the researcher.

---

## Corner forgiveness (FAIR-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Snappy / arcade-faithful | Window opens ~4-6px early; forgives timing, no overshoot | (lean) |
| Generous / modern | Window opens ~10-14px early; very forgiving, can feel auto-steered | |
| You decide | Lean snappy/arcade-faithful, tunable | ✓ |

**User's choice:** **You decide** → Claude leans snappy / arcade-faithful (~4–6px early window on the
existing input buffer), tunable.
**Notes:** Today turns register only in the ~7px at-junction window (`12 <= center % TILE <= 18`);
early input is dropped → overshoot. Build on `direction_command` / `update_direction`.

---

## Tuning loop

| Option | Description | Selected |
|--------|-------------|----------|
| Build → you playtest → re-bless | Implement w/ tunable consts; user playtests on Windows & signs off; THEN one Linux/Docker re-bless | ✓ |
| Defaults + dev hotkeys | Same plus throwaway in-game live-tune keys removed before re-bless | |
| Trust defaults | Claude picks values; one confirm playtest; re-bless | |

**User's choice:** **Build → you playtest → re-bless.**
**Notes:** Re-bless happens only after feel is signed off — never against interim numbers. Reinforces
the locked single-re-bless-on-Linux/Docker discipline.

## Claude's Discretion

- Exact final values within the stated ranges (catch ~14–16px, ghost speed ~1.85, corner window
  ~4–6px) — starting points, dialed in by the user during the playtest loop.
- Corner-window mechanic (FAIR-03) explicitly delegated ("You decide").

## Deferred Ideas

None — discussion stayed within phase scope.
