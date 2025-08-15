class RefactoredEngine:
    def __init__(self, max_depth=2, method="expectimax"):
        self.max_depth = max_depth
        self.method = method

    def evaluate(self, board, symbol):
        # Simple heuristic: +10 for win, -10 for loss, +1 for center control
        score = 0
        center = len(board) // 2
        if board[center][center] == symbol:
            score += 1
        return score

    def get_valid_moves(self, board):
        return [(r, c) for r in range(len(board)) for c in range(len(board[r])) if board[r][c] == ""]

    def simulate_move(self, board, move, symbol):
        r, c = move
        new_board = [row[:] for row in board]
        new_board[r][c] = symbol
        return new_board

    def minimax(self, board, depth, alpha, beta, maximizing_symbol):
        opponent = "O" if maximizing_symbol == "X" else "X"
        if depth == 0:
            return self.evaluate(board, maximizing_symbol), None

        best_move = None
        moves = self.get_valid_moves(board)
        if maximizing_symbol:
            max_eval = float('-inf')
            for move in moves:
                new_board = self.simulate_move(board, move, maximizing_symbol)
                eval, _ = self.minimax(new_board, depth - 1, alpha, beta, False)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = self.simulate_move(board, move, opponent)
                eval, _ = self.minimax(new_board, depth - 1, alpha, beta, True)
                if eval < min_eval:
                    min_eval = eval
                    best_move = move
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval, best_move

    def expectimax(self, board, depth, maximizing_symbol):
        opponent = "O" if maximizing_symbol == "X" else "X"
        if depth == 0:
            return self.evaluate(board, maximizing_symbol), None

        best_move = None
        moves = self.get_valid_moves(board)
        if maximizing_symbol:
            max_eval = float('-inf')
            for move in moves:
                new_board = self.simulate_move(board, move, maximizing_symbol)
                eval, _ = self.expectimax(new_board, depth - 1, False)
                if eval > max_eval:
                    max_eval = eval
                    best_move = move
            return max_eval, best_move
        else:
            total = 0
            for move in moves:
                new_board = self.simulate_move(board, move, opponent)
                eval, _ = self.expectimax(new_board, depth - 1, True)
                total += eval
            avg_eval = total / len(moves) if moves else 0
            return avg_eval, None

    def select_best_move(self, board, symbol):
        if self.method == "minimax":
            _, move = self.minimax(board, self.max_depth, float('-inf'), float('inf'), True)
        else:
            _, move = self.expectimax(board, self.max_depth, True)
        return move