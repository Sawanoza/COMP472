import math
import copy
import time
import argparse

class MiniChess:
    def __init__(self):
        self.current_game_state = self.init_board()
        self.unchanged_turns = 0 #Counter consecutive turns with no piece capture (for draw detection)
        self.last_piece_count = 0 #Stores previous turn's empty square count
        self.log_file = "game_log.txt" #Log file
        self.turn_count = 1 #Keeps track of turn nb (full turns)
        self.initialize_log() #Initializes log file with starting board state

    ###Creates or resets the log file and records the initial board state
    def initialize_log(self):
        """Initialize the game log with the starting board."""
        with open(self.log_file, "w") as f:
            f.write("Mini Chess Game Log\n\n")
            f.write("Initial Board Configuration:\n")
            f.write(self.board_to_string(self.current_game_state) + "\n")

    ###Logs the current turn, player move and updated board state to a file
    def log_game_state(self, player, move):
        start, end = move
        
        #Convert start and end pos to chess notation (ex: start=(4, 0) to A1)
        move_str = f"Move from {chr(start[1] + ord('A'))}{5 - start[0]} to {chr(end[1] + ord('A'))}{5 - end[0]}"

        #Create a string with player, details and updated board state
        log_entry = (
            f"Player: {player.capitalize()}\n"
            f"Turn #{self.turn_count}\n"
            f"Action: {move_str}\n"
            f"Updated Board:\n{self.board_to_string(self.current_game_state)}\n"
        )

        #Print to console
        print(f"\nPlayer: {player.capitalize()}")
        print(f"Turn #{self.turn_count}")
        print(f"Action: {move_str}")
        print(f"Updated Board:")

        #Write to file
        with open(self.log_file, "a") as f:
            f.write(log_entry + "\n")

    ###Convert the board into a readable string format (for file output)
    def board_to_string(self, game_state):
        #Iterate through each row in board and for each piece in row, pad it with spaces (align)
        board_str = "\n".join(" ".join(piece.rjust(3) for piece in row) for row in game_state["board"])
        return board_str + "\n  A   B   C   D   E\n"

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

        #Identify start/end
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

        #Extract piece type
        piece_type = piece[1]

        #Calculate row and col diff between start/end 
        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)

        if piece_type == 'K': #King
            if row_diff > 1 or col_diff > 1: #King can move 1 square in any direction
                return False
        elif piece_type == 'Q': #Queen
            if row_diff != 0 and col_diff != 0 and row_diff != col_diff: #Queen moves straight & diagonal: if row & col != 0 -> both need ==
                return False
            #Check for obstructions in path
            if not self.is_path_clear(game_state, start, end):
                return False
        elif piece_type == 'B': #Bishop
            if row_diff != col_diff: #Bishop moves diagonal: row == col
                return False
            #Check for obstructions in path
            if not self.is_path_clear(game_state, start, end):
                return False
        elif piece_type == 'N': #Knight
            if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)): #Knight moves "L"
                return False
        elif piece_type == 'p': #Pawn
            if piece[0] == 'w': #White pawn
                if end_row > start_row: #Pawns can only move forward (up: 5 -> 1 == 0 -> 4)
                    return False
                if row_diff != 1: #Move 1 row only
                    return False
                if col_diff == 0: #Forward move (no capture)
                    if target_piece != '.': #Forward square must be empty
                        return False
                elif col_diff == 1: #Diagonal capture move
                    if target_piece == '.' or target_piece[0] == 'w': #Must capture opponent's piece
                        return False
            else: #Black pawn
                if end_row < start_row: #Pawns can only move forward (down: 5 -> 1 == 0 -> 4)
                    return False
                if row_diff != 1:
                    return False
                if col_diff == 0: 
                    if target_piece != '.': 
                        return False
                elif col_diff == 1:
                    if target_piece == '.' or target_piece[0] == 'b': 
                        return False

        #if all checks pass, move is valid
        return True

    ###Check if path between two squares is clear (no pieces blocking the way)
    def is_path_clear(self, game_state, start, end):
        start_row, start_col = start
        end_row, end_col = end

        #Determine direction of movement (step size per row/col)
        row_step = 1 if end_row > start_row else -1 if end_row < start_row else 0 #(down = 1 | up = -1 | else = 0)
        col_step = 1 if end_col > start_col else -1 if end_col < start_col else 0 #(right = 1 | left = -1 | else = 0)

        #Check each square along path (excluding start & end squares)
        current_row, current_col = start_row + row_step, start_col + col_step
        while (current_row != end_row) or (current_col != end_col):
            #If any square along path is not empty, return False (path blocked)
            if game_state["board"][current_row][current_col] != '.':
                return False  #Path is blocked
            
            #Move to next square along path
            current_row += row_step
            current_col += col_step

        return True #if loop completes, path is clear

    """
    Returns a list of valid moves

    Args:
        - game_state:   dictionary | Dictionary representing the current game state
    Returns:
        - valid moves:   list | A list of nested tuples corresponding to valid moves [((start_row, start_col),(end_row, end_col)),((start_row, start_col),(end_row, end_col))]
    """
    def valid_moves(self, game_state):
        #return list of all valid moves
        valid_moves = []

        #Iterate through each square on the board (5x5)
        for row in range(5):
            for col in range(5):
                piece = game_state["board"][row][col]

                #If square contains piece and belongs to current player
                if piece != '.' and piece[0] == game_state["turn"][0]:
                    #Generate all possible moves for this piece
                    for dr in range(-2, 3): #Row delta: -2 to +2 (move range)
                        for dc in range(-2, 3): #Column delta: -2 to +2 (move range)
                            end_row = row + dr
                            end_col = col + dc
                            move = ((row, col), (end_row, end_col)) #Current pos to possible end pos

                            #If move is valid, add it to list
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
    #Execute a move, update board, check win/draw conditions, switch turns
    def make_move(self, game_state, move):
        start = move[0] #Starting pos (row, col)
        end = move[1] #Destination pos (row, col)

        start_row, start_col = start
        end_row, end_col = end
        piece = game_state["board"][start_row][start_col] #Get piece being moved

        #Check if move results in pawn promotion
        if piece[1] == 'p': #if piece is pawn
            if piece[0] == 'w' and end_row == 0: #White pawn reaches 5th row (row 0 in board array)
                piece = 'wQ' #Promote to white Queen
            elif piece[0] == 'b' and end_row == 4: #Black pawn reaches 1st row (row 4 in board array)
                piece = 'bQ' #Promote to black Queen

        #Update the board
        game_state["board"][start_row][start_col] = '.' #Clear old pos
        game_state["board"][end_row][end_col] = piece #Place piece in new pos

        self.log_game_state(game_state["turn"], move)  #Log move

        #Count nb empty squares to track game progression
        piece_count = sum(row.count('.') for row in game_state["board"])

        #Check if a King has been captured (winning condition)
        board_str = ''.join(''.join(row) for row in game_state["board"])
        if 'wK' not in board_str or 'bK' not in board_str: #If a king is missing
            winner = "Black" if 'wK' not in board_str else "White" #Determine winner
            
            #Log & display win message
            with open(self.log_file, "a") as f:
                f.write(f"{winner} Wins! In {self.turn_count} turns!\n")

            self.display_board(game_state) #Show final board state
            print(f"{winner} Wins!") #Print win message
            exit(0)

        #Check for draw condition (10 FULL turns with no piece captured)
        if piece_count == self.last_piece_count:
            self.unchanged_turns += 1 #Increment unchanged turn counter if no piece captured
        else:
            self.unchanged_turns = 0 #Reset counter if piece was captured

        self.last_piece_count = piece_count #Store current piece count for next turn

        #If 10 full turns (20 moves) pass without capture -> draw
        if self.unchanged_turns == 19:
            print("Game ends in a draw!")
            with open(self.log_file, "a") as f:
                f.write("Game ended in a draw after 10 full turns.\n")
            exit(0)

        #Switch turns
        previous_turn = game_state["turn"]
        game_state["turn"] = "black" if game_state["turn"] == "white" else "white"

        #Increment `turn_count` only after White & Black have played
        if previous_turn == "black":  #Black just moved, meaning full turn complete
            self.turn_count += 1

        return game_state #return updated game state

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