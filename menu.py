import math
import pygame
import theme
from settings import (
    WIDTH, HEIGHT, FPS,
    COLOR_YELLOW, COLOR_WHITE, COLOR_GRAY, COLOR_RED, COLOR_GREEN,
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

COLOR_BACKDROP = (6, 6, 18)  # deep navy-black, matches the web page body


def _draw_backdrop(screen):
    """Fill the navy backdrop and lay the CRT scanline overlay. Every screen
    starts here so the whole app shares one arcade canvas."""
    screen.fill(COLOR_BACKDROP)
    screen.blit(theme.scanline_overlay((WIDTH, HEIGHT), spacing=3, alpha=45), (0, 0))


def _blit_center(screen, surface, center):
    screen.blit(surface, surface.get_rect(center=center))


def _render_main_menu(screen, selected, banner_text=None, frame=0):
    """Draw one main-menu frame: glowing pixel title, optional banner, and the
    Play/Leaderboard/Quit options with the selected one glowing yellow.

    The title glow radius is modulated by ``frame`` so the wordmark "breathes"
    with a gentle sine-wave pulse (6–8 px, ~12-frame period)."""
    _draw_backdrop(screen)

    pulse_radius = 6 + int(2 * (0.5 + 0.5 * math.sin(frame * 0.08)))   # 6..8 px, gentle
    title = theme.glow_text("PAC-MAN", theme.pixel_font(theme.SIZE_TITLE), COLOR_YELLOW, radius=pulse_radius)
    _blit_center(screen, title, (WIDTH // 2, 150))

    if banner_text:
        banner = theme.pixel_font(theme.SIZE_SMALL).render(banner_text, True, COLOR_YELLOW)
        _blit_center(screen, banner, (WIDTH // 2, 230))

    menu_font = theme.pixel_font(theme.SIZE_MENU)
    for i, option in enumerate(MENU_OPTIONS):
        y = 350 + i * 70
        if i == selected:
            surf = theme.glow_text(option, menu_font, COLOR_YELLOW, radius=4)
            rect = surf.get_rect(center=(WIDTH // 2, y))
            screen.blit(surf, rect)
            cursor = theme.glow_text(">", menu_font, COLOR_YELLOW, radius=4)
            screen.blit(cursor, cursor.get_rect(midright=(rect.left - 16, y)))
        else:
            surf = menu_font.render(option, True, COLOR_WHITE)
            _blit_center(screen, surf, (WIDTH // 2, y))


def _render_initials(screen, letters, slot):
    """Draw one initials-entry frame: header, three bracketed letter slots (the
    active one glows yellow with up/down arrows), and the control hint."""
    _draw_backdrop(screen)

    header = theme.glow_text("ENTER YOUR INITIALS", theme.pixel_font(theme.SIZE_HEADING),
                             COLOR_YELLOW, radius=4)
    _blit_center(screen, header, (WIDTH // 2, 200))

    letter_font = theme.pixel_font(theme.SIZE_TITLE)
    hint_font = theme.pixel_font(theme.SIZE_SMALL)
    total_width = 3 * 80 + 2 * 40
    start_x = (WIDTH - total_width) // 2
    for i in range(3):
        letter_char = chr(ord("A") + letters[i])
        x = start_x + i * 120 + 40
        if i == slot:
            bracket = theme.glow_text(f"[ {letter_char} ]", letter_font, COLOR_YELLOW, radius=4)
            _blit_center(screen, bracket, (x, 400))
            _blit_center(screen, hint_font.render("^", True, COLOR_GRAY), (x, 330))
            _blit_center(screen, hint_font.render("v", True, COLOR_GRAY), (x, 470))
        else:
            bracket = letter_font.render(f"[ {letter_char} ]", True, COLOR_WHITE)
            _blit_center(screen, bracket, (x, 400))

    hint = hint_font.render("UP/DOWN: change letter   LEFT/RIGHT: move   ENTER: confirm",
                            True, COLOR_GRAY)
    _blit_center(screen, hint, (WIDTH // 2, 600))


_EMPTY_TEXT = {
    "week": "No scores yet this week. Be the first!",
    "all": "No scores yet. Be the first!",
}


def _render_leaderboard(screen, active, entries, last_week_initials):
    """Draw one leaderboard frame: glowing header, This Week | All Time tab bar
    (active side yellow), optional last-week subtitle (This Week only), and the
    board — offline/empty messages or dot-leader rows with rank 1 in yellow."""
    _draw_backdrop(screen)
    entry_font = theme.pixel_font(theme.SIZE_BODY)
    hint_font = theme.pixel_font(theme.SIZE_SMALL)

    header = theme.glow_text("LEADERBOARD", theme.pixel_font(theme.SIZE_HEADING),
                             COLOR_YELLOW, radius=5)
    _blit_center(screen, header, (WIDTH // 2, 80))

    # Tab bar: only the active label is yellow; separators/inactive gray.
    prefix = entry_font.render("< ", True, COLOR_GRAY)
    week_label = entry_font.render("This Week", True,
                                   COLOR_YELLOW if active == "week" else COLOR_GRAY)
    sep = entry_font.render(" | ", True, COLOR_GRAY)
    all_label = entry_font.render("All Time", True,
                                  COLOR_YELLOW if active == "all" else COLOR_GRAY)
    suffix = entry_font.render(" >", True, COLOR_GRAY)
    runs = (prefix, week_label, sep, all_label, suffix)
    tab_w = sum(s.get_width() for s in runs)
    tx, ty = WIDTH // 2 - tab_w // 2, 128
    for surf in runs:
        screen.blit(surf, (tx, ty - surf.get_height() // 2))
        tx += surf.get_width()

    if active == "week" and last_week_initials:
        subtitle = entry_font.render(f"Last week: {last_week_initials}", True, COLOR_GRAY)
        _blit_center(screen, subtitle, (WIDTH // 2, 158))

    if entries is None:
        _blit_center(screen, entry_font.render("Could not connect to leaderboard.", True, COLOR_GRAY),
                     (WIDTH // 2, HEIGHT // 2))
    elif len(entries) == 0:
        _blit_center(screen, entry_font.render(_EMPTY_TEXT[active], True, COLOR_GRAY),
                     (WIDTH // 2, HEIGHT // 2))
    else:
        for i, entry in enumerate(entries):
            rank = f"{i + 1}."
            initials = entry["initials"]
            score = str(entry["score"])
            fill = max(0, LEADERBOARD_LINE_WIDTH - len(rank) - len(initials) - len(score))
            line = f"{rank} {initials} {'.' * fill} {score}"
            color = COLOR_YELLOW if i == 0 else COLOR_WHITE
            _blit_center(screen, entry_font.render(line, True, color), (WIDTH // 2, 180 + i * 50))

    hint = hint_font.render("LEFT/RIGHT: switch board   ESC/ENTER: back", True, COLOR_GRAY)
    _blit_center(screen, hint, (WIDTH // 2, HEIGHT - 80))


def _render_game_over(screen, score, is_new_best, game_won, identity_error=False):
    """Draw one game-over/victory frame: glowing title (green win / red loss),
    score, optional NEW BEST!, optional identity-error notice, and the hint."""
    _draw_backdrop(screen)
    title_font = theme.pixel_font(theme.SIZE_TITLE)
    score_font = theme.pixel_font(theme.SIZE_MENU)
    hint_font = theme.pixel_font(theme.SIZE_SMALL)

    if game_won:
        title = theme.glow_text("VICTORY!", title_font, COLOR_GREEN, radius=6)
    else:
        title = theme.glow_text("GAME OVER", title_font, COLOR_RED, radius=6)
    _blit_center(screen, title, (WIDTH // 2, 250))

    _blit_center(screen, score_font.render(f"Score: {score}", True, COLOR_WHITE), (WIDTH // 2, 400))

    if is_new_best:
        best = theme.glow_text("NEW BEST!", score_font, COLOR_YELLOW, radius=4)
        _blit_center(screen, best, (WIDTH // 2, 480))

    if identity_error:
        _blit_center(screen, hint_font.render("Score not saved — identity error", True, COLOR_GRAY),
                     (WIDTH // 2, 540))

    _blit_center(screen, hint_font.render("Press SPACE for menu", True, COLOR_GRAY),
                 (WIDTH // 2, HEIGHT - 100))


def _show_loading(screen):
    """Render the navy 'Loading...' frame (shown before a fetch)."""
    _draw_backdrop(screen)
    loading = theme.pixel_font(theme.SIZE_HEADING).render("Loading...", True, COLOR_WHITE)
    _blit_center(screen, loading, (WIDTH // 2, HEIGHT // 2))
    pygame.display.flip()


def run_main_menu(screen, timer, banner_text=None):
    """Display main menu. Returns the selected option string: 'Play', 'Leaderboard', or 'Quit'.

    When ``banner_text`` is truthy, a got-passed banner line is rendered in yellow at
    y=230 (between the title and the first option), mirroring the passive-notice idiom
    in run_game_over_screen. The string is built/capped by main.py (D-06); this only
    renders it. With ``banner_text=None`` the menu renders exactly as before.
    """
    selected = 0
    frame = 0

    while True:
        timer.tick(FPS)
        frame += 1
        _render_main_menu(screen, selected, banner_text, frame)

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
    if current_initials and len(current_initials) == 3:
        letters = [ord(c) - ord("A") for c in current_initials.upper()]
    else:
        letters = [0, 0, 0]  # A, A, A
    slot = 0

    while True:
        timer.tick(FPS)
        _render_initials(screen, letters, slot)

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
    # Per-view lazy cache. This Week is fetched on open; All Time stays _UNFETCHED
    # until the first toggle. None=offline, []=empty, [...]=data (truth table).
    views = {"week": _UNFETCHED, "all": _UNFETCHED}
    active = "week"

    # Fetch This Week up front (open-on view, D-02), plus a best-effort last-week
    # champion fetch for the subtitle. last_week is independent of the toggle cache.
    _show_loading(screen)
    views["week"] = api_service.get_leaderboard(scope="week")
    last_week = api_service.get_leaderboard(scope="last_week")
    last_week_initials = last_week[0]["initials"] if last_week else None

    while True:
        timer.tick(FPS)
        _render_leaderboard(screen, active, views[active], last_week_initials)

        for event in pygame.event.get():
            week_entries = views["week"] if views["week"] is not _UNFETCHED else None
            if event.type == pygame.QUIT:
                return True, week_entries
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return False, week_entries
                elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    active = "all" if active == "week" else "week"
                    if views[active] is _UNFETCHED:
                        _show_loading(screen)
                        views[active] = api_service.get_leaderboard(scope="all")

        pygame.display.flip()


def run_game_over_screen(screen, timer, score, is_new_best, game_won, identity_error=False):
    """Show game over/victory screen with score. Returns after user presses SPACE.

    When ``identity_error`` is set (a tampered/invalid identity blocked the submit,
    D-05/D-06), render a small gray "Score not saved — identity error" line so the
    player sees why the score did not reach the board. The game stays fully playable;
    this is a passive notice, not a modal.
    """
    while True:
        timer.tick(FPS)
        _render_game_over(screen, score, is_new_best, game_won, identity_error)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    return "menu"

        pygame.display.flip()
