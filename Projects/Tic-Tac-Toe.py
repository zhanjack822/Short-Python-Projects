import pygame
import sys

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 600
HEIGHT = 700
LINE_WIDTH = 15
BOARD_ROWS = 3
BOARD_COLS = 3
SQUARE_SIZE = WIDTH // BOARD_COLS
CIRCLE_RADIUS = SQUARE_SIZE // 3
CIRCLE_WIDTH = 15
CROSS_WIDTH = 25
SPACE = SQUARE_SIZE // 4
BUTTON_HEIGHT = 50
BUTTON_WIDTH = 200

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Tic Tac Toe')

# Font
font = pygame.font.Font(None, 40)

# Game variables
board = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
player = 'X'
game_over = False


# Draw grid lines
def draw_lines():
    # Horizontal lines
    for i in range(1, BOARD_ROWS):
        pygame.draw.line(screen, BLACK, (0, i * SQUARE_SIZE), (WIDTH, i * SQUARE_SIZE), LINE_WIDTH)

    # Vertical lines
    for i in range(1, BOARD_COLS):
        pygame.draw.line(screen, BLACK, (i * SQUARE_SIZE, 0), (i * SQUARE_SIZE, WIDTH), LINE_WIDTH)


# Draw X and O figures
def draw_figures():
    for row in range(BOARD_ROWS):
        for col in range(BOARD_COLS):
            if board[row][col] == 'O':
                pygame.draw.circle(screen, BLUE,
                                   (int(col * SQUARE_SIZE + SQUARE_SIZE / 2),
                                    int(row * SQUARE_SIZE + SQUARE_SIZE / 2)),
                                   CIRCLE_RADIUS, CIRCLE_WIDTH)
            elif board[row][col] == 'X':
                pygame.draw.line(screen, RED,
                                 (col * SQUARE_SIZE + SPACE, row * SQUARE_SIZE + SPACE),
                                 (col * SQUARE_SIZE + SQUARE_SIZE - SPACE,
                                  row * SQUARE_SIZE + SQUARE_SIZE - SPACE),
                                 CROSS_WIDTH)
                pygame.draw.line(screen, RED,
                                 (col * SQUARE_SIZE + SPACE,
                                  row * SQUARE_SIZE + SQUARE_SIZE - SPACE),
                                 (col * SQUARE_SIZE + SQUARE_SIZE - SPACE,
                                  row * SQUARE_SIZE + SPACE),
                                 CROSS_WIDTH)


# Check for win
def check_win(player):
    # Check rows
    for row in range(BOARD_ROWS):
        if all([board[row][col] == player for col in range(BOARD_COLS)]):
            return True

    # Check columns
    for col in range(BOARD_COLS):
        if all([board[row][col] == player for row in range(BOARD_ROWS)]):
            return True

    # Check diagonals
    if all([board[i][i] == player for i in range(BOARD_ROWS)]):
        return True
    if all([board[i][BOARD_ROWS - 1 - i] == player for i in range(BOARD_ROWS)]):
        return True

    return False


# Check if board is full
def is_board_full():
    return all([board[row][col] is not None for row in range(BOARD_ROWS) for col in range(BOARD_COLS)])


# Draw reset button
def draw_reset_button():
    button_rect = pygame.Rect((WIDTH - BUTTON_WIDTH) // 2, HEIGHT - BUTTON_HEIGHT - 20,
                              BUTTON_WIDTH, BUTTON_HEIGHT)
    pygame.draw.rect(screen, GRAY, button_rect)
    text = font.render("Reset", True, BLACK)
    text_rect = text.get_rect(center=button_rect.center)
    screen.blit(text, text_rect)
    return button_rect


# Draw status text
def draw_status(status_text):
    status = font.render(status_text, True, BLACK)
    status_rect = status.get_rect(center=(WIDTH // 2, HEIGHT - BUTTON_HEIGHT - 60))
    screen.blit(status, status_rect)


# Reset game
def reset_game():
    global board, game_over, player
    board = [[None for _ in range(BOARD_COLS)] for _ in range(BOARD_ROWS)]
    game_over = False
    player = 'X'
    screen.fill(WHITE)
    draw_lines()
    return "Player X's turn"


# Main game loop
def main():
    global game_over, player
    screen.fill(WHITE)
    draw_lines()
    status_text = "Player X's turn"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouseX, mouseY = event.pos

                # Check if reset button is clicked
                reset_button = draw_reset_button()  # Get the button rect
                if reset_button.collidepoint(event.pos):
                    status_text = reset_game()
                    continue

                # Handle board clicks
                if not game_over and mouseY < WIDTH:
                    clicked_row = mouseY // SQUARE_SIZE
                    clicked_col = mouseX // SQUARE_SIZE

                    if board[clicked_row][clicked_col] is None:
                        board[clicked_row][clicked_col] = player
                        draw_figures()

                        if check_win(player):
                            game_over = True
                            status_text = f"Player {player} wins!"
                        elif is_board_full():
                            game_over = True
                            status_text = "It's a draw!"
                        else:
                            player = 'O' if player == 'X' else 'X'
                            status_text = f"Player {player}'s turn"

        # Draw everything
        reset_button = draw_reset_button()
        draw_status(status_text)
        pygame.display.update()


if __name__ == '__main__':
    main()