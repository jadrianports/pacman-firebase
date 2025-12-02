import pygame


class Ghost:
    def __init__(self, ghost_type):
        """
        ghost_type: string ID ('blinky','pinky','inky','clyde')
        """

        self.ghost_type = ghost_type

        # default starting positions (you can edit these later)
        start_positions = {
            "blinky": (56, 58),
            "inky":   (440, 388),
            "pinky":  (440, 438),
            "clyde":  (440, 438)
        }

        self.x, self.y = start_positions[ghost_type]

        # core state
        self.direction = 0
        self.speed = 2
        self.dead = False
        self.in_box = False
        self.id = ["blinky", "pinky", "inky", "clyde"].index(ghost_type)

        # load sprites
        self.load_images()

        # rect for collision
        self.rect = pygame.Rect(self.get_center()[0] - 18,
                                self.get_center()[1] - 18,
                                36, 36)


    # -------------------------------------------------------------
    # IMAGE LOADING
    # -------------------------------------------------------------

    def load_images(self):
        """Loads ghost sprites from folder based on ghost type."""

        color_map = {
            "blinky": "red",
            "pinky": "pink",
            "inky": "blue",
            "clyde": "orange"
        }

        color = color_map[self.ghost_type]

        # normal colored ghost
        normal_img = pygame.image.load(f"assets/ghosts/{color}.png")

        # load & scale all needed frames
        self.img_normal = pygame.transform.scale(normal_img, (45, 45))
        self.img_spooked = pygame.transform.scale(
            pygame.image.load("assets/ghosts/powerup.png"), (45, 45)
        )
        self.img_dead = pygame.transform.scale(
            pygame.image.load("assets/ghosts/dead.png"), (45, 45)
        )


    # -------------------------------------------------------------
    # HELPER FUNCTIONS
    # -------------------------------------------------------------

    def get_center(self):
        return self.x + 22, self.y + 22


    # -------------------------------------------------------------
    # DRAWING
    # -------------------------------------------------------------

    def draw(self, screen, powerup_active, eaten_list):
        """Draw ghost depending on current state + powerup state."""

        if self.dead:
            img = self.img_dead

        else:
            if powerup_active:
                if eaten_list[self.id]:
                    img = self.img_normal    # recovering ghost → normal color
                else:
                    img = self.img_spooked   # vulnerable
            else:
                img = self.img_normal

        # draw sprite
        screen.blit(img, (self.x, self.y))

        # update rect for collisions
        cx, cy = self.get_center()
        self.rect.x = cx - 18
        self.rect.y = cy - 18


    # -------------------------------------------------------------
    # CHECK COLLISIONS
    # -------------------------------------------------------------

    def check_collisions(self):
        self.turns = [False, False, False, False]
        if 