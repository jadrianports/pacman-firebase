import os
import sys

import pygame
from settings import (
    WIDTH, HEIGHT, FPS, API_SUBMIT_SCORE_URL, API_LEADERBOARD_URL, HMAC_SECRET_FILE_NAME,
    BANNER_FETCH_TIMEOUT_SECONDS, BANNER_NAME_CAP,
)
from game import Game
from menu import run_main_menu, run_initials_entry, run_leaderboard, run_game_over_screen
from api_service import ApiService
from local_storage import load_identity, save_initials, IDENTITY_STATUS_TAMPERED
from leaderboard_crypto import sign_submission, de_obfuscate
from paths import resource_path
import marker
import theme
import updater
import display


def _load_hmac_secret():
    """Resolve the shared HMAC secret without ever embedding a literal in source.

    Resolution order:
    1. Frozen (shipped exe): import the build-baked ``_baked_secret`` module that
       ``build.py`` generates, and de-obfuscate its ``OBFUSCATED_SECRET`` (the XOR/
       base64 counterpart to the build-time embedding, D-09/D-10). The raw secret is
       never a literal in committed source — only the obfuscated form is baked in.
    2. Dev: read the gitignored ``hmac_secret.local`` from the repo root.
    3. Dev fallback: an env var (``LEADERBOARD_HMAC_SECRET``).
    Returns ``None`` if no secret is available — dev runs without it still play; the
    submissions just will not verify server-side.
    """
    if getattr(sys, "frozen", False):
        try:
            import _baked_secret  # generated at build time by build.py (D-09/D-10)
            return de_obfuscate(_baked_secret.OBFUSCATED_SECRET.encode("ascii")).decode("utf-8")
        except Exception:
            return None

    # Dev: gitignored local file next to this module, then env fallback.
    local_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), HMAC_SECRET_FILE_NAME)
    try:
        if os.path.exists(local_path):
            with open(local_path, "r") as f:
                value = f.read().strip()
            if value:
                return value
    except OSError:
        pass
    return os.environ.get("LEADERBOARD_HMAC_SECRET") or None


def _format_banner(names):
    """Build the got-passed banner line from sorted passer initials (D-06).

    Applies the UI-SPEC cap (``BANNER_NAME_CAP`` = 3): list all names joined by
    ", " when within the cap; otherwise list the first 3 then " +{K} more". Always
    suffixes " passed you this week!". ``names`` is expected already sorted/deduped.
    Returns None for an empty list (no banner).
    """
    if not names:
        return None
    if len(names) <= BANNER_NAME_CAP:
        listed = ", ".join(names)
    else:
        listed = ", ".join(names[:BANNER_NAME_CAP]) + f" +{len(names) - BANNER_NAME_CAP} more"
    return f"{listed} passed you this week!"


def main():
    pygame.init()
    # Window / taskbar icon (cosmetic — never block startup if the asset is missing).
    try:
        pygame.display.set_icon(pygame.image.load(resource_path("assets/icon.png")))
    except Exception:
        pass
    # Normal 2-D SCALED display for menus; upgraded to OPENGL per Play session (Task 6).
    screen = display.init()
    pygame.display.set_caption("PAC-MAN")
    timer = pygame.time.Clock()

    # Best-effort auto-update (frozen builds only; never blocks startup).
    def _update_notice(msg):
        screen.fill((6, 6, 18))
        surf = theme.pixel_font(theme.SIZE_HEADING).render(msg, True, (255, 255, 0))
        screen.blit(surf, surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        pygame.display.flip()

    updater.check_and_apply(on_status=_update_notice)

    render_surface = pygame.Surface([WIDTH, HEIGHT])

    api = ApiService(API_SUBMIT_SCORE_URL, API_LEADERBOARD_URL)
    secret = _load_hmac_secret()

    # Load / migrate identity ONCE at startup, before the initials-entry check (D-04).
    # A migrated identity that already carries initials is treated as already-set
    # (no re-prompt). A present-but-invalid blob comes back TAMPERED and blocks submit.
    identity = load_identity(secret)
    machine_id = identity["machine_id"]
    initials = identity["initials"]
    identity_tampered = identity["status"] == IDENTITY_STATUS_TAMPERED

    # Force initials entry only on a genuine fresh launch (valid identity, no initials).
    if not identity_tampered and initials is None:
        initials = run_initials_entry(screen, timer)
        if initials is None:  # Window closed
            pygame.quit()
            return
        save_initials(initials, secret)

    # Launch got-passed banner compute (RIVAL-01), all best-effort — never break
    # startup (SC-4). Load the unsigned marker; if absent (cold start, D-18) or it
    # has no tracked this-week best (D-05: no score to be passed on), no banner.
    # Otherwise do a SHORT-timeout This Week fetch (D-09, single blocking call, no
    # threading); offline/slow -> no banner. New passers = board initials scoring
    # above our tracked best, minus those already above us at last board view (D-11/D-12).
    banner_text = None
    tracked_best = None
    initials_above = set()
    _marker = marker.read_marker()
    if _marker is not None and _marker.get("tracked_best") is not None:
        tracked_best = _marker["tracked_best"]
        initials_above = set(_marker.get("initials_above", []))
        this_week = api.get_leaderboard(scope="week", timeout=BANNER_FETCH_TIMEOUT_SECONDS)
        if this_week:
            above_now = {e["initials"] for e in this_week if e["score"] > tracked_best}
            new_passers = sorted(above_now - initials_above)
            banner_text = _format_banner(new_passers)

    # Main state loop
    while True:
        choice = run_main_menu(screen, timer, banner_text=banner_text)

        if choice == "Quit":
            break

        elif choice == "Play":
            import present as _present
            game = Game(render_surface, timer)
            game.juice = True
            game.present_fn = lambda: _present.present(render_surface, game.shake.update(1.0 / FPS))
            result = game.run()
            screen = display.init()   # ensure window/logical are fresh for menus

            if result is None:  # Window closed during game
                break

            score = result["score"]
            game_won = result["game_won"]

            if identity_tampered:
                # D-05/D-06: a tampered identity blocks submission entirely; the game
                # stays fully playable and the game-over screen shows the notice.
                is_new_best = False
                action = run_game_over_screen(
                    screen, timer, score, is_new_best, game_won, identity_error=True
                )
            else:
                # Sign the submission with the build-baked secret (D-07) and POST it in
                # the "signature" field. API tells us if it's a new best.
                signature = sign_submission(machine_id, initials, score, secret) if secret else None
                response = api.submit_score(machine_id, initials, score, signature)
                is_new_best = response is not None and response.get("is_new_best", False)
                action = run_game_over_screen(
                    screen, timer, score, is_new_best, game_won, identity_error=False
                )

                # Submit-path tracked-best update (D-11): keep the locally tracked
                # this-week best current so the next launch's passer comparison is
                # accurate. Re-baseline to this score for the current client week and
                # persist; the marker writer is best-effort (swallows errors).
                if response is not None:
                    week_id = marker.client_current_week_id()
                    tracked_best = max(tracked_best or 0, score)
                    marker.write_marker(week_id, tracked_best, initials_above)

            if action == "quit":
                break

        elif choice == "Leaderboard":
            # Open the board; it returns (quit_requested, this_week_entries) (O-3).
            # Opening the board clears the on-screen banner for the session AND rewrites
            # the marker baseline — the ONLY place initials_above is reset (D-07/D-10).
            quit_requested, this_week_entries = run_leaderboard(screen, timer, api)
            banner_text = None
            if this_week_entries and tracked_best is not None:
                initials_above = {
                    e["initials"] for e in this_week_entries if e["score"] > tracked_best
                }
                marker.write_marker(
                    marker.client_current_week_id(), tracked_best, initials_above
                )
            # Honor a window-close while the board was open (WR-01) — without an
            # out-of-band quit signal this fell through and re-displayed the menu.
            if quit_requested:
                break

    pygame.quit()


if __name__ == "__main__":
    main()
