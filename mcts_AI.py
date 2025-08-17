
import copy
import random
import time

###--- This class handles the MonteCarlo AI logic
class MonteCarloAI:
    ###--- Initializes the agent with player symbols and number of simulations per move

    def __init__(self, player_symbol, opponent_symbol, simulations=500):
        self.player = player_symbol
        self.opponent = opponent_symbol
        self.simulations = simulations
        self.stats = {}  # {(row, col): {"wins": x, "visits": y}}

    ###--- Runs simulations for each legal move to estimate win rates

    def run_simulation(self, board_state):
        self.stats.clear()
        start_time = time.time()

        ###--- Get all possible moves from the current board state
        legal_moves = self.get_legal_moves(board_state)

        ###--- Initialize stats for each move and run simulations
        for move in legal_moves:
            self.stats[move] = {"wins": 0, "visits": 0}

            ###--- Simulate multiple games for each move

            for _ in range(self.simulations):
                result = self.simulate_random_game(board_state, move)
                self.stats[move]["visits"] += 1
                if result == self.player:
                    self.stats[move]["wins"] += 1
        ###--- Record how long the simulation took
        self.elapsed_time = time.time() - start_time

    ###--- Selects the move with the highest win rate from simulation stats
    def get_best_move(self):
        best_move = None
        best_win_rate = -1
        ###--- Iterate through all moves and find the one with the best win rati
        for move, data in self.stats.items():
            win_rate = data["wins"] / data["visits"] if data["visits"] > 0 else 0
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_move = move

        return best_move

    def visualize_path(self):
        # Placeholder for future visualization logic
        return self.stats

    ###--- Returns a list of all empty tiles (legal moves) on the board

    def get_legal_moves(self, board_state):
        return [(r, c) for r in range(len(board_state)) for c in range(len(board_state[0])) if board_state[r][c] == ""]

    ###--- Simulates a full random game starting from a given move

    def simulate_random_game(self, board_state, move):
        board = copy.deepcopy(board_state)
        board[move[0]][move[1]] = self.player
        current_player = self.opponent

        ###--- Play until there's a winner or the board is full
        while True:
            winner = self.check_winner(board)
            if winner:
                return winner
            ###--- Check for draw if board is full
            if all(cell != "" for row in board for cell in row):
                return "Draw"
            ###--- Get remaining legal moves
            legal = self.get_legal_moves(board)
            if not legal:
                return "Draw"
            ###--- Randomly select a move and switch players
            r, c = random.choice(legal)
            board[r][c] = current_player
            current_player = self.player if current_player == self.opponent else self.opponent

    ###--- Checks the board for a winner by scanning all tiles

    def check_winner(self, board):
        # Basic horizontal/vertical/diagonal check for 5x5
        for r in range(len(board)):
            for c in range(len(board[0])):
                if board[r][c] == "":
                    continue
                if self.check_line(board, r, c):
                    return board[r][c]
        return None

    ###--- Checks if a winning line of 5 symbols starts from a given tile

    def check_line(self, board, r, c):
        symbol = board[r][c]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        ##--- Try each direction to see if it forms a line of 5 matching symbols
        for dr, dc in directions:
            count = 0
            for i in range(5):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < len(board) and 0 <= nc < len(board[0]) and board[nr][nc] == symbol:
                    count += 1
                else:
                    break
            ###--- Return True if a complete line of 5 is found
            if count == 5:
                return True
        return False
