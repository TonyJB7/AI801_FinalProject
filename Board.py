###--------------------------------------------------------------------------------
### Game: Disrupt-O-Tac
### Authors: Project Group 2 -  Antonio Blanco
### Date: 8/17/2025
### Description: Main board to evaluate Markov and Expectimax
###
###---------------------------------------------------------------------------------

###--- Libraries
import os
import random
import sys
import time
import pygame

###--- Used for the reporting
import logging
import datetime
import pandas as pd
import csv

###--- External modules coded by project team
###--- Import of the analytics output algorithm
from analytics_tracker import AnalyticsTrackerSummary, AnalyticsTrackerDetails, AnalyticsTrackerAgents

###--- Import of all the agents
from mcts_AI import MonteCarloAI
from expectimax_AI import RefactoredEngine
from markov_AI import MarkovAgent
reward_easy="Markov_config\\rewards.csv"
reward_hard="Markov_config\\rewards_hard.csv"
selected_reward=reward_hard
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
pygame.display.set_caption("Disrupt-O-Tac")
####--- Init Game state - Go to
corner_positions = {(0, 0), (0, COLS - 1), (ROWS - 1, 0), (ROWS - 1, COLS - 1)}
edge_positions = {(r, c) for r in range(ROWS) for c in range(COLS)
                  if (r, c) not in corner_positions and (r == 0 or c == 0 or r == ROWS - 1 or c == COLS - 1)}
clicks = []
board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]

###--- Booleans and flags that changes the states
highlight_tile = None
highlight_start_time = None
interaction_paused = False
pending_removal = False
game_over = False
visualize = True
debug_mode = False  # Toggle for debug prints

###current_player = "Human"  # or "AI" if AI goes first
###Initialize the default setting for the menu screen

current_player = "Human"
game_mode = "human_vs_ai"
previous_game_mode=None
selected_agent_ai1 = "MCTS"
selected_agent_ai2 = "MCTS"
iterations_ai1 = 200
iterations_ai2 = 200
show_start_screen = True

###--- Initializing the different turn states including traps
last_starting_player = None
pending_ai_turn = False
next_player_after_trap = None
trap_triggered_this_turn = False
players = []
player_lookup = {}


###--- Initializing the analytics and flags uses in analytics
trackerSummary = AnalyticsTrackerSummary()
trackerDetails = AnalyticsTrackerDetails()
trackerAgents = AnalyticsTrackerAgents()
log_winner=None
isDraw=False
play_id=None
win_count=0
lose_count=0
tiles_removed_count=0
move_count = {"X": 0, "O": 0}
turn_count = 0

###---Debug Variables
#move_count=0

###--- Making this constant a pygame event so that is can be called as an event
AI_MOVE_EVENT = pygame.USEREVENT + 1
def main():
    # your code here
    print("Running Board logic...")
    input("Press Enter to exit...")



###---------------------------------------------------
### The following Module creates the object used for login the moves
### all of these calls are for the use in analytical reporting

class GameLogger:
    def __init__(self):
        self.play_id = None
        self.game_mode = None
        self.moves = []
        self.tiles_removed = 0

    def start_new_game(self, game_mode):
        self.play_id = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_mode = game_mode
        self.moves.clear()
        self.tiles_removed = 0
        print(f"[LOGGER] New game started: {self.play_id}")

    ###--- Captures the agent information for AI vs AI
    def log_agents(self, ai1_type, ai1_iterations, ai2_type, ai2_iterations):
        self.agent_info = {
            "AI1_type": ai1_type,
            "AI1_iterations": ai1_iterations,
            "AI2_type": ai2_type,
            "AI2_iterations": ai2_iterations
        }
        trackerAgents.log_agents(
            play_id=self.play_id,
            game_mode=self.game_mode,
            ai1_type=ai1_type,
            ai1_iterations=ai1_iterations,
            ai2_type=ai2_type,
            ai2_iterations=ai2_iterations
        )
    ###--- When called it captures the play-by-play of a player or AI each turn
    def log_move(self, player, position, shape, tiles_removed_pos=None):
        self.moves.append({
            "play_id": self.play_id,
            "game_mode": self.game_mode,
            "player": player,
            "position": position,
            "shape": shape,
            "tiles_removed_pos": tiles_removed_pos or []
        })

    ###--- When called it captures the position of the trapped removed for the purposes of reporting
    def log_tile_removal(self, position):
        self.tiles_removed += 1
        if self.moves:
            self.moves[-1]["tiles_removed_pos"].append(position)

    ###--- When called this is when we write to file the summary and the detailed
    def finalize(self, move_count, board_state):
        winner_symbol = "X" if check_winner("X") else "O" if check_winner("O") else None

        if winner_symbol:
            loser_symbol = "O" if winner_symbol == "X" else "X"
            winner_name = next((m["player"] for m in reversed(self.moves) if m["shape"] == winner_symbol), "Unknown")
            loser_name = next((m["player"] for m in reversed(self.moves) if m["shape"] == loser_symbol), "Unknown")

            trackerSummary.log_game(
                play_id=self.play_id,
                game_mode=self.game_mode,
                winner=winner_name,
                win_moves=move_count[winner_symbol],
                win_shape=winner_symbol,
                lose=loser_name,
                lose_moves=move_count[loser_symbol],
                lose_shape=loser_symbol,
                tiles_removed=self.tiles_removed
            )
        else:
            trackerSummary.log_game(
                play_id=self.play_id,
                game_mode=self.game_mode,
                winner="Draw",
                win_moves=0,
                win_shape="Draw",
                lose="Draw",
                lose_moves=0,
                lose_shape="Draw",
                tiles_removed=self.tiles_removed
            )

        for move in self.moves:
            trackerDetails.log_game(**move)
###----------------------------------------------------------------------
### Traditional Player class that holds the information of the player
### In this case what matters is the symbol and control of the AI

class Player:
    def __init__(self, name, is_ai, symbol=None, agent=None, iterations=100):
        self.name = name
        self.is_ai = is_ai
        self.symbol = symbol  # "X" or "O"
        self.agent = agent    # Optional: your AI agent instance
        self.iterations = iterations  # Optional: for MCTS or other AI configs

    ###--- When called it will verify if it is the ai turn, and will play according to the symbol
    def play_ai_move(self):
        if not self.is_ai or not self.agent:
            print(f"[ERROR] {self.name} has no valid AI agent.")
            return False

        print(f"AI turn started for {self.name}")
        start_time = time.time()

        opponent_symbol = "O" if self.symbol == "X" else "X"
        move = handle_ai_turn(self.name, self.agent, self.iterations, self.symbol, opponent_symbol)

        ###--- Only record the move if it is considered a valid move
        ###--- i.e. Space available, correct turn
        if move:
            board_state[move[0]][move[1]] = self.symbol
            clicks.append((self.symbol, move))
            end_time = time.time()
            print(f"{self.name} placed {self.symbol} at {move}, took {end_time - start_time:.3f}s")
            return True

        print(f"[WARNING] {self.name} failed to select a move.")
        return False

###-------------------------------------------------------------
### Module to manage the turn of each player, query the current player
### Find out if it is the 5th turn to trigger the trap tile
class TurnManager:
    def __init__(self, mode):
        self.mode = mode
        self.players = self._init_players(mode)
        self.current_index = 0
        self.turn_count = 0

    #define the players
    def _init_players(self, mode):
        if mode == "human_vs_ai":
            return ["Human", "AI1"]
        elif mode == "ai_vs_ai":
            return ["AI1", "AI2"]
        else:
            return ["Human"]

   ###--- Able to query the  current player
    def get_current_player(self):

        return self.players[self.current_index]
    # #Needed fort expectimax
    # def set_current_player(self, symbol):
    #     # Optional: map symbol to index if needed
    #     if symbol == "X":
    #         self.current_index = 0
    #     elif symbol == "O":
    #         self.current_index = 1

    ###--- when called the it changes the player
    def advance_turn(self):
        self.turn_count += 1
        self.current_index = (self.current_index + 1) % len(self.players)

    ###--- checks if its the 5th turn, if so activate the trap
    def should_trigger_trap(self):
        return self.turn_count > 0 and self.turn_count % 5 == 0
    ###--- reset the player turn
    def reset(self):
        #self.turn_count = 0
        self.current_index = 0
    ###--- clear for a new game or round
    def reset_turn_count(self):
        self.turn_count = 0

###-------------------------------------------------------------
### Module to manage the turn of each player, query the current player
### Find out if it is the 5th turn to trigger the trap tile
class TrapManager:
    def __init__(self, trigger_interval=5, animation_duration=2.0):
        self.trigger_interval = trigger_interval
        self.animation_duration = animation_duration
        self.active = False
        self.tile = None
        self.start_time = None

    ###--- Query if it is the 5th turn. "Mod 5 = 0" means residual 0 on multiples of 5
    def should_trigger(self, turn_count):
        return not self.active and turn_count > 0 and turn_count % self.trigger_interval == 0

    ###--- Start the removal process
    def trigger(self):
        self.tile = choose_random_tile()
        self.start_time = time.time()
        self.active = True

    ###--- once the tile is selected start an animation and then remove
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
            logger.log_tile_removal([row, col])
            self.reset()
            return True  # Tile was removed
        return False  # Still animating

    ###--- reset the animation for next time
    def reset(self):
        self.active = False
        self.tile = None
        self.start_time = None

###-----------------------------------------------------------------------------
### Module to crete the input boxes used for iteration, accept keyboard input
### and limit the iterations to 10,000
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
        return max(1, min(val, 10000))  ###--- limit teration between 1 and 10,000


###----------------------------------------------------------
### Utility functions. These are all the graphical functions
### Buttons, radio buttons and labes. made into groups for
### easier movement as a unit

###--- creates an array of the GUI elements for easy transport
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

    draw_radio_button("Human vs AI", buttons["human_vs_ai"].x + 10, buttons["human_vs_ai"].y + 10,
                      game_mode == "human_vs_ai")
    draw_radio_button("AI vs AI", buttons["ai_vs_ai"].x + 10, buttons["ai_vs_ai"].y + 10, game_mode == "ai_vs_ai")

    screen.blit(font.render("Iterations AI 1:", True, (255, 255, 255)), (offset_x - 10, offset_y + 280))
    agents_search = ["MCTS", "Expectimax", "Markov"]

    ###--- Easy display of the radio buttons
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
    global iterations_ai1, iterations_ai2, show_start_screen, WIDTH, HEIGHT
    global offset_x, offset_y, previous_game_mode, turn_manager, trap_manager

    x, y = pos
    print(f"Click at X: {x}, Y: {y}")
    print(f"Click at X: {WIDTH}, Y: {HEIGHT}")
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


    if game_mode != previous_game_mode and debug_mode:
        logging.debug(f"[WARNING] game_mode changed in draw start screen from {previous_game_mode} to {game_mode}")
        previous_game_mode = game_mode
###---------------------------------------------------------------------------------------
### End of main menu block
###---------------------------------------------------------------------------

###----------------------------------------------------------------------------------
### Draw the game board. Rotate the pieces based on the grid position
### Initialization at the top of screen
### One image for type of tile, then rotated and moved to fill the board
###-----------------------------------------------------------------------------------

def get_corner_rotation(row, col):
    return {(0, 0): 0, (0, COLS - 1): 270, (ROWS - 1, COLS - 1): 180, (ROWS - 1, 0): 90}.get((row, col), 0)

def get_edge_rotation(row, col):
    if row == 0: return 0
    elif col == COLS - 1: return 270
    elif row == ROWS - 1: return 180
    elif col == 0: return 90
    return 0

###--- This is where the main board that player play
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



###--- Used to select the trap tile
def choose_random_tile():
    return random.randint(0, ROWS - 1), random.randint(0, COLS - 1)

###--- Captures the position
def get_tile_from_click(pos):
    x, y = pos
    col = (x - offset_x) // TILE_SIZE
    row = (y - offset_y) // TILE_SIZE
    return row, col

###--- X is two diagonal lines, O is a circle
def draw_symbol(surface, symbol, x, y):
    if symbol == "X":
        pygame.draw.line(surface, RED, (x - 25, y - 25), (x + 25, y + 25), 5)
        pygame.draw.line(surface, RED, (x - 25, y + 25), (x + 25, y - 25), 5)
    elif symbol == "O":
        pygame.draw.circle(surface, GREEN, (x, y), 25, 5)

def check_winner(symbol):
    for r in range(ROWS):
        if all(board_state[r][c] == symbol for c in range(COLS)):###--- Horizonatal check
            return True
    for c in range(COLS):
        if all(board_state[r][c] == symbol for r in range(ROWS)):###--- Vertical check
            return True
    if all(board_state[i][i] == symbol for i in range(ROWS)): ###--Check Diagonal
        return True
    if all(board_state[i][COLS - 1 - i] == symbol for i in range(ROWS)): ###--- check Draw
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

###--- Keep game over screen until a selection is made.
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


###--- continues updating the board
def update_game_state():
    global highlight_tile, highlight_start_time

    #  Draw all placed symbols
    for symbol, (row, col) in clicks:
        x = offset_x + col * TILE_SIZE + TILE_SIZE // 2
        y = offset_y + row * TILE_SIZE + TILE_SIZE // 2
        #if not headless:
        draw_symbol(screen, symbol, x, y)

    # Animate trap tile if active
    if pending_removal and highlight_tile and highlight_start_time:
        row, col = highlight_tile
        tile_x = offset_x + col * TILE_SIZE
        tile_y = offset_y + row * TILE_SIZE
        elapsed = time.time() - highlight_start_time
        thickness = 6 if int((elapsed * 4) % 2) else 3
        pygame.draw.rect(screen, RED, (tile_x, tile_y, TILE_SIZE, TILE_SIZE), thickness)


###--- Uses class player to create the current players based on the selection of game mode
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

###--- Every time there is the turn of a human, this function is called everytime
###--- There is an vlieck click event
def handle_human_turn(pos, symbol="X"):
    global move_count
    if interaction_paused or game_over:
        return False

    row, col = get_tile_from_click(pos)
    if board_state[row][col] == "":
        board_state[row][col] = symbol
        clicks.append((symbol, (row, col)))
        logger.log_move(current_player, [row, col], symbol)
        move_count[symbol] += 1
        if debug_mode:
            print(f"[DEBUG] Human move registered at ({row}, {col}) with symbol '{symbol}'")

        return True

        #return True
    return False

###--- Based on the AI agent that was selected it will call the appropriate
###--- AI class module to execute their algorithms
def handle_ai_turn(player_id, agent_type, iterations, symbol, opponent):
    global move_count
    if interaction_paused or game_over:
        return None

    print(f"AI turn started for {player_id}")
    start_time = time.time()

    move = None
    if agent_type == "MCTS":
        ###--- we need to build the tree first. then selects move
        ai = MonteCarloAI(symbol, opponent, simulations=iterations)
        ai.run_simulation(board_state)
        move = ai.get_best_move()
    elif agent_type == "Expectimax":
        engine = RefactoredEngine(max_depth=2, method=agent_type.lower())
        move = engine.select_best_move(board_state, symbol)

    elif agent_type == "Markov":
        ai_m = MarkovAgent(symbol, opponent, selected_reward)
        move= ai_m.select_move(board_state)
    else:
        print(f"Unknown agent type: {agent_type}")
        return None
    ###--- only write to board if a valid move was capatured in move
    if move:
        board_state[move[0]][move[1]] = symbol
        clicks.append((symbol, move))
        end_time = time.time()
        print(f"{player_id} placed {symbol} at {move}, took {end_time - start_time:.3f}s")
        logger.log_move(current_player, move, symbol)
        move_count[symbol] += 1
        return move
    return None


### Reset the main menu
def reset_ui():
    global input_boxes, buttons
    input_boxes, buttons = setup_ui_elements(offset_x, offset_y, WIDTH, HEIGHT)

###--- After a game over, if player presses R, the game resets the necessary
###--- Variables to a clean state.
def reset_game():
    global board_state, clicks, highlight_tile, highlight_start_time, isDraw, tiles_remove_count
    global pending_removal, interaction_paused, game_over, winner_count, loser_count, move_count

    board_state = [["" for _ in range(COLS)] for _ in range(ROWS)]
    clicks = []
    highlight_tile = None
    highlight_start_time = None
    pending_removal = False
    interaction_paused = False
    game_over = False
    turn_manager.reset_turn_count()
    turn_manager.reset()
    logger.start_new_game(game_mode)
    logger.log_agents(
        ai1_type=selected_agent_ai1,
        ai1_iterations=iterations_ai1,
        ai2_type=selected_agent_ai2 if game_mode == "ai_vs_ai" else "Human",
        ai2_iterations=iterations_ai2 if game_mode == "ai_vs_ai" else "-"
    )

    winner_count = 0
    loser_count = 0
    move_count = {"X": 0, "O": 0}
    isDraw = False
    tiles_remove_count=0

# ###--- Not used
# def create_agent(agent_type, depth=2):
#     if agent_type == "MCTS":
#         return lambda board, symbol, opponent, iterations: MonteCarloAI(symbol, opponent, simulations=iterations)
#     elif agent_type == "Expectimax":
#         return lambda board, symbol, opponent, iterations: RefactoredEngine(turn_manager, trap_manager, win_manager, depth).select_best_move(board, symbol, method="expectimax")
#     elif agent_type == "Minimax":
#         return lambda board, symbol, opponent, iterations: RefactoredEngine(turn_manager, trap_manager, win_manager, depth).select_best_move(board, symbol, method="minimax")
#     elif agent_type == "Markov":
#         return lambda board, symbol, opponent, iterations: run_markov_agent(board, symbol)
#     return None
#
###--- This is a patch for an issue where pygame was ignoring some clicks from the mouse
def is_click_stable(pos1, pos2, tolerance=5):
    if pos1 is None or pos2 is None:
        return False
    return abs(pos1[0] - pos2[0]) <= tolerance and abs(pos1[1] - pos2[1]) <= tolerance

# ###--- Not used, substitued by the TrapManager class.
# def handle_trap_logic():
#     global interaction_paused, ai_next_move_time
#
#     if trap_manager.should_trigger(turn_manager.turn_count):
#         trap_manager.trigger()
#         interaction_paused = True
#
#     if trap_manager.active:
#         removed = trap_manager.update(screen)
#         if removed:
#             interaction_paused = False
#             current_player = turn_manager.get_current_player()
#             if current_player.startswith("AI"):
#                 ai_next_move_time = time.time() + 0.5
#
# ###---Not used, substituted by handle_ai_turn
# def play_ai_move(self):
#     move = self.get_move(board)
#     if move:
#         board.place_move(move, self.symbol)
#         logging.debug(f"{self.name} placed at {move}")
#
#         return True
#     return False

ai_next_move_time = time.time() + 0.5  # 500ms delay
input_boxes, buttons = setup_ui_elements(offset_x, offset_y, WIDTH, HEIGHT)


logging.basicConfig(level=logging.DEBUG)

###--- used for debut to filter out some unwantted events from showing
pygame.event.set_blocked([
    pygame.WINDOWSHOWN,
    pygame.WINDOWENTER,
    pygame.WINDOWLEAVE,
    pygame.WINDOWFOCUSGAINED,
    pygame.TEXTEDITING
])

###Some initializations for the main
logger = GameLogger()
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
simulation_counter = 0
###--------------------------------------------------------
# Change Here fpr the number of simulations for AI vs AI
max_simulation = 3
###--------------------------------------------------------
headless = False
if headless:
    os.environ["SDL_VIDEODRIVER"] = "dummy"

###--------------------------------------------------------
### Main Loop starts here
### PyGame requires a refresh of the screen per frames there is no input pause
### All user interactions (Events) are capture here
###
while running:
    ###--- Event to handle the main selection screen
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
    #if not headless: ###--- used for simulation to prevent GUI
    draw_board()
    #game_mode = "ai_vs_ai"

    ###--- Hover highlight when Human is hovering over the board.
    if not interaction_paused and not game_over and game_mode == "human_vs_ai":
        mouse_pos = pygame.mouse.get_pos()
        hover_row, hover_col = get_tile_from_click(mouse_pos)
        if 0 <= hover_row < ROWS and 0 <= hover_col < COLS:
            hover_x = offset_x + hover_col * TILE_SIZE
            hover_y = offset_y + hover_row * TILE_SIZE
            pygame.draw.rect(screen, (255, 255, 0), (hover_x, hover_y, TILE_SIZE, TILE_SIZE), 3)

    current_player = turn_manager.get_current_player()

    ###---------
    ### Check the current state of the turns, if human turn then
    ### Check for mouse events and save those x and y positions
    ###
    if game_mode == "human_vs_ai" and turn_manager.get_current_player() == "Human":
        for event in pygame.event.get():
            if event.type not in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION]:
                logging.debug(f"[IGNORED] Unknown event type: {event.type}")
                continue
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_down_pos = pygame.mouse.get_pos()
                mouse_down_time = pygame.time.get_ticks()
            ###--- checking for mouse release due to a bug, this is to
            ###--- ensure that the click was capture
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

    ###--- checks the turn of the current AI Player, sends the current player information
    ###--- to Player module and execute the move
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
    ###--- Trap logic
    ###--- Trigger trap if needed
    if trap_manager.should_trigger(turn_manager.turn_count):
        logging.debug(f"[TRAP] Triggering trap at turn {turn_manager.turn_count}")

        trap_manager.trigger()
        interaction_paused = True

    ###--- Animate trap
    if trap_manager.active:
        removed = trap_manager.update(screen)
        if removed:
            interaction_paused = False
            turn_manager.reset_turn_count()  # Reset turn count after trap
            ###--- Trigger AI if it's their turn after trap
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


    ###--- After all the moves, evaluations have been complete, update the possition of the
    ###--- of the board
    update_game_state()

    ###--- Win check every turn
    if check_winner("X") or check_winner("O"):
        winner = "X" if check_winner("X") else "O"
        logger.finalize(move_count, board_state)

        ####---Turn off after simulation
        show_game_over_screen(winner)
        game_over = True


        if game_mode == "human_vs_ai":
            wait_for_game_over_input()
            game_over = False

        elif simulation_counter <= max_simulation:
            simulation_counter += 1
            reset_game()
            game_over = False

        else:
            game_over = True
            running = False

        # winner_symbol = "X" if check_winner("X") else "O"
        # loser_symbol = "O" if winner_symbol == "X" else "X"

    # Draw check
    if not check_winner("X") and not check_winner("O"):
        board_full = all(board_state[row][col] != "" for row in range(ROWS) for col in range(COLS))

        if board_full:
            ###--- turn off for simulation
            show_game_over_screen("Draw")
            logger.finalize(move_count, board_state)

            game_over = True
            if game_mode == "human_vs_ai":
                wait_for_game_over_input()
                game_over = False


            elif simulation_counter <= max_simulation:
                simulation_counter += 1
                pygame.time.wait(1000)
                reset_game()
            else:
                game_over = True
                running = False

    pygame.display.flip()
    clock.tick(60)


pygame.quit()


###--- Load individual logs
summary_df = pd.read_csv("Analytics\\game_stats_summary.csv")
details_df = pd.read_csv("Analytics\\game_stats_details.csv")
agents_df = pd.read_csv("Analytics\\game_stats_agents.csv")

###--- Merge them step-by-step on play_id
merged_df = summary_df.merge(details_df, on="play_id", how="left")
merged_df = merged_df.merge(agents_df, on="play_id", how="left")

###--- Export to a new combined CSV
merged_df.to_csv("Analytics\\game_stats_combined.csv", index=False)

###--- Game quit
sys.exit()
