import csv
import random
from utils import check_winner, is_center

###--- This class implements a rule-based Markov agent using configurable rewards
class MarkovAgent:
    ###--- Initializes the agent with symbols and loads reward values from CSV
    def __init__(self, symbol, opponent, reward_file="Markov_config\\rewards.csv"):
        self.symbol = symbol
        self.opponent = opponent
        self.rewards = self.load_rewards(reward_file)

    ###--- Loads reward values for different move types from a CSV file
    def load_rewards(self, path):
        rewards = {}
        with open(path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            ###--- Parse each row and store reward values by move type
            for row in reader:
                rewards[row['move_type']] = float(row['reward'])
        return rewards

    ###--- Evaluates the strategic value of placing a symbol at (row, col)
    def evaluate_tile(self, board, row, col):
        ###--- Penalize invalid moves (already occupied)
        if board[row][col] != "":
            return self.rewards.get("invalid", -100)
        ###--- Simulate AI move and check for winning outcome
        score = self.rewards.get("neutral", 0)

        ###--- Simulate AI move
        board_copy = [r[:] for r in board]
        board_copy[row][col] = self.symbol

        ###--- Check if this move wins the game
        if check_winner(self.symbol, board_copy):
            score += self.rewards.get("win", 0)

        ###--- Simulate opponent move to detect and block threats
        board_threat = [r[:] for r in board]
        board_threat[row][col] = self.opponent
        if check_winner(self.opponent, board_threat):
            score += self.rewards.get("block", 0)

        ###--- Add positional bonus for center control

        if is_center(board, row, col):
            score += self.rewards.get("center_control", 0)

        return score

    ###--- Selects the move with the highest evaluated score

    def select_move(self, board):
        best_score = float('-inf')
        best_moves = []
        ###--- Evaluate every tile and track the best scoring moves
        for r in range(len(board)):
            for c in range(len(board[r])):
                score = self.evaluate_tile(board, r, c)
                ###--- Update best score and reset best moves list
                if score > best_score:
                    best_score = score
                    best_moves = [(r, c)]
                ###--- If score ties best, add to candidate list

                elif score == best_score:
                    best_moves.append((r, c))
        return random.choice(best_moves) if best_moves else None

    ###--- Static method to check if placing opponent symbol at (r, c) creates a threat
    def is_threat(board, r, c, opponent_symbol):
        board[r][c] = opponent_symbol
        threat = check_winner(board, opponent_symbol)
        board[r][c] = None  # undo move
        return threat


