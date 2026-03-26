import pygame
from paths import resource_path
from settings import (
    WIDTH, HEIGHT, FPS,
    COLOR_YELLOW, COLOR_WHITE, COLOR_GRAY, COLOR_RED, COLOR_GREEN,
    FONT_TITLE, FONT_MENU, FONT_SMALL,
    MENU_OPTIONS,
)


def run_main_menu(screen, timer):
    """Display main menu. Returns the selected option string: 'Play', 'Leaderboard', 'Change Initials', or 'Quit'."""
    title_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_TITLE)
    option_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_MENU)
    selected = 0

    while True:
        timer.tick(FPS)
        screen.fill("black")

        # Title
        title = title_font.render("PAC-MAN", True, COLOR_YELLOW)
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        screen.blit(title, title_rect)

        # Menu options
        for i, option in enumerate(MENU_OPTIONS):
            color = COLOR_YELLOW if i == selected else COLOR_WHITE
            text = option_font.render(option, True, color)
            text_rect = text.get_rect(center=(WIDTH // 2, 350 + i * 70))
            screen.blit(text, text_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "Quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(MENU_OPTIONS)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(MENU_OPTIONS)
                elif event.key == pygame.K_RETURN:
                    return MENU_OPTIONS[selected]

        pygame.display.flip()


def run_initials_entry(screen, timer, current_initials=None):
    """Arcade-style 3-letter initials entry. Returns the 3-letter string (e.g. 'JAM')."""
    header_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_MENU)
    letter_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_TITLE)
    hint_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_SMALL)

    if current_initials and len(current_initials) == 3:
        letters = [ord(c) - ord("A") for c in current_initials.upper()]
    else:
        letters = [0, 0, 0]  # A, A, A
    slot = 0

    while True:
        timer.tick(FPS)
        screen.fill("black")

        # Header
        header = header_font.render("ENTER YOUR INITIALS", True, COLOR_YELLOW)
        header_rect = header.get_rect(center=(WIDTH // 2, 200))
        screen.blit(header, header_rect)

        # Letter slots
        total_width = 3 * 80 + 2 * 40  # 3 slots, 2 gaps
        start_x = (WIDTH - total_width) // 2
        for i in range(3):
            letter_char = chr(ord("A") + letters[i])
            color = COLOR_YELLOW if i == slot else COLOR_WHITE
            x = start_x + i * 120 + 40

            # Draw bracket
            bracket = letter_font.render(f"[ {letter_char} ]", True, color)
            bracket_rect = bracket.get_rect(center=(x, 400))
            screen.blit(bracket, bracket_rect)

            # Draw up/down arrows for active slot
            if i == slot:
                arrow_up = hint_font.render("^", True, COLOR_GRAY)
                arrow_up_rect = arrow_up.get_rect(center=(x, 330))
                screen.blit(arrow_up, arrow_up_rect)
                arrow_down = hint_font.render("v", True, COLOR_GRAY)
                arrow_down_rect = arrow_down.get_rect(center=(x, 470))
                screen.blit(arrow_down, arrow_down_rect)

        # Hint
        hint = hint_font.render("UP/DOWN: change letter   LEFT/RIGHT: move   ENTER: confirm", True, COLOR_GRAY)
        hint_rect = hint.get_rect(center=(WIDTH // 2, 600))
        screen.blit(hint, hint_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    letters[slot] = (letters[slot] - 1) % 26
                elif event.key == pygame.K_DOWN:
                    letters[slot] = (letters[slot] + 1) % 26
                elif event.key == pygame.K_LEFT:
                    slot = (slot - 1) % 3
                elif event.key == pygame.K_RIGHT:
                    slot = (slot + 1) % 3
                elif event.key == pygame.K_RETURN:
                    return "".join(chr(ord("A") + l) for l in letters)

        pygame.display.flip()


def run_leaderboard(screen, timer, api_service):
    """Fetch and display top 10 leaderboard. Returns when user presses ESC or ENTER."""
    header_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_MENU)
    entry_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_SMALL)
    hint_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_SMALL)

    # Show loading screen
    screen.fill("black")
    loading = header_font.render("Loading...", True, COLOR_WHITE)
    loading_rect = loading.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(loading, loading_rect)
    pygame.display.flip()

    # Fetch data
    entries = api_service.get_leaderboard()

    while True:
        timer.tick(FPS)
        screen.fill("black")

        # Header
        header = header_font.render("LEADERBOARD", True, COLOR_YELLOW)
        header_rect = header.get_rect(center=(WIDTH // 2, 80))
        screen.blit(header, header_rect)

        if entries is None:
            # Offline
            msg = entry_font.render("Could not connect to leaderboard.", True, COLOR_GRAY)
            msg_rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(msg, msg_rect)
        elif len(entries) == 0:
            msg = entry_font.render("No scores yet. Be the first!", True, COLOR_GRAY)
            msg_rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(msg, msg_rect)
        else:
            for i, entry in enumerate(entries):
                rank = f"{i + 1}."
                initials = entry["initials"]
                score = str(entry["score"])
                dots = "." * (30 - len(rank) - len(initials) - len(score))
                line = f"{rank} {initials} {dots} {score}"
                color = COLOR_YELLOW if i == 0 else COLOR_WHITE
                text = entry_font.render(line, True, color)
                text_rect = text.get_rect(center=(WIDTH // 2, 180 + i * 50))
                screen.blit(text, text_rect)

        # Hint
        hint = hint_font.render("Press ESC or ENTER to go back", True, COLOR_GRAY)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 80))
        screen.blit(hint, hint_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return

        pygame.display.flip()


def run_game_over_screen(screen, timer, score, is_new_best, game_won):
    """Show game over/victory screen with score. Returns after user presses SPACE."""
    title_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_TITLE)
    score_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_MENU)
    hint_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_SMALL)

    while True:
        timer.tick(FPS)
        screen.fill("black")

        # Title
        if game_won:
            title = title_font.render("VICTORY!", True, COLOR_GREEN)
        else:
            title = title_font.render("GAME OVER", True, COLOR_RED)
        title_rect = title.get_rect(center=(WIDTH // 2, 250))
        screen.blit(title, title_rect)

        # Score
        score_text = score_font.render(f"Score: {score}", True, COLOR_WHITE)
        score_rect = score_text.get_rect(center=(WIDTH // 2, 400))
        screen.blit(score_text, score_rect)

        # New best
        if is_new_best:
            best_text = score_font.render("NEW BEST!", True, COLOR_YELLOW)
            best_rect = best_text.get_rect(center=(WIDTH // 2, 480))
            screen.blit(best_text, best_rect)

        # Hint
        hint = hint_font.render("Press SPACE for menu", True, COLOR_GRAY)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 100))
        screen.blit(hint, hint_rect)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "menu"

        pygame.display.flip()
