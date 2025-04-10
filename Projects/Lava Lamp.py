import pygame
import numpy as np
import random

# Window dimensions
width, height = 800, 600
center_x = width / 2

# Lava lamp dimensions
lamp_bottom_width = 150
lamp_top_width = 0.6 * lamp_bottom_width
lamp_height = 300
lamp_x = (width - lamp_bottom_width) // 2
lamp_y = (height - lamp_height) // 2
top_y = lamp_y + lamp_height

# Unit vectors that point from the top corners to the bottom corners
left_vector = np.array([(lamp_top_width - lamp_bottom_width) / 2, -lamp_height])
left_vector = left_vector / np.linalg.norm(left_vector)
right_vector = np.array([(lamp_bottom_width - lamp_top_width) / 2, -lamp_height])
right_vector = right_vector / np.linalg.norm(right_vector)

# Physical constants
g = 9.81  # gravity m/s^2
dt = 0.1  # time step
dx = 1.0  # spatial resolution for temperature
alpha = 0.001  # thermal diffusivity for wax (approx)
steps = lamp_height  # one cell per pixel vertically

# Temperature boundaries
bottom_temp = 60.0  # °C
top_temp = 20.0  # °C

# Solvent (translucent liquid) properties
translucent_color = (0, 0, 255)
translucent_density = 940  # kg/m³

# Opaque blob (wax) properties
opaque_color = (255, 0, 0)
opaque_density_at_reference = 950  # kg/m³
coefficient_of_expansion = -0.0004  # 1/K (note the negative sign)
reference_temperature = 20.0  # °C
heat_transfer_coeff = 0.05  # can be tuned for realism

# Lamp base and top colour
metallic_silver = (192, 192, 192)

# Nightstand dimensions
nightstand_height = 40
nightstand_color = (180, 140, 100)  # Wood-like tone

# Blob properties
class Blob:
    def __init__(self, x, y, radius):
        # Randomize the blob's initial x and y positions
        x += random.uniform(-30, 30)  # Offset by ±30 pixels
        y += random.uniform(-30, 30)  # Offset by ±30 pixels
        self.x = x
        self.y = y
        self.radius = radius
        self.temperature = get_temperature_at_y(y)
        self.density = self.calculate_density()
        self.vy = 0
        self.vx = 0  # Horizontal velocity

    def calculate_density(self):
        return opaque_density_at_reference * (1 + coefficient_of_expansion * (self.temperature - reference_temperature))

    def update(self, temp_profile):
        solvent_temp = get_temperature_at_y(self.y, temp_profile)

        # Newton's law of heating
        self.temperature += heat_transfer_coeff * (solvent_temp - self.temperature)

        # Recalculate density with updated temperature
        self.density = self.calculate_density()

        # Compute buoyant force and vertical motion
        specific_net_force = (self.density - translucent_density) * g
        acceleration = specific_net_force / self.density
        self.vy += acceleration * dt
        self.y += self.vy  # Update vertical position

        # Contain blobs within the lamp (vertical boundaries)
        min_y = lamp_y + self.radius
        max_y = lamp_y + lamp_height - self.radius
        if self.y < min_y:
            self.y = min_y
            self.vy = 0
        elif self.y > max_y:
            self.y = max_y
            self.vy = 0

        # Handle horizontal collisions with the walls
        handle_wall_collision(self)

        # Update horizontal position
        self.x += self.vx

    def draw(self, screen):
        pygame.draw.circle(screen, opaque_color, (int(self.x), int(self.y)), self.radius)


def interpolate_color(cold, hot, t):
    """Linearly interpolate between two RGB colors."""
    return tuple(int(c + (h - c) * t) for c, h, t in zip(cold, hot, [t]*3))


def draw_temperature_gradient(screen, temps):
    for i, temp in enumerate(temps):
        norm_temp = (temp - top_temp) / (bottom_temp - top_temp)
        color = interpolate_color((0, 0, 255), (255, 0, 0), norm_temp)  # Blue to Red
        y = lamp_y + int(i * lamp_height / steps)
        pygame.draw.rect(
            screen, color,
            (lamp_x + 2, y, lamp_bottom_width - 4, lamp_height / steps)
        )

# Heat diffusion function
def update_temperature_profile(temps):
    new_temps = temps.copy()
    for i in range(1, len(temps) - 1):
        new_temps[i] = temps[i] + alpha * dt / dx**2 * (temps[i+1] - 2*temps[i] + temps[i-1])
    new_temps[-1] = bottom_temp
    new_temps[0] = top_temp
    return new_temps

# Map vertical position to temperature
def get_temperature_at_y(y, temps=None):
    index = int((y - lamp_y) / lamp_height * (steps - 1))
    index = max(0, min(steps - 1, index))
    if temps:
        return temps[index]
    else:
        return bottom_temp + (top_temp - bottom_temp) * (index / steps)

def draw_lamp(screen):
    # Create a trapezoidal shape for the lamp
    top_x = lamp_x + (lamp_bottom_width - lamp_top_width) // 2
    bottom_x = lamp_x

    # Define points for trapezoid
    points = [
        (top_x, lamp_y),  # top left
        (top_x + lamp_top_width, lamp_y),  # top right
        (bottom_x + lamp_bottom_width, lamp_y + lamp_height),  # bottom right
        (bottom_x, lamp_y + lamp_height),  # bottom left
    ]

    pygame.draw.polygon(screen, (255, 255, 255), points, 2)  # Draw trapezoidal lamp border
    pygame.draw.polygon(screen, translucent_color, points)  # Fill the lamp with translucent color

    # draw the top and bottom of the lava lamp
    top_width = lamp_top_width * 0.6  # narrow top edge of trapezoid

    base_top_width = lamp_bottom_width * 0.6
    base_top_height = lamp_height * 0.2

    base_bottom_height = base_top_height

    top = [
        (center_x - top_width / 2, lamp_y - base_top_height),
        (center_x + top_width / 2, lamp_y - base_top_height),
        (center_x + lamp_top_width / 2, lamp_y),
        (center_x - lamp_top_width / 2, lamp_y)
    ]
    pygame.draw.polygon(screen, metallic_silver, top, 2)  # Draw trapezoidal lamp border
    pygame.draw.polygon(screen, metallic_silver, top)  # Fill the lamp with translucent color

    # Base upper trapezoid (inverted)
    base_upper = [
        (center_x - base_top_width / 2, top_y + base_top_height),
        (center_x + base_top_width / 2, top_y + base_top_height),
        (center_x + lamp_bottom_width / 2, top_y),
        (center_x - lamp_bottom_width / 2, top_y)
    ]
    pygame.draw.polygon(screen, metallic_silver, base_upper, 2)
    pygame.draw.polygon(screen, metallic_silver, base_upper)

    # Base lower trapezoid
    base_lower = [
        (center_x - base_top_width / 2, top_y + base_bottom_height),
        (center_x + base_top_width / 2, top_y + base_bottom_height),
        (center_x + lamp_bottom_width / 2, top_y + 2 * base_bottom_height),
        (center_x - lamp_bottom_width / 2, top_y + 2 * base_bottom_height)
    ]
    pygame.draw.polygon(screen, metallic_silver, base_lower, 2)
    pygame.draw.polygon(screen, metallic_silver, base_lower)

def draw_blobs(screen, blobs):
    for blob in blobs:
        blob.draw(screen)

def draw_background(screen):
    # Background wall color
    wall_color = (230, 210, 255)  # Light lavender/pink

    # Fill background
    screen.fill(wall_color)

    # Draw a crayon-like sun
    pygame.draw.circle(screen, (255, 200, 0), (60, 60), 20)

def get_lamp_wall_bounds(y):
    relative_y = (y - lamp_y) / lamp_height
    relative_y = max(0, min(1, relative_y))  # Clamp to [0, 1]
    half_width = lamp_top_width / 2 + (lamp_bottom_width - lamp_top_width) / 2 * relative_y
    left = center_x - half_width
    right = center_x + half_width
    return left, right


def handle_wall_collision(blob):
    left, right = get_lamp_wall_bounds(blob.y)

    # Left wall collision (using left_vector)
    if (blob.x - blob.radius <= left) or (blob.x + blob.radius >= right):  # Check if the blob collides with the left wall
        relative_velocity = np.array([blob.vx, blob.vy])

        # Calculate the dot product of velocity and wall direction vector
        dot_product_left = np.dot(relative_velocity, left_vector)

        # Reflect the velocity parallel to the wall using the dot product
        blob.vx = dot_product_left * left_vector[0]
        blob.vy = dot_product_left * left_vector[1]


def main():
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Lava Lamp Simulation")
    clock = pygame.time.Clock()

    # Initialize blobs
    num_blobs = 3  # Set number of blobs
    blob_radius = 20  # Set radius of blobs

    blobs = []
    for _ in range(num_blobs):
        # Randomly initialize the x-coordinate of each blob within the lamp's bottom width
        blob_x = random.uniform(lamp_x + blob_radius + 5, lamp_x + lamp_bottom_width - blob_radius - 5)
        blob_y = lamp_y + lamp_height - blob_radius - random.uniform(0, 20) # Position the blob at the bottom of the lamp
        blobs.append(Blob(blob_x, blob_y, blob_radius))

    # Initialize temperature profile
    temperature_profile = [top_temp + (bottom_temp - top_temp) * (i / steps) for i in range(steps)]

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        temperature_profile = update_temperature_profile(temperature_profile)

        screen.fill((255, 255, 255))
        draw_background(screen)

        # lamp body
        draw_lamp(screen)

        # Draw the nightstand
        pygame.draw.rect(screen, nightstand_color, (0, height - nightstand_height, width, nightstand_height))

        for blob in blobs:
            blob.update(temperature_profile)

        draw_blobs(screen, blobs)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
