import sys
import os
import pygame
import random
import time

from analytics_tracker import AnalyticsTrackerSummary, AnalyticsTrackerDetails

pygame.init()
screen_info = pygame.display.Info()

# Directories
project_dir = os.path.dirname(os.path.abspath(__file__))
asset_dir = os.path.join(project_dir, "Art_Assets\\")

# Assets
background = pygame.image.load(asset_dir + "background.png")
board = pygame.image.load(asset_dir + "board.png")
center_tile = pygame.image.load(asset_dir + "center_tile.png")
corner_tile = pygame.image.load(asset_dir + "corner_tile.png")
edge_tile = pygame.image.load(asset_dir + "edge_tile.png")

# Colors
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (128, 128, 128)
RED, BLUE, GREEN = (255, 0, 0), (0, 0, 255), (0, 255, 0)

# Board settings
BOARD_SIZE = 500
TILE_SIZE = 100
ROWS, COLS = 5, 5

# Screen setup
scale_factor = 0.8
WIDTH = int(screen_info.current_w * scale_factor)
HEIGHT = int(screen_info.current_h * scale_factor)
offset_x = (WIDTH - BOARD_SIZE) // 2
offset_y = (HEIGHT - BOARD_SIZE) // 2
scaled_background = pygame.transform.scale(background, (WIDTH, HEIGHT))
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# Game state
corner_positions = {(0, 0), (0, COLS - 1), (ROWS - 1, 0), (ROWS - 1, COLS - 1)}
edge_positions = {(r, c) for r in range(ROWS) for c in range(COLS)
                  if (r, c) not in corner_positions and (r == 0 or c == 0 or r == ROWS - 1 or c == COLS - 1)}
clicks = []
board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]
highlight_tile = None
highlight_start_time = None
interaction_paused = False
pending_removal = False
game_over = False
turn_count = 0
game_mode = "human_vs_ai"
visualize = True
debug_mode = True  # Toggle for debug prints

trackerSummary = AnalyticsTrackerSummary()
trackerDetails = AnalyticsTrackerDetails()

# Utility functions
def get_corner_rotation(row, col):
    return {(0, 0): 0, (0, COLS - 1): 270, (ROWS - 1, COLS - 1): 180, (ROWS - 1, 0): 90}.get((row, col), 0)

def get_edge_rotation(row, col):
    if row == 0: return 0
    elif col == COLS - 1: return 270
    elif row == ROWS - 1: return 180
    elif col == 0: return 90
    return 0

def choose_random_tile():
    return random.randint(0, ROWS - 1), random.randint(0, COLS - 1)

def get_tile_from_click(pos):
    x, y = pos
    col = (x - offset_x) // TILE_SIZE
    row = (y - offset_y) // TILE_SIZE
    return row, col

def draw_symbol(surface, symbol, x, y):
    if symbol == "X":
        pygame.draw.line(surface, RED, (x - 25, y - 25), (x + 25, y + 25), 5)
        pygame.draw.line(surface, RED, (x - 25, y + 25), (x + 25, y - 25), 5)
    elif symbol == "O":
        pygame.draw.circle(surface, GREEN, (x, y), 25, 5)

def check_winner(symbol):
    for r in range(ROWS):
        if all(board_state[r][c] == symbol for c in range(COLS)):
            return True
    for c in range(COLS):
        if all(board_state[r][c] == symbol for r in range(ROWS)):
            return True
    if all(board_state[i][i] == symbol for i in range(ROWS)):
        return True
    if all(board_state[i][COLS - 1 - i] == symbol for i in range(ROWS)):
        return True
    return False

def show_game_over_screen(winner):
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(BLACK)
    font = pygame.font.SysFont("Arial", 48)
    text = font.render(f"{winner} wins!", True, WHITE)
    textinput = font.render("Press Esc to quit or R to restart", True, WHITE)
    screen.blit(overlay, (0, 0))
    screen.blit(text, text.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
    screen.blit(textinput, textinput.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))
    pygame.display.flip()
    time.sleep(2)

def reset_game():
    global board_state, clicks, turn_count, highlight_tile, highlight_start_time
    global pending_removal, interaction_paused, game_over
    board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]
    clicks = []
    turn_count = 0
    highlight_tile = None
    highlight_start_time = None
    pending_removal = False
    interaction_paused = False
    game_over = False

def wait_for_game_over_input():
    global running
    waiting = True
    while waiting:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                waiting = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                    waiting = False
                elif event.key == pygame.K_r:
                    reset_game()
                    waiting = False

def draw_board():
    screen.blit(scaled_background, (0, 0))
    screen.blit(board, (offset_x, offset_y))
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

def handle_click(event):
    global turn_count
    if interaction_paused or game_over:
        return
    mouse_pos = pygame.mouse.get_pos()
    row, col = get_tile_from_click(mouse_pos)
    if 0 <= row < ROWS and 0 <= col < COLS:
        if board_state[row][col] == "":
            clicks.append(("X" if event.button == 1 else "O", (row, col)))
            board_state[row][col] = "X" if event.button == 1 else "O"
            turn_count += 1
            if debug_mode:
                print(f"Click: {board_state[row][col]} at ({row}, {col})")

def update_game_state():
    global highlight_tile, highlight_start_time, pending_removal, interaction_paused
    global game_over, turn_count

    for symbol, (row, col) in clicks:
        x = offset_x + col * TILE_SIZE + TILE_SIZE // 2
        y = offset_y + row * TILE_SIZE + TILE_SIZE // 2
        draw_symbol(screen, symbol, x, y)

    if turn_count % 5 == 0 and turn_count != 0 and not pending_removal:
        highlight_tile = choose_random_tile()
        highlight_start_time = time.time()
        pending_removal = True
        interaction_paused = True
        turn_count = 0

    if highlight_tile and pending_removal:
        elapsed = time.time() - highlight_start_time
        row, col = highlight_tile
        tile_x = offset_x + col * TILE_SIZE
        tile_y = offset_y + row * TILE_SIZE
        thickness = 6 if int((elapsed * 4) % 2) else 3
        pygame.draw.rect(screen, RED, (tile_x, tile_y, TILE_SIZE, TILE_SIZE), thickness)
        if elapsed >= 2:
            clicks[:] = [item for item in clicks if item[1] != highlight_tile]
            board_state[row][col] = ""
            highlight_tile = None
            highlight_start_time = None
            pending_removal = False
            interaction_paused = False

# Main loop
running = True
while running:
    draw_board()

    if not interaction_paused and not game_over:
        mouse_pos = pygame.mouse.get_pos()
        hover_row, hover_col = get_tile_from_click(mouse_pos)
        if 0 <= hover_row < ROWS and 0 <= hover_col < COLS:
            hover_x = offset_x + hover_col * TILE_SIZE
            hover_y = offset_y + hover_row * TILE_SIZE
            pygame.draw.rect(screen, (255, 255, 0), (hover_x, hover_y, TILE_SIZE, TILE_SIZE), 3)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            handle_click(event)

    update_game_state()


    # Check for winner
    if check_winner("X") or check_winner("O"):
        winner = "X" if check_winner("X") else "O"
        show_game_over_screen(winner)
        game_over = True

        if game_mode == "human_vs_ai":
            wait_for_game_over_input()
            game_over = False
        elif game_mode == "ai_vs_ai":
            reset_game()
            game_over = False
    # Check for draw
    if not check_winner("X") and not check_winner("O"):
        #board_full = all(board[row][col] != "" for row in range(ROWS) for col in range(COLS))
        ###--- Board state tracks the moves
        board_full = all(board_state[row][col] != "" for row in range(ROWS) for col in range(COLS))
        if board_full:
            show_game_over_screen("Draw")
            game_over = True

            if game_mode == "human_vs_ai":
                wait_for_game_over_input()
                game_over = False
            elif game_mode == "ai_vs_ai":
                pygame.time.wait(1000)  # Optional short pause
                reset_game()
                game_over = False


    pygame.display.flip()

# Final analytics logging (optional — move inside game-over logic if needed)
trackerSummary.log_game(
    play_id="ABC1234",
    game_mode="HvAI",
    winner="Human",
    win_moves=22,
    win_shape='X',
    lose='AI',
    lose_moves=21,
    lose_shape='O',
    tiles_removed=4
)

trackerDetails.log_game(
    play_id="ABC1234",
    game_mode="HvAI",
    player="Human",
    position=[2, 2],
    shape='X',
    tiles_removed_pos=['N', 'N']
)

pygame.quit()
sys.exit()



