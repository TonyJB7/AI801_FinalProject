import sys
import os
import pygame
import random
import time
from analytics_tracker import AnalyticsTracker

pygame.init()  # ← This must happen first
tracker = AnalyticsTracker()
screen_info = pygame.display.Info()

###---Project Directory
project_dir=os.path.dirname(os.path.abspath(__file__))
###---Game imgaes
asset_dir=os.path.join(project_dir,"Art_Assets\\")


###--- Load the image
background = pygame.image.load(asset_dir+"background.png")

board = pygame.image.load(asset_dir+"board.png")

center_tile = pygame.image.load(asset_dir+"center_tile.png")
corner_tile = pygame.image.load(asset_dir+"corner_tile.png")
edge_tile = pygame.image.load(asset_dir+"edge_tile.png")

###--- Colors to be used in the game
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128,128,128)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)

###--- Resolution setting
BOARD_SIZE = 500
TILE_SIZE = 100
ROWS, COLS = 5, 5
#WIDTH, HEIGHT = 700, 900
#screen_info=pygame.display.Info()
#info = pygame.display.Info()
screen_width = screen_info.current_w
screen_height = screen_info.current_h
scale_factor = 0.8  # Use 80% of screen size, for example
WIDTH = int(screen_width * scale_factor)
HEIGHT = int(screen_height * scale_factor)
#screen = pygame.display.set_mode((WIDTH, HEIGHT))
offset_x = (WIDTH - BOARD_SIZE) // 2
offset_y = (HEIGHT - BOARD_SIZE) // 2
scaled_background = pygame.transform.scale(background, (WIDTH, HEIGHT))
#offset_x = 100  # Try adjusting this interactively
#offset_y = 250  # Same here
###--- Define corner and edge positions as (row, col) grid coordinates
corner_positions = {(0, 0), (0, COLS - 1), (ROWS - 1, 0), (ROWS - 1, COLS - 1)}
edge_positions = set()
clicks = []
board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))

def get_corner_rotation(row, col):
    if row == 0 and col == 0:       # Top-left corner
        return 0
    elif row == 0 and col == COLS - 1:  # Top-right
        return 270
    elif row == ROWS - 1 and col == COLS - 1:  # Bottom-right
        return 180
    elif row == ROWS - 1 and col == 0:        # Bottom-left
        return 90
    return 0  # fallback


def get_edge_rotation(row, col):
    if row == 0: return 0          # Top edge
    elif col == COLS - 1: return 270   # Right edge
    elif row == ROWS - 1: return 180  # Bottom edge
    elif col == 0: return 90       # Left edge
    return 0

def choose_random_tile():
    r = random.randint(0, ROWS - 1)
    c = random.randint(0, COLS - 1)
    return (r, c)

def tile_center(row, col):
    x = offset_x + col * TILE_SIZE + TILE_SIZE // 2
    y = offset_y + row * TILE_SIZE + TILE_SIZE // 2
    return (x, y)

def check_winner(symbol):
    # Horizontal
    for r in range(ROWS):
        if all(board_state[r][c] == symbol for c in range(COLS)):
            return True

    # Vertical
    for c in range(COLS):
        if all(board_state[r][c] == symbol for r in range(ROWS)):
            return True

    # Diagonal (\)
    if all(board_state[i][i] == symbol for i in range(ROWS)):
        return True

    # Diagonal (/)
    if all(board_state[i][COLS - 1 - i] == symbol for i in range(ROWS)):
        return True

    return False

highlight_tile = None
highlight_start_time = 0

for r in range(ROWS):
    for c in range(COLS):
        if (r, c) not in corner_positions:
            if r == 0 or c == 0 or r == ROWS - 1 or c == COLS - 1:
                edge_positions.add((r, c))


running = True
turn_count = 0
highlight_tile = None
highlight_start_time = None
pending_removal = False
game_mode = "human_vs_ai"  # or "ai_vs_ai"
visualize = True  # Toggle graphics on/off
#if visualize:
    # draw tiles, board, symbols, highlights...


while running:



    ### Draw static elements
    screen.blit(scaled_background, (0, 0))
    screen.blit(board, (offset_x, offset_y))  # if you want to offset it

    ### Draw the grid of tiles
    for row in range(ROWS):
        for col in range(COLS):
            x = offset_x + col * TILE_SIZE
            y = offset_y + row * TILE_SIZE

            if (row, col) in corner_positions:
                tile = pygame.transform.rotate(corner_tile, get_corner_rotation(row, col))
            elif (row, col) in edge_positions:
                tile = pygame.transform.rotate(edge_tile, get_edge_rotation(row, col))
            else:
                tile = center_tile

            screen.blit(tile, (x, y))

            ##font = pygame.font.SysFont(None, 24)
           ## label = font.render(f"({row},{col})", True, (255, 0, 0))
    hover_mouse_x, hover_mouse_y = pygame.mouse.get_pos()
    hover_col = (hover_mouse_x - offset_x) // TILE_SIZE
    hover_row = (hover_mouse_y - offset_y) // TILE_SIZE

    if 0 <= hover_row < ROWS and 0 <= hover_col < COLS:
        hover_x = offset_x + hover_col * TILE_SIZE
        hover_y = offset_y + hover_row * TILE_SIZE
        pygame.draw.rect(screen, (255, 255, 0), (hover_x, hover_y, TILE_SIZE, TILE_SIZE), 3)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if event.type == pygame.MOUSEBUTTONDOWN:

            click_col = (mouse_x - offset_x) // TILE_SIZE
            click_row = (mouse_y - offset_y) // TILE_SIZE

            if 0 <= click_row < ROWS and 0 <= click_col < COLS:
                center_x = offset_x + click_col * TILE_SIZE + TILE_SIZE // 2
                center_y = offset_y + click_row * TILE_SIZE + TILE_SIZE // 2
                center = (center_x, center_y)
                if not any(pos == center for _, pos in clicks):

                    if event.button == 1:
                        clicks.append(("X", (center_x, center_y)))
                        turn_count += 1

                    elif event.button == 3:
                        clicks.append(("O", (center_x, center_y)))
                        turn_count += 1
                    if not board_state[click_row][click_col]:  # tile unoccupied
                        if event.button == 1:
                            board_state[click_row][click_col] = "X"
                            check_winner("X")
                        elif event.button == 3:
                            board_state[click_row][click_col] = "O"
                            check_winner("O")
                else: print("Invalid click")


    for symbol, (x, y) in clicks:
        if symbol == "X":
            pygame.draw.line(screen, RED, (x - 25, y - 25), (x + 25, y + 25), 5)
            pygame.draw.line(screen, RED, (x - 25, y + 25), (x + 25, y - 25), 5)
        elif symbol == "O":
            pygame.draw.circle(screen, GREEN, (x, y), 25, 5)

    if turn_count % 5 == 0 and turn_count != 0 and not pending_removal:
        r, c = choose_random_tile()
        highlight_tile = (r, c)
        highlight_start_time = time.time()
        pending_removal = True

        turn_count = 0

    if highlight_tile and pending_removal:
        elapsed = time.time() - highlight_start_time
        row, col = highlight_tile
        tile_x = offset_x + col * TILE_SIZE
        tile_y = offset_y + row * TILE_SIZE

        # Flashing effect: alternate thickness based on time
        pulse = int((elapsed * 4) % 2)  # toggles between 0 and 1 every 0.25s
        thickness = 3 if pulse else 6
        pygame.draw.rect(screen, RED, (tile_x, tile_y, TILE_SIZE, TILE_SIZE), thickness)

        if elapsed >= 2:
            center = offset_x + col * TILE_SIZE + TILE_SIZE // 2, offset_y + row * TILE_SIZE + TILE_SIZE // 2
            clicks = [item for item in clicks if item[1] != center]
            pending_removal = False
            highlight_tile = None
            highlight_start_time = None

    pygame.display.flip()  # 🚨 Important: this makes all blitted surfaces visible



# Quit Pygame
pygame.quit()
sys.exit()




