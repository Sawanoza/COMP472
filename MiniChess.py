import math
import copy
import time
import argparse

class MiniChess:
    def __init__(self):
        self.current_game_state = self.init_board()

    """
    Initialize the board

    Args:
        - None
    Returns:
        - state: A dictionary representing the state of the game
    """
    def init_board(self):
        state = {
                "board": 
                [['bK', 'bQ', 'bB', 'bN', '.'],
                ['.', '.', 'bp', 'bp', '.'],
                ['.', '.', '.', '.', '.'],
                ['.', 'wp', 'wp', '.', '.'],
                ['.', 'wN', 'wB', 'wQ', 'wK']],
                "turn": 'white',
                }
        return state

    """
    Prints the board
    
    Args:
        - game_state: Dictionary representing the current game state
    Returns:
        - None
    """
    def display_board(self, game_state):
        print()
        for i, row in enumerate(game_state["board"], start=1):
            print(str(6-i) + "  " + ' '.join(piece.rjust(3) for piece in row))
        print()
        print("     A   B   C   D   E")
        print()

    """
    Check if the move is valid    
    
    Args: 
        - game_state:   dictionary | Dictionary representing the current game state
        - move          tuple | the move which we check the validity of ((start_row, start_col),(end_row, end_col))
    Returns:
        - boolean representing the validity of the move
    """
    def is_valid_move(self, game_state, move):
        start, end = move
        start_row, start_col = start
        end_row, end_col = end

        piece = game_state["board"][start_row][start_col]
        target_piece = game_state["board"][end_row][end_col]

        #Check if piece belongs to current player
        if piece[0] != game_state["turn"][0]:
            return False

        #Check if target square is occupied by player's own piece
        if target_piece != '.' and target_piece[0] == piece[0]:
            return False

        #Check if move is within the bounds of board
        if not (0 <= end_row < 5 and 0 <= end_col < 5):
            return False

        #Piece specific move validation
        piece_type = piece[1]
        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)

        if piece_type == 'K': #King
            if row_diff > 1 or col_diff > 1:
                return False
        elif piece_type == 'Q': #Queen
            if row_diff != 0 and col_diff != 0 and row_diff != col_diff:
                return False
        elif piece_type == 'B': #Bishop
            if row_diff != col_diff:
                return False
        elif piece_type == 'N': #Knight
            if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)):
                return False
        elif piece_type == 'p': #Pawn
            if piece[0] == 'w': #White pawn
                if end_row > start_row: #Pawns can only move forward (up)
                    return False
                if row_diff != 1 or (col_diff != 0 and col_diff != 1):
                    return False
            else: #Black pawn
                if end_row < start_row: #Pawns can only move forward (down)
                    return False
                if row_diff != 1 or (col_diff != 0 and col_diff != 1):
                    return False

        return True

    """
    Returns a list of valid moves

    Args:
        - game_state:   dictionary | Dictionary representing the current game state
    Returns:
        - valid moves:   list | A list of nested tuples corresponding to valid moves [((start_row, start_col),(end_row, end_col)),((start_row, start_col),(end_row, end_col))]
    """
    def valid_moves(self, game_state):
        # Return a list of all the valid moves.
        # Implement basic move validation
        # Check for out-of-bounds, correct turn, move legality, etc
        
        #MAKE IT SO PIECES (BESIDES KNIGHT) CANT JUMP OVER PIECES
        #MAKE PAWNS TRANSFORM INTO QUEEN WHEN REACHING THE OTHER SIDE

        valid_moves = []
        for row in range(5):
            for col in range(5):
                piece = game_state["board"][row][col]
                if piece != '.' and piece[0] == game_state["turn"][0]:
                    #Generate all possible moves for this piece
                    for dr in range(-2, 3): #Rows: -2 to +2
                        for dc in range(-2, 3): #Columns: -2 to +2
                            end_row = row + dr
                            end_col = col + dc
                            move = ((row, col), (end_row, end_col))
                            if self.is_valid_move(game_state, move):
                                valid_moves.append(move)
        return valid_moves

    """
    Modify to board to make a move

    Args: 
        - game_state:   dictionary | Dictionary representing the current game state
        - move          tuple | the move to perform ((start_row, start_col),(end_row, end_col))
    Returns:
        - game_state:   dictionary | Dictionary representing the modified game state
    """
    def make_move(self, game_state, move):
        start = move[0]
        end = move[1]
        start_row, start_col = start
        end_row, end_col = end
        piece = game_state["board"][start_row][start_col]
        game_state["board"][start_row][start_col] = '.'
        game_state["board"][end_row][end_col] = piece
        game_state["turn"] = "black" if game_state["turn"] == "white" else "white"

        return game_state

    """
    Parse the input string and modify it into board coordinates

    Args:
        - move: string representing a move "B2 B3"
    Returns:
        - (start, end)  tuple | the move to perform ((start_row, start_col),(end_row, end_col))
    """
    def parse_input(self, move):
        try:
            start, end = move.split()
            start = (5-int(start[1]), ord(start[0].upper()) - ord('A'))
            end = (5-int(end[1]), ord(end[0].upper()) - ord('A'))
            return (start, end)
        except:
            return None

    """
    Game loop

    Args:
        - None
    Returns:
        - None
    """
    def play(self):
        print("Welcome to Mini Chess! Enter moves as 'B2 B3'. Type 'exit' to quit.")
        while True:
            self.display_board(self.current_game_state)
            move = input(f"{self.current_game_state['turn'].capitalize()} to move: ")
            if move.lower() == 'exit':
                print("Game exited.")
                exit(1)

            move = self.parse_input(move)
            if not move or not self.is_valid_move(self.current_game_state, move):
                print("Invalid move. Try again.")
                continue

            self.make_move(self.current_game_state, move)

if __name__ == "__main__":
    game = MiniChess()
    game.play()