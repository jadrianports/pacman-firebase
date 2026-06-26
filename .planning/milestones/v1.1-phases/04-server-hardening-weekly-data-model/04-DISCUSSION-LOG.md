# Phase 4: Server Hardening & Weekly Data Model - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-06-14
**Phase:** 4-server-hardening-weekly-data-model
**Areas discussed:** HMAC rollout gap, Sanity ceiling value, Weekly reset feel & retention,
Permanent-initials conflict, Threat model (user-requested), Prune cleanup trigger, Replay protection,
Rate limiting, HMAC binding scope, Hardening of abuse vectors (user-requested)

---

## Threat Model (user-requested analysis)

The user asked: *"discuss to me how, theoretically, could abuse these factors now that we've added
security to them to the machine_id and the three letter name file?"* — and later: *"is there a way to
prevent those or harden those?"*

No options were presented (this was an analysis, not a choice). Key findings carried into CONTEXT.md:
- The HMAC secret is extractable from the PyInstaller exe → HMAC stops curl/web/casual tampering, not a
  decompiler. Accepted altitude.
- Identity is resettable by deleting the local file (no accounts) → "permanent" = per-machine_id.
- Vectors with cheap, worthwhile hardening: machine_id binding in the signature, server-time week
  bucketing, machine_id kept out of API responses, max-instances cap, light secret obfuscation.

---

## HMAC rollout gap

| Option | Description | Selected |
|--------|-------------|----------|
| Grace period + flip | Accept unsigned during P4→P5 gap, reject invalid sigs; flip "require" flag after Phase 5 client ships. Board never goes dark; rejection still built/tested. | ✓ |
| Hard cutover | Server requires a valid signature immediately on deploy; every un-updated friend's board breaks until Phase 5. | |
| Bundle P4+P5 deploy | Build enforcement in P4 but don't deploy the enforcing server until the P5 signed client is ready. | |

**User's choice:** Grace period + flip
**Notes:** Avoids breaking friends' currently-shipped exe (which posts unsigned); no regression vs. today.

---

## Sanity ceiling value

| Option | Description | Selected |
|--------|-------------|----------|
| Tight ~25,000 | ~1.7× the proven perfect run (14,620); maximizes anti-cheat value. | |
| Moderate ~50,000 | ~3.4× perfect; extra safety margin, still 10× tighter than the current 500K. | ✓ |
| Keep 500,000 | No change; only blocks overflow/garbage given real scores top out <15K. | |

**User's choice:** Moderate ~50,000
**Notes:** Single non-repeating board; mathematical perfect run ≈ 14,620 (242 dots×10 + 200 pellets +
12,000 max ghost points). 50K leaves headroom for analysis edges / near-term scoring tweaks.

---

## Weekly reset feel & retention

| Option | Description | Selected |
|--------|-------------|----------|
| Keep all weeks | Buckets accumulate; no cleanup job; trivial against 1GB free tier; leaves season-archives possible. | |
| Current + last week only | Prune anything older than last week; needs a cleanup mechanism; no payoff since season-archives are out of scope. | ✓ |

**User's choice:** Current + last week only
**Notes:** Reset feel itself is fixed by requirements (Monday 00:00 UTC; All Time persists). Retention
choice creates the prune-trigger decision below. Last week's bucket must survive for Phase 6.

---

## Permanent-initials conflict

| Option | Description | Selected |
|--------|-------------|----------|
| Keep original, accept score | Score still counts (if new best); initials stay first-submitted; new initials silently ignored. | ✓ |
| Reject the whole submission | Refuse entirely if initials don't match locked ones; brittle — could drop a legit new best. | |

**User's choice:** Keep original, accept score
**Notes:** Today's code rewrites initials on every new best — must change. Honors permanence without
punishing a legit higher score; blocks tag-swapping.

---

## HMAC binding scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full payload incl. machine_id | Sign machine_id + initials + score; binds the signature to a specific identity. | ✓ |
| Score only | Sign just the score; not bound to identity, weaker against lifting/swapping. | |

**User's choice:** Full payload incl. machine_id
**Notes:** Free to do; closes the signature-lifting/impersonation angle. Exact serialization left to planning.

---

## Replay protection

| Option | Description | Selected |
|--------|-------------|----------|
| No replay defense — accept | Submit is "only-if-higher" so replay is a no-op; nonce/timestamp adds clock-skew fragility for ~zero gain. | ✓ |
| Add signed timestamp + freshness window | Reject submissions outside a skew window; hardens against captured-request reuse, at cost of clock-sync brittleness. | |

**User's choice:** No replay defense — accept

---

## Rate limiting

| Option | Description | Selected |
|--------|-------------|----------|
| Cap function max-instances + accept | Bound cost/blast-radius on a flood; otherwise accept low-likelihood risk; no per-request state. | ✓ |
| Per-machine cooldown | Reject if machine_id wrote within N seconds; bypassable by minting machine_ids. | |
| Nothing | No throttle at all; full quota-exhaustion risk. | |

**User's choice:** Cap function max-instances + accept

---

## Prune cleanup trigger

| Option | Description | Selected |
|--------|-------------|----------|
| Lazy delete-on-write | Prune buckets older than last week opportunistically on submission; no scheduler to deploy. | ✓ |
| Scheduled cleanup | Cloud Scheduler weekly job; deterministic but adds a scheduled function + Pub/Sub wiring. | |

**User's choice:** Lazy delete-on-write
**Notes:** Stale weeks are harmless clutter until the next write; avoids cron/Pub/Sub maintenance.

---

## Claude's Discretion

Handed to research/planning (design these; do not re-ask the user):
- Exact HMAC scheme (canonical serialization, HMAC-SHA256, server secret in env var/runtime config).
- `get_leaderboard` scope-param shape + default scope (recommend default = current week).
- Week-bucket storage mechanism (separate collection vs. `week_id` field vs. timestamp-range).
- `week_id` format / Monday-00:00-UTC week math (server-time derived).
- Verifying the committed `cloud_functions/` is the intended reconciled baseline.
- Locked-as-obvious (no downside): week buckets use server time only; machine_id stays out of API responses.

## Deferred Ideas

- Replay-verification of scores (COMP-F1) — out of scope; deferred.
- Season-history archives (BOARD-F1) — out of scope; drove the "current + last week only" choice.
- Heavier anti-abuse (per-machine/IP rate-limiting, nonce/timestamp replay, PyArmor) — rejected as overkill.
- Friend groups / private join-code boards (SOCL-F1) — out of scope for v1.1.
