# actions.py
def restart_game(player, ghosts, eaten_ghost, board):
    """
    Reset all game objects and flags to initial state.
    """
    # Reset player
    player.reset()

    # Reset ghosts
    positions = [(56, 58, 0), (440, 388, 2), (440, 438, 2), (440, 438, 2)]
    for ghost, (x, y, dir) in zip(ghosts, positions):
        ghost.reset(x, y, dir)

    # Reset eaten flags
    for i in range(4):
        eaten_ghost[i] = False

    # Return new game state
    return {
        'lives': 3,
        'powerup': False,
        'power_counter': 0,
        'startup_counter': 0,
        'game_over': False,
        'game_won': False,
        'level': board.tiles
    }


def submit_score(score):
    # Placeholder for leaderboard submission
    print(f"Submitting score: {score}")


def view_leaderboards():
    # Placeholder for leaderboard display
    print("Displaying leaderboards...")
