import pygame
import math

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
slingshot_launch_origin = (slingshot_x, slingshot_y - arm_height)

# Target properties
targets = [(700, 100), (700, 300), (700, 500)]

# Projectile properties
projectile_radius = 10

# Gravity (pixels per second squared)
gravity = 981


class Projectile:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += gravity * dt

    def draw(self, screen):
        pygame.draw.circle(screen, red, (int(self.x), int(self.y)), projectile_radius)


def draw_slingshot(screen):
    # Prong tips
    left_arm_top = (slingshot_x - arm_spread, slingshot_y - arm_height)
    right_arm_top = (slingshot_x + arm_spread, slingshot_y - arm_height)

    # Arms (Y shape)
    pygame.draw.line(screen, brown, (slingshot_x, slingshot_y), left_arm_top, 6)
    pygame.draw.line(screen, brown, (slingshot_x, slingshot_y), right_arm_top, 6)

    # Handle
    pygame.draw.rect(screen, dark_brown, (slingshot_x - 5, slingshot_y, 10, grip_height))

    return left_arm_top, right_arm_top


def main():
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    slingshot_retracted = False
    projectile = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                slingshot_retracted = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and slingshot_retracted:
                mouse_x, mouse_y = event.pos
                dx = mouse_x - slingshot_launch_origin[0]
                dy = mouse_y - slingshot_launch_origin[1]

                if dx >= 0:
                    slingshot_retracted = False
                    continue  # Only allow pulling left

                angle = math.atan2(dy, dx)
                distance = math.hypot(dx, dy)
                speed = distance / max_extent * 500
                vx = -math.cos(angle) * speed
                vy = -math.sin(angle) * speed
                projectile = Projectile(slingshot_x, slingshot_y - arm_height, vx, vy)
                slingshot_retracted = False

        screen.fill(white)

        # Draw slingshot and get prong tips
        left_tip, right_tip = draw_slingshot(screen)

        # Draw elastic band if pulled
        if slingshot_retracted:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - slingshot_x
            dy = mouse_y - slingshot_y
            angle = math.atan2(dy, dx)
            distance = min(math.hypot(dx, dy), max_extent)
            end_x = slingshot_x + math.cos(angle) * distance
            end_y = slingshot_y + math.sin(angle) * distance

            pygame.draw.line(screen, black, left_tip, (end_x, end_y), 2)
            pygame.draw.line(screen, black, right_tip, (end_x, end_y), 2)

        # Draw targets
        for target in targets:
            pygame.draw.circle(screen, green, target, 20)

        # Update and draw projectile
        if projectile:
            projectile.update(1 / 60)
            projectile.draw(screen)
            if projectile.x > width or projectile.y > height:
                projectile = None

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
