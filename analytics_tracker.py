import csv
import os
from datetime import datetime

class AnalyticsTrackerSummary:
    def __init__(self, filename="game_stats_summary.csv"):
        self.filename = filename
        self.fieldnames = ["timestamp", "playID", "winner","Winmoves", "winShape", "lose",
                           "loseShape", "loseMveos", "tiles_removed"]
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_game(self, playID, game_mode, winner, Winmoves, winShape,
                 lose, loseMveos, loseShape, tiles_removed):
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "playID": playID,
            "game_mode": game_mode,
            "winner": winner,
            "Winmoves": Winmoves,
            "winShape": winShape,
            "lose": lose,
            "loseMveos": loseMveos,
            "loseShape": loseShape,
            "tiles_removed": tiles_removed
        }
        with open(self.filename, mode="a", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(log_entry)

class AnalyticsTrackerDetails:
    def __init__(self, filename="game_stats_details.csv"):
        self.filename = filename
        self.fieldnames = ["timestamp", "playID", "gameMode","player","position",
                           "shape","tiles_removed_pos"]
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_game(self, playID, game_mode, player,position, shape, tiles_removed_pos):
        log_entry = {
            "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "playID": playID,
            "game_mode": game_mode,
            "player": player,
            "position": position,
            "shape": shape,
            "tiles_removed_pos": tiles_removed_pos
        }
        with open(self.filename, mode="a", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(log_entry)
