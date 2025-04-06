import pygame
import numpy as np
from numpy.typing import NDArray
import sys
import tkinter as tk
from tkinter import messagebox

# Initialize tkinter for error popups
root = tk.Tk()
root.withdraw()

# Window dimensions
width, height = 800, 600

# Colors for UI elements and background
white = (255, 255, 255)
black = (0, 0, 0)
blue = (0, 0, 255)
gray = (200, 200, 200)

# Initialize Pygame and set up the screen and clock
pygame.init()
screen = pygame.display.set_mode((width, height))
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)

# UI panel configuration
ui_panel_height = 150
ui_margin = 10
widget_spacing = 40
label_offset = 20

# Default wave parameters
wave_types = ['Zero', 'Sine', 'Cosine', 'Exponential', 'Dirac Delta']  # List of wave function types
selected_disp_type = wave_types[0]  # Default initial displacement is zero
selected_vel_type = wave_types[0]  # Default initial velocity is zero
amplitude = 1.0  # Amplitude of the wave
wavenumber = 1.0  # Wavenumber
wave_speed = 1.0  # Wave speed

# State flags to control simulation flow
paused = True
reset = True
started = False

# Spatial and temporal grid setup
num_points = 500  # Number of spatial points
x_vals = np.linspace(0, 2 * np.pi * 10, num_points)  # Create an array of spatial points (10 wavelengths)
u_vals = np.zeros_like(x_vals)  # Initial displacement
v_vals = np.zeros_like(x_vals)  # Initial velocity
time_step = 0.01
dx = x_vals[1] - x_vals[0]  # Spatial step

# UI Rects: Defining the positions of all UI elements on the screen
start_pause_button_rect = pygame.Rect(ui_margin, height - ui_panel_height + ui_margin + 20, 100, 30)
stop_button_rect = pygame.Rect(start_pause_button_rect.right + ui_margin, start_pause_button_rect.y, 100, 30)
disp_dropdown_rect = pygame.Rect(stop_button_rect.right + ui_margin, stop_button_rect.y, 150, 30)
vel_dropdown_rect = pygame.Rect(disp_dropdown_rect.right + ui_margin, disp_dropdown_rect.y, 150, 30)
amplitude_textbox_rect = pygame.Rect(vel_dropdown_rect.right + ui_margin, vel_dropdown_rect.y, 60, 30)
wavenumber_textbox_rect = pygame.Rect(amplitude_textbox_rect.right + ui_margin + 20, amplitude_textbox_rect.y, 60, 30)

# Input state: Track which textbox is currently being edited
active_input = None
text_inputs = {'amplitude': str(amplitude),
               'wavenumber': str(wavenumber)}  # Store inputs for amplitude and wavenumber


def draw_ui() -> None:
    """
    Draw the user interface elements on the screen.
    """
    pygame.draw.rect(screen, white, (0, height - ui_panel_height, width, ui_panel_height))

    # Buttons
    pygame.draw.rect(screen, gray if started else black, start_pause_button_rect, 2)
    pygame.draw.rect(screen, black, stop_button_rect, 2)
    pygame.draw.rect(screen, gray if started else black, disp_dropdown_rect, 2)
    pygame.draw.rect(screen, gray if started else black, vel_dropdown_rect, 2)
    pygame.draw.rect(screen, gray if started else black, amplitude_textbox_rect, 2)
    pygame.draw.rect(screen, gray if started else black, wavenumber_textbox_rect, 2)

    # Labels for each UI element
    screen.blit(font.render("Init. Displacement", True, black),
                (disp_dropdown_rect.x, disp_dropdown_rect.y - label_offset))
    screen.blit(font.render("Init. Velocity", True, black), (vel_dropdown_rect.x, vel_dropdown_rect.y - label_offset))
    screen.blit(font.render("Amplitude", True, black),
                (amplitude_textbox_rect.x, amplitude_textbox_rect.y - label_offset))
    screen.blit(font.render("Wave number", True, black),
                (wavenumber_textbox_rect.x, wavenumber_textbox_rect.y - label_offset))

    # Text shown on buttons and textboxes
    screen.blit(font.render('Start' if paused else 'Pause', True, black),
                (start_pause_button_rect.x + 10, start_pause_button_rect.y + 5))
    screen.blit(font.render('Stop', True, black), (stop_button_rect.x + 10, stop_button_rect.y + 5))
    screen.blit(font.render(selected_disp_type, True, black), (disp_dropdown_rect.x + 10, disp_dropdown_rect.y + 5))
    screen.blit(font.render(selected_vel_type, True, black), (vel_dropdown_rect.x + 10, vel_dropdown_rect.y + 5))
    screen.blit(font.render(text_inputs['amplitude'], True, black),
                (amplitude_textbox_rect.x + 5, amplitude_textbox_rect.y + 5))
    screen.blit(font.render(text_inputs['wavenumber'], True, black),
                (wavenumber_textbox_rect.x + 5, wavenumber_textbox_rect.y + 5))


def get_wave(func_type: str) -> NDArray:
    """
    Returns the initial wave profile (displacement or velocity) based on the selected function type.

    :param str func_type: Type of wave function, needs to be one of 'Sine', 'Cosine', 'Exponential', or 'Zero'
    :return: Array representing the initial wave.
    """
    if func_type == 'Sine':
        return amplitude * np.sin(wavenumber * x_vals)
    elif func_type == 'Cosine':
        return amplitude * np.cos(wavenumber * x_vals)
    elif func_type == 'Exponential':
        x0 = np.mean(x_vals)
        return amplitude * np.exp(-wavenumber * np.abs(x_vals - x0))
    elif func_type == 'Zero':
        return np.zeros_like(x_vals)  # Zero displacement/velocity
    elif func_type == 'Dirac Delta':
        return get_dirac_delta_velocity() # Return Dirac delta approximation


def get_dirac_delta_velocity() -> NDArray:
    """
    Returns an approximation of the Dirac delta function for the velocity using a narrow Gaussian distribution.

    :return: Array representing the Dirac delta velocity.
    """
    delta_width = 0.1  # Controls the width of the approximation
    center = num_points // 2  # Location of the Dirac delta (center of the domain)
    velocity = np.exp(-0.5 * ((x_vals - x_vals[center]) / delta_width) ** 2)  # Gaussian approximation
    return amplitude * velocity


def draw_wave() -> None:
    """
    Draw the current wave on the screen based on the current wave profile (u_vals).
    """
    y = u_vals  # Current displacement (wave)
    points = [(int(i * width / num_points), int(height / 2 - y_i * 100)) for i, y_i in enumerate(y)]  # Scale the wave
    for i in range(len(points) - 1):
        pygame.draw.line(screen, blue, points[i], points[i + 1], 2)  # Draw wave as a series of connected lines


def initialize_wave() -> bool:
    """
    Initializes the wave profile (u_vals, v_vals) based on the user inputs for the initial conditions.
    If the wave number is not a positive number , the function will generate an error popup indicating the mistake in
    the user's input.

    :returns: True if initial conditions are valid, otherwise returns false.
    """
    global u_vals, v_vals, amplitude, wavenumber

    try:
        # Convert user input strings to float and validate
        amplitude = float(text_inputs['amplitude'])
        wavenumber = float(text_inputs['wavenumber'])

        # Ensure wavenumber is positive
        if wavenumber <= 0:
            raise ValueError()

        u_vals = get_wave(selected_disp_type)  # Set initial displacement using selected displacement function
        v_vals = get_wave(selected_vel_type)  # Set initial velocity using selected velocity function

    except ValueError:
        messagebox.showerror("Input Error", f"Wave number must be a positive number, "
                                            f"but input {wavenumber} detected")  # Show error if invalid input
        return False

    return True


def update_wave() -> None:
    """
    Update the wave simulation by solving the wave equation numerically.
    This uses a finite difference method to update the vertical displacement (u_vals) and
    its time derivative (v_vals) at each time step.
    """
    global u_vals, v_vals
    c2 = wave_speed ** 2
    u_xx = np.zeros_like(u_vals)  # Initialize second derivative array
    u_xx[1:-1] = (u_vals[:-2] - 2 * u_vals[1:-1] + u_vals[
                                                   2:]) / dx ** 2  # Second spatial derivative using finite differences
    v_vals += time_step * c2 * u_xx  # Update velocity based on acceleration (second spatial derivative)
    u_vals += time_step * v_vals  # Update displacement based on velocity


# Main simulation loop
running = True
while running:
    screen.fill(black)  # Fill the screen with black to clear previous frame

    # Event handling (keyboard and mouse input)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # change flag status when user clicks on the screen
        elif event.type == pygame.MOUSEBUTTONDOWN:

            # User clicks on start button
            if start_pause_button_rect.collidepoint(event.pos) and not started:
                if initialize_wave():
                    paused = not paused
                    started = True

            # User clicks on stop button
            elif stop_button_rect.collidepoint(event.pos):
                paused = True
                started = False
                u_vals = np.zeros_like(x_vals)
                v_vals = np.zeros_like(x_vals)

            # disables interaction with initial condition options when simulation is running
            elif not started:
                if disp_dropdown_rect.collidepoint(event.pos):
                    i = wave_types.index(selected_disp_type)
                    selected_disp_type = wave_types[(i + 1) % len(wave_types)]

                elif vel_dropdown_rect.collidepoint(event.pos):
                    i = wave_types.index(selected_vel_type)
                    selected_vel_type = wave_types[(i + 1) % len(wave_types)]

                elif amplitude_textbox_rect.collidepoint(event.pos):
                    active_input = 'amplitude'

                elif wavenumber_textbox_rect.collidepoint(event.pos):
                    active_input = 'wavenumber'

        # update the parameter text boxes when user is typing
        elif event.type == pygame.KEYDOWN and active_input:
            if event.key == pygame.K_RETURN:
                active_input = None  # Stop editing

            elif event.key == pygame.K_BACKSPACE:
                text_inputs[active_input] = text_inputs[active_input][:-1]  # Remove last character

            else:
                text_inputs[active_input] += event.unicode  # Append new character

    if not paused and started:
        update_wave()  # Update wave state if the simulation is running
        draw_wave()  # Draw the updated wave on the screen

    draw_ui()  # Draw the UI elements

    pygame.display.flip()  # Update the display
    clock.tick(60)  # Set the frame rate to 60 FPS

# Clean up Pygame and exit the program
pygame.quit()
sys.exit()