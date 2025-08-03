import csv
import os
from datetime import datetime

class AnalyticsTracker:
    def __init__(self, filename="game_stats.csv"):
        self.filename = filename
        self.fieldnames = ["timestamp", "game_mode", "winner", "moves", "tiles_removed"]
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, mode="w", newline='') as file:
                writer = csv.DictWriter(file, fieldnames=self.fieldnames)
                writer.writeheader()

    def log_game(self, game_mode, winner, moves, tiles_removed):
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "game_mode": game_mode,
            "winner": winner,
            "moves": moves,
            "tiles_removed": tiles_removed
        }
        with open(self.filename, mode="a", newline='') as file:
            writer = csv.DictWriter(file, fieldnames=self.fieldnames)
            writer.writerow(log_entry)
