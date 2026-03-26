import pygame
from settings import WIDTH, HEIGHT, API_SUBMIT_SCORE_URL, API_LEADERBOARD_URL
from game import Game
from menu import run_main_menu, run_initials_entry, run_leaderboard, run_game_over_screen
from api_service import ApiService
from local_storage import get_machine_id, get_initials, save_initials


def main():
    pygame.init()
    screen = pygame.display.set_mode([WIDTH, HEIGHT])
    pygame.display.set_caption("PAC-MAN")
    timer = pygame.time.Clock()

    api = ApiService(API_SUBMIT_SCORE_URL, API_LEADERBOARD_URL)
    machine_id = get_machine_id()

    # Force initials entry on first launch
    if get_initials() is None:
        initials = run_initials_entry(screen, timer)
        if initials is None:  # Window closed
            pygame.quit()
            return
        save_initials(initials)

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
            initials = get_initials()

            # Submit score — API tells us if it's a new best
            response = api.submit_score(machine_id, initials, score)
            is_new_best = response is not None and response.get("is_new_best", False)

            # Show game over screen
            action = run_game_over_screen(screen, timer, score, is_new_best, game_won)
            if action == "quit":
                break

        elif choice == "Leaderboard":
            run_leaderboard(screen, timer, api)

    pygame.quit()


if __name__ == "__main__":
    main()
