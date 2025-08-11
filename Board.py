###--------------------------------------------------------------------------------
### Game: Disrupt-O-Tac
### Authors: Project Group 2 - Amir Ayazi, Antonio Blanco
### Date:
### Description
###---------------------------------------------------------------------------------

###--- Libraries
import os
import random
import sys
import time
import pygame
#from sympy import false

###--- External modules coded by project team
from analytics_tracker import AnalyticsTrackerSummary, AnalyticsTrackerDetails
from mcts_AI import MonteCarloAI

###-------------------------------------------------
### Initialization of variables, setting, options
###
###--------------------------------------------------
pygame.init()
screen_info = pygame.display.Info()
clock = pygame.time.Clock()

###--- Directories for assets will be relative path
project_dir = os.path.dirname(os.path.abspath(__file__))
asset_dir = os.path.join(project_dir, "Art_Assets\\")

###---Simple assets created in GIMP
background = pygame.image.load(asset_dir + "background.png")###---Clouds
board = pygame.image.load(asset_dir + "board.png")###--- board solid (not visible by users)

###--- The tiles of the game. 3 created and programmatically duplicated
center_tile = pygame.image.load(asset_dir + "center_tile.png")
corner_tile = pygame.image.load(asset_dir + "corner_tile.png")
edge_tile = pygame.image.load(asset_dir + "edge_tile.png")

###--- Basic  Colors
WHITE, BLACK, GRAY = (255, 255, 255), (0, 0, 0), (128, 128, 128)
RED, BLUE, GREEN = (255, 0, 0), (0, 0, 255), (0, 255, 0)

###--- Board settings (Do not change as it is sized properly) if need to change the
###--- size of the game. Use scale_factor
BOARD_SIZE = 500
TILE_SIZE = 100
ROWS, COLS = 5, 5

###--- Screen setup
scale_factor = 0.8
WIDTH = int(screen_info.current_w * scale_factor)
HEIGHT = int(screen_info.current_h * scale_factor)
offset_x = (WIDTH - BOARD_SIZE) // 2
offset_y = (HEIGHT - BOARD_SIZE) // 2

###--- Scales based on screen resolution
scaled_background = pygame.transform.scale(background, (WIDTH, HEIGHT))
screen = pygame.display.set_mode((WIDTH, HEIGHT))

####--- Init Game state
corner_positions = {(0, 0), (0, COLS - 1), (ROWS - 1, 0), (ROWS - 1, COLS - 1)}
edge_positions = {(r, c) for r in range(ROWS) for c in range(COLS)
                  if (r, c) not in corner_positions and (r == 0 or c == 0 or r == ROWS - 1 or c == COLS - 1)}
clicks = []
board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]
###--- Booleans
highlight_tile = None
highlight_start_time = None
interaction_paused = False
pending_removal = False
game_over = False
visualize = True
debug_mode = True  # Toggle for debug prints
###current_player = "Human"  # or "AI" if AI goes first
current_player = "Human"
last_starting_player = None
turn_count = 0
game_mode = "human_vs_ai"
###game_mode = "ai_vs_ai"
selected_agent_ai1 = "MCTS"
selected_agent_ai2 = "MCTS"
iterations_ai1 = 200
iterations_ai2 = 200
show_start_screen = True
pending_ai_turn = False
next_player_after_trap = None
trap_triggered_this_turn = False


#clock = pygame.time.Clock()


###--- Initializing the analytics
trackerSummary = AnalyticsTrackerSummary()
trackerDetails = AnalyticsTrackerDetails()
AI_MOVE_EVENT = pygame.USEREVENT + 1
class Player:
    def __init__(self, name, is_ai, symbol=None, agent=None, iterations=100):
        self.name = name
        self.is_ai = is_ai
        self.symbol = symbol  # "X" or "O"
        self.agent = agent    # Optional: your AI agent instance
        self.iterations = iterations  # Optional: for MCTS or other AI configs

    def play_ai_move(self):
        if self.agent:
            row, col = self.agent.select_move(board_state, self.symbol, self.iterations)
            board_state[row][col] = self.symbol
            print(f"{self.name} placed {self.symbol} at ({row}, {col})")
        else:
            print(f"No agent assigned to {self.name}")
class TurnManager:
    def __init__(self, players):
        self.players = players
        self.current_index = 0
        self.override_player = None

    def get_current_player(self):
        return self.override_player or self.players[self.current_index]

    def get_next_player(self):
        return self.players[(self.current_index + 1) % len(self.players)]

    def override_current_player(self, player):
        self.override_player = player

    def advance_turn(self):
        if self.override_player:
            self.override_player = None
        else:
            self.current_index = (self.current_index + 1) % len(self.players)

class TrapManager:
    def __init__(self, turn_manager):
        self.turn_manager = turn_manager
        self.trap_active = False
        self.trap_resolved_this_turn = False

    def trigger_trap(self, triggering_player):
        self.trap_active = True
        self.trap_resolved_this_turn = False
        print(f"Trap triggered by {triggering_player.name}")

        # Determine who should play due to trap
        trap_target = self.turn_manager.get_next_player()
        print(f"Next player after trap: {trap_target.name}")

        # Temporarily override turn for trap resolution
        self.turn_manager.override_current_player(trap_target)
        self.resolve_trap_effect(trap_target)

    def resolve_trap_effect(self, trap_target):
        if trap_target.is_ai:
            print(f"Resuming trap turn for {trap_target.name}")
            trap_target.play_ai_move()
            self.trap_resolved_this_turn = True
            self.remove_trap()

    def remove_trap(self):
        print("Trap removed.")
        self.trap_active = False
        self.trap_resolved_this_turn = False
        self.turn_manager.advance_turn()
class InputBox:
    def __init__(self, x, y, w, h, text='', font=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('gray')
        self.color_active = pygame.Color('dodgerblue')
        self.color = self.color_inactive
        self.text = text
        self.font = font or pygame.font.SysFont(None, 24)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isdigit() and len(self.text) < 5:
                self.text += event.unicode
            self.txt_surface = self.font.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)

    def get_value(self):
        val = int(self.text) if self.text.isdigit() else 0
        return max(1, min(val, 10000))  # Clamp between 1 and 10,000


###--- Utility functions
def setup_ui_elements(offset_x, offset_y, WIDTH, HEIGHT):
    font = pygame.font.SysFont(None, 32)

    input_boxes = {
        "iterations_ai1": InputBox(offset_x + 150, offset_y + 280, 100, 30, font=font),
        "iterations_ai2": InputBox(offset_x + 150, offset_y + 400, 100, 30, font=font)
    }

    buttons = {
        "human_vs_ai": pygame.Rect(offset_x + 100, offset_y + 160, 20, 20),
        "ai_vs_ai": pygame.Rect(offset_x + 300, offset_y + 160, 20, 20),
        "start": pygame.Rect(WIDTH // 2 - 75, HEIGHT - 100, 150, 50)
    }

    return input_boxes, buttons

def draw_radio_button(label, x, y, selected):
    font = pygame.font.SysFont("Arial", 24)
    color = (0, 200, 0) if selected else (200, 200, 200)
    pygame.draw.circle(screen, color, (x, y), 10)
    pygame.draw.circle(screen, (255, 255, 255), (x, y), 10, 2)
    text = font.render(label, True, (255, 255, 255))
    screen.blit(text, (x + 20, y - 12))

def draw_agent_selector(label, x, y, selected_agent):
    font = pygame.font.SysFont("Arial", 24)
    agents = ["MCTS", "Expectimax", "Markov"]
    text = font.render(label + ":", True, (255, 255, 255))
    screen.blit(text, (x, y))

    for i, agent in enumerate(agents):
        selected = (agent == selected_agent)
        draw_radio_button(agent, x + 120 + i * 120, y + 10, selected)

def draw_input_box(label, x, y, value):
    font = pygame.font.SysFont("Arial", 24)
    text = font.render(f"{label}: {value}", True, (255, 255, 255))
    pygame.draw.rect(screen, (255, 255, 255), (x + 150, y, 100, 30), 2)
    screen.blit(text, (x, y))

def draw_button(label, x, y):
    font = pygame.font.SysFont("Arial", 28)
    pygame.draw.rect(screen, (0, 120, 255), (x, y, 150, 50))
    text = font.render(label, True, (255, 255, 255))
    screen.blit(text, text.get_rect(center=(x + 75, y + 25)))

def draw_start_screen(screen, offset_x, offset_y, WIDTH, HEIGHT, input_boxes, buttons, selected_agent_ai1, selected_agent_ai2, game_mode):
    font = pygame.font.SysFont(None, 32)

    screen.fill((30, 30, 30))
    screen.blit(font.render("Select Game Mode:", True, (255, 255, 255)), (offset_x + 100, offset_y + 120))
    #pygame.draw.rect(screen, (200, 200, 200), buttons["human_vs_ai"])
    #pygame.draw.rect(screen, (200, 200, 200), buttons["ai_vs_ai"])
    draw_radio_button("Human vs AI", buttons["human_vs_ai"].x + 10, buttons["human_vs_ai"].y + 10,
                      game_mode == "human_vs_ai")
    draw_radio_button("AI vs AI", buttons["ai_vs_ai"].x + 10, buttons["ai_vs_ai"].y + 10, game_mode == "ai_vs_ai")
    #screen.blit(font.render("Human vs AI", True, (255, 255, 255)), (offset_x + 130, offset_y + 160))
    #screen.blit(font.render("AI vs AI", True, (255, 255, 255)), (offset_x + 330, offset_y + 160))
    screen.blit(font.render("Iterations AI 1:", True, (255, 255, 255)), (offset_x - 10, offset_y + 280))
    agents_search = ["MCTS", "Expectimax", "Markov"]
    for i, agent in enumerate(agents_search):
        bx = offset_x + 120 + i * 150
        selected = (agent == selected_agent_ai1)
        draw_radio_button(agent, bx, offset_y + 230, selected)
        #print(f"Agent {agent} selected: {selected} ")
        if game_mode == "ai_vs_ai":
            selected2 = (agent == selected_agent_ai2)
            draw_radio_button(agent, bx, offset_y + 350, selected2)
            #print(f"Agent2 {agent} selected: {selected} ")
            screen.blit(font.render("Iterations AI 2:", True, (255, 255, 255)), (offset_x - 10 , offset_y + 400))

    #for box in input_boxes.values():
        #box.draw(screen)
    input_boxes["iterations_ai1"].draw(screen)
    if game_mode == "ai_vs_ai":
        input_boxes["iterations_ai2"].draw(screen)

    pygame.draw.rect(screen, (0, 255, 0), buttons["start"])
    screen.blit(font.render("Start", True, (0, 0, 0)), (buttons["start"].x + 40, buttons["start"].y + 10))

def handle_events(event, input_boxes):

    for box in input_boxes.values():
        box.handle_event(event)

def handle_start_screen_click(pos):
    global game_mode, selected_agent_ai1, selected_agent_ai2, current_player
    global iterations_ai1, iterations_ai2, show_start_screen
    global offset_x, offset_y

    x, y = pos
    print(f"Click at X: {x}, Y: {y}")

    # Game mode toggle
    if 670 <= x <= 720 and 370 <= y <= 400:
        game_mode = "human_vs_ai"
        print("Game mode set to Human vs AI")

    elif 870 <= x <= 920 and 370 <= y <= 400:
        game_mode = "ai_vs_ai"


    # Agent selection

    agents = ["MCTS", "Expectimax", "Markov"]
    for i, agent in enumerate(agents):
        bx = 120 + i * 150
        rx = offset_x + bx
        ry1 = offset_y + 230
        ry2 = offset_y + 350

        if rx - 10 <= x <= rx + 10:
            if game_mode == "human_vs_ai" and ry1 - 10 <= y <= ry1 + 10:
                selected_agent_ai1 = agent
            elif game_mode == "ai_vs_ai":
                if ry1 - 10 <= y <= ry1 + 10:
                    selected_agent_ai1 = agent
                elif ry2 - 10 <= y <= ry2 + 10:
                    selected_agent_ai2 = agent

    # Start button
    if WIDTH // 2 - 75 <= x <= WIDTH // 2 + 75 and HEIGHT - 100 <= y <= HEIGHT - 50:
        show_start_screen = False
        iterations_ai1 = input_boxes["iterations_ai1"].get_value()
        iterations_ai2 = input_boxes["iterations_ai2"].get_value()
        if game_mode == "human_vs_ai":
            current_player = "Human"
        else:
            current_player = "AI1"

        reset_game()


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

# def reset_game():
#     global board_state, clicks, turn_count, highlight_tile, highlight_start_time
#     global pending_removal, interaction_paused, game_over
#     board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]
#     clicks = []
#     turn_count = 0
#     highlight_tile = None
#     highlight_start_time = None
#     pending_removal = False
#     interaction_paused = False
#     game_over = False
#     if game_mode == "ai_vs_ai" and turn_count == 0:
#         pygame.time.set_timer(AI_MOVE_EVENT, 500)



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
 global turn_count, trap_triggered_this_turn
 if interaction_paused or game_over:
     return
 mouse_pos = pygame.mouse.get_pos()
 row, col = get_tile_from_click(mouse_pos)
 if 0 <= row < ROWS and 0 <= col < COLS:
     if board_state[row][col] == "":
         clicks.append(("X" if event.button == 1 else "O", (row, col)))
         board_state[row][col] = "X" if event.button == 1 else "O"
         turn_count += 1
         trap_triggered_this_turn = False

         if debug_mode:
             print(f"Click: {board_state[row][col]} at ({row}, {col})")
def update_game_state():
    global highlight_tile, highlight_start_time

    #  Draw all placed symbols
    for symbol, (row, col) in clicks:
        x = offset_x + col * TILE_SIZE + TILE_SIZE // 2
        y = offset_y + row * TILE_SIZE + TILE_SIZE // 2
        draw_symbol(screen, symbol, x, y)

    # Animate trap tile if active
    if pending_removal and highlight_tile and highlight_start_time:
        row, col = highlight_tile
        tile_x = offset_x + col * TILE_SIZE
        tile_y = offset_y + row * TILE_SIZE
        elapsed = time.time() - highlight_start_time
        thickness = 6 if int((elapsed * 4) % 2) else 3
        pygame.draw.rect(screen, RED, (tile_x, tile_y, TILE_SIZE, TILE_SIZE), thickness)
def create_players(game_mode):
    if game_mode == "human_vs_ai":
        return [
            Player(name="Human", is_ai=False, symbol="X"),
            Player(name="AI1", is_ai=True, symbol="O", agent=selected_agent_ai1, iterations=iterations_ai1)
        ]
    elif game_mode == "ai_vs_ai":
        return [
            Player(name="AI1", is_ai=True, symbol="X", agent=selected_agent_ai1, iterations=iterations_ai1),
            Player(name="AI2", is_ai=True, symbol="O", agent=selected_agent_ai2, iterations=iterations_ai2)
        ]
    else:
        raise ValueError(f"Unsupported game mode: {game_mode}")

def trap_tile():
    global highlight_tile, highlight_start_time, pending_removal, interaction_paused
    global pending_ai_turn, current_player, next_player_after_trap
    global ai_next_move_time, turn_count, trap_triggered_this_turn

    #  Trigger trap only once per qualifying turn
    if turn_count % 5 == 0 and turn_count != 0 and not pending_removal and not trap_triggered_this_turn:
        highlight_tile = choose_random_tile()
        highlight_start_time = time.time()
        pending_removal = True
        interaction_paused = True
        trap_triggered_this_turn = True
        print(f"Trap triggered. Highlighting tile {highlight_tile}")
        return

    # Handle trap animation timing and removal
    if pending_removal and highlight_tile and highlight_start_time:
        elapsed = time.time() - highlight_start_time
        if elapsed >= 2:
            row, col = highlight_tile

            # Remove tile from board and clicks
            clicks[:] = [item for item in clicks if item[1] != highlight_tile]
            board_state[row][col] = ""

            # Reset trap flags
            highlight_tile = None
            highlight_start_time = None
            pending_removal = False
            interaction_paused = False

            # ▶ Resume correct player
            if pending_ai_turn and next_player_after_trap:
                current_player = next_player_after_trap

                if game_mode == "human_vs_ai":
                    if current_player == "AI1":
                        pygame.time.set_timer(AI_MOVE_EVENT, 500)

                elif game_mode == "ai_vs_ai":
                    ai_next_move_time = time.time() + 0.5

                print(f"Trap removed. Resuming turn for {current_player}")
                pending_ai_turn = False
                next_player_after_trap = None
# def update_game_state():
#     global highlight_tile, highlight_start_time, pending_removal, interaction_paused, pending_ai_turn
#     global game_over, turn_count, ai_next_move_time, current_player, last_starting_player, next_player_after_trap
#
#     for symbol, (row, col) in clicks:
#         x = offset_x + col * TILE_SIZE + TILE_SIZE // 2
#         y = offset_y + row * TILE_SIZE + TILE_SIZE // 2
#         draw_symbol(screen, symbol, x, y)
#
#     if turn_count % 5 == 0 and turn_count != 0 and not pending_removal:
#         highlight_tile = choose_random_tile()
#         highlight_start_time = time.time()
#         pending_removal = True
#         interaction_paused = True
#         turn_count = 0
#
#     if highlight_tile and pending_removal:
#         elapsed = time.time() - highlight_start_time
#         row, col = highlight_tile
#         tile_x = offset_x + col * TILE_SIZE
#         tile_y = offset_y + row * TILE_SIZE
#         thickness = 6 if int((elapsed * 4) % 2) else 3
#         pygame.draw.rect(screen, RED, (tile_x, tile_y, TILE_SIZE, TILE_SIZE), thickness)
#         if elapsed >= 2:
#             clicks[:] = [item for item in clicks if item[1] != highlight_tile]
#             board_state[row][col] = ""
#             highlight_tile = None
#             highlight_start_time = None
#             pending_removal = False
#             interaction_paused = False
#
#             if pending_ai_turn and next_player_after_trap:
#                 current_player = next_player_after_trap
#                 if game_mode == "human_vs_ai" and current_player == "AI1":
#                     pygame.time.set_timer(AI_MOVE_EVENT, 500)
#                 elif game_mode == "human_vs_ai" and current_player == "Human":
#                     pass  # Wait for human click
#                 elif game_mode == "ai_vs_ai":
#                     ai_next_move_time = time.time() + 0.5
#
#                 print(f"Trap removed. Resuming turn for {current_player}")
#                 pending_ai_turn = False
#                 next_player_after_trap = None
            # Resume AI turn if it's AI's move
            #if game_mode == "human_vs_ai" and current_player == "AI1":
            #    print("Trap removed. Resuming AI turn for AI1")
           #     pygame.time.set_timer(AI_MOVE_EVENT, 500)
           # elif game_mode == "ai_vs_ai":
            #    print(f"Trap removed. Resuming AI turn for {current_player}")
            #    ai_next_move_time = time.time() + 0.5


# def handle_human_turn(pos):
#     row, col = get_tile_from_click(pos)
#     if board_state[row][col] == "":
#         board_state[row][col] = "X"
#         clicks.append(("X", (row, col)))
#         return True
#     return False
# def handle_human_turn(pos):
#     global current_player, turn_count
#     if interaction_paused or game_over:
#         return False  # Block input during trap animation
#
#     row, col = get_tile_from_click(pos)
#     if board_state[row][col] == "":
#         board_state[row][col] = "X"
#         clicks.append(("X", (row, col)))
#         current_player = "AI1"
#         turn_count += 1
#
#         ##pygame.time.wait(100000)
#         ###--- Delay AI move to allow rendering and trap animation
#         pygame.time.set_timer(AI_MOVE_EVENT, 500)  # 500ms delay
#
#
#         return True
#     return False
# def handle_ai_turn():
#     global current_player, turn_count
#     if interaction_paused or game_over:
#         return False  # Block input during trap animation
#
#     ai = MonteCarloAI("O", "X", simulations=100)
#     ai.run_simulation(board_state)
#     move = ai.get_best_move()
#     board_state[move[0]][move[1]] = "O"
#     clicks.append(("O", move))
#     turn_count += 1
#     print(f"AI placed O at {move}, turn_count = {turn_count}")
def handle_human_turn_old(pos):
    global current_player, turn_count, pending_ai_turn, trap_triggered_this_turn
    if interaction_paused or game_over:
        return False

    row, col = get_tile_from_click(pos)
    if board_state[row][col] == "":
        board_state[row][col] = "X"
        clicks.append(("X", (row, col)))
        turn_count += 1
        trap_triggered_this_turn = False

        # Don't switch turn yet — wait for update_game_state to handle trap
        pending_ai_turn = True
        return True
    return False
def handle_human_turn(pos):
    global current_player, turn_count, pending_ai_turn, next_player_after_trap, trap_triggered_this_turn
    if interaction_paused or game_over:
        return False

    row, col = get_tile_from_click(pos)
    print(f"Row: {row}, Col: {col} clicked")
    if board_state[row][col] == "":
        board_state[row][col] = "X"
        clicks.append(("X", (row, col)))
        turn_count += 1
        trap_triggered_this_turn = False

        # If trap will trigger next, defer turn switch
        if turn_count % 5 == 0:
            pending_ai_turn = True
            next_player_after_trap = "AI1"
        else:
            current_player = "AI1"
            pygame.time.set_timer(AI_MOVE_EVENT, 500)

        return True
    return False
# def handle_ai_turn(player_id, agent_type, iterations, symbol, opponent):
#
#     global turn_count
#     if interaction_paused or game_over:
#         return
#     print(f"AI turn started for {player_id}")
#     start_time = time.time()
#
#     #symbol = "X" if player_id == "AI1" else "O"
#     #opponent = "O" if symbol == "X" else "X"
#
#     if agent_type == "MCTS":
#         ai = MonteCarloAI(symbol, opponent, simulations=iterations)
#         ai.run_simulation(board_state)
#         move = ai.get_best_move()
#     elif agent_type == "Expectimax":
#         move = run_expectimax(board_state, symbol, depth=2)
#     elif agent_type == "Markov":
#         move = run_markov_agent(board_state, symbol)
#
#     board_state[move[0]][move[1]] = symbol
#     clicks.append((symbol, move))
#     turn_count += 1
#     end_time = time.time()
#     print(f"{player_id} placed {symbol} at {move}, turn_count = {turn_count}")
#     print(f"AI turn Ended for {player_id}, took {end_time - start_time:.3f} seconds")

    # if game_over or not get_available_moves(board):
    #     print(f"No moves available for {player_id}")
    #     return

###---Main
##if game_mode == "ai_vs_ai" and turn_count == 0:
  ##  pygame.time.set_timer(AI_MOVE_EVENT, 500)

def handle_ai_turn(player_id, agent_type, iterations, symbol, opponent):
    global turn_count, pending_ai_turn, next_player_after_trap, interaction_paused, ai_next_move_time
    global pending_removal, highlight_tile, highlight_start_time, current_player, next_player_after_trap, trap_triggered_this_turn

    if interaction_paused or game_over:
        return

    print(f"AI turn started for {player_id}")
    start_time = time.time()

    # Run agent
    if agent_type == "MCTS":
        ai = MonteCarloAI(symbol, opponent, simulations=iterations)
        ai.run_simulation(board_state)
        move = ai.get_best_move()
    elif agent_type == "Expectimax":
        move = run_expectimax(board_state, symbol, depth=2)
    elif agent_type == "Markov":
        move = run_markov_agent(board_state, symbol)

    # Apply move
    board_state[move[0]][move[1]] = symbol
    clicks.append((symbol, move))
    turn_count += 1
    trap_triggered_this_turn = False

    print(f"{player_id} placed {symbol} at {move}, turn_count = {turn_count}")
    end_time = time.time()
    print(f"AI turn Ended for {player_id}, took {end_time - start_time:.3f} seconds")

    # # Trap logic: every 5 turns
    # if turn_count % 5 == 0:
    #     interaction_paused = True
    #     pending_removal = True
    #     highlight_tile = move
    #     highlight_start_time = time.time()
    #
    #     # Alternate next player
    #     next_player_after_trap = "AI2" if player_id == "AI1" else "AI1"
    #     pending_ai_turn = True
    #     print(f"Trap triggered by {player_id}. Next: {next_player_after_trap}")
    # else:
        # Normal switch
    current_player = "AI2" if player_id == "AI1" else "AI1"
    ai_next_move_time = time.time() + 0.5
def reset_ui():
    global input_boxes, buttons
    input_boxes, buttons = setup_ui_elements(offset_x, offset_y, WIDTH, HEIGHT)
def reset_game():
    global board_state, clicks, turn_count, highlight_tile, highlight_start_time
    global pending_removal, interaction_paused, game_over, current_player, last_starting_player

    board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]
    clicks = []
    turn_count = 0
    highlight_tile = None
    highlight_start_time = None
    pending_removal = False
    interaction_paused = False
    game_over = False

    # Alternate starting player
    if game_mode == "human_vs_ai":
        current_player = "AI1" if last_starting_player == "Human" else "Human"
    elif game_mode == "ai_vs_ai":
        current_player = "AI2" if last_starting_player == "AI1" else "AI1"
    else:
        current_player = "Human"  # fallback for other modes

    last_starting_player = current_player
ai_next_move_time = time.time() + 0.5  # 500ms delay
input_boxes, buttons = setup_ui_elements(offset_x, offset_y, WIDTH, HEIGHT)
#turn_manager = TurnManager(game_mode)
waiting_for_continue = False

#trap_manager = TrapManager(turn_manager)
players = create_players(game_mode)
turn_manager = TurnManager(players)
trap_manager = TrapManager(turn_manager)
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        if show_start_screen:
            handle_events(event, input_boxes)
            if event.type == pygame.MOUSEBUTTONDOWN:
                handle_start_screen_click(event.pos)

    if show_start_screen:
        draw_start_screen(screen, offset_x, offset_y, WIDTH, HEIGHT, input_boxes, buttons,
                          selected_agent_ai1, selected_agent_ai2, game_mode)
        pygame.display.flip()
        clock.tick(60)
        continue

    # --- Game logic and rendering ---
    draw_board()

    # Hover highlight for human
    if not interaction_paused and not game_over and game_mode == "human_vs_ai":
        if turn_manager.get_current_player().name == "Human":
            mouse_pos = pygame.mouse.get_pos()
            hover_row, hover_col = get_tile_from_click(mouse_pos)
            if 0 <= hover_row < ROWS and 0 <= hover_col < COLS:
                hover_x = offset_x + hover_col * TILE_SIZE
                hover_y = offset_y + hover_row * TILE_SIZE
                pygame.draw.rect(screen, (255, 255, 0), (hover_x, hover_y, TILE_SIZE, TILE_SIZE), 3)

    # Trap resolution pause
    if interaction_paused and time.time() - highlight_start_time >= 2:
        interaction_paused = False
        trap_manager.remove_trap()

    # --- Turn Handling ---
    current_player = turn_manager.get_current_player()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if game_mode == "human_vs_ai" and current_player.name == "Human":
            if event.type == pygame.MOUSEBUTTONDOWN:
                if handle_human_turn(pygame.mouse.get_pos()):
                    turn_manager.advance_turn()
                    if turn_manager.is_trap_turn():
                        highlight_tile = choose_random_tile()
                        highlight_start_time = time.time()
                        interaction_paused = True
                        trap_manager.trigger_trap(current_player)
                    else:
                        pygame.time.set_timer(AI_MOVE_EVENT, 500)

    # AI vs Human
    if game_mode == "human_vs_ai" and current_player.name == "AI1" and not interaction_paused:
        current_player.play_ai_move()
        turn_manager.advance_turn()
        if turn_manager.is_trap_turn():
            highlight_tile = choose_random_tile()
            highlight_start_time = time.time()
            interaction_paused = True
            trap_manager.trigger_trap(current_player)
        else:
            pygame.time.set_timer(AI_MOVE_EVENT, 0)

    # AI vs AI
    if game_mode == "ai_vs_ai" and time.time() >= ai_next_move_time and not interaction_paused:
        current_player.play_ai_move()
        turn_manager.advance_turn()
        if turn_manager.is_trap_turn():
            highlight_tile = choose_random_tile()
            highlight_start_time = time.time()
            interaction_paused = True
            trap_manager.trigger_trap(current_player)
        else:
            ai_next_move_time = time.time() + 0.5

    trap_tile()
    update_game_state()

    # Win check
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
            turn_manager = TurnManager(game_mode)

    # Draw check
    if not check_winner("X") and not check_winner("O"):
        board_full = all(board_state[row][col] != "" for row in range(ROWS) for col in range(COLS))
        if board_full:
            show_game_over_screen("Draw")
            game_over = True
            if game_mode == "human_vs_ai":
                wait_for_game_over_input()
                game_over = False
            elif game_mode == "ai_vs_ai":
                pygame.time.wait(1000)
                reset_game()
                game_over = False
                turn_manager = TurnManager(game_mode)

    pygame.display.flip()
    clock.tick(60)

###--- Final analytics logging (optional — move inside game-over logic if needed)
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



