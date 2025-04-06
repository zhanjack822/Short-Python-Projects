import pygame
import random
import math

# Window dimensions
width, height = 800, 600

# Colors
white: tuple[int, int, int] = (255, 255, 255)
red: tuple[int, int, int] = (255, 0, 0)
orange: tuple[int, int, int] = (255, 165, 0)
yellow: tuple[int, int, int] = (255, 255, 0)
blue: tuple[int, int, int] = (100, 200, 255)
purple: tuple[int, int, int] = (180, 100, 255)
green: tuple[int, int, int] = (100, 255, 100)

# Rocket properties
rocket_vel: int = 5
rocket_width: int = 10
rocket_height: int = 30
rocket_tail_height: int = 5

# Explosion properties
explosion_size: int = 50
explosion_particles: int = 100
particle_size: int = 2

# Physics parameters for pressure wave
pressure_decay_rate: float = 0.2
wave_speed: int = 1
max_wave_radius: int = 300  # Max radius for the pressure wave effect

# Tracer properties
max_tracer_velocity = 2
tracer_size = 3

def colour_blend(colour_start: tuple[int, int, int], colour_end: tuple[int, int, int], t: float) -> tuple[int, ...]:
    """
    Blends two colors based on the interpolation factor t.

    :param colour_start: The starting color (RGB).
    :param colour_end: The ending color (RGB).
    :param t: The interpolation factor, where 0 <= t <= 1.

    :return: The blended color as an RGB tuple.
    """
    return tuple(int(colour_start[i] + (colour_end[i] - colour_start[i]) * t) for i in range(3))

class PressureWave:
    """
    Represents a pressure wave that emanates from a rocket explosion.

    Attributes:
    int x: The x-coordinate of the wave's origin.
    int y: The y-coordinate of the wave's origin.
    int radius: The current radius of the pressure wave.
    int pressure: The current pressure of the wave.
    int time_alive: The number of frames the wave has been alive.

    Methods:
    update() -> None: Updates the wave's radius and pressure.
    apply_force(particle_x, particle_y) -> tuple[float, float]: Calculates the force applied to a particle by the wave.
    """
    def __init__(self, x: int, y: int, initial_radius: int = 0, initial_pressure: int = 255) -> None:
        self.x = x
        self.y = y
        self.radius = initial_radius
        self.pressure = initial_pressure
        self.time_alive = 0
        self.initial_pressure = initial_pressure  # To keep track of the initial pressure

    def update(self) -> None:
        """
        Updates the wave's radius and pressure, following a gas-like behavior
        where the pressure decreases with the inverse of the radius.
        """
        self.radius += wave_speed
        # Apply the gas law-like behavior where pressure decreases as the inverse of the radius
        if self.radius > 0:
            self.pressure = self.initial_pressure / self.radius  # Decreases with radius expansion
        else:
            self.pressure = 0

        self.time_alive += 1

        if self.radius > max_wave_radius:
            self.pressure = 0

    def apply_force(self, particle_x: int, particle_y: int) -> tuple[float, float]:
        """
        Calculates the force exerted on a particle by the pressure wave.
        """
        dist = math.sqrt((particle_x - self.x) ** 2 + (particle_y - self.y) ** 2)

        if dist < self.radius:
            force_magnitude = self.pressure * (1 - dist / self.radius)
            force_direction_x = (particle_x - self.x) / dist
            force_direction_y = (particle_y - self.y) / dist
            return force_magnitude * force_direction_x, force_magnitude * force_direction_y
        return 0, 0


class Rocket:
    """
    Represents a rocket launched in the game.

    Attributes:
    int x: The current x-coordinate of the rocket.
    int y: The current y-coordinate of the rocket.
    int vel: The velocity at which the rocket moves upwards.
    int target_y: The y-coordinate the rocket is targeting for detonation.
    trail (list[tuple[int, int]]): A list of previous positions to create a trail effect.
    color (tuple[int, int, int]): The color of the rocket.

    Methods:
    update() -> None: Updates the rocket's position and adds a trail.
    should_explode() -> bool: Determines whether the rocket has reached its target and should explode.
    draw(screen) -> None: Draws the rocket on the screen along with its trail.
    """
    def __init__(self, x: int, y: int, target_y: int, color: tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.vel = rocket_vel
        self.target_y = target_y
        self.trail = []
        self.color = color

    def update(self) -> None:
        """
        Updates the rocket's position and creates a trail behind it.
        :returns: None
        """
        self.trail.append((self.x, self.y))
        if len(self.trail) > 15:
            self.trail.pop(0)

        self.y -= self.vel

    def should_explode(self) -> bool:
        """
        Determines if the rocket has reached its target and should explode.

        :return: True if the rocket has reached the target, otherwise False.
        """
        return self.y <= self.target_y

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the rocket and its trail on the screen.

        :param pygame.Surface screen: The Pygame screen surface to draw on.
        :returns: None
        """
        for i, (tx, ty) in enumerate(self.trail):
            t = i / len(self.trail)
            color = colour_blend((255, 255, 255), self.color, t)  # white → rocket color
            alpha = int(255 * t)

            trail_surface = pygame.Surface((3, 3), pygame.SRCALPHA)
            trail_surface.fill((*color, alpha))
            screen.blit(trail_surface, (tx, ty))

        # Draw the rocket body as a triangle with a small rectangle as the tail
        rocket_points = [
            (self.x, self.y),  # Tip of the rocket
            (self.x - rocket_width // 2, self.y + rocket_height),  # Left side
            (self.x + rocket_width // 2, self.y + rocket_height),  # Right side
        ]
        pygame.draw.polygon(screen, self.color, rocket_points)

        # Rocket tail (small rectangle)
        pygame.draw.rect(screen, self.color, (self.x - rocket_width // 4, self.y + rocket_height, rocket_width // 2, rocket_tail_height))

class Explosion:
    """
    Represents an explosion at the rocket's detonation point.

    Attributes:
    int x: The x-coordinate of the explosion's center.
    int y: The y-coordinate of the explosion's center.
    int blast_radius: The current radius of the explosion's blast effect.
    int max_radius : The maximum radius the explosion can reach.
    int blast_alpha: The opacity of the explosion's blast.
    list[dict] particles: A list of particles representing the explosion's visual effects.

    Methods:
    update() -> None: Updates the particles' positions and fades them over time.
    draw(screen) -> None: Draws the explosion particles on the screen.
    """
    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y
        self.blast_radius = 10
        self.max_radius = 100
        self.blast_alpha = 100
        self.particles = []

        for _ in range(explosion_particles):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(2, 6)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed

            color = random.choice([red, orange, yellow, blue, purple, green])

            self.particles.append({
                'x': x,
                'y': y,
                'vx': vx,
                'vy': vy,
                'color': color,
                'alpha': 255,
                'lifetime': 60
            })

    def update(self) -> None:
        """
        Updates the particles' positions, velocities, and their lifetimes.

        :returns: None
        """
        for particle in self.particles:
            particle['x'] += particle['vx']
            particle['y'] += particle['vy']
            particle['vy'] += 0.05  # Optional: gravity effect
            particle['lifetime'] -= 1
            particle['alpha'] = max(0, int(255 * (particle['lifetime'] / 60)))

        self.particles = [p for p in self.particles if p['lifetime'] > 0]

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the explosion particles on the screen.

        :param pygame.Surface screen: The Pygame screen surface to draw on.
        :returns: None
        """
        for particle in self.particles:
            particle_surface = pygame.Surface((particle_size, particle_size), pygame.SRCALPHA)
            r, g, b = particle['color']
            a = particle['alpha']
            particle_surface.fill((r, g, b, a))
            screen.blit(particle_surface, (int(particle['x']), int(particle['y'])))

class Tracer:
    """
    Represents a tracer particle that follows the rocket's trajectory and is affected by pressure waves.

    Attributes:
    int x: The current x-coordinate of the tracer.
    int y: The current y-coordinate of the tracer.
    float vel_x: The x-component of the tracer's velocity.
    float vel_y: The y-component of the tracer's velocity.
    tuple[int, int, int] color: The color of the tracer.

    Methods:
    update(pressure_waves) -> None: Updates the tracer's position and velocity based on pressure waves.
    draw(screen) -> None: Draws the tracer on the screen.
    """
    def __init__(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.vel_x = random.uniform(-max_tracer_velocity, max_tracer_velocity)
        self.vel_y = random.uniform(-max_tracer_velocity, max_tracer_velocity)
        self.color = color

    def update(self, pressure_waves: list[PressureWave]) -> None:
        """
        Updates the tracer's position and velocity based on pressure waves.

        :param list[PressureWave] pressure_waves: A list of active pressure waves.
        :returns: None
        """
        self.x += self.vel_x
        self.y += self.vel_y

        for wave in pressure_waves:
            force_x, force_y = wave.apply_force(self.x, self.y)
            # Increase the influence on velocity for debugging
            self.vel_x += force_x * 0.5  # Apply a larger influence on velocity for testing
            self.vel_y += force_y * 0.5  # Apply a larger influence on velocity for testing

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the tracer on the screen.

        :param pygame.Surface screen: The Pygame screen surface to draw on.
        :returns: None
        """
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), tracer_size)

class Flash:
    """
    Represents a flash of light created at the rocket's explosion point.

    Attributes:
    int x: The x-coordinate of the flash's origin.
    int y : The y-coordinate of the flash's origin.
    int radius : The current radius of the flash.
    int max_radius: The maximum radius the flash can reach.
    tuple[int, int, int] color: The color of the flash.
    int alpha: The current alpha transparency of the flash.

    Methods:
    update() -> None: Expands the flash's radius and decreases its alpha transparency.
    draw(screen) -> None: Draws the flash on the screen.
    """
    def __init__(self, x: int, y: int, color: tuple[int, int, int]) -> None:
        self.x = x
        self.y = y
        self.radius = 0
        self.max_radius = 100
        self.color = color
        self.alpha = 150

    def update(self) -> None:
        """
        Expands the flash's radius and decreases its alpha transparency.
        """
        self.radius += 2  # Increase radius of flash
        self.alpha = max(0, self.alpha - 7)  # Increased fade speed for more transparency
        if self.radius > self.max_radius:
            self.alpha = 0  # Once the flash is fully expanded, set alpha to 0

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the flash on the screen.

        :param pygame.Surface screen: The Pygame screen surface to draw on.
        :returns: None
        """
        for r in range(self.radius, 0, -5):
            t = r / self.radius
            color = colour_blend(self.color, (0, 0, 0), t)  # Dim the color as radius increases
            alpha = int(self.alpha * (1 - r / self.max_radius))  # Increased transparency effect
            flash_surface = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            flash_surface.fill((*color, alpha))
            flash_surface.set_colorkey((0, 0, 0, 0))  # Make the center fully transparent
            screen.blit(flash_surface, (self.x - r, self.y - r))

def draw_ammo(screen: pygame.Surface, ammo_count: int) -> None:
    """
    Draws the ammo counter on the screen.

    :param pygame.Surface screen: The Pygame screen surface to draw on.
    :param int ammo_count: The current number of rockets available.
    :returns: None
    """
    rocket_icon_width = 15
    for i in range(ammo_count):
        pygame.draw.polygon(screen, white, [
            (width - (i + 1) * (rocket_icon_width + 5), height - 40),  # Tip of the rocket
            (width - (i + 1) * (rocket_icon_width + 5) - rocket_icon_width // 2, height - 10),  # Left side
            (width - (i + 1) * (rocket_icon_width + 5) + rocket_icon_width // 2, height - 10),  # Right side
        ])
        pygame.draw.rect(screen, white, (
            width - (i + 1) * (rocket_icon_width + 5) - rocket_icon_width // 4,
            height - 10,
            rocket_icon_width // 2,
            5
        ))

def main() -> None:
    """
    Main game loop where the Pygame environment is initialized and rockets, explosions, pressure waves, etc., are handled.
    """
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    rockets = []
    explosions = []
    pressure_waves = []
    tracers = []
    flashes = []

    ammo = 10
    reload_time = 0

    # Create fixed stars
    stars = [(random.randint(0, width), random.randint(0, height)) for _ in range(100)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ammo > 0:
                    rocket_x, rocket_y = pygame.mouse.get_pos()
                    flash_color = random.choice([red, orange, yellow, blue, purple, green])  # Random flash color
                    rockets.append(Rocket(rocket_x, height, rocket_y, flash_color))
                    ammo -= 1

        screen.fill((0, 0, 50))  # Dark blue background

        # Draw stars
        for star_x, star_y in stars:
            pygame.draw.circle(screen, white, (star_x, star_y), 2)

        # handle rockets
        for rocket in rockets:
            rocket.update()
            rocket.draw(screen)
            if rocket.should_explode():
                explosions.append(Explosion(rocket.x, rocket.y))
                pressure_waves.append(PressureWave(rocket.x, rocket.y))  # Create a new pressure wave
                flashes.append(Flash(rocket.x, rocket.y, rocket.color))  # Create a flash effect
                rockets.remove(rocket)

        # handle flashes
        for flash in flashes:
            flash.update()
            flash.draw(screen)
            if flash.alpha <= 0:
                flashes.remove(flash)

        # handle explosions
        for explosion in explosions:
            explosion.update()
            explosion.draw(screen)
            if len(explosion.particles) < explosion_particles // 2:
                explosions.remove(explosion)

        # Update and apply the pressure wave forces
        for wave in pressure_waves:
            wave.update()

        # Handle tracers affected by the pressure waves
        for tracer in tracers:
            tracer.update(pressure_waves)
            tracer.draw(screen)

        # Handle ammo reloading
        if ammo < 10:
            reload_time += 1
            if reload_time >= 120:  # 2 seconds
                ammo += 1
                reload_time = 0

        # Draw ammo counter
        draw_ammo(screen, ammo)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
