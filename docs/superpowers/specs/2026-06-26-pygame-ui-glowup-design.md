# PyGame UI Glow-Up — Two-Branch Design Spec

**Date:** 2026-06-26
**Status:** Approved design — pending spec review before planning
**Author:** brainstormed with James

## Problem

The Phase 07 web leaderboard (`pacman-firebase.web.app`) has a sharp retro-arcade
identity — Press Start 2P pixel font, reserved yellow accent, navy panels, pellet
motifs, CRT feel, favicon/branding. The in-game PyGame UI does not: every screen uses
the generic `freesansbold.ttf` on a flat black fill with no motifs or motion. The game
now looks blander than its own website.

## Goal

Bring the game's visuals up to — and past — the web page, explored as **two parallel
directions on separate branches** so they can be compared directly and a winner merged.
`main` is never at risk.

- **Branch A — Brand Match:** faithfully port the web aesthetic to the game's menu
  screens. Consistent brand, lower risk, gameplay untouched.
- **Branch B — Bold Reinvention:** a full game-feel glow-up — juicier menus **and** a
  gameplay presentation layer (glow, particles, bloom, screen-shake, CRT), arcade-cabinet
  energy.

Both cover all four screen groups: **main menu / title**, **initials entry +
leaderboard**, **in-game HUD + gameplay**, **game-over / pause**.

## Non-Goals

- No change to gameplay logic: ghost AI, movement, collision, scoring, box-exit timing,
  wrap, scatter — all byte-for-byte untouched.
- No re-blessing of golden traces (the design avoids needing it).
- No new gameplay features. This is purely visual/feel.

## Hard Constraints

1. **Determinism is sacred.** `tests/test_frame_hash.py` and `tests/test_golden_traces.py`
   render real gameplay frames and hash them. The full suite (146 passed / 9 skipped) must
   stay green on both branches.
2. **Ghost eyes preserved.** The classic directional ghost eyes — and the iconic
   "eyes-only ghost returning to the box" eaten state — must survive the glow-up. Glow/bloom
   must never wash them out.
3. **`.exe` must still build and launch on a clean machine** via PyInstaller. All new data
   files (font, theme JSON) and native deps (zengl) bundled correctly.
4. **Tasteful.** Bold-branch gameplay juice is dialed ~10–15% below the brainstorm mockup —
   energetic, not carnival.

## Shared Foundation (both branches)

1. **Migrate `pygame` → `pygame-ce`.** Validated as a true drop-in via an isolated-venv
   spike: pygame-ce 2.5.7 installed clean, all game modules imported, and the
   simulation-integrity tests (`frame_hash`, `ghost_micro`) passed **30/9 — identical to
   classic** under CE's newer SDL (2.32.10). No `fastevent` usage in the codebase (the one
   removed module). `requirements.txt`: `pygame==2.6.1` → `pygame-ce==2.5.7`. Bundles
   identically under PyInstaller. Unlocks `gaussian_blur()`/`box_blur()` (glow/bloom),
   `fblits()` (fast particles), premultiplied alpha, and `FRect` for free.
2. **Press Start 2P** TTF added as a bundled asset, loaded through the existing
   `resource_path()` helper (mirrors how the web page self-hosts it; reuse
   `web/public/fonts/PressStart2P-Regular.ttf`).
3. **New `theme.py` module** — single home for: pixel-font loader + named sizes, color
   tokens (reuse `settings.COLOR_YELLOW/WHITE/GRAY/RED/GREEN`), and small render helpers
   (glow-text via a blurred bright copy + additive blit; scanline-overlay builder). Both
   branches consume this; it keeps `menu.py`/`game.py` render code focused.

## The Determinism Firewall (key architectural decision)

The maze **and** HUD are drawn in `game.py` and are part of the hashed frame. Therefore
**every in-game visual change is a presentation layer gated behind a `juice` flag**:

- `juice=off` → `game.py` renders exactly as it does today → frame hashes unchanged →
  `frame_hash`/`golden_traces` pass untouched. Deterministic tests always run with
  `juice=off`.
- `juice=on` → the full glow-up renders. This is the default for real play.
- The hash, where computed, is taken on the **pre-shader logical surface**; the zengl CRT
  pass is applied only to the final display blit, after any hashing.
- **New test:** assert that with `juice=off`, rendered frames are byte-identical to the
  pre-change baseline (a regression guard on the firewall itself).

The standalone `menu.py` screens (main menu, initials, leaderboard, game-over) are **not**
part of the gameplay golden traces, so they can be restyled freely on both branches without
a flag.

## Branch A — Brand Match (`redesign/brand-match`)

- Port the web aesthetic to the four `menu.py` screens using **pygame_gui** with a custom
  **JSON theme**: navy panels, reserved `#FFFF00` accent (wordmark / active tab / rank-1 /
  focus only), Press Start 2P, gray supporting text, a translucent scanline overlay, and a
  vignette. Mirror the web page's layout/copy where they share semantics (tab bar, dot-leader
  leaderboard rows, verbatim state strings).
- pygame_gui co-exists with hand-drawn rendering and is themed entirely via JSON — it does
  not take over the loop.
- **Gameplay (`game.py`) untouched** → no `juice` flag needed on this branch; golden traces
  are trivially safe.
- Production-ready: new UI tests (theme loads, screens construct, key handlers intact),
  full suite green.

## Branch B — Bold Reinvention (`redesign/bold-reinvention`)

- Everything Brand Match does to the menus, but **juicier**: pulsing multi-glow title,
  animated chomping Pac-Man crossing a pellet trail (with a ghost on its tail — eyes
  intact), glowing menu cursor, floating particles.
- **Gameplay glow-up** as the `juice`-gated presentation layer in `game.py`:
  - Glowing pellets; pulsing power-pellets.
  - Chomp sparks trailing Pac-Man (hand-rolled particles: list of light structs updated by
    dt, drawn with `fblits` + `BLEND_RGB_ADD`).
  - Ghost-eat **bloom + score pop** and a **subtle screen-shake** (display-blit offset, not
    a simulation change).
  - Pixel-font **HUD**: `SCORE n` + Pac-Man life icons (replacing the `freesansbold` score
    text + scaled sprites), juice-gated.
  - **Ghost eyes preserved** — eyes/pupils rendered on top of any ghost glow; eaten-ghost
    "eyes-only" return state kept and unobscured.
  - Intensity ~10–15% below the mockup.
- **Real CRT** via a **zengl** post-process shader (scanlines + barrel curvature + mild
  bloom/phosphor) over the final display surface. zengl chosen over moderngl specifically
  to avoid the `glcontext` PyInstaller bundling failure; it is self-contained. Bold-branch-
  only dependency.
- Production-ready: UI tests + the `juice=off == baseline` determinism guard; full suite
  green with `juice=off`.

## Comparison & Ship

**Live side-by-side (primary).** Both branches checked out simultaneously via **git
worktrees** into sibling folders — `../pacman-brand-match/` and
`../pacman-bold-reinvention/` — each with its own `.venv` (pygame_gui on both; zengl on
Bold only). Run **both games at once, two windows side by side**, flipping through the same
screens in real time. No `git switch` churn.

**Contact sheet (secondary).** A headless capture script (`SDL_VIDEODRIVER=dummy`)
screenshots every screen — menu, initials, leaderboard, game-over, and a representative
gameplay frame — in both styles and montages them into a single before/after image. Same
technique used to verify the web page. Gives an at-a-glance diff without launching and a
durable artifact.

**Ship.** Pick the winner → merge that branch to `main` → delete both worktrees/branches.
Fully reversible at every step; `main` stays on classic-or-CE only when a branch is merged.

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| pygame-ce migration breaks the game | Proven safe via isolated-venv spike (tests identical); reversible — lives on a branch, `main` untouched |
| Gameplay juice changes frame hashes | Determinism firewall: `juice` flag, tests run `juice=off`; explicit `juice=off == baseline` test |
| Golden traces need re-blessing | Avoided by design; if ever required, existing Linux-Docker re-bless process is the fallback |
| zengl/pygame_gui/font not bundled in `.exe` | Add font + theme JSON + zengl to the PyInstaller spec; verify clean-machine launch as an explicit task |
| Ghost eyes lost to glow | Hard constraint + dedicated check; eyes drawn last, above glow |

## Open Questions

None blocking. Per-branch visual detail (exact glow radii, shake magnitude, shader
parameters) is tuning, resolved during implementation against the dialed-back target.
