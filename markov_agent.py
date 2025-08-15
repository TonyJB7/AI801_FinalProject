import csv
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

        # Simulate move
        board_copy = [r[:] for r in board]
        board_copy[row][col] = self.symbol

        if check_winner(self.symbol, board_copy):
            score += self.rewards.get("win", 0)
        elif check_winner(self.opponent, board_copy):
            score += self.rewards.get("block", 0)

        if is_center(board, row, col):
            score += self.rewards.get("center_control", 0)

        return score

    def select_move(self, board):
        best_score = float('-inf')
        best_move = None
        for r in range(len(board)):
            for c in range(len(board[r])):
                score = self.evaluate_tile(board, r, c)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
        return best_move