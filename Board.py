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
import logging



#from sympy import false

###--- External modules coded by project team
from analytics_tracker import AnalyticsTrackerSummary, AnalyticsTrackerDetails
from mcts_AI import MonteCarloAI
#from start_screen import StartScreenManager


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
previous_game_mode=None
###game_mode = "ai_vs_ai"
selected_agent_ai1 = "MCTS"
selected_agent_ai2 = "MCTS"
iterations_ai1 = 200
iterations_ai2 = 200
show_start_screen = True
pending_ai_turn = False
next_player_after_trap = None
trap_triggered_this_turn = False
players = []
player_lookup = {}


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
        if not self.is_ai or not self.agent:
            print(f"[ERROR] {self.name} has no valid AI agent.")
            return False

        print(f"AI turn started for {self.name}")
        start_time = time.time()

        opponent_symbol = "O" if self.symbol == "X" else "X"
        move = handle_ai_turn(self.name, self.agent, self.iterations, self.symbol, opponent_symbol)

        if move:
            board_state[move[0]][move[1]] = self.symbol
            clicks.append((self.symbol, move))
            end_time = time.time()
            print(f"{self.name} placed {self.symbol} at {move}, took {end_time - start_time:.3f}s")
            return True

        print(f"[WARNING] {self.name} failed to select a move.")
        return False
    # def play_ai_move(self):
    #     if not self.is_ai or not self.agent:
    #         print(f"[ERROR] {self.name} has no valid AI agent.")
    #         return False  #  No move placed
    #
    #     print(f"AI turn started for {self.name}")
    #     start_time = time.time()
    #
    #     move = None
    #     if isinstance(self.agent, MonteCarloAI):
    #         self.agent.run_simulation(board_state)
    #         move = self.agent.get_best_move()
    #     elif hasattr(self.agent, "select_move"):
    #         move = self.agent.select_move(board_state, self.symbol, self.iterations)
    #
    #     if move:
    #         board_state[move[0]][move[1]] = self.symbol
    #         clicks.append((self.symbol, move))
    #         end_time = time.time()
    #         print(f"{self.name} placed {self.symbol} at {move}, took {end_time - start_time:.3f}s")
    #         return True  #  Move was placed
    #
    #     print(f"[WARNING] {self.name} failed to select a move.")
    #     return False  #  No move placed
    # def play_ai_move(self):
    #     if not self.is_ai or not self.agent:
    #         print(f"[ERROR] {self.name} has no valid AI agent.")
    #         return
    #
    #     print(f"AI turn started for {self.name}")
    #     start_time = time.time()
    #
    #     move = None
    #     if isinstance(self.agent, MonteCarloAI):
    #         self.agent.run_simulation(board_state)
    #         move = self.agent.get_best_move()
    #     elif hasattr(self.agent, "select_move"):
    #         move = self.agent.select_move(board_state, self.symbol, self.iterations)
    #
    #     if move:
    #         board_state[move[0]][move[1]] = self.symbol
    #         clicks.append((self.symbol, move))
    #         end_time = time.time()
    #         print(f"{self.name} placed {self.symbol} at {move}, took {end_time - start_time:.3f}s")


class TurnManager:
    def __init__(self, mode):
        self.mode = mode
        self.players = self._init_players(mode)
        self.current_index = 0
        self.turn_count = 0

    def _init_players(self, mode):
        if mode == "human_vs_ai":
            return ["Human", "AI1"]
        elif mode == "ai_vs_ai":
            return ["AI1", "AI2"]
        else:
            return ["Human"]

    def get_current_player(self):

        return self.players[self.current_index]

    def advance_turn(self):
        self.turn_count += 1
        self.current_index = (self.current_index + 1) % len(self.players)

    def should_trigger_trap(self):
        return self.turn_count > 0 and self.turn_count % 5 == 0

    def reset(self):
        #self.turn_count = 0
        self.current_index = 0

    def reset_turn_count(self):
        self.turn_count = 0


class TrapManager:
    def __init__(self, trigger_interval=5, animation_duration=2.0):
        self.trigger_interval = trigger_interval
        self.animation_duration = animation_duration
        self.active = False
        self.tile = None
        self.start_time = None

    def should_trigger(self, turn_count):
        return not self.active and turn_count > 0 and turn_count % self.trigger_interval == 0

    def trigger(self):
        self.tile = choose_random_tile()
        self.start_time = time.time()
        self.active = True

    def update(self, screen):
        if not self.active or not self.tile:
            return False

        elapsed = time.time() - self.start_time
        row, col = self.tile
        tile_x = offset_x + col * TILE_SIZE
        tile_y = offset_y + row * TILE_SIZE
        thickness = 6 if int((elapsed * 4) % 2) else 3
        pygame.draw.rect(screen, RED, (tile_x, tile_y, TILE_SIZE, TILE_SIZE), thickness)

        if elapsed >= self.animation_duration:
            board_state[row][col] = ""
            clicks[:] = [item for item in clicks if item[1] != self.tile]
            self.reset()
            return True  # Tile was removed
        return False  # Still animating

    def reset(self):
        self.active = False
        self.tile = None
        self.start_time = None

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
    global  previous_game_mode
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
    if game_mode != previous_game_mode:
        logging.debug(f"[WARNING] game_mode changed in draw start screen from {previous_game_mode} to {game_mode}")
    previous_game_mode = game_mode


def handle_events(event, input_boxes):

    for box in input_boxes.values():
        box.handle_event(event)

def handle_start_screen_click(pos):
    global game_mode, selected_agent_ai1, selected_agent_ai2, current_player, player_lookup
    global iterations_ai1, iterations_ai2, show_start_screen
    global offset_x, offset_y, previous_game_mode, turn_manager, trap_manager

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

        players = create_players(game_mode, selected_agent_ai1, selected_agent_ai2,
                                 iterations_ai1, iterations_ai2)
        player_lookup = {player.name: player for player in players}
        turn_manager = TurnManager(game_mode)
        trap_manager = TrapManager()

        reset_game()

    if game_mode != previous_game_mode:
        logging.debug(f"[WARNING] game_mode changed in draw start screen from {previous_game_mode} to {game_mode}")
        previous_game_mode = game_mode
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

# def handle_click(event):
#  global turn_count, trap_triggered_this_turn
#  if interaction_paused or game_over:
#      return
#  mouse_pos = pygame.mouse.get_pos()
#  row, col = get_tile_from_click(mouse_pos)
#  if 0 <= row < ROWS and 0 <= col < COLS:
#      if board_state[row][col] == "":
#          clicks.append(("X" if event.button == 1 else "O", (row, col)))
#          board_state[row][col] = "X" if event.button == 1 else "O"
#          turn_count += 1
#          trap_triggered_this_turn = False
#
#          if debug_mode:
#              print(f"Click: {board_state[row][col]} at ({row}, {col})")
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

def create_players_old(game_mode):
    global previous_game_mode
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

    # if game_mode != previous_game_mode:
    #     logging.debug(f"[WARNING] game_mode changed from {previous_game_mode} to {game_mode}")
    # previous_game_mode = game_mode

def create_players(game_mode, selected_agent_ai1, selected_agent_ai2, iterations_ai1, iterations_ai2):
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
def create_players_delete(game_mode, selected_agent_ai1, selected_agent_ai2, iterations_ai1, iterations_ai2):
    if game_mode == "human_vs_ai":
        return [
            Player(name="Human", is_ai=False, symbol="X"),
            Player(name="AI1", is_ai=True, symbol="O",
                   agent=get_agent(selected_agent_ai1, "O", "X", iterations_ai1),
                   iterations=iterations_ai1)
        ]
    elif game_mode == "ai_vs_ai":
        return [
            Player(name="AI1", is_ai=True, symbol="X",
                   agent=get_agent(selected_agent_ai1, "X", "O", iterations_ai1),
                   iterations=iterations_ai1),
            Player(name="AI2", is_ai=True, symbol="O",
                   agent=get_agent(selected_agent_ai2, "O", "X", iterations_ai2),
                   iterations=iterations_ai2)
        ]

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
def handle_human_turn(pos, symbol="X"):
    if interaction_paused or game_over:
        return False

    row, col = get_tile_from_click(pos)
    if board_state[row][col] == "":
        board_state[row][col] = symbol
        clicks.append((symbol, (row, col)))
        if debug_mode:
            print(f"[DEBUG] Human move registered at ({row}, {col}) with symbol '{symbol}'")

        return True

        #return True
    return False

def handle_ai_turn(player_id, agent_type, iterations, symbol, opponent):
    if interaction_paused or game_over:
        return None

    print(f"AI turn started for {player_id}")
    start_time = time.time()

    if agent_type == "MCTS":
        ai = MonteCarloAI(symbol, opponent, simulations=iterations)
        ai.run_simulation(board_state)
        move = ai.get_best_move()
    elif agent_type == "Expectimax":
        move = run_expectimax(board_state, symbol, depth=2)
    elif agent_type == "Markov":
        move = run_markov_agent(board_state, symbol)
    else:
        print(f"Unknown agent type: {agent_type}")
        return None

    if move:
        board_state[move[0]][move[1]] = symbol
        clicks.append((symbol, move))
        end_time = time.time()
        print(f"{player_id} placed {symbol} at {move}, took {end_time - start_time:.3f}s")
        return move
    return None
def reset_ui():
    global input_boxes, buttons
    input_boxes, buttons = setup_ui_elements(offset_x, offset_y, WIDTH, HEIGHT)
def reset_game():
    global board_state, clicks, highlight_tile, highlight_start_time
    global pending_removal, interaction_paused, game_over

    board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]
    clicks = []
    highlight_tile = None
    highlight_start_time = None
    pending_removal = False
    interaction_paused = False
    game_over = False

    turn_manager.reset()

def create_agent(agent_type, symbol, opponent_symbol, iterations):
    if agent_type == "MCTS":
        return MonteCarloAI(symbol, opponent_symbol, simulations=iterations)
    elif agent_type == "Expectimax":
        return ExpectimaxAgent(symbol, opponent_symbol, depth=2)
    elif agent_type == "Markov":
        return MarkovAgent(symbol, opponent_symbol)
    return None

def is_click_stable(pos1, pos2, tolerance=5):
    if pos1 is None or pos2 is None:
        return False
    return abs(pos1[0] - pos2[0]) <= tolerance and abs(pos1[1] - pos2[1]) <= tolerance

def handle_trap_logic():
    global interaction_paused, ai_next_move_time

    if trap_manager.should_trigger(turn_manager.turn_count):
        trap_manager.trigger()
        interaction_paused = True

    if trap_manager.active:
        removed = trap_manager.update(screen)
        if removed:
            interaction_paused = False
            current_player = turn_manager.get_current_player()
            if current_player.startswith("AI"):
                ai_next_move_time = time.time() + 0.5

def play_ai_move(self):
    move = self.get_move(board)
    if move:
        board.place_move(move, self.symbol)
        logging.debug(f"{self.name} placed at {move}")
        return True
    return False

ai_next_move_time = time.time() + 0.5  # 500ms delay
input_boxes, buttons = setup_ui_elements(offset_x, offset_y, WIDTH, HEIGHT)
# if game_mode == "human_vs_ai":
#     agent = create_agent(selected_agent_ai1, symbol="O", opponent_symbol="X", iterations=iterations_ai1)
#     player1 = Player(name="Human", is_ai=False, symbol="X")
#     player2 = Player(name="AI1", is_ai=True, symbol="O", agent=agent, iterations=iterations_ai1)
# elif game_mode == "ai_vs_ai":
#     agent1 = create_agent(selected_agent_ai1, symbol="X", opponent_symbol="O", iterations=iterations_ai1)
#     agent2 = create_agent(selected_agent_ai2, symbol="O", opponent_symbol="X", iterations=iterations_ai2)
#     player1 = Player(name="AI1", is_ai=True, symbol="X", agent=agent1, iterations=iterations_ai1)
#     player2 = Player(name="AI2", is_ai=True, symbol="O", agent=agent2, iterations=iterations_ai2)

#game_mode = "human_vs_ai"
#players = create_players(game_mode)
if game_mode != previous_game_mode:
    logging.debug(f"[WARNING] game_mode changed create players from {previous_game_mode} to {game_mode}")
previous_game_mode = game_mode

if game_mode != previous_game_mode:
    logging.debug(f"[WARNING] game_mode changed Turn Manager from {previous_game_mode} to {game_mode}")
previous_game_mode = game_mode
trap_manager = TrapManager()
if game_mode != previous_game_mode:
    logging.debug(f"[WARNING] game_mode changed Trap Manager from {previous_game_mode} to {game_mode}")
previous_game_mode = game_mode
logging.basicConfig(level=logging.DEBUG)
#player_lookup = {player.name: player for player in players}

pygame.event.set_blocked([
    pygame.WINDOWSHOWN,
    pygame.WINDOWENTER,
    pygame.WINDOWLEAVE,
    pygame.WINDOWFOCUSGAINED,
    pygame.TEXTEDITING
])

mouse_down_pos = None
mouse_down_time = None
CLICK_TIMEOUT = 1000  # milliseconds
#start_screen = StartScreenManager(screen, offset_x, offset_y, WIDTH, HEIGHT)
#show_start_screen = True
config = None
#turn_manager = TurnManager(game_mode)
#trap_manager = TrapManager(turn_manager)
debug_mode = True
waiting_for_continue = False
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
    draw_board()
    #game_mode = "ai_vs_ai"
    # Hover highlight
    if not interaction_paused and not game_over and game_mode == "human_vs_ai":
        mouse_pos = pygame.mouse.get_pos()
        hover_row, hover_col = get_tile_from_click(mouse_pos)
        if 0 <= hover_row < ROWS and 0 <= hover_col < COLS:
            hover_x = offset_x + hover_col * TILE_SIZE
            hover_y = offset_y + hover_row * TILE_SIZE
            pygame.draw.rect(screen, (255, 255, 0), (hover_x, hover_y, TILE_SIZE, TILE_SIZE), 3)

    current_player = turn_manager.get_current_player()


    if game_mode == "human_vs_ai" and turn_manager.get_current_player() == "Human":
        for event in pygame.event.get():
            if event.type not in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                logging.debug(f"[IGNORED] Unknown event type: {event.type}")
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down_pos = pygame.mouse.get_pos()
                mouse_down_time = pygame.time.get_ticks()

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                mouse_up_pos = pygame.mouse.get_pos()
                release_time = pygame.time.get_ticks()

                if mouse_down_pos and mouse_down_time:
                    if (release_time - mouse_down_time) <= CLICK_TIMEOUT:
                        if is_click_stable(mouse_down_pos, mouse_up_pos):
                            if handle_human_turn(mouse_up_pos):
                                turn_manager.advance_turn()
                                pygame.time.set_timer(AI_MOVE_EVENT, 500)

                mouse_down_pos = None
                mouse_down_time = None



    # Handle AI turn
    # elif current_player.startswith("AI") and not interaction_paused:
    #     if game_mode == "human_vs_ai":
    #         handle_ai_turn("AI1", selected_agent_ai1, iterations_ai1, "O", "X")
    #         turn_manager.advance_turn()
    #         pygame.time.set_timer(AI_MOVE_EVENT, 0)
    #
    #     elif game_mode == "ai_vs_ai" and time.time() >= ai_next_move_time:
    #         # if current_player == "AI1":
    #         #     handle_ai_turn("AI1", selected_agent_ai1, iterations_ai1, "X", "O")
    #         # else:
    #         #     handle_ai_turn("AI2", selected_agent_ai2, iterations_ai2, "O", "X")
    #         ai_player = player_lookup.get(current_player)
    #         if ai_player and ai_player.is_ai:
    #             ai_player.play_ai_move()
    #
    #         turn_manager.advance_turn()
    #         ai_next_move_time = time.time() + 0.5
    elif current_player.startswith("AI") and not interaction_paused:
        if game_mode == "human_vs_ai":
            handle_ai_turn("AI1", selected_agent_ai1, iterations_ai1, "O", "X")
            turn_manager.advance_turn()
            pygame.time.set_timer(AI_MOVE_EVENT, 0)

        elif game_mode == "ai_vs_ai" and time.time() >= ai_next_move_time:
            ai_player = player_lookup.get(current_player)
            print(f"Ai player is {ai_player}")
            if ai_player and ai_player.is_ai:
                move_placed = ai_player.play_ai_move()  # Must return True if move was placed

                if move_placed:
                    # Trap logic only after real move
                    if turn_manager.should_trigger_trap():
                        logging.debug(f"[TRAP] Triggering trap at turn {turn_manager.turn_count}")
                        trap_manager.trigger()
                        interaction_paused = True

                    turn_manager.advance_turn()
                    ai_next_move_time = time.time() + 0.5
    # Trap logic
    # Trigger trap if needed
    if trap_manager.should_trigger(turn_manager.turn_count):
        logging.debug(f"[TRAP] Triggering trap at turn {turn_manager.turn_count}")

        trap_manager.trigger()
        interaction_paused = True

    # Animate trap
    if trap_manager.active:
        removed = trap_manager.update(screen)
        if removed:
            interaction_paused = False
            #turn_manager.reset_turn_count()  # Reset turn count after trap
            # Trigger AI if it's their turn after trap
            current_player = turn_manager.get_current_player()
            if current_player.startswith("AI"):
                if game_mode == "human_vs_ai":
                    handle_ai_turn("AI1", selected_agent_ai1, iterations_ai1, "O", "X")
                    turn_manager.advance_turn()
                elif game_mode == "ai_vs_ai":
                    if current_player == "AI1":
                        handle_ai_turn("AI1", selected_agent_ai1, iterations_ai1, "X", "O")
                    else:
                        handle_ai_turn("AI2", selected_agent_ai2, iterations_ai2, "O", "X")
                    turn_manager.advance_turn()
                    ai_next_move_time = time.time() + 0.5


    update_game_state()

    # Win check
    if check_winner("X") or check_winner("O"):
        winner = "X" if check_winner("X") else "O"
        show_game_over_screen(winner)
        game_over = True
        if game_mode == "human_vs_ai":
            wait_for_game_over_input()
            game_over = False
        else:
            reset_game()
            game_over = False

    # Draw check
    if not check_winner("X") and not check_winner("O"):
        board_full = all(board_state[row][col] != "" for row in range(ROWS) for col in range(COLS))
        if board_full:
            show_game_over_screen("Draw")
            game_over = True
            if game_mode == "human_vs_ai":
                wait_for_game_over_input()
                game_over = False
            else:
                pygame.time.wait(1000)
                reset_game()

    pygame.display.flip()
    clock.tick(60)
# --- Final Analytics Logging (optional) ---
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


