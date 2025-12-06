# Build Pac-Man from Scratch in Python with PyGame!!
import copy
import pygame
import math
from settings import *
from pacman import Pacman
from ghosts import Ghost
from controls import ControlManager
from board import Board
from interface import Interface
from gamestate import GameState

pygame.init()
state = GameState()
font = pygame.font.Font('freesansbold.ttf', 20)
board = Board()
level = board.tiles
## instantiate Ghosts
blinky = Ghost("blinky")
pinky = Ghost("pinky")
inky = Ghost("inky")
clyde = Ghost("clyde")
ghosts = [blinky, inky, pinky, clyde]
###    instantiate Pacman object ###
player = Pacman()
interface = Interface(font, player)
controls = ControlManager()


# animation / flicker counter (kept global for minimal change)
counter = 0
flicker = False

# game state
score = 0

powerup = False
power_counter = 0
eaten_ghost = [False, False, False, False]

moving = False
startup_counter = 0
lives = 3
game_over = False
game_won = False


run = True
while run:
    TIMER.tick(FPS)

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
        for g in ghosts:
            if not g.dead:
                g.speed = 2  # NORMAL SPEED
        eaten_ghost = [False, False, False, False]
    ## SHORT COUNTDOWN BEFORE GAME ACTUALLY STARTS
    if startup_counter < 180:
        moving = False
        startup_counter += 1
    else:
        moving = True

    screen.fill('black')
    board.draw(screen, flicker, BLUE)

    # draw all ghosts
    for ghost in ghosts:
        ghost.draw(screen, powerup, eaten_ghost)
    ##
    # draw player via object
    player.draw(screen)
    # collision checks and movement logic via Pacman object
    center_x, center_y = player.get_center()
    # compute allowed turns with the global function (unchanged logic)
    player.set_turns_allowed(player.compute_turns(level))
    player.update_direction()
    # --- GHOST LOGIC ---
    for ghost in ghosts:
        ghost.update_target(player.x, player.y, powerup, eaten_ghost)
        ghost.turns, ghost.in_box = ghost.check_collisions(level)

    if moving:
        player.move()
        if not blinky.dead and not blinky.in_box:
            blinky.move_blinky()
        else:
            blinky.move_clyde()
        if not pinky.dead and not pinky.in_box:
            pinky.move_pinky()
        else:
            pinky.move_clyde()
        if not inky.dead and not inky.in_box:
            inky.move_inky()
        else:
            inky.move_clyde()
        clyde.move_clyde()
        print(eaten_ghost)

    # respawn ghosts that went back to the box
    for ghost in ghosts:
        if ghost.in_box and ghost.dead:
            ghost.dead = False
    player.handle_wraparound()
    # pellet collisions / scoring (uses player object now)
    score, powerup, power_counter, eaten_ghost = player.check_collisions(
        level, powerup, power_counter, eaten_ghost
    )

    interface.draw(
        screen,
        score,
        powerup,
        lives,
        game_over,
        game_won,
        player.images
    )

    player_circle =  pygame.Rect(center_x - 20, center_y - 20, 40, 40)

    for i, ghost in enumerate(ghosts):
        if ghost.dead:
            ghost.speed = 4  # returning to box → fastest
        elif powerup:
            if not eaten_ghost[i]:
                ghost.speed = 1  # vulnerable → slower
            else:
                ghost.speed = GHOST_SPEED  # eaten → slightly faster

    ## Collision with ghosts
    def reset_round():
        global lives, startup_counter, powerup, power_counter, eaten_ghost, game_over, moving

        lives -= 1
        startup_counter = 0
        powerup = False
        power_counter = 0

        # reset player to its class-defined starting position
        player.reset()  # uses Pacman's start_position and start_direction

        # Reset all ghosts to their starting positions
        for ghost in ghosts:
            ghost.reset_to_start()

        eaten_ghost[:] = [False, False, False, False]

        if lives <= 0:
            game_over = True
            moving = False


    # --- COLLISION HANDLING ---
    for i, ghost in enumerate(ghosts):
        # powered-up ghost collision
        if powerup and player_circle.colliderect(ghost.rect) and not ghost.dead and not eaten_ghost[i]:
            n_eaten = eaten_ghost.count(True)
            ghost.dead = True
            eaten_ghost[i] = True
            player.score += (2 ** n_eaten) * 100

        # normal collision or powered-up ghost already eaten
        elif (not powerup or (powerup and eaten_ghost[i])) and player_circle.colliderect(ghost.rect) and not ghost.dead:
            if lives > 0:
                reset_round()
    score = player.score



    ## CONTROLS
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

        controls.handle_event(event, player)

    # this loop duplicates the earlier update_direction behavior, kept for parity
    for i in range(4):
        if player.direction_command == i and player.turns_allowed[i]:
            player.direction = i

    if clyde.in_box and clyde.dead:
        clyde.dead = False

    pygame.display.flip()


pygame.quit()

# sound effects, restart and winning messages