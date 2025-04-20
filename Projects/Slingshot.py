import pygame
import math
from typing import Tuple, Optional

# Window size
width, height = 800, 600

# Colors
white = (255, 255, 255)
red = (255, 0, 0)
brown = (139, 69, 19)
dark_brown = (101, 67, 33)
green = (0, 255, 0)
black = (0, 0, 0)

# Slingshot properties
slingshot_x, slingshot_y = 150, height // 2
max_extent = 100
arm_height = 60
arm_spread = 30
grip_height = 40

# Target properties
targets = [(700, 100), (700, 300), (700, 500)]

# Projectile properties
projectile_radius = 10

# Gravity (pixels per second squared)
gravity = 981


class Projectile:
    """
    Class object for the slingshot projectile.

    :param x: Initial x-position of the projectile.
    :param y: Initial y-position of the projectile.
    :param vx: Initial x-velocity of the projectile.
    :param vy: Initial y-velocity of the projectile.
    """

    def __init__(self, x: float, y: float, vx: float, vy: float) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def update(self, dt: float) -> None:
        """
        Update the position and velocity of the projectile.

        :param dt: Time interval since the last update (in seconds).
        """
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += gravity * dt

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the projectile on the given screen.

        :param screen: The Pygame surface on which the projectile is drawn.
        """
        pygame.draw.circle(screen, red, (int(self.x), int(self.y)), projectile_radius)


def draw_slingshot(screen: pygame.Surface) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Draws the slingshot on the screen.

    :param screen: The Pygame surface on which the slingshot is drawn.
    :return: A tuple containing the positions of the left and right prong tips.
    """
    # Prong tips
    left_arm_top = (slingshot_x - arm_spread, slingshot_y - arm_height)
    right_arm_top = (slingshot_x + arm_spread, slingshot_y - arm_height)

    # Arms (Y shape)
    pygame.draw.line(screen, brown, (slingshot_x, slingshot_y), left_arm_top, 6)
    pygame.draw.line(screen, brown, (slingshot_x, slingshot_y), right_arm_top, 6)

    # Handle
    pygame.draw.rect(screen, dark_brown, (slingshot_x - 5, slingshot_y, 10, grip_height))

    return left_arm_top, right_arm_top


def main() -> None:
    """
    Main game loop for the slingshot simulation.

    - Initializes Pygame, handles input events, updates the game state, and draws the screen.
    - Handles projectile launch and target collision.
    """
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    slingshot_retracted = False
    projectile: Optional[Projectile] = None
    pouch_pos = (slingshot_x, slingshot_y - arm_height)

    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            # stop the game if the player quits
            if event.type == pygame.QUIT:
                running = False

            # set a retracted flag to true if the player clicks and holds the LMB
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                slingshot_retracted = True

            # launch the projectile when the player lets go of LMB
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and slingshot_retracted:
                # displacement in pouch position from the center of the slingshot prongs
                dx = pouch_pos[0] - slingshot_x
                dy = pouch_pos[1] - (slingshot_y - arm_height)

                # only allow the projectile to launch if slingshot is pulled to the left
                if dx >= 0:
                    slingshot_retracted = False
                    continue

                # Calculate the angle and speed for projectile motion
                angle = math.atan2(dy, dx)
                distance = math.hypot(dx, dy)
                speed = distance / max_extent * 900
                vx = -math.cos(angle) * speed
                vy = -math.sin(angle) * speed
                projectile = Projectile(pouch_pos[0], pouch_pos[1], vx, vy)
                slingshot_retracted = False

        # Update screen
        screen.fill(white)

        # Draw slingshot and get prong tips
        left_tip, right_tip = draw_slingshot(screen)

        # Draw elastic when pulled
        if slingshot_retracted:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - slingshot_x
            dy = mouse_y - (slingshot_y - arm_height)
            angle = math.atan2(dy, dx)
            distance = min(math.hypot(dx, dy), max_extent)
            pouch_x = slingshot_x + math.cos(angle) * distance
            pouch_y = (slingshot_y - arm_height) + math.sin(angle) * distance
            pouch_pos = (pouch_x, pouch_y)

            pygame.draw.line(screen, black, left_tip, pouch_pos, 2)
            pygame.draw.line(screen, black, right_tip, pouch_pos, 2)

        # Draw targets
        for target in targets:
            pygame.draw.circle(screen, green, target, 20)

        # Update and draw projectile
        if projectile:
            projectile.update(1 / 60)
            projectile.draw(screen)

            # Check if projectile is out of bounds and reset if so
            if projectile.x < 0 or projectile.x > width or projectile.y < 0 or projectile.y > height:
                projectile = None

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
