import pygame
from paths import resource_path
from settings import (
    WIDTH, HEIGHT, FPS,
    COLOR_YELLOW, COLOR_WHITE, COLOR_GRAY, COLOR_RED, COLOR_GREEN,
    FONT_TITLE, FONT_MENU, FONT_SMALL,
    MENU_OPTIONS, LEADERBOARD_LINE_WIDTH,
)

# Sentinel distinguishing "this view has never been fetched" from the three
# meaningful cache states a fetch can yield (Pitfall 1 / board-view truth table):
#   _UNFETCHED -> needs a fetch (never sits across frames)
#   None       -> offline ("Could not connect to leaderboard.")
#   []         -> empty (per-view empty-state string)
#   [...]      -> data (board rows)
# A plain None cache value would collide with the offline state, so a dedicated
# object() identity is used instead.
_UNFETCHED = object()


def run_main_menu(screen, timer, banner_text=None):
    """Display main menu. Returns the selected option string: 'Play', 'Leaderboard', or 'Quit'.

    When ``banner_text`` is truthy, a got-passed banner line is rendered in yellow at
    y=230 (between the title and the first option), mirroring the passive-notice idiom
    in run_game_over_screen. The string is built/capped by main.py (D-06); this only
    renders it. With ``banner_text=None`` the menu renders exactly as before.
    """
    title_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_TITLE)
    option_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_MENU)
    banner_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_SMALL)
    selected = 0

    while True:
        timer.tick(FPS)
        screen.fill("black")

        # Title
        title = title_font.render("PAC-MAN", True, COLOR_YELLOW)
        title_rect = title.get_rect(center=(WIDTH // 2, 150))
        screen.blit(title, title_rect)

        # Got-passed banner (D-06) — yellow, only when present (passive-notice idiom).
        if banner_text:
            banner = banner_font.render(banner_text, True, COLOR_YELLOW)
            banner_rect = banner.get_rect(center=(WIDTH // 2, 230))
            screen.blit(banner, banner_rect)

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


def _show_loading(screen, header_font):
    """Render the existing white centered 'Loading...' frame (shown before a fetch)."""
    screen.fill("black")
    loading = header_font.render("Loading...", True, COLOR_WHITE)
    loading_rect = loading.get_rect(center=(WIDTH // 2, HEIGHT // 2))
    screen.blit(loading, loading_rect)
    pygame.display.flip()


def run_leaderboard(screen, timer, api_service):
    """Display the weekly/all-time leaderboard with a This Week <-> All Time toggle.

    Opens on This Week (D-02). LEFT/RIGHT flip the active view; All Time is
    lazy-fetched once on the first toggle to it (D-14). The last-week champion
    subtitle shows on This Week only, hidden when absent (D-04/D-16). Returns when
    the user presses ESC or ENTER.

    Board-open seam (O-3, return-based): returns a ``(quit_requested, week_entries)``
    tuple. ``week_entries`` is the freshly-fetched This Week entries (the same list
    rendered, no extra network call) so main.py can rewrite the marker baseline exactly
    once per board open — ``None`` if This Week was offline / unavailable, ``[]`` if
    empty, or the entries list on success. ``quit_requested`` is True only when the user
    closed the window (pygame.QUIT); ESC/ENTER ("back") returns it False. This gives the
    caller an out-of-band quit signal so a window-close while the board is open is honored
    instead of silently re-displaying the main menu (WR-01), matching the quit-propagation
    contract of every sibling screen.
    """
    header_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_MENU)
    entry_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_SMALL)
    hint_font = pygame.font.Font(resource_path("freesansbold.ttf"), FONT_SMALL)

    # Per-view lazy cache. This Week is fetched on open; All Time stays _UNFETCHED
    # until the first toggle. None=offline, []=empty, [...]=data (truth table).
    views = {"week": _UNFETCHED, "all": _UNFETCHED}
    active = "week"

    # Fetch This Week up front (open-on view, D-02), plus a best-effort last-week
    # champion fetch for the subtitle. last_week is independent of the toggle cache.
    _show_loading(screen, header_font)
    views["week"] = api_service.get_leaderboard(scope="week")
    last_week = api_service.get_leaderboard(scope="last_week")
    last_week_initials = last_week[0]["initials"] if last_week else None

    empty_text = {
        "week": "No scores yet this week. Be the first!",
        "all": "No scores yet. Be the first!",
    }

    while True:
        timer.tick(FPS)
        screen.fill("black")

        entries = views[active]

        # Header
        header = header_font.render("LEADERBOARD", True, COLOR_YELLOW)
        header_rect = header.get_rect(center=(WIDTH // 2, 80))
        screen.blit(header, header_rect)

        # Tab indicator: active side yellow, inactive side + separators gray (D-03).
        # Rendered as three runs so only the active label is yellow.
        prefix = entry_font.render("< ", True, COLOR_GRAY)
        week_label = entry_font.render(
            "This Week", True, COLOR_YELLOW if active == "week" else COLOR_GRAY
        )
        sep = entry_font.render(" | ", True, COLOR_GRAY)
        all_label = entry_font.render(
            "All Time", True, COLOR_YELLOW if active == "all" else COLOR_GRAY
        )
        suffix = entry_font.render(" >", True, COLOR_GRAY)
        tab_w = (prefix.get_width() + week_label.get_width() + sep.get_width()
                 + all_label.get_width() + suffix.get_width())
        tx = WIDTH // 2 - tab_w // 2
        ty = 128
        for surf in (prefix, week_label, sep, all_label, suffix):
            screen.blit(surf, (tx, ty - surf.get_height() // 2))
            tx += surf.get_width()

        # Last-week champion subtitle — This Week only, hidden when absent (D-16).
        if active == "week" and last_week_initials:
            subtitle = entry_font.render(
                f"Last week: {last_week_initials}", True, COLOR_GRAY
            )
            subtitle_rect = subtitle.get_rect(center=(WIDTH // 2, 152))
            screen.blit(subtitle, subtitle_rect)

        if entries is None:
            # Offline (per active view; the other cached view still renders when toggled)
            msg = entry_font.render("Could not connect to leaderboard.", True, COLOR_GRAY)
            msg_rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(msg, msg_rect)
        elif len(entries) == 0:
            msg = entry_font.render(empty_text[active], True, COLOR_GRAY)
            msg_rect = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2))
            screen.blit(msg, msg_rect)
        else:
            for i, entry in enumerate(entries):
                rank = f"{i + 1}."
                initials = entry["initials"]
                score = str(entry["score"])
                fill = max(0, LEADERBOARD_LINE_WIDTH - len(rank) - len(initials) - len(score))
                dots = "." * fill
                line = f"{rank} {initials} {dots} {score}"
                color = COLOR_YELLOW if i == 0 else COLOR_WHITE
                text = entry_font.render(line, True, color)
                text_rect = text.get_rect(center=(WIDTH // 2, 180 + i * 50))
                screen.blit(text, text_rect)

        # Hint
        hint = hint_font.render("LEFT/RIGHT: switch board   ESC/ENTER: back", True, COLOR_GRAY)
        hint_rect = hint.get_rect(center=(WIDTH // 2, HEIGHT - 80))
        screen.blit(hint, hint_rect)

        for event in pygame.event.get():
            week_entries = views["week"] if views["week"] is not _UNFETCHED else None
            if event.type == pygame.QUIT:
                return True, week_entries
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return False, week_entries
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    active = "all" if active == "week" else "week"
                    # Lazy-fetch All Time the first time it becomes active (D-14).
                    if views[active] is _UNFETCHED:
                        _show_loading(screen, header_font)
                        views[active] = api_service.get_leaderboard(scope="all")

        pygame.display.flip()


def run_game_over_screen(screen, timer, score, is_new_best, game_won, identity_error=False):
    """Show game over/victory screen with score. Returns after user presses SPACE.

    When ``identity_error`` is set (a tampered/invalid identity blocked the submit,
    D-05/D-06), render a small gray "Score not saved — identity error" line so the
    player sees why the score did not reach the board. The game stays fully playable;
    this is a passive notice, not a modal.
    """
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

        # Identity error — score could not be submitted (D-06). Gray, passive notice
        # mirroring the "Could not connect to leaderboard." graceful-degrade tone.
        if identity_error:
            notice = hint_font.render("Score not saved — identity error", True, COLOR_GRAY)
            notice_rect = notice.get_rect(center=(WIDTH // 2, 540))
            screen.blit(notice, notice_rect)

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
