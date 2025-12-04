import pygame

class Interface:
    def __init__(self, font, player):
        self.font = font
        self.player = player

    def draw(self, screen, score, powerup, lives, game_over, game_won, images):
        # Score
        score_text = self.font.render(f"Score: {score}", True, "white")
        screen.blit(score_text, (10, 920))

        # Powerup Indicator
        if powerup:
            pygame.draw.circle(screen, "blue", (140, 930), 15)

        # Lives
        for i in range(lives):
            screen.blit(
                pygame.transform.scale(images[0], (30, 30)),
                (650 + i * 40, 915)
            )

        # Game Over Screen
        if game_over:
            pygame.draw.rect(screen, "white", [50, 200, 800, 300], 0, 10)
            pygame.draw.rect(screen, "dark gray", [70, 220, 760, 260], 0, 10)
            gameover_text = self.font.render("Game over! Space bar to restart!", True, "red")
            screen.blit(gameover_text, (100, 300))

        # Victory Screen
        if game_won:
            pygame.draw.rect(screen, "white", [50, 200, 800, 300], 0, 10)
            pygame.draw.rect(screen, "dark gray", [70, 220, 760, 260], 0, 10)
            gameover_text = self.font.render("Victory! Space bar to restart!", True, "green")
            screen.blit(gameover_text, (100, 300))
