import copy
import random
import time

class MonteCarloAI:
    def __init__(self, player_symbol, opponent_symbol, simulations=500):
        self.player = player_symbol
        self.opponent = opponent_symbol
        self.simulations = simulations
        self.stats = {}  # {(row, col): {"wins": x, "visits": y}}

    def run_simulation(self, board_state):
        self.stats.clear()
        start_time = time.time()

        legal_moves = self.get_legal_moves(board_state)

        for move in legal_moves:
            self.stats[move] = {"wins": 0, "visits": 0}

            for _ in range(self.simulations):
                result = self.simulate_random_game(board_state, move)
                self.stats[move]["visits"] += 1
                if result == self.player:
                    self.stats[move]["wins"] += 1

        self.elapsed_time = time.time() - start_time

    def get_best_move(self):
        best_move = None
        best_win_rate = -1

        for move, data in self.stats.items():
            win_rate = data["wins"] / data["visits"] if data["visits"] > 0 else 0
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_move = move

        return best_move

    def visualize_path(self):
        # Placeholder for future visualization logic
        return self.stats

    def get_legal_moves(self, board_state):
        return [(r, c) for r in range(len(board_state)) for c in range(len(board_state[0])) if board_state[r][c] == ""]

    def simulate_random_game(self, board_state, move):
        board = copy.deepcopy(board_state)
        board[move[0]][move[1]] = self.player
        current_player = self.opponent

        while True:
            winner = self.check_winner(board)
            if winner:
                return winner
            if all(cell != "" for row in board for cell in row):
                return "Draw"

            legal = self.get_legal_moves(board)
            if not legal:
                return "Draw"

            r, c = random.choice(legal)
            board[r][c] = current_player
            current_player = self.player if current_player == self.opponent else self.opponent

    def check_winner(self, board):
        # Basic horizontal/vertical/diagonal check for 5x5
        for r in range(len(board)):
            for c in range(len(board[0])):
                if board[r][c] == "":
                    continue
                if self.check_line(board, r, c):
                    return board[r][c]
        return None

    def check_line(self, board, r, c):
        symbol = board[r][c]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
        for dr, dc in directions:
            count = 0
            for i in range(5):
                nr, nc = r + dr * i, c + dc * i
                if 0 <= nr < len(board) and 0 <= nc < len(board[0]) and board[nr][nc] == symbol:
                    count += 1
                else:
                    break
            if count == 5:
                return True
        return False
