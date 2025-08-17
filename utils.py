###---- used  for checking Markov win

def check_winner(symbol, board):
    ### Basic win logic for 3x3
    for row in board:
        if all(cell == symbol for cell in row):
            return True
    for col in range(3):
        if all(board[row][col] == symbol for row in range(3)):
            return True
    if all(board[i][i] == symbol for i in range(3)):
        return True
    if all(board[i][2 - i] == symbol for i in range(3)):
        return True
    return False

def is_center(board, row, col):
    return row == len(board) // 2 and col == len(board[0]) // 2