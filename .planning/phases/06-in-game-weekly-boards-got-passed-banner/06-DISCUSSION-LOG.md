# Phase 6: In-Game Weekly Boards & Got-Passed Banner - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-19
**Phase:** 6-in-game-weekly-boards-got-passed-banner
**Areas discussed:** Last-week champion source, Board toggle UX, Got-passed banner logic, Banner placement & timing, Banner accuracy mechanics, Board fetch strategy, Empty & cold-start states, Your-row highlight & styling

---

## Last-Week Champion Source (BOARD-04)

| Option | Description | Selected |
|--------|-------------|----------|
| Add scope=last_week | New scope value querying `week_id == previous_week_id(current_week_id())`; reuses the existing query + composite index | ✓ |
| Embed in weekly response | Add a `last_week_champion` field to the `scope=week` payload | |
| You decide | Hand the mechanism to research/planning | |

**User's choice:** Add scope=last_week
**Notes:** Paired with payload choice → return the **same top-10 shape** (`{entries:[{initials,score}]}`); client takes `entries[0]`. (Alt: champion-only payload — rejected for shape consistency.) → CONTEXT D-01.

---

## Board Toggle UX (BOARD-03)

| Option | Description | Selected |
|--------|-------------|----------|
| Default view: This Week | Open on the weekly board (server default, competitive focus) | ✓ |
| Default view: All Time | Open on all-time (closest to today's single board) | |
| Toggle: LEFT/RIGHT arrows | Arrow keys flip the two boards + `< This Week \| All Time >` indicator | ✓ |
| Toggle: TAB | TAB cycles the active board | |
| Toggle: Up/Down or a letter | Some other binding | |
| Champ line: Subtitle on This Week | Under the header, This Week view only | ✓ |
| Champ line: Persistent line | Always under the header regardless of view | |
| Champ line: Footer line | Down by the back hint | |

**User's choice:** This Week default · LEFT/RIGHT toggle with tab indicator · "Last week: BOB" subtitle on This Week only
**Notes:** → CONTEXT D-02, D-03, D-04.

---

## Got-Passed Banner Logic (RIVAL-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Watch This Week | Your this-week best vs the weekly board; no weekly score → no banner | ✓ |
| Watch All Time | Your all-time best vs the all-time board | |
| Watch both boards | Track passes on both, name together | |
| Name all, capped | List new passers' initials, cap to one line (e.g. JIM, BOB, ACE +2 more) | ✓ |
| Top passer only | Name just the single highest new score | |
| Name all, no cap | List every passer regardless of count | |
| Reset only on opening board | Baseline updates only when the player actually views the board | ✓ |
| Clear once shown | Baseline updates as soon as the banner displays at launch | |

**User's choice:** This Week · name all (capped) · reset only when the board is opened
**Notes:** → CONTEXT D-05, D-06, D-07. Faithful to RIVAL-01's "since they last viewed the board."

---

## Banner Placement & Timing (RIVAL-01 presentation)

| Option | Description | Selected |
|--------|-------------|----------|
| Line on the main menu | Prominent non-blocking line under the title, reuses run_main_menu | ✓ |
| Pre-menu callout screen | A brief dedicated screen before the menu | |
| Transient splash | Auto-dismissing toast (needs frame-counted timing) | |
| Quick blocking check | One startup fetch, short timeout, silent skip if slow/offline | ✓ |
| Never block launch | Background/async fetch so the menu never waits | |
| Clears when you open the board | Opening the board clears it + resets the cross-launch baseline | ✓ |
| Clears on acknowledge | Any keypress/game-start dismisses it for the session | |
| Stays all session | Remains on the menu until app close | |

**User's choice:** Main-menu line · quick blocking fetch (short timeout) · clears when the board is opened
**Notes:** → CONTEXT D-08, D-09, D-10. One coherent rule: board-open both clears and re-baselines.

---

## Banner Accuracy Mechanics

| Option | Description | Selected |
|--------|-------------|----------|
| Track what you submit | Persist your max this-week score locally, stamped with week_id | ✓ |
| Locate yourself on the board | Find your row by initials (+score) | |
| Passer key: by initials | Store initials above you at last view; new = initials newly above | ✓ |
| Passer key: by initials + score | Any (initials, score) change above you counts as new | |
| Passer key: by count only | Compare how many sit above you | |

**User's choice:** Track your own submissions for "your best" · detect new passers by initials
**Notes:** → CONTEXT D-11, D-12. machine_id is stripped (Phase 4 D-10), so no self-location on the board; same-initials collision accepted as harmless (Phase 5 D-03).

---

## Board Fetch Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy per view | Open fetches This Week (+ last-week subtitle); All Time on first toggle; cache per visit | ✓ |
| Fetch all on open | Fetch week, all, last_week up front | |
| Degrade per view | Each view shows its own offline line; subtitle hides on failure; other view still works | ✓ |
| Whole screen offline | Any single failure marks the entire screen offline | |

**User's choice:** Lazy per view · degrade per view
**Notes:** → CONTEXT D-14, D-15. `api_service.get_leaderboard` gains a `scope` param.

---

## Empty & Cold-Start States

| Option | Description | Selected |
|--------|-------------|----------|
| No last-wk champ: hide subtitle | Render nothing where the subtitle would go | ✓ |
| No last-wk champ: show a dash | "Last week: —" placeholder | |
| Empty week: weekly variant | "No scores yet this week. Be the first!" | ✓ |
| Empty week: reuse generic | Existing "No scores yet. Be the first!" on both boards | |

**User's choice:** Hide the subtitle when no champ · weekly-specific empty-state wording
**Notes:** → CONTEXT D-16, D-17. All Time keeps the original empty-state line.

---

## Your-Row Highlight & Styling

| Option | Description | Selected |
|--------|-------------|----------|
| No self-highlight | Keep current styling (rank 1 yellow, rest white) | ✓ |
| Best-effort highlight | Highlight the row matching your initials + tracked best score | |
| Defer to UI-SPEC | Leave self-highlight to /gsd-ui-phase | |

**User's choice:** No self-highlight
**Notes:** → CONTEXT D-19. Tab-indicator look + overall board visuals can route to /gsd-ui-phase (UI hint: yes).

---

## Claude's Discretion

- Marker file name + on-disk format (unsigned JSON).
- Short launch-fetch timeout value (~1–3s).
- Banner color/placement + name-cap count (subject to /gsd-ui-phase).
- `scope` query-param wiring in `api_service.get_leaderboard` and the per-view cache held in the board loop.
- The initials-above-you set representation + duplicate-initials tie handling.
- Whether the last-week subtitle fetch is issued alongside the week fetch on open or just-in-time.

## Deferred Ideas

- Full last-week leaderboard view (scope=last_week returns top-10; Phase 6 shows only the champ) — natural for Phase 7 / future.
- Self-row highlight — revisit only if a reliable self-identifier exists.
- Season-history archives / friend groups — already out of scope for v1.1 (BOARD-F1 / SOCL-F1).
