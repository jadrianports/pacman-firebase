# Requirements: Pac-Man (pacman-firebase) — v1.1 More Competitive

**Defined:** 2026-06-14
**Core Value:** It feels like real Pac-Man — four ghosts with distinct, hand-tuned personalities the player can read and outplay. That behavior is precious and must never silently regress.

**Milestone goal:** Make the leaderboard something friends actually compete on — trustworthy enough that scores can't be casually forged, and alive enough that people keep fighting over it.

> REQ-IDs use new categories (IDENT, COMP, BOARD, WEB, RIVAL) numbered from 01. v1.0 used HRN/TST/REF/BUG/HYG. `COMP-01` here is the formal expression of the anti-cheat gap carried forward from the v1.0 close (scores were client-trusted).

## v1 Requirements

Requirements for this milestone. Each maps to exactly one roadmap phase.

### Identity & Tamper-Resistance (client-side)

- [ ] **IDENT-01**: Player identity files (`machine_id`, initials) are stored outside the game folder (not next to the exe), so they aren't trivially discovered
- [ ] **IDENT-02**: Identity files are stored obfuscated rather than as human-readable plaintext
- [ ] **IDENT-03**: Identity files carry an HMAC signature; the game detects tampering on load and refuses to submit a tampered identity

### Anti-Cheat / Score Integrity (server-side)

- [ ] **COMP-01**: The server verifies the HMAC signature on each score submission and rejects forged or unsigned submissions (a raw `curl` does not make the board)
- [ ] **COMP-02**: The server rejects scores above a sanity ceiling (impossible scores cannot be submitted)
- [ ] **COMP-03**: The server enforces permanent initials — a machine's initials are locked on first submission and cannot be changed by later submissions

### Weekly Boards

- [ ] **BOARD-01**: Scores are bucketed by week; a "This Week" board shows the current week's top scores, resetting at Monday 00:00 UTC
- [ ] **BOARD-02**: An "All Time" board is retained alongside the weekly board
- [ ] **BOARD-03**: The player can toggle between "This Week" and "All Time" views in-game
- [ ] **BOARD-04**: The previous week's champion is shown (e.g. "Last week: BOB")

### Web Leaderboard

- [ ] **WEB-01**: A public web page hosted on Firebase Hosting displays the leaderboard, fetching from the existing API
- [ ] **WEB-02**: The web page is mobile-first / readable on a phone, in an arcade style matching the game
- [ ] **WEB-03**: The web page mirrors the in-game boards (This Week / All Time)

### Rivalry

- [ ] **RIVAL-01**: On launch, the game shows a banner naming any player(s) who have beaten the player's score since they last viewed the board (graceful no-op when offline or on first launch)

## Future Requirements

Acknowledged but deferred — not in this milestone's roadmap.

### Score Integrity

- **COMP-F1**: Replay-verification of scores — server re-runs the recorded input trace through the deterministic sim to confirm the score is earnable. The unforgeable ceiling; deferred because HMAC + sanity ceiling is the right altitude for a friends board.

### Boards

- **BOARD-F1**: Season-history archive — scroll past weekly boards, not just last week's champ.

### Social

- **SOCL-F1**: Private friend groups / join-code boards — scope a board to a specific crew.

## Out of Scope

Explicitly excluded for this milestone, with reasoning, to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Local-file encryption beyond obfuscation + HMAC | Client-side secrets are extractable; the server is the real enforcement boundary. Stronger local crypto is theater. |
| New gameplay (levels, mazes, modes, fruit) | Belongs to the next milestone (More Fun), not Competitive. |
| Changing ghost-AI decision behavior | Locked spec — preserved byte-for-byte; the CI golden net stays green. |
| Friend groups / season archives | Deferred to Future Requirements above; a single shared exe already *is* one friend group. |

## Traceability

Which phase covers which requirement. Populated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| IDENT-01 | Phase 5 | Pending |
| IDENT-02 | Phase 5 | Pending |
| IDENT-03 | Phase 5 | Pending |
| COMP-01 | Phase 4 | In Progress |
| COMP-02 | Phase 4 | In Progress |
| COMP-03 | Phase 4 | In Progress |
| BOARD-01 | Phase 4 | In Progress |
| BOARD-02 | Phase 4 | In Progress |
| BOARD-03 | Phase 6 | Pending |
| BOARD-04 | Phase 6 | Pending |
| WEB-01 | Phase 7 | Pending |
| WEB-02 | Phase 7 | Pending |
| WEB-03 | Phase 7 | Pending |
| RIVAL-01 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 14 total
- Mapped to phases: 14 ✓ (each to exactly one phase)
- Unmapped: 0 ✓

**Phase distribution:**
- Phase 4 (Server Hardening & Weekly Data Model): COMP-01, COMP-02, COMP-03, BOARD-01, BOARD-02 (5)
- Phase 5 (Client Identity Hardening): IDENT-01, IDENT-02, IDENT-03 (3)
- Phase 6 (In-Game Weekly Boards & Got-Passed Banner): BOARD-03, BOARD-04, RIVAL-01 (3)
- Phase 7 (Web Leaderboard Page): WEB-01, WEB-02, WEB-03 (3)

> Status note: Phase 4 requirements are marked **In Progress** as Phase 4 is the active phase entering planning; downstream phases (5-7) remain **Pending** until reached.

---
*Requirements defined: 2026-06-14*
*Last updated: 2026-06-14 after roadmap creation (phases 4-7 mapped)*
