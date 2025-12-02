# Build Pac-Man from Scratch in Python with PyGame!!
import copy
from board import boards
import pygame
import math
from settings import *
from pacman import Pacman
from ghosts import Ghost

pygame.init()
screen = pygame.display.set_mode([WIDTH, HEIGHT])
timer = pygame.time.Clock()
font = pygame.font.Font('freesansbold.ttf', 20)
level = copy.deepcopy(boards)
color = 'blue'
PI = math.pi
###    instantiate Pacman object ###
player = Pacman()


# animation / flicker counter (kept global for minimal change)
counter = 0
flicker = False

# game state
score = 0
powerup = False
power_counter = 0
eaten_ghost = [False, False, False, False]

moving = False
ghost_speeds = [2, 2, 2, 2]
startup_counter = 0
lives = 3
game_over = False
game_won = False


def draw_misc():
    score_text = font.render(f'Score: {score}', True, 'white')
    screen.blit(score_text, (10, 920))
    if powerup:
        pygame.draw.circle(screen, 'blue', (140, 930), 15)
    for i in range(lives):
        screen.blit(pygame.transform.scale(player.images[0], (30, 30)), (650 + i * 40, 915))
    if game_over:
        pygame.draw.rect(screen, 'white', [50, 200, 800, 300], 0, 10)
        pygame.draw.rect(screen, 'dark gray', [70, 220, 760, 260], 0, 10)
        gameover_text = font.render('Game over! Space bar to restart!', True, 'red')
        screen.blit(gameover_text, (100, 300))
    if game_won:
        pygame.draw.rect(screen, 'white', [50, 200, 800, 300], 0, 10)
        pygame.draw.rect(screen, 'dark gray', [70, 220, 760, 260], 0, 10)
        gameover_text = font.render('Victory! Space bar to restart!', True, 'green')
        screen.blit(gameover_text, (100, 300))


def check_collisions(player_obj, power, power_count, eaten_ghosts):
    """
    Updated to accept player object so it uses player.get_center() and player.x
    Maintains original scoring/powerup behavior.
    """
    center_x, center_y = player_obj.get_center()

    if 0 < player_obj.x < 870:
        tile = level[center_y // TILE_HEIGHT][center_x // TILE_WIDTH]
        if tile == 1:
            level[center_y // TILE_HEIGHT][center_x // TILE_WIDTH] = 0
            player_obj.score += 10
        elif tile == 2:
            level[center_y // TILE_HEIGHT][center_x // TILE_WIDTH] = 0
            player_obj.score += 50
            power = True
            power_count = 0
            eaten_ghosts = [False, False, False, False]

    return player_obj.score, power, power_count, eaten_ghosts


## DRAW MAP CIRCLES, BIG CIRCLES AND WALLS
def draw_board():
    num1 = TILE_HEIGHT
    num2 = TILE_WIDTH
    for i in range(len(level)):
        for j in range(len(level[i])):
            if level[i][j] == 1:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 4)
            if level[i][j] == 2 and not flicker:
                pygame.draw.circle(screen, 'white', (j * num2 + (0.5 * num2), i * num1 + (0.5 * num1)), 10)
            if level[i][j] == 3:
                pygame.draw.line(screen, color, (j * num2 + (0.5 * num2), i * num1),
                                 (j * num2 + (0.5 * num2), i * num1 + num1), 3)
            if level[i][j] == 4:
                pygame.draw.line(screen, color, (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)
            if level[i][j] == 5:
                pygame.draw.arc(screen, color, [(j * num2 - (num2 * 0.4)) - 2, (i * num1 + (0.5 * num1)), num2, num1],
                                0, PI / 2, 3)
            if level[i][j] == 6:
                pygame.draw.arc(screen, color,
                                [(j * num2 + (num2 * 0.5)), (i * num1 + (0.5 * num1)), num2, num1], PI / 2, PI, 3)
            if level[i][j] == 7:
                pygame.draw.arc(screen, color, [(j * num2 + (num2 * 0.5)), (i * num1 - (0.4 * num1)), num2, num1], PI,
                                3 * PI / 2, 3)
            if level[i][j] == 8:
                pygame.draw.arc(screen, color,
                                [(j * num2 - (num2 * 0.4)) - 2, (i * num1 - (0.4 * num1)), num2, num1], 3 * PI / 2,
                                2 * PI, 3)
            if level[i][j] == 9:
                pygame.draw.line(screen, 'white', (j * num2, i * num1 + (0.5 * num1)),
                                 (j * num2 + num2, i * num1 + (0.5 * num1)), 3)


def check_position(centerx, centery, direction, level_map):
    """
    Global check_position preserves your original logic but now takes direction and level_map.
    Returns list: [R_allowed, L_allowed, U_allowed, D_allowed]
    """
    turns = [False, False, False, False]
    # check collisions based on center x and center y of player +/- fudge number
    if centerx // 30 < 29:
        if direction == 0:
            if level_map[centery // TILE_HEIGHT][(centerx - FUDGE_FACTOR) // TILE_WIDTH] < 3:
                turns[1] = True
        if direction == 1:
            if level_map[centery // TILE_HEIGHT][(centerx + FUDGE_FACTOR) // TILE_WIDTH] < 3:
                turns[0] = True
        if direction == 2:
            if level_map[(centery + FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                turns[3] = True
        if direction == 3:
            if level_map[(centery - FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                turns[2] = True

        if direction == 2 or direction == 3:
            if 12 <= centerx % TILE_WIDTH <= 18:
                if level_map[(centery + FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[3] = True
                if level_map[(centery - FUDGE_FACTOR) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[2] = True
            if 12 <= centery % TILE_HEIGHT <= 18:
                if level_map[centery // TILE_HEIGHT][(centerx - TILE_WIDTH) // TILE_WIDTH] < 3:
                    turns[1] = True
                if level_map[centery // TILE_HEIGHT][(centerx + TILE_WIDTH) // TILE_WIDTH] < 3:
                    turns[0] = True
        if direction == 0 or direction == 1:
            if 12 <= centerx % TILE_WIDTH <= 18:
                if level_map[(centery + TILE_HEIGHT) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[3] = True
                if level_map[(centery - TILE_HEIGHT) // TILE_HEIGHT][centerx // TILE_WIDTH] < 3:
                    turns[2] = True
            if 12 <= centery % TILE_HEIGHT <= 18:
                if level_map[centery // TILE_HEIGHT][(centerx - FUDGE_FACTOR) // TILE_WIDTH] < 3:
                    turns[1] = True
                if level_map[centery // TILE_HEIGHT][(centerx + FUDGE_FACTOR) // TILE_WIDTH] < 3:
                    turns[0] = True
    else:
        turns[0] = True
        turns[1] = True

    return turns


run = True
while run:
    timer.tick(FPS)

    # keep main-loop animation counter for flicker/animation timing
    if counter < 19:
        counter += 1
        if counter > 3:
            flicker = False
    else:
        counter = 0
        flicker = True

    # sync player animation counter to main counter
    player.set_animation_counter(counter)

    ## START POWERUP COUNTDOWN
    if powerup and power_counter < 600:
        power_counter += 1
    ## STOP POWERUP ONCE COUNTDOWN RUNS OUT
    elif powerup and power_counter >= 600:
        power_counter = 0
        powerup = False
        eaten_ghost = [False, False, False, False]
    ## SHORT COUNTDOWN BEFORE GAME ACTUALLY STARTS
    if startup_counter < 180:
        moving = False
        startup_counter += 1
    else:
        moving = True

    screen.fill('black')
    draw_board()
    blinky = Ghost("blinky")
    pinky = Ghost("pinky")
    inky = Ghost("inky")
    clyde = Ghost("clyde")

    ghosts = [blinky, pinky, inky, clyde]
    for ghost in ghosts:
        ghost.draw(screen, powerup, eaten_ghost)
    # draw player via object
    player.draw(screen)
    # collision checks and movement logic via Pacman object
    center_x, center_y = player.get_center()
    # compute allowed turns with the global function (unchanged logic)
    player.set_turns_allowed(check_position(center_x, center_y, player.direction, level))
    player.update_direction()
    if moving:
        player.move()
    player.handle_wraparound()

    # pellet collisions / scoring (uses player object now)
    score, powerup, power_counter, eaten_ghost = check_collisions(player, powerup, power_counter, eaten_ghost)

    # push back score into global score variable (to preserve draw_misc usage)
    score = player.score

    draw_misc()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                player.direction_command = 0
            if event.key == pygame.K_LEFT:
                player.direction_command = 1
            if event.key == pygame.K_UP:
                player.direction_command = 2
            if event.key == pygame.K_DOWN:
                player.direction_command = 3
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_RIGHT and player.direction_command == 0:
                player.direction_command = player.direction
            if event.key == pygame.K_LEFT and player.direction_command == 1:
                player.direction_command = player.direction
            if event.key == pygame.K_UP and player.direction_command == 2:
                player.direction_command = player.direction
            if event.key == pygame.K_DOWN and player.direction_command == 3:
                player.direction_command = player.direction

    # this loop duplicates the earlier update_direction behavior, kept for parity
    for i in range(4):
        if player.direction_command == i and player.turns_allowed[i]:
            player.direction = i

    pygame.display.flip()

pygame.quit()

# sound effects, restart and winning messages
