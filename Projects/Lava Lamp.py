import pygame
import numpy as np
import random

# Window dimensions
width, height = 800, 600
center_x = width / 2

# Lava lamp dimensions
lamp_bottom_width = 150
lamp_top_width = 0.4 * lamp_bottom_width
lamp_height = 300
lamp_x = (width - lamp_bottom_width) // 2
lamp_y = (height - lamp_height) // 2
top_y = lamp_y + lamp_height

# Create a trapezoidal shape for the lamp
top_x = lamp_x + (lamp_bottom_width - lamp_top_width) // 2
bottom_x = lamp_x

# Define points for fluid filled chamber of lamp
top_left = (top_x, lamp_y)
top_right = (top_x + lamp_top_width, lamp_y)
bottom_left = (bottom_x, lamp_y + lamp_height)
bottom_right = (bottom_x + lamp_bottom_width, lamp_y + lamp_height)
points = [
    top_left,
    top_right,
    bottom_right,
    bottom_left,
]

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

# Base upper trapezoid (inverted)
base_upper = [
    (center_x - base_top_width / 2, top_y + base_top_height),
    (center_x + base_top_width / 2, top_y + base_top_height),
    (center_x + lamp_bottom_width / 2, top_y),
    (center_x - lamp_bottom_width / 2, top_y)
]

# Base lower trapezoid
base_lower = [
    (center_x - base_top_width / 2, top_y + base_bottom_height),
    (center_x + base_top_width / 2, top_y + base_bottom_height),
    (center_x + lamp_bottom_width / 2, top_y + 2 * base_bottom_height),
    (center_x - lamp_bottom_width / 2, top_y + 2 * base_bottom_height)
]

# Unit vectors that point from the top corners to the bottom corners
left_vector = np.array([(lamp_top_width - lamp_bottom_width) / 2, lamp_height])
left_vector = left_vector / np.linalg.norm(left_vector)
right_vector = np.array([(lamp_bottom_width - lamp_top_width) / 2, lamp_height])
right_vector = right_vector / np.linalg.norm(right_vector)

# normal vectors pointing inward for each canted wall
n_left = np.array([-left_vector[1], left_vector[0]])
n_right = np.array([right_vector[1], -right_vector[0]])

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
opaque_color = (251, 128, 22)
opaque_density_at_reference = 950  # kg/m³
coefficient_of_expansion = -0.0004  # 1/K (note the negative sign)
reference_temperature = 20.0  # °C
heat_transfer_coefficient = 0.05  # can be tuned for realism

# Lamp base and top colour
metallic_silver = (192, 192, 192)

# Nightstand dimensions
nightstand_height = 40
nightstand_color = (180, 140, 100)  # Wood-like tone

# Blob properties
class Blob:
    """
    Represents a wax blob inside the lava lamp.

    Attributes
    ----------
    x : float
        The horizontal position of the blob.
    y : float
        The vertical position of the blob.
    radius : int
        The radius of the blob.
    temperature : float
        The current temperature of the blob in Celsius.
    density : float
        The current density of the blob in kg/m^3.
    vy : float
        The vertical velocity of the blob.
    vx : float
        The horizontal velocity of the blob.
    collided_left : bool
        Whether the blob is currently colliding with the left wall.
    collided_right : bool
        Whether the blob is currently colliding with the right wall.
    distance_left : float
        Distance from the left wall.
    distance_right : float
        Distance from the right wall.
    """

    def __init__(self, x: float, y: float, radius: int):
        self.x = x
        self.y = y
        self.radius = radius
        self.temperature = get_temperature_at_y(y)
        self.density = self.calculate_density()
        self.vy = 0
        self.vx = 0  # Horizontal velocity
        self.collided_left = False
        self.collided_right = False
        self.distance_left = 0
        self.distance_right = 0

    def calculate_density(self) -> float:
        """
        Calculate the current density of the blob based on its temperature using the linear thermal expansion model.

        :return: Updated density of the blob
        """
        return opaque_density_at_reference * (1 + coefficient_of_expansion * (self.temperature - reference_temperature))

    def update(self, temp_profile: list[float]) -> None:
        """
        Update the blob's temperature, density, and position based on buoyancy and collisions.

        :param temp_profile: The vertical temperature profile in the lamp
        :return: None
        """
        solvent_temp = get_temperature_at_y(self.y, temp_profile)

        # Newton's law of heating
        self.temperature += heat_transfer_coefficient * (solvent_temp - self.temperature)

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
        self.collided_left, self.collided_right = handle_wall_collision(self)

        # Update horizontal position
        self.x += self.vx

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draws the updated or initialized blobs

        :param pygame.Surface screen: screen that blobs will be drawn on
        :return: None
        """

        pygame.draw.circle(screen, opaque_color, (int(self.x), int(self.y)), self.radius)


def interpolate_color(cold: tuple[int, int, int], hot: tuple[int, int, int], t: float) -> tuple[int, ...]:
    """
    Linearly interpolate between two RGB colors to draw a colour gradient
    :param tuple[int, int, int] cold: cold colour RGB
    :param tuple[int, int, int] hot: hot colour RBG
    :param float t: scaled parameter between 0 and 1, indicating how far along the gradient to return an interpolated
    colour for
    :return: RBG colour between the hot and cold colours
    """

    return tuple(int(c + (h - c) * t) for c, h, t in zip(cold, hot, [t]*3))


def draw_temperature_gradient(screen: pygame.Surface, temps: list[float]) -> None:
    """
    Draw a vertical temperature gradient inside the lava lamp's fluid chamber

    :param pygame.Screen screen: screen surface that the gradient will be drawn on
    :param temps: list of temperature values for each step within the gradient
    :return: None
    """

    # Create a transparent surface
    gradient_surface = pygame.Surface((width, height), pygame.SRCALPHA)

    for i, temp in enumerate(temps):
        norm_temp = (temp - top_temp) / (bottom_temp - top_temp)
        color = interpolate_color((0, 0, 255), (255, 0, 0), norm_temp) + (200,)  # Add alpha for transparency

        y = lamp_y + int(i * lamp_height / steps)
        pygame.draw.rect(
            gradient_surface, color,
            (lamp_x, y, lamp_bottom_width, lamp_height / steps)
        )

    # Mask to the lamp polygon shape
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.polygon(mask, (255, 255, 255, 255), points)
    gradient_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

    # Blit the masked gradient to the main screen
    screen.blit(gradient_surface, (0, 0))

# Heat diffusion function
def update_temperature_profile(temps: list[float]) -> list[float]:
    """
    Update the temperature profile using the 1D heat equation.

    :param list[float] temps: list of temperature values for each step of the current temperature profile
    :return: list of temperature values for the updated temperature profile
    """

    new_temps = temps.copy()
    for i in range(1, len(temps) - 1):
        new_temps[i] = temps[i] + alpha * dt / dx**2 * (temps[i+1] - 2*temps[i] + temps[i-1])
    new_temps[-1] = bottom_temp
    new_temps[0] = top_temp
    return new_temps

# Map vertical position to temperature
def get_temperature_at_y(y: float, temps: list[float] = None) -> float:
    """
    Map  a vertical coordinate to its corresponding temperature.
    :param float y: y-coordinate being checked
    :param list[float] temps: temperature profile
    :return: The temperature at the given y coordinate within the temperature profile
    """

    index = int((y - lamp_y) / lamp_height * (steps - 1))
    index = max(0, min(steps - 1, index))
    if temps:
        return temps[index]
    else:
        return bottom_temp + (top_temp - bottom_temp) * (index / steps)

def draw_lamp(screen: pygame.Surface) -> None:
    """
    Draw the lamp's structure
    :param pygame.Surface screen: pygame surface on which the lamp is to be drawn
    :return: None
    """

    # draw the lamp top
    pygame.draw.polygon(screen, metallic_silver, top, 2)
    pygame.draw.polygon(screen, metallic_silver, top)

    # draw the upper portion of lamp base
    pygame.draw.polygon(screen, metallic_silver, base_upper, 2)
    pygame.draw.polygon(screen, metallic_silver, base_upper)

    # draw the lower portion of the lamp base
    pygame.draw.polygon(screen, metallic_silver, base_lower, 2)
    pygame.draw.polygon(screen, metallic_silver, base_lower)


def draw_blobs(screen: pygame.Surface, blobs: list[Blob]) -> None:
    """
    Draw the wax blobs
    :param pygame.Surface screen: pygame surface on which the wax blobs are drawn
    :param list[Blob] blobs: list of Blobs to be drawn
    :return: None
    """
    for blob in blobs:
        blob.draw(screen)

def draw_background(screen: pygame.Surface) -> None:
    """
    Draws the background for the simulation
    :param pygame.Surface screen: pygame surface on which the background is drawn
    :return: None
    """
    # Background wall color
    wall_color = (230, 210, 255)  # Light lavender/pink

    # Fill background
    screen.fill(wall_color)

    # Draw a crayon-like sun
    pygame.draw.circle(screen, (255, 200, 0), (60, 60), 20)


def handle_wall_collision(blob: Blob) -> tuple[bool, bool]:
    """
    Check if a wax blob has collided with the angled lamp walls and adjusts the velocity if a collision is detected.
    :param Blob blob: wax blob being checked
    :return: A pair of boolean values, the first for if the wax blob has collided with the left wall, the latter for
    if the wax blob has collided with the right wall. The return values are for debugging purposes.
    """
    blob_pos = np.array([blob.x, blob.y])

    disp_br = np.array(bottom_right) - blob_pos  # displacement to bottom right corner
    disp_bl = np.array(bottom_left) - blob_pos  # displacement to bottom left corner

    blob.distance_left = np.abs(np.dot(disp_bl, n_left))
    blob.distance_right = np.abs(np.dot(disp_br, n_right))

    collided_left = False
    collided_right = False

    # Left wall collision (using left_vector)
    if blob.distance_left <= blob.radius and blob.vy < 0:  # Check if the blob collides with the left wall as it moves up
        collided_left = True
        relative_velocity = np.array([blob.vx, blob.vy])

        # Calculate the dot product of velocity and wall direction vector
        dot_product_left = np.dot(relative_velocity, left_vector)

        # Set the velocity parallel to the wall using the dot product
        blob.vx = dot_product_left * left_vector[0]
        blob.vy = dot_product_left * left_vector[1]

    # Right wall collision (using right_vector)
    elif blob.distance_right <= blob.radius and blob.vy < 0:  # Check if the blob collides with the right wall as it moves up
        collided_right = True
        relative_velocity = np.array([blob.vx, blob.vy])

        # Calculate the dot product of velocity and wall direction vector
        dot_product_right = np.dot(relative_velocity, right_vector)

        # Set the velocity parallel to the wall using the dot product
        blob.vx = dot_product_right * right_vector[0]
        blob.vy = dot_product_right * right_vector[1]

    return collided_left, collided_right


def draw_debug_info(screen: pygame.Surface, blobs: list[Blob]) -> None:
    """
    Adds a real time readout of each blob's density and temperature
    :param pygame.Surface screen: pygame surface on which the debug information is drawn on
    :param list[Blob] blobs: list of Blobs whose data is to be drawn
    :return: None
    """
    # Prepare font for debug text
    font = pygame.font.SysFont(None, 16)

    for blob in blobs:
        debug_text = f"T={blob.temperature:.1f}°C ρ={blob.density:.1f} kg/m^3"
        text_surface = font.render(debug_text, True, (0, 0, 0))
        screen.blit(text_surface, (blob.x + 10, blob.y - 10))

def main() -> int:
    """
    Main loop of the simulation. Initializes the window, spawns blobs, updates temperature and motion, and handles
    drawing.
    :return: Returns 0 if the game is closed correctly.
    """
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Lava Lamp Simulation")
    clock = pygame.time.Clock()

    # Initialize blobs
    num_blobs = 2  # Set number of blobs
    blob_radius = 25  # Set radius of blobs

    blobs = []

    for _ in range(num_blobs):
        # Randomly initialize the y-coordinate
        blob_y = lamp_y + lamp_height - blob_radius - random.uniform(0, 50) # Position the blob at the bottom of the lamp

        # x-boundaries for where the blobs can spawn
        left_x_bound = top_left[0] + ((blob_y - top_left[1]) / left_vector[1]) * left_vector[0]  # x_pos of wall at blob's y
        left_offset = blob_radius * np.abs(np.dot(n_left, np.array([1, 0])))

        right_x_bound = top_right[0] + ((blob_y - top_right[1]) / right_vector[1]) * right_vector[0]
        right_offset = blob_radius * np.abs(np.dot(n_right, np.array([1, 0])))

        # randomly initialize the x-coordinate, initialize blob and append to blobs
        blob_x = random.uniform(left_x_bound + left_offset, right_x_bound - right_offset)
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

        # lamp body and temperature overlay
        draw_temperature_gradient(screen, temperature_profile)
        draw_lamp(screen)

        # Draw the nightstand
        pygame.draw.rect(screen, nightstand_color, (0, height - nightstand_height, width, nightstand_height))

        # draw and update blobs and their data readouts
        for blob in blobs:
            blob.update(temperature_profile)

        draw_blobs(screen, blobs)
        draw_debug_info(screen, blobs)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    return 0

if __name__ == "__main__":
    main()