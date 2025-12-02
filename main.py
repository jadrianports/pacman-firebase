import pygame
import copy
from settings import *
from player import Player  # Changed import back to player.py
from ghosts import Ghost
from settings import boards  # Changed import to get boards from settings

pygame.init()
screen = pygame.display.set_mode([WIDTH, HEIGHT])
pygame.display.set_caption("Pac-Man Refactored")
timer = pygame.time.Clock()
font = pygame.font.Font('freesansbold.ttf', 20)

# Initialize Game Objects
level = copy.deepcopy(boards)
player = Player()

# Ghost Setup
blinky = Ghost(56, 58, (0, 0), 2, 'assets/ghosts/red.png', 0, False, False, 0)
inky = Ghost(440, 388, (0, 0), 2, 'assets/ghosts/blue.png', 2, False, False, 1)
pinky = Ghost(440, 438, (0, 0), 2, 'assets/ghosts/pink.png', 2, False, False, 2)
clyde = Ghost(440, 438, (0, 0), 2, 'assets/ghosts/orange.png', 2, False, False, 3)
ghosts = [blinky, inky, pinky, clyde]

game_over = False
game_won = False
powerup = False
power_counter = 0  # Global state variable
eaten_ghost = [False, False, False, False]
startup_counter = 0
moving = False


def draw_board(level):
    num1 = TILE_HEIGHT
    num2 = TILE_WIDTH
    for i in range(len(level)):
        for j in range(len(level[i])):
            if level[i][j] == 1:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
            if level[i][j] == 2 and not powerup:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10)
            if level[i][j] == 3:
                pygame.draw.line(screen, BLUE, (j * num2 + (0.5 * num2), i * num1),
                                 (j * num2 + (0.5 * num2), i * num1 + num1), 3)
            if level[i][j] == 4:
                pygame.draw.line(screen, BLUE, (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
            if level[i][j] == 5:
                pygame.draw.arc(screen, BLUE, [(j * num2 - (num2 * 0.4)) - 2, (i * num1 + (0.5 * num1)), num2, num1],
                                0, PI / 2, 3)
            if level[i][j] == 6:
                pygame.draw.arc(screen, BLUE,
                                [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1], PI / 2, PI, 3)
            if level[i][j] == 7:
                pygame.draw.arc(screen, BLUE, [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1], PI,
                                3 * PI / 2, 3)
            if level[i][j] == 8:
                pygame.draw.arc(screen, BLUE,
                                [(j * num2 - (num2 * 0.4)) - 2, (i * num1 - (0.4 * num1)), num2, num1], 3 * PI / 2,
                                2 * PI, 3)
            if level[i][j] == 9:
                pygame.draw.line(screen, 'white', (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)


def check_consumptions(level, player, powerup, eaten_ghost, current_power_counter):  # <-- power_counter added here
    # Calculate player's grid coordinates
    pl_center_x = player.x + 23
    pl_center_y = player.y + 24
    grid_x = pl_center_x // TILE_WIDTH
    grid_y = pl_center_y // TILE_HEIGHT

    game_won_local = False

    # Check if Pac-Man is within a cell boundary (tolerance 10 pixels)
    if 0 < player.x < 870 and 0 < player.y < 950:
        center_x_offset = pl_center_x % TILE_WIDTH
        center_y_offset = pl_center_y % TILE_HEIGHT

        if center_x_offset > (TILE_WIDTH // 3) and center_x_offset < (TILE_WIDTH * 2 // 3) \
                and center_y_offset > (TILE_HEIGHT // 3) and center_y_offset < (TILE_HEIGHT * 2 // 3):

            # Check for Standard Dot (1)
            if level[grid_y][grid_x] == 1:
                level[grid_y][grid_x] = 0  # Consume dot
                player.score += 10

            # Check for Power Pellet (2)
            elif level[grid_y][grid_x] == 2:
                level[grid_y][grid_x] = 0  # Consume pellet
                player.score += 50
                powerup = True
                current_power_counter = 0  # Reset counter if power pellet is eaten
                eaten_ghost = [False, False, False, False]

    # Check win condition (no more dots or pellets)
    total_dots = sum(row.count(1) + row.count(2) for row in level)
    if total_dots == 0:
        game_won_local = True

    return level, powerup, current_power_counter, eaten_ghost, game_won_local  # <-- power_counter returned


def check_collisions(player, ghosts, powerup, eaten_ghost, lives):
    for i, ghost in enumerate(ghosts):
        # We need a proper rect for player for collision to work
        player.rect = pygame.Rect(player.x, player.y, 45, 45)

        if player.rect.colliderect(ghost.rect):
            if powerup and not eaten_ghost[i]:
                # Eat ghost
                eaten_ghost[i] = True
                # Scoring logic (multiplying by number of ghosts already eaten in this powerup cycle)
                score_multiplier = sum(eaten_ghost[:i]) + 1
                player.score += 200 * score_multiplier

                # Reset ghost to box
                ghost.x = 440
                ghost.y = 438
                ghost.in_box = True
                ghost.dead = True
            elif not powerup and not ghost.dead:
                # Ghost eats Pac-Man
                lives -= 1
                return lives, True, powerup, eaten_ghost
    return lives, False, powerup, eaten_ghost


def draw_misc():
    score_text = font.render(f'Score: {player.score}', True, WHITE)
    screen.blit(score_text, (10, 920))
    if powerup:
        # Indicator for powerup active (flicker for last third of powerup timer)
        if power_counter < 120 or power_counter % 30 < 15:
            pygame.draw.circle(screen, BLUE, (140, 930), 15)
    for i in range(player.lives):
        screen.blit(pygame.transform.scale(player.images[0], (30, 30)), (650 + i * 40, 915))
    if game_over and not game_won:
        pygame.draw.rect(screen, WHITE, [50, 200, 800, 300], 0, 10)
        pygame.draw.rect(screen, 'dark gray', [70, 220, 760, 260], 0, 10)
        gameover_text = font.render('Game over! Space bar to restart!', True, RED)
        screen.blit(gameover_text, (100, 300))
    if game_won:
        pygame.draw.rect(screen, WHITE, [50, 200, 800, 300], 0, 10)
        pygame.draw.rect(screen, 'dark gray', [70, 220, 760, 260], 0, 10)
        win_text = font.render('YOU WON! Space bar to play again!', True, GREEN)
        screen.blit(win_text, (100, 300))


def get_targets(player_obj):
    # Simplified target logic: ghosts always target Pac-Man's center
    p_x, p_y = player_obj.x + 22, player_obj.y + 22
    return [(p_x, p_y), (p_x, p_y), (p_x, p_y), (p_x, p_y)]


run = True
while run:
    timer.tick(FPS)
    screen.fill(BLACK)

    # Powerup timer logic
    if powerup and not game_over:
        power_counter += 1
        if power_counter > 180:  # Powerup lasts for 3 seconds (180 frames at 60 FPS)
            power_counter = 0
            powerup = False
            eaten_ghost = [False, False, False, False]  # Reset eaten status

    # Game Start/Pause Logic
    if startup_counter < 180 and not game_over and not game_won:
        moving = False
        startup_counter += 1
    else:
        moving = True

    draw_board(level)

    # ------------------ Core Logic Updates ------------------
    # 1. Check for dot/pellet consumption
    # PASS and RECEIVE power_counter here to fix UnboundLocalError
    level, powerup, power_counter, eaten_ghost, game_won_flag = check_consumptions(level, player, powerup, eaten_ghost,
                                                                                   power_counter)

    if game_won_flag:
        game_won = True
        game_over = True  # Treat win as game end state
        moving = False

    draw_misc()

    player.draw(screen)
    # Player's rect is needed for collision checks
    player.rect = pygame.Rect(player.x, player.y, 45, 45)
    if moving:
        player.update(level)

    # Ghost Logic
    targets = get_targets(player)
    for i, ghost in enumerate(ghosts):
        ghost.target = targets[i]
        if moving:
            # Ghost movement includes updating the ghost's collision rect
            ghost.update(level, powerup, eaten_ghost[i])
            # Ghost drawing must happen after update to ensure rect is current
        ghost.rect = ghost.draw(screen, powerup, eaten_ghost[i])

    # 2. Check for player-ghost collisions
    if moving and not game_over and not game_won:
        player.lives, game_over_hit, powerup, eaten_ghost = check_collisions(player, ghosts, powerup, eaten_ghost,
                                                                             player.lives)

        if game_over_hit:
            if player.lives > 0:
                # Reset player position
                player.x, player.y = 450, 663
                player.direction = 0
                startup_counter = 0  # Re-enter startup phase
            else:
                game_over = True
    # --------------------------------------------------------

    # Event Handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT: player.direction_command = 0
            if event.key == pygame.K_LEFT: player.direction_command = 1
            if event.key == pygame.K_UP: player.direction_command = 2
            if event.key == pygame.K_DOWN: player.direction_command = 3
            if event.key == pygame.K_SPACE and (game_over or game_won):
                # Full Game Reset logic
                player = Player()
                level = copy.deepcopy(boards)
                game_over = False
                game_won = False
                powerup = False
                power_counter = 0
                eaten_ghost = [False, False, False, False]
                startup_counter = 0
                # Re-initialize ghosts
                blinky = Ghost(56, 58, (0, 0), 2, 'assets/ghosts/red.png', 0, False, False, 0)
                inky = Ghost(440, 388, (0, 0), 2, 'assets/ghosts/blue.png', 2, False, False, 1)
                pinky = Ghost(440, 438, (0, 0), 2, 'assets/ghosts/pink.png', 2, False, False, 2)
                clyde = Ghost(440, 438, (0, 0), 2, 'assets/ghosts/orange.png', 2, False, False, 3)
                ghosts = [blinky, inky, pinky, clyde]

    pygame.display.flip()

pygame.quit()