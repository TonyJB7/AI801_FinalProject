import csv
import random
from utils import check_winner, is_center

class MarkovAgent:
    def __init__(self, symbol, opponent, reward_file="Markov_config\\rewards.csv"):
        self.symbol = symbol
        self.opponent = opponent
        self.rewards = self.load_rewards(reward_file)

    def load_rewards(self, path):
        rewards = {}
        with open(path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rewards[row['move_type']] = float(row['reward'])
        return rewards

    def evaluate_tile(self, board, row, col):
        if board[row][col] != "":
            return self.rewards.get("invalid", -100)

        score = self.rewards.get("neutral", 0)

        ###--- Simulate AI move
        board_copy = [r[:] for r in board]
        board_copy[row][col] = self.symbol

        ###--- Check if this move wins the game
        if check_winner(self.symbol, board_copy):
            score += self.rewards.get("win", 0)

        ###--- Simulate opponent move to detect threat
        board_threat = [r[:] for r in board]
        board_threat[row][col] = self.opponent
        if check_winner(self.opponent, board_threat):
            score += self.rewards.get("block", 0)

        ###--- Positional heuristic
        if is_center(board, row, col):
            score += self.rewards.get("center_control", 0)

        return score
    def select_move(self, board):
        best_score = float('-inf')
        best_moves = []
        for r in range(len(board)):
            for c in range(len(board[r])):
                score = self.evaluate_tile(board, r, c)
                if score > best_score:
                    best_score = score
                    best_moves = [(r, c)]
                elif score == best_score:
                    best_moves.append((r, c))
        return random.choice(best_moves) if best_moves else None

    def is_threat(board, r, c, opponent_symbol):
        board[r][c] = opponent_symbol
        threat = check_winner(board, opponent_symbol)
        board[r][c] = None  # undo move
        return threat


