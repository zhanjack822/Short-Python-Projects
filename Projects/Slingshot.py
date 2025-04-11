import pygame
import math

# Window size
WIDTH, HEIGHT = 800, 600

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)

# Slingshot properties
SLINGSHOT_X, SLINGSHOT_Y = 50, HEIGHT // 2
SLINGSHOT_RADIUS = 20
MAX_EXTENT = 200

# Target properties
TARGETS = [(700, 100), (700, 300), (700, 500)]

# Projectile properties
PROJECTILE_RADIUS = 10

# Gravity
GRAVITY = 9.81

class Projectile:
    def __init__(self, x, y, vx, vy):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += GRAVITY * dt

    def draw(self, screen):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), PROJECTILE_RADIUS)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()

    slingshot_retracted = False
    slingshot_start = (0, 0)
    projectile = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                slingshot_start = event.pos
                slingshot_retracted = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and slingshot_retracted:
                mouse_x, mouse_y = event.pos
                dx = mouse_x - SLINGSHOT_X
                dy = mouse_y - SLINGSHOT_Y
                angle = math.atan2(dy, dx)
                distance = math.hypot(dx, dy)
                speed = distance / MAX_EXTENT * 500
                vx = math.cos(angle) * speed
                vy = math.sin(angle) * speed
                projectile = Projectile(SLINGSHOT_X, SLINGSHOT_Y, vx, vy)
                slingshot_retracted = False

        screen.fill(WHITE)

        if slingshot_retracted:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            dx = mouse_x - SLINGSHOT_X
            dy = mouse_y - SLINGSHOT_Y
            angle = math.atan2(dy, dx)
            distance = min(math.hypot(dx, dy), MAX_EXTENT)
            end_x = SLINGSHOT_X + math.cos(angle) * distance
            end_y = SLINGSHOT_Y + math.sin(angle) * distance
            pygame.draw.line(screen, (0, 0, 0), (SLINGSHOT_X, SLINGSHOT_Y), (end_x, end_y), 5)

        for target in TARGETS:
            pygame.draw.circle(screen, (0, 255, 0), target, 20)

        if projectile:
            projectile.update(1 / 60)
            projectile.draw(screen)
            if projectile.x > WIDTH or projectile.y > HEIGHT:
                projectile = None

        pygame.draw.circle(screen, (0, 0, 0), (SLINGSHOT_X, SLINGSHOT_Y), SLINGSHOT_RADIUS)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()

