import copy
from collections import defaultdict

#Import AI
from AI import AI

class MiniChess:
    def __init__(self):
        #1) Ask for play mode
        valid_modes = {"H-H", "H-AI", "AI-H", "AI-AI"}
        while True:
            play_mode = input("Enter play mode (H-H, H-AI, AI-H, AI-AI): ").strip().upper()
            if play_mode in valid_modes:
                self.mode = play_mode #store selected mode
                mode_parts = play_mode.split("-") #split mode into player1 and player2 types
                self.player1_type = mode_parts[0]
                self.player2_type = mode_parts[1]
                break
            print("Invalid mode. Valid options: H-H, H-AI, AI-H, AI-AI.\n")

        #2) Check if mode is H-H
        if self.mode == "H-H":
            #If no AI, default max_turns, AI timeout, alpha-beta, and heuristic
            self.max_turns = 999 #No limit in H vs H games
            self.timeout = "X" #No AI in H vs H games
            self.use_alpha_beta = False #No AI in H vs H games
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
                heuristic_str = input("Enter heuristic (e0, e1, e2): ").strip().lower()
                if heuristic_str in {"e0", "e1", "e2"}:
                    self.heuristic_name = heuristic_str #store heuristic choice
                    #assign corresponding heuristic function
                    if heuristic_str == "e0":
                        self.heuristic_func = self.heuristic_e0
                    elif heuristic_str == "e1":
                        self.heuristic_func = self.heuristic_e1
                    else:
                        self.heuristic_func = self.heuristic_e2
                    break
                print("Invalid choice. Valid heuristics: e0, e1, e2.\n")
        
        #Initialize game state
        self.current_game_state = self.init_board() #Create inital board setup
        self.unchanged_turns = 0 #Counter consecutive turns with no piece capture (for draw detection)
        self.last_piece_count = 12 #Stores previous turn's piece count (start with 12 pieces)
        self.turn_count = 1 #Keeps track of turn nb (full turns)

        #stats for AI
        self.states_explored = 0 #Counter of states evaluated by AI
        self.states_by_depth = defaultdict(int) #Dictionary to track states explored at each depth

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
            
            #Log AI-specific info if at least 1 player is AI
            if 'AI' in self.mode:
                f.write(f"Max turns: {self.max_turns}\n")
                f.write(f"Timeout: {self.timeout} seconds\n")
                f.write(f"Alpha-beta: {self.use_alpha_beta}\n")
                f.write(f"Heuristic: {self.heuristic_name}\n")
            
            f.write("\nInitial Board Configuration:\n")
            f.write(self.board_to_string(self.current_game_state) + "\n\n")

    ###Logs the current game state, including player moves and AI specific details if applicable
    def log_game_state(self, player, move, time_taken=None, heuristic_score=None, search_score=None):
        #Unpack move coordinates
        start, end = move
        
        #Convert start and end pos to chess notation (ex: start=(4, 0) to A1)
        move_str = f"Move from {chr(start[1] + ord('A'))}{5 - start[0]} to {chr(end[1] + ord('A'))}{5 - end[0]}"

        #Create a string with player & details
        base_entry = [
            f"\nPlayer: {player.capitalize()}",
            f"Turn #{self.turn_count - 1 if player == 'black' else self.turn_count}",
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
        console_entry = base_entry[:]  #copy of base_entry

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
        stats = [] #List to store AI stats
        
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
        for depth, count in sorted(self.states_by_depth.items()): #sort by depth level (keys -> depth level | values -> nb states explored), .items() will return K-V pairs from dictionary 
            by_depth.append(f"{depth}={format_number(count)}")
        stats.append(f"Cumulative states explored by depth: {' '.join(by_depth)}")
        
        #Percentage by depth
        total = sum(self.states_by_depth.values()) #calculate total nb states explored
        if total > 0: #makes sure at least 1 state was explored
            percentages = []
            for depth, count in sorted(self.states_by_depth.items()): #iterate through states_by_depth in ascending order of depth levels
                if count > 0:  #Only include depth levels where states were explored
                    percentages.append(f"{depth}={count/total*100:.1f}%")
            stats.append(f"Cumulative % states explored by depth: {' '.join(percentages)}")
        
        #Average branching factor (Approximate: total nodes / non-leaf nodes)
        if total > 0:
            leaf_nodes = self.states_by_depth.get(max(self.states_by_depth.keys()), 0) #identify leaf nodes (deepest depth level in search tree)
            non_leaf_nodes = total - leaf_nodes #calculate non-leaf nodes (total nodes - deepest level nodes)
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
        #Unpack move into start and end positions
        start, end = move
        start_row, start_col = start
        end_row, end_col = end

        #Check if start/end position is within bounds
        if not (0 <= start_row < 5 and 0 <= start_col < 5):
            return False
        if not (0 <= end_row < 5 and 0 <= end_col < 5):
            return False

        #Identify piece at start/end pos
        piece = game_state["board"][start_row][start_col]
        target_piece = game_state["board"][end_row][end_col]

        #Check if start square has a piece
        if piece == '.':
            return False

        #Check if piece belongs to current player
        if piece[0] != game_state["turn"][0]: #'w' for white, 'b' for black
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
                            move = ((row, col), (end_row, end_col)) #Current pos to possible end pos

                            #If move valid, add to list
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
    def make_move(self, game_state, move, update_game=True, time_taken=None, heuristic_score=None, search_score=None):
        #Create deep copy of game state to not modify original (AI needs to evaluate potential moves without changing actual game state)
        if update_game:
            new_state = game_state #modify original state
        else:
            new_state = copy.deepcopy(game_state) #work on a copy
        
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

        #Store current player (for logs)
        current_player = new_state["turn"]

        #Switch turns/player
        previous_turn = new_state["turn"]
        new_state["turn"] = "black" if new_state["turn"] == "white" else "white"

        #Increment `turn_count` only after White & Black have played
        if update_game and previous_turn == "black": #black just moved, meaning full turn complete
            self.turn_count += 1

        if update_game:
            #Count pieces on the board to track game progression
            piece_count = sum(1 for row in new_state["board"] for cell in row if cell != '.')

            #Check if a King has been captured (winning condition)
            board_str = ''.join(''.join(row) for row in new_state["board"])
            if 'wK' not in board_str or 'bK' not in board_str: #If a king is missing
                winner = "Black" if 'wK' not in board_str else "White" #Determine winner
                
                #log winning move
                self.log_game_state(current_player, move, time_taken, heuristic_score, search_score)

                #Log & display win message
                with open(self.log_file, "a") as f:
                    f.write(f"{winner} Wins! In {self.turn_count} turns!\n")

                self.display_board(new_state) #Show final board state
                print(f"{winner} Wins! In {self.turn_count} turns!") #Print win message
                exit(0)

            #Check for draw condition (specified number of turns with no piece captured)
            if piece_count == self.last_piece_count:
                self.unchanged_turns += 1 #Increment unchanged turn counter if no piece captured
            else:
                self.unchanged_turns = 0 #Reset counter if piece was captured

            self.last_piece_count = piece_count #Store current piece count for next turn

            #If 10 full turns pass (20 turns) without capture -> draw
            if self.unchanged_turns >= 20:
                #Log move before declaring draw
                self.log_game_state(current_player, move, time_taken, heuristic_score, search_score)
                self.display_board(new_state)
                print(f"Game ends in a draw after 10 turns without piece capture!")
                with open(self.log_file, "a") as f:
                    f.write(f"Game ended in a draw after 10 full turns without piece capture.\n")
                exit(0)
            
            #If we've reached the maximum number of turns overall -> draw
            if self.turn_count > self.max_turns and current_player == "black": #only check AFTER black has moved on final turn
                #Log move before declaring draw
                self.log_game_state(current_player, move, time_taken, heuristic_score, search_score)
                self.display_board(new_state)
                print(f"Game ends in a draw after reaching maximum {self.max_turns} turns!")
                with open(self.log_file, "a") as f:
                    f.write(f"Game ended in a draw after reaching maximum {self.max_turns} turns.\n")
                exit(0)

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
          positive score favors White, negative score favors Black
        """
        #Initialize scores for White and Black
        white_score = 0
        black_score = 0

        #Loop through every row of the board
        for row in game_state["board"]:
            for cell in row: #Iterate through each cell in the row
                #Evaluate White pieces
                if cell == 'wp': #White Pawn
                    white_score += 1
                elif cell == 'wB': #White Bishop
                    white_score += 3
                elif cell == 'wN': #White Knight
                    white_score += 3
                elif cell == 'wQ': #White Queen
                    white_score += 9
                elif cell == 'wK': #White King
                    white_score += 999

                #Evaluate Black pieces
                elif cell == 'bp': #Black Pawn
                    black_score += 1
                elif cell == 'bB': #Black Bishop
                    black_score += 3
                elif cell == 'bN': #Black Knight
                    black_score += 3
                elif cell == 'bQ': #Black Queen
                    black_score += 9
                elif cell == 'bK': #Black King
                    black_score += 999

        #Compute heuristic value
        return white_score - black_score
    
    def heuristic_e1(self, game_state):
        """
        Advanced heuristic e1: Base material values (same as e0) + positional bonuses:
        - Pawns get bonus for advancement toward promotion
        - Knights and Bishops get bonus for central positions
        - Queens get bonus for mobility (number of valid moves)
        - Penalize pieces that are under attack
        """
        #Base material values (same as e0)
        material_score = self.heuristic_e0(game_state)
        
        #Position & mobility score
        positional_score = 0
        
        #Get all attacked positions on board
        attacks = self.get_attacked_positions(game_state)
        
        #Evaluate each piece's positional advantage or disadvantage
        for row in range(5):
            for col in range(5):
                piece = game_state["board"][row][col]
                if piece == '.': #skip empty squares
                    continue
                
                color = piece[0]  #'w' or 'b'
                piece_type = piece[1]  #'p', 'N', 'B', 'Q', 'K'
                multiplier = 1 if color == 'w' else -1 #positive for white, negative for black
                
                #Pawn advancement bonus (closer to promotion = better)
                if piece_type == 'p':
                    if color == 'w':
                        #White pawns move upward, row 0 is best
                        advancement_bonus = (4 - row) * 0.2
                    else:
                        #Black pawns move downward, row 4 is best
                        advancement_bonus = row * 0.2
                    positional_score += advancement_bonus * multiplier
                
                #Center control bonus for Knights and Bishops
                if piece_type in ['N', 'B']:
                    #Manhattan distance from center (2,2)
                    center_distance = abs(row - 2) + abs(col - 2)
                    center_bonus = (4 - center_distance) * 0.15 #Closer to center = higher bonus
                    positional_score += center_bonus * multiplier
                
                #Mobility bonus for Queens (higher mobility = stronger position)
                if piece_type == 'Q':
                    #Temp switch turn to calculate Queen's possible moves
                    original_turn = game_state["turn"]
                    temp_state = copy.deepcopy(game_state)
                    temp_state["turn"] = color #set turn to queen's color
                    
                    queen_moves = 0
                    #count nb of valid moves the Queen can make
                    for end_row in range(5):
                        for end_col in range(5):
                            move = ((row, col), (end_row, end_col))
                            if self.is_valid_move(temp_state, move):
                                queen_moves += 1
                    
                    mobility_bonus = queen_moves * 0.1 #reward for having more available moves
                    positional_score += mobility_bonus * multiplier
                
                #Penalty for being under attack
                position = (row, col)
                if position in attacks: #if this position is under attack
                    attackers = attacks[position]
                    for attacker in attackers:
                        attacker_piece = game_state["board"][attacker[0]][attacker[1]]
                        #If attacker belongs to opponent
                        if attacker_piece[0] != color:
                            piece_value = 1 if piece_type == 'p' else 3 if piece_type in ['N', 'B'] else 9 if piece_type == 'Q' else 20
                            attack_penalty = piece_value * 0.15 #Higher penalty for more valuable pieces
                            positional_score -= attack_penalty * multiplier
        
        #combine material and positional scores
        return material_score + positional_score

    def heuristic_e2(self, game_state):
        """
        Advanced heuristic e2: Builds on e1 and adds strategic factors:
        - King safety (penalize exposed kings)
        - Piece coordination (bonus for pieces protecting each other)
        - Pawn structure (bonus for connected pawns)
        - Control of central squares
        - Bonus for having the initiative (having the move is an advantage)
        """
        #Start with e1 evaluation (material, position, mobility bonuses)
        base_score = self.heuristic_e1(game_state)
        
        #Additional strategic considerations
        strategic_score = 0
        
        #Get all attacks and defenses
        attacks = self.get_attacked_positions(game_state)
        defenses = self.get_defended_positions(game_state)
        
        # ------------------------------------ 1. Central Control Bonus --------------------------------------
        central_squares = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3), (3, 1), (3, 2), (3, 3)]
        white_central_control = 0
        black_central_control = 0
        
        #Evaluate control over central squares
        for square in central_squares:
            row, col = square
            #Count attackers of each color for this square
            white_attackers = sum(1 for pos in attacks.get(square, []) if game_state["board"][pos[0]][pos[1]][0] == 'w')
            black_attackers = sum(1 for pos in attacks.get(square, []) if game_state["board"][pos[0]][pos[1]][0] == 'b')
            
            #Award points for controlling central squares for the side with more attackers
            if white_attackers > black_attackers:
                white_central_control += 0.15
            elif black_attackers > white_attackers:
                black_central_control += 0.15
        
        strategic_score += white_central_control - black_central_control
        
        # --------------------------------------- 2. King Safety ---------------------------------------------
        for row in range(5):
            for col in range(5):
                piece = game_state["board"][row][col]
                if piece == '.':
                    continue
                
                color = piece[0]  #'w' or 'b'
                piece_type = piece[1]  #'p', 'N', 'B', 'Q', 'K'
                multiplier = 1 if color == 'w' else -1
                position = (row, col)
                
                #King safety: Penalize kings that are under attack
                if piece_type == 'K':
                    #Count attacks near the king
                    king_zone = []
                    for r in range(max(0, row-1), min(5, row+2)):
                        for c in range(max(0, col-1), min(5, col+2)):
                            king_zone.append((r, c))
                    
                    #Count enemy attacks in king zone
                    enemy_attacks = 0
                    for zone_pos in king_zone:
                        if zone_pos in attacks:
                            for attacker_pos in attacks[zone_pos]:
                                attacker = game_state["board"][attacker_pos[0]][attacker_pos[1]]
                                if attacker[0] != color:
                                    enemy_attacks += 1
                    
                    #Higher penalty for more enemy attacks near the king
                    king_safety_penalty = enemy_attacks * 0.2
                    strategic_score -= king_safety_penalty * multiplier
                
                # ------------------ 3. Piece Coordination (Defended Pieces Bonus) ---------------------------
                if position in defenses:
                    defenders = defenses[position] #get list of pieces defending this position
                    friendly_defenders = sum(1 for def_pos in defenders if game_state["board"][def_pos[0]][def_pos[1]][0] == color)
                    coordination_bonus = friendly_defenders * 0.1
                    strategic_score += coordination_bonus * multiplier
                
                # -------------------- 4. Pawn Structure (Connected Pawns Bonus) -----------------------------
                if piece_type == 'p':
                    #Check for adjacent pawns of same color
                    adjacent_pawns = 0
                    for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                        r, c = row + dr, col + dc
                        if 0 <= r < 5 and 0 <= c < 5:
                            adj_piece = game_state["board"][r][c]
                            if adj_piece != '.' and adj_piece[0] == color and adj_piece[1] == 'p':
                                adjacent_pawns += 1
                    
                    pawn_structure_bonus = adjacent_pawns * 0.15
                    strategic_score += pawn_structure_bonus * multiplier
        
        # -------------------- 5. Initiative Bonus (Having the Move) -----------------------------
        if game_state["turn"] == 'white':
            strategic_score += 0.1
        else:
            strategic_score -= 0.1
        
        return base_score + strategic_score

    def get_attacked_positions(self, game_state):
        """
        Helper method: find all positions that are under attack
        Returns dictionary mapping positions to lists of attacker positions {Keys -> Attacked positions | Values -> list of attacker positions}
        """
        attacks = {}
        
        #Temp set turn to white to check white attacks
        temp_state = copy.deepcopy(game_state)
        temp_state["turn"] = "white"
        
        #Loop through every board square (white only)
        for row in range(5):
            for col in range(5):
                piece = game_state["board"][row][col]
                if piece != '.' and piece[0] == 'w':
                    #test all possible moves for white
                    for end_row in range(5):
                        for end_col in range(5):
                            move = ((row, col), (end_row, end_col))
                            #if move is valid
                            if self.is_valid_move(temp_state, move):
                                attacked_pos = (end_row, end_col) #store attacked position
                                if attacked_pos not in attacks:
                                    attacks[attacked_pos] = []
                                attacks[attacked_pos].append((row, col)) #store attacker position
        
        #Temp set turn to black to check black attacks
        temp_state["turn"] = "black"
        
        #Loop through every board square (black only)
        for row in range(5):
            for col in range(5):
                piece = game_state["board"][row][col]
                if piece != '.' and piece[0] == 'b':
                    #test all possible moves for black
                    for end_row in range(5):
                        for end_col in range(5):
                            move = ((row, col), (end_row, end_col))
                            #if move is valid
                            if self.is_valid_move(temp_state, move):
                                attacked_pos = (end_row, end_col) #store attacked position
                                if attacked_pos not in attacks:
                                    attacks[attacked_pos] = []
                                attacks[attacked_pos].append((row, col)) #store attacker position
        
        return attacks

    def get_defended_positions(self, game_state):
        """
        Helper method: find all positions that are defended by friendly pieces
        Returns dictionary mapping positions to lists of defender positions
        """
        defenses = {}
        attacks = self.get_attacked_positions(game_state) #find all positions that are under attack (helps determine if piece is attacked by a friendly piece (defended))
        
        #Check if pieces are defended (attacked by friendly pieces)
        for row in range(5):
            for col in range(5):
                piece = game_state["board"][row][col]
                if piece == '.':
                    continue
                
                color = piece[0]
                position = (row, col)
                
                #identify friendly defenders
                if position in attacks:
                    defenders = []
                    for attacker_pos in attacks[position]:
                        attacker = game_state["board"][attacker_pos[0]][attacker_pos[1]]
                        if attacker[0] == color: #Same color = defender
                            defenders.append(attacker_pos)
                    
                    #Store defended pieces
                    if defenders:
                        defenses[position] = defenders
        
        return defenses

    def play(self):
        print(f"\nWelcome to Mini Chess! Game mode: {self.mode}")
        
        #Continue until max turns reached or game ends (win/draw) | Allow game to continue through the FULL final turn
        while self.turn_count <= self.max_turns or (self.turn_count == self.max_turns + 1 and self.current_game_state["turn"] == "white"):
            #Display board & current turn
            self.display_board(self.current_game_state)
            current_player = self.current_game_state["turn"]
            print(f"{current_player.capitalize()}'s turn ({self.turn_count}/{self.max_turns})")
            
            #Determine if current player is human or AI
            is_ai_turn = (current_player == "white" and self.player1_type == "AI") or (current_player == "black" and self.player2_type == "AI")
            
            if is_ai_turn:
                #AI's turn: use AIP to generate move
                ai_player = AI(self, self.heuristic_func)
                print(f"AI thinking (max {self.timeout} seconds)...")
                move, search_score, time_taken, explored, states_by_depth = ai_player.get_move(self.current_game_state) #AI chosen move, Minimax or A-B evaluation, time AI took to decide, states AI analyzed, search breakdown per depth
                
                #Update AI stats (how many states AI analyzed & update dictionary)
                self.states_explored += explored
                for depth, count in states_by_depth.items():
                    self.states_by_depth[depth] += count
                
                #Calculate heuristic score for logging
                heuristic_score = self.heuristic_func(self.current_game_state)
                
                #Display AI chosen move
                print(f"AI chooses: {chr(move[0][1] + ord('A'))}{5 - move[0][0]} to {chr(move[1][1] + ord('A'))}{5 - move[1][0]}")
                
                #Make the move and log with AI stats
                new_state = copy.deepcopy(self.current_game_state)
                self.current_game_state = self.make_move(new_state, move, True, time_taken, heuristic_score, search_score)
                #Only log here if game isn't going to end (since make_move handles logging for end conditions)
                if self.turn_count <= self.max_turns or (self.current_game_state["turn"] != "white"):
                    self.log_game_state(current_player, move, time_taken, heuristic_score, search_score)
                
            else:
                #Human's turn: get input from console
                while True:
                    #user input
                    move_input = input("Enter your move (e.g., 'B2 B3') or 'exit' to quit: ")
                    
                    if move_input.lower() == 'exit':
                        print("Game exited.")
                        exit(1)
                    
                    #converts input to a move
                    move = self.parse_input(move_input)
                    if not move:
                        with open(self.log_file, "a") as f:
                            f.write(f"Invalid input format by {current_player.capitalize()}: '{move_input}'\n\n")
                        print("Invalid format. Please use format like 'B2 B3'.")
                        continue
                    
                    #check if move is legal
                    if not self.is_valid_move(self.current_game_state, move):
                        with open(self.log_file, "a") as f:
                            f.write(f"Invalid move attempt by {current_player.capitalize()}: '{move_input}'\n\n")
                        print("Invalid move. Try again.")
                        continue
                    
                    #Make the move
                    new_state = copy.deepcopy(self.current_game_state)
                    self.current_game_state = self.make_move(new_state, move)
                    
                    #Only log here if game isn't going to end (since make_move handles logging for end conditions)
                    if self.turn_count <= self.max_turns or (self.current_game_state["turn"] != "white"):
                        self.log_game_state(current_player, move)
                    break
            
        #Check if max turns reached
        self.display_board(self.current_game_state)
        print(f"Game ended after {self.max_turns} turns. It's a draw!")
        with open(self.log_file, "a") as f:
            f.write(f"Game ended in a draw after reaching maximum turns ({self.max_turns}).\n")

if __name__ == "__main__":
    game = MiniChess()
    game.play()