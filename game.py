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


pygame.init()
font = pygame.font.Font('freesansbold.ttf', 20)
board = Board()
level = board.tiles
## instantiate Ghosts
blinky = Ghost("blinky")
pinky = Ghost("pinky")
inky = Ghost("inky")
clyde = Ghost("clyde")
ghosts = [blinky, pinky, inky, clyde]
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
    if moving:
        player.move()
        # --- GHOST LOGIC ---
        for ghost in ghosts:
            ghost.center_x, ghost.center_y = ghost.get_center()
            ghost.turns, ghost.in_box = ghost.check_collisions(level)
            ghost.update_target(blinky, inky, pinky, clyde, player.x, player.y, powerup, eaten_ghost)

        # move Clyde only for now
        clyde.move_clyde()

        # respawn ghosts that went back to the box
        for ghost in ghosts:
            if ghost.in_box and ghost.dead:
                ghost.dead = False
    player.handle_wraparound()
    # pellet collisions / scoring (uses player object now)
    score, powerup, power_counter, eaten_ghost = player.check_collisions(
        level, powerup, power_counter, eaten_ghost
    )

    # push back score into global score variable (to preserve draw_misc usage)
    score = player.score

    interface.draw(
        screen,
        score,
        powerup,
        lives,
        game_over,
        game_won,
        player.images
    )

    player_circle = pygame.draw.circle(screen, 'black', (center_x, center_y), 20, 2)

    if powerup:
        clyde.speed = 1
    if eaten_ghost[3]:
         clyde.speed = 2
    if clyde.dead:
        clyde.speed = 4

    ## Collision with ghosts
    if not powerup:
        if (player_circle.colliderect(blinky.rect) and not blinky.dead) or \
                (player_circle.colliderect(inky.rect) and not inky.dead) or \
                (player_circle.colliderect(pinky.rect) and not pinky.dead) or \
                (player_circle.colliderect(clyde.rect) and not clyde.dead):
            if lives > 0:
                lives -= 1
                startup_counter = 0
                powerup = False
                power_counter = 0
                player.x = 450
                player.y = 663
                player.direction = 0
                player.direction_command = 0
                clyde.x = 440
                clyde.y = 438
                clyde.direction = 2
                eaten_ghost = [False, False, False, False]
                blinky.dead = False
                inky.dead = False
                clyde.dead = False
                pinky.dead = False
            else:
                game_over = True
                moving = False
                startup_counter = 0
    if powerup and player_circle.colliderect(clyde.rect) and eaten_ghost[3] and not clyde.dead:
        if lives > 0:
            powerup = False
            power_counter = 0
            lives -= 1
            startup_counter = 0
            player.x = 450
            player.y = 663
            player.direction = 0
            player.direction_command = 0
            clyde.x = 440
            clyde.y = 438
            clyde.direction = 2
            eaten_ghost = [False, False, False, False]
            blinky_dead = False
            inky_dead = False
            clyde.dead = False
            pinky_dead = False
        else:
            game_over = True
            moving = False
            startup_counter = 0
    if powerup and player_circle.colliderect(clyde.rect) and not clyde.dead and not eaten_ghost[3]:
        clyde.dead = True
        eaten_ghost[3] = True
        score += (2 ** eaten_ghost.count(True)) * 100


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