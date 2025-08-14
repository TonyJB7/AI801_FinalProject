import csv
import os
from datetime import datetime

class AnalyticsTrackerSummary:
    def __init__(self, filename="Analytics\\game_stats_summary.csv"):
        self.filename = filename
        self.fieldnames = ["play_id", "game_mode", "winner","win_moves", "win_shape", "lose",
                           "lose_shape", "lose_moves", "tiles_removed"]
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_game(self, play_id, game_mode, winner, win_moves, win_shape,
                 lose, lose_moves, lose_shape, tiles_removed):
        log_entry = {
            "play_id": play_id,
            "game_mode": game_mode,
            "winner": winner,
            "win_moves": win_moves,
            "win_shape": win_shape,
            "lose": lose,
            "lose_moves": lose_moves,
            "lose_shape": lose_shape,
            "tiles_removed": tiles_removed
        }
        with open(self.filename, mode="a", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(log_entry)

class AnalyticsTrackerDetails:
    def __init__(self, filename="Analytics\\game_stats_details.csv"):
        self.filename = filename
        self.fieldnames = ["play_id", "game_mode","player","position",
                           "shape","tiles_removed_pos"]
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_game(self, play_id, game_mode, player,position, shape, tiles_removed_pos):
        log_entry = {
            "play_id": play_id,
            "game_mode": game_mode,
            "player": player,
            "position": position,
            "shape": shape,
            "tiles_removed_pos": tiles_removed_pos
        }
        with open(self.filename, mode="a", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(log_entry)
class AnalyticsTrackerAgents:
    def __init__(self, filename="Analytics\\game_stats_agents.csv"):
        self.filename = filename
        self.fieldnames = ["play_id", "game_mode", "AI1_type", "AI1_iterations", "AI2_type", "AI2_iterations"]
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_agents(self, play_id, game_mode, ai1_type, ai1_iterations, ai2_type, ai2_iterations):
        log_entry = {
            "play_id": play_id,
            "game_mode": game_mode,
            "AI1_type": ai1_type,
            "AI1_iterations": ai1_iterations,
            "AI2_type": ai2_type,
            "AI2_iterations": ai2_iterations
        }
        with open(self.filename, mode="a", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(log_entry)

class AnalyticsTrackerCombined:
    def __init__(self, filename="Analytics\\game_stats_combined.csv"):
        self.filename = filename
        self.fieldnames = [
            "play_id", "game_mode", "winner", "win_moves", "win_shape",
            "lose", "lose_moves", "lose_shape", "tiles_removed",
            "AI1_type", "AI1_iterations", "AI2_type", "AI2_iterations"
        ]
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_combined(self, play_id, game_mode, winner, win_moves, win_shape,
                     lose, lose_moves, lose_shape, tiles_removed,
                     ai1_type, ai1_iterations, ai2_type, ai2_iterations):
        log_entry = {
            "play_id": play_id,
            "game_mode": game_mode,
            "winner": winner,
            "win_moves": win_moves,
            "win_shape": win_shape,
            "lose": lose,
            "lose_moves": lose_moves,
            "lose_shape": lose_shape,
            "tiles_removed": tiles_removed,
            "AI1_type": ai1_type,
            "AI1_iterations": ai1_iterations,
            "AI2_type": ai2_type,
            "AI2_iterations": ai2_iterations
        }
        with open(self.filename, mode="a", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(log_entry)