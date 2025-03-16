import math
import copy
import time
import argparse
from collections import defaultdict

#Import AIPlayer
from AIPlayer import AIPlayer

class MiniChess:
    def __init__(self):
        #1) Ask for play mode
        valid_modes = {"H-H", "H-AI", "AI-H", "AI-AI"}
        while True:
            play_mode = input("Enter play mode (H-H, H-AI, AI-H, AI-AI): ").strip().upper()
            if play_mode in valid_modes:
                self.mode = play_mode
                mode_parts = play_mode.split("-")
                self.player1_type = mode_parts[0]
                self.player2_type = mode_parts[1]
                break
            print("Invalid mode. Valid options: H-H, H-AI, AI-H, AI-AI.\n")

        #2) Check if mode is H-H
        if self.mode == "H-H":
            #If no AI, default max_turns, AI timeout, alpha-beta, and heuristic
            self.max_turns = 999
            self.timeout = "X"
            self.use_alpha_beta = False
        else:
            #a) Ask for max turns
            while True:
                max_turns_str = input("Enter maximum number of turns (e.g., 100): ").strip()
                try:
                    max_turns = int(max_turns_str)
                    if max_turns > 0:
                        self.max_turns = max_turns
                        break
                except ValueError:
                    pass
                print("Invalid number. Please enter a positive integer.\n")

            #b) Ask for AI timeout
            while True:
                timeout_str = input("Enter AI timeout in seconds (e.g., 5): ").strip()
                try:
                    timeout = int(timeout_str)
                    if timeout > 0:
                        self.timeout = timeout
                        break
                except ValueError:
                    pass
                print("Invalid timeout. Please enter a positive integer.\n")

            #c) Ask for minimax or alpha-beta
            while True:
                ab_str = input("Use minimax? (false) or alpha-beta? (true): ").strip().lower()
                if ab_str in ("true", "false"):
                    self.use_alpha_beta = (ab_str == "true")
                    break
                print("Please type 'true' or 'false'.\n")

            #d) Ask for heuristic (e0, e1, e2)
            while True:
                heuristic_str = input("Enter heuristic (e0, e1 (WIP), e2 (WIP)): ").strip().lower()
                if heuristic_str in {"e0", "e1", "e2"}:
                    self.heuristic_name = heuristic_str
                    #set actual function pointer based on heuristic chosen
                    if heuristic_str == "e0":
                        self.heuristic_func = self.heuristic_e0
                    elif heuristic_str == "e1":
                        self.heuristic_func = self.heuristic_e1
                    else:
                        self.heuristic_func = self.heuristic_e2
                    break
                print("Invalid choice. Valid heuristics: e0, e1, e2.\n")
        
        
        self.current_game_state = self.init_board()
        self.unchanged_turns = 0 #Counter consecutive turns with no piece capture (for draw detection)
        self.last_piece_count = 12 #Stores previous turn's piece count (start with 12 pieces)
        self.turn_count = 1 #Keeps track of turn nb (full turns)

        #stats for AI
        self.states_explored = 0
        self.states_by_depth = defaultdict(int)

        #Create log file name based on parameters
        self.log_file = f"gameTrace-{str(self.use_alpha_beta).lower()}-{self.timeout}-{self.max_turns}.txt"

        #Initialize log file with game parameters
        self.initialize_log()

    ###Creates or resets the log file and records the initial parameters and board state
    def initialize_log(self):
        with open(self.log_file, "w") as f:
            f.write("Mini Chess Game Log\n\n")
            f.write("Game Parameters:\n")
            f.write(f"Play mode: {self.mode}\n")
            
            #Log AI-specific info if applicable
            if 'AI' in self.mode:
                f.write(f"Max turns: {self.max_turns}\n")
                f.write(f"Timeout: {self.timeout} seconds\n")
                f.write(f"Alpha-beta: {self.use_alpha_beta}\n")
                f.write(f"Heuristic: {self.heuristic_name}\n")
            
            f.write("\nInitial Board Configuration:\n")
            f.write(self.board_to_string(self.current_game_state) + "\n\n")

    ###Logs the current turn, player move and updated board state to a file
    def log_game_state(self, player, move, time_taken=None, heuristic_score=None, search_score=None):
        start, end = move
        
        #Convert start and end pos to chess notation (ex: start=(4, 0) to A1)
        move_str = f"Move from {chr(start[1] + ord('A'))}{5 - start[0]} to {chr(end[1] + ord('A'))}{5 - end[0]}"

        #Create a string with player & details
        base_entry = [
            f"Player: {player.capitalize()}",
            f"Turn #{self.turn_count if player == 'black' else self.turn_count}",
            f"Action: {move_str}"
        ]

        #If AI move, log search details
        if (player == "white" and self.player1_type == "AI") or (player == "black" and self.player2_type == "AI"):
            if time_taken is not None:
                base_entry.append(f"Time for this action: {time_taken:.5f} sec")
            if heuristic_score is not None:
                base_entry.append(f"Heuristic score: {heuristic_score}")
            if search_score is not None:
                base_entry.append(f"{'Alpha-beta' if self.use_alpha_beta else 'Minimax'} search score: {search_score}")
        
        #text line for the updated board
        updated_board_line = f"Updated Board:\n{self.board_to_string(self.current_game_state)}"

        #Build final log entry (including updated board)
        log_entry = base_entry + [updated_board_line]

        #Build console entry (EXCLUDING updated board)
        console_entry = base_entry[:]  #copy

        #Print to console
        for line in console_entry:
            print(line)

        #Add AI cumulative statistics if applicable
        if (player == "white" and self.player1_type == "AI") or (player == "black" and self.player2_type == "AI"):
            stats = self.get_ai_stats()
            for stat in stats:
                log_entry.append(stat)

        #Write to file
        with open(self.log_file, "a") as f:
            f.write("\n".join(log_entry) + "\n\n")

    ###Generate statistics about AI performance for logs
    def get_ai_stats(self):
        stats = []
        
        #Format numbers with K (1000), M (1000000) suffixes
        def format_number(num):
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.1f}k"
            else:
                return str(num)
        
        #Total states explored
        stats.append(f"Cumulative states explored: {format_number(self.states_explored)}")
        
        #States by depth
        by_depth = []
        for depth, count in sorted(self.states_by_depth.items()):
            by_depth.append(f"{depth}={format_number(count)}")
        stats.append(f"Cumulative states explored by depth: {' '.join(by_depth)}")
        
        #Percentage by depth
        total = sum(self.states_by_depth.values())
        if total > 0:
            percentages = []
            for depth, count in sorted(self.states_by_depth.items()):
                if count > 0:  #Only include non-zero counts
                    percentages.append(f"{depth}={count/total*100:.1f}%")
            stats.append(f"Cumulative % states explored by depth: {' '.join(percentages)}")
        
        #Average branching factor (Approximate: total nodes / non-leaf nodes)
        if total > 0:
            leaf_nodes = self.states_by_depth.get(max(self.states_by_depth.keys()), 0)
            non_leaf_nodes = total - leaf_nodes
            avg_branching = total / max(1, non_leaf_nodes)
            stats.append(f"Average branching factor: {avg_branching:.1f}")
        
        return stats

    ###Convert the board into a readable string format (for file output)
    def board_to_string(self, game_state):
        #Iterate through each row in board and for each piece in row, pad it with spaces (align)
        board_str = "\n".join(f"{5-i} " + " ".join(piece.rjust(3) for piece in row) for i, row in enumerate(game_state["board"]))
        return board_str + "\n    A   B   C   D   E"

    """
    Initialize the board

    Args:
        - None
    Returns:
        - state: A dictionary representing the state of the game
    """
    def init_board(self):
        state = {
            "board": [
                ['bK', 'bQ', 'bB', 'bN', '.'],
                ['.', '.', 'bp', 'bp', '.'],
                ['.', '.', '.', '.', '.'],
                ['.', 'wp', 'wp', '.', '.'],
                ['.', 'wN', 'wB', 'wQ', 'wK']
            ],
            "turn": 'white'
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

        #Check if start/end position is within bounds
        if not (0 <= start_row < 5 and 0 <= start_col < 5):
            return False
        if not (0 <= end_row < 5 and 0 <= end_col < 5):
            return False

        #Identify start/end
        piece = game_state["board"][start_row][start_col]
        target_piece = game_state["board"][end_row][end_col]

        #Check if start square has a piece
        if piece == '.':
            return False

        #Check if piece belongs to current player
        if piece[0] != game_state["turn"][0]:
            return False

        #Check if target square is occupied by player's own piece
        if target_piece != '.' and target_piece[0] == piece[0]:
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
                if end_row >= start_row: #Pawns can only move forward (up: 5 -> 1 == 0 -> 4)
                    return False
                if row_diff != 1: #Move 1 row only
                    return False
                if col_diff == 0: #Forward move (no capture)
                    if target_piece != '.': #Forward square must be empty
                        return False
                elif col_diff == 1: #Diagonal capture move
                    if target_piece == '.' or target_piece[0] == 'w': #Must capture opponent's piece
                        return False
                else:
                    return False #Any other movement is invalid
            else: #Black pawn
                if end_row <= start_row: #Pawns can only move forward (down: 5 -> 1 == 0 -> 4)
                    return False
                if row_diff != 1:
                    return False
                if col_diff == 0: 
                    if target_piece != '.': 
                        return False
                elif col_diff == 1:
                    if target_piece == '.' or target_piece[0] == 'b': 
                        return False
                else:
                    return False #Any other movement is invalid
        else:
            return False #Unrecognized piece type

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
                    for end_row in range(5):
                        for end_col in range(5):
                            move = ((row, col), (end_row, end_col)) # Current pos to possible end pos

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
    def make_move(self, game_state, move, update_game=True):
        #Create deep copy of game state to not modify original (AI needs to evaluate potential moves without changing actual game state)
        if update_game:
            new_state = game_state
        else:
            new_state = copy.deepcopy(game_state)
        
        start = move[0] #Starting pos (row, col)
        end = move[1] #Destination pos (row, col)

        start_row, start_col = start
        end_row, end_col = end
        piece = new_state["board"][start_row][start_col] #Get piece being moved

        #Check if move results in pawn promotion
        if piece[1] == 'p': #if piece is pawn
            if piece[0] == 'w' and end_row == 0: #White pawn reaches 5th row (row 0 in board array)
                piece = 'wQ' #Promote to white Queen
            elif piece[0] == 'b' and end_row == 4: #Black pawn reaches 1st row (row 4 in board array)
                piece = 'bQ' #Promote to black Queen

        #Update the board
        new_state["board"][start_row][start_col] = '.' #Clear old pos
        new_state["board"][end_row][end_col] = piece #Place piece in new pos

        if update_game:
            # Count pieces on the board to track game progression
            piece_count = sum(1 for row in new_state["board"] for cell in row if cell != '.')

            # Check if a King has been captured (winning condition)
            board_str = ''.join(''.join(row) for row in new_state["board"])
            if 'wK' not in board_str or 'bK' not in board_str: # If a king is missing
                winner = "Black" if 'wK' not in board_str else "White" # Determine winner
                
                # Log & display win message
                with open(self.log_file, "a") as f:
                    f.write(f"{winner} Wins! In {self.turn_count} turns!\n")

                self.display_board(new_state) # Show final board state
                print(f"{winner} Wins!") # Print win message
                exit(0)

            # Check for draw condition (specified number of turns with no piece captured)
            if piece_count == self.last_piece_count:
                self.unchanged_turns += 1 # Increment unchanged turn counter if no piece captured
            else:
                self.unchanged_turns = 0 # Reset counter if piece was captured

            self.last_piece_count = piece_count # Store current piece count for next turn

            # If max_turns full turns pass without capture -> draw
            if self.unchanged_turns >= self.max_turns * 2:
                print(f"Game ends in a draw after {self.max_turns} turns without piece capture!")
                with open(self.log_file, "a") as f:
                    f.write(f"Game ended in a draw after {self.max_turns} full turns without piece capture.\n")
                exit(0)
            
            # If we've reached the maximum number of turns overall -> draw
            if self.turn_count >= self.max_turns and new_state["turn"] == "black":
                print(f"Game ends in a draw after reaching maximum {self.max_turns} turns!")
                with open(self.log_file, "a") as f:
                    f.write(f"Game ended in a draw after reaching maximum {self.max_turns} turns.\n")
                exit(0)

        #Switch turns/player
        previous_turn = new_state["turn"]
        new_state["turn"] = "black" if new_state["turn"] == "white" else "white"

        #Increment `turn_count` only after White & Black have played
        if update_game and previous_turn == "black":  #black just moved, meaning full turn complete
            self.turn_count += 1

        return new_state #return updated game state

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

    #Heuristic functions
    def heuristic_e0(self, game_state):
        """
        Basic material-based heuristic e0:
          Pawn=1, Bishop=3, Knight=3, Queen=9, King=999
          e0 = (WhiteTotal) - (BlackTotal)
        """
        white_score = 0
        black_score = 0
        for row in game_state["board"]:
            for cell in row:
                if cell == 'wp':
                    white_score += 1
                elif cell == 'wB':
                    white_score += 3
                elif cell == 'wN':
                    white_score += 3
                elif cell == 'wQ':
                    white_score += 9
                elif cell == 'wK':
                    white_score += 999
                elif cell == 'bp':
                    black_score += 1
                elif cell == 'bB':
                    black_score += 3
                elif cell == 'bN':
                    black_score += 3
                elif cell == 'bQ':
                    black_score += 9
                elif cell == 'bK':
                    black_score += 999
        return white_score - black_score

    def play(self):
        print(f"\nWelcome to Mini Chess! Game mode: {self.mode}")
        
        # Continue until max turns reached or game ends (win/draw)
        while self.turn_count <= self.max_turns:
            self.display_board(self.current_game_state)
            current_player = self.current_game_state["turn"]
            print(f"{current_player.capitalize()}'s turn ({self.turn_count}/{self.max_turns})")
            
            # Determine if current player is human or AI
            is_ai_turn = (current_player == "white" and self.player1_type == "AI") or \
                        (current_player == "black" and self.player2_type == "AI")
            
            if is_ai_turn:
                # AI's turn - use AIPlayer to generate move
                ai_player = AIPlayer(self, self.heuristic_func)
                
                print(f"AI thinking (max {self.timeout} seconds)...")
                move, search_score, time_taken, explored, states_by_depth = ai_player.get_move(self.current_game_state)
                
                # Update AI stats
                self.states_explored += explored
                for depth, count in states_by_depth.items():
                    self.states_by_depth[depth] += count
                
                # Calculate heuristic score for logging
                heuristic_score = self.heuristic_func(self.current_game_state)
                
                print(f"AI chooses: {chr(move[0][1] + ord('A'))}{5 - move[0][0]} to {chr(move[1][1] + ord('A'))}{5 - move[1][0]}")
                
                # Make the move and log with AI stats
                new_state = copy.deepcopy(self.current_game_state)
                self.current_game_state = self.make_move(new_state, move)
                self.log_game_state(current_player, move, time_taken, heuristic_score, search_score)
                
            else:
                # Human's turn - get input from console
                while True:
                    move_input = input("Enter your move (e.g., 'B2 B3') or 'exit' to quit: ")
                    
                    if move_input.lower() == 'exit':
                        print("Game exited.")
                        exit(1)
                    
                    move = self.parse_input(move_input)
                    if not move:
                        with open(self.log_file, "a") as f:
                            f.write(f"Invalid input format by {current_player.capitalize()}: '{move_input}'\n\n")
                        print("Invalid format. Please use format like 'B2 B3'.")
                        continue
                    
                    if not self.is_valid_move(self.current_game_state, move):
                        with open(self.log_file, "a") as f:
                            f.write(f"Invalid move attempt by {current_player.capitalize()}: '{move_input}'\n\n")
                        print("Invalid move. Try again.")
                        continue
                    
                    # Make the move
                    new_state = copy.deepcopy(self.current_game_state)
                    self.current_game_state = self.make_move(new_state, move)

                    #log move
                    self.log_game_state(current_player, move)

                    break
            
            # Check if max turns reached
            if self.turn_count > self.max_turns:
                print(f"Game ended after {self.max_turns} turns. It's a draw!")
                with open(self.log_file, "a") as f:
                    f.write(f"Game ended in a draw after reaching maximum turns ({self.max_turns}).\n")
                break
        
        # Final board display
        self.display_board(self.current_game_state)
        print("Game complete!")

if __name__ == "__main__":
    game = MiniChess()
    game.play()