import os
import sys

import pygame
from settings import WIDTH, HEIGHT, API_SUBMIT_SCORE_URL, API_LEADERBOARD_URL, HMAC_SECRET_FILE_NAME
from game import Game
from menu import run_main_menu, run_initials_entry, run_leaderboard, run_game_over_screen
from api_service import ApiService
from local_storage import load_identity, save_initials, IDENTITY_STATUS_TAMPERED
from leaderboard_crypto import sign_submission, de_obfuscate


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


def main():
    pygame.init()
    screen = pygame.display.set_mode([WIDTH, HEIGHT])
    pygame.display.set_caption("PAC-MAN")
    timer = pygame.time.Clock()

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

    # Main state loop
    while True:
        choice = run_main_menu(screen, timer)

        if choice == "Quit":
            break

        elif choice == "Play":
            game = Game(screen, timer)
            result = game.run()

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

            if action == "quit":
                break

        elif choice == "Leaderboard":
            run_leaderboard(screen, timer, api)

    pygame.quit()


if __name__ == "__main__":
    main()
