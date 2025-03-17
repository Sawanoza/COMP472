import time

class AIPlayer:
    ###Initialize the AI player
    def __init__(self, game, heuristic_function, max_depth=3):
        self.game = game #store minichess instance to access game-related functions
        self.heuristic = heuristic_function #stores selected heuristic function for move evaluation
        self.max_depth = max_depth #limits how deep AI searches
        self.use_alpha_beta = game.use_alpha_beta #determine AI search strategy (True -> Alpha-Beta Pruning | False -> Regular Minimax)
        self.max_time = game.timeout #AI move timeout

        self.states_explored = 0 #Keep count of how many game states AI analyzes
        self.states_by_depth = {i: 0 for i in range(1, max_depth + 1)} #Dictionary stores how many nodes were explored at each depth (ex: depth 3 = {1: 0, 2: 0, 3: 0})
        self.start_time = 0 #store when AI starts thinking

    ###Determines best move AI can find within the search depth and time limit
    def get_move(self, game_state):
        self.start_time = time.time() #Records start time to track execution time
        self.states_explored = 0 #total states analyzed
        self.states_by_depth = {i: 0 for i in range(1, self.max_depth + 1)} #tracks search depth stats

        is_maximizing = (game_state["turn"] == "white") #if white playing -> AI maximizes (True) | if black playing -> AI minimizes (False)

        #Selects search algorithm (Alpha-Beta Pruning or Regular Minimax)
        if self.use_alpha_beta:
            best_score, best_move = self.alpha_beta(game_state, 0, float('-inf'), float('inf'), is_maximizing) #pass current board pos, initial depth, alpha-beta boundaries, whether max or min
        else:
            best_score, best_move = self.minimax(game_state, 0, is_maximizing) #pass current board pos, initial depth, whether max or min

        #Compute total time taken for move selection
        elapsed = time.time() - self.start_time

        #Handle novalid move (failsafe)
        if best_move is None:
            #if no move was found, fallback to first valid move
            valid = self.game.valid_moves(game_state)
            if valid:
                best_move = valid[0] #pick first available move
                best_score = self.heuristic(game_state)

        return best_move, best_score, elapsed, self.states_explored, self.states_by_depth

    ###Determine best move using Minimax (Returns score, move)
    def minimax(self, game_state, depth, is_maximizing):
        #track explored states
        self.states_explored += 1 #increment state count for AI stats
        if depth < self.max_depth:
            self.states_by_depth[depth + 1] += 1 #records how many states explored at each depth

        #Check time limit
        if (time.time() - self.start_time) >= self.max_time:
            return self.heuristic(game_state), None

        #Check depth limit (stop searching deeper than max_depth)
        if depth == self.max_depth:
            return self.heuristic(game_state), None

        #Get all possible moves
        moves = self.game.valid_moves(game_state) #retrieve all legal moves
        if not moves: #if no moves -> evaluate directly
            return self.heuristic(game_state), None

        #Maximizing player (white)
        best_move = None
        if is_maximizing:
            best_score = float('-inf') #start with lowest possible score
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False) #simulate move
                score, _ = self.minimax(new_state, depth + 1, False) #repeat (recursive) with minimizing player
                if score > best_score:
                    best_score = score
                    best_move = m #update best move
            return best_score, best_move
        else: #Minimizing player (black)
            best_score = float('inf') #Start with highest possible score
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False) #simulate move
                score, _ = self.minimax(new_state, depth + 1, True) #repeat (recursive) with maximizing player
                if score < best_score:
                    best_score = score
                    best_move = m #update best move
            return best_score, best_move

    ###Determine best move using Alpha-Beta Pruning
    def alpha_beta(self, game_state, depth, alpha, beta, is_maximizing):
        #track explored states
        self.states_explored += 1 #increment state count for AI stats
        if depth < self.max_depth:
            self.states_by_depth[depth + 1] += 1 #records how many states explored at each depth

        #Check time limit
        if (time.time() - self.start_time) >= self.max_time:
            return self.heuristic(game_state), None

        #Check depth limit
        if depth == self.max_depth:
            return self.heuristic(game_state), None

        #Get all possible moves
        moves = self.game.valid_moves(game_state) #retrieve all legal moves
        if not moves: #if no moves -> evaluate directly
            return self.heuristic(game_state), None

        best_move = None

        #Maximizing player (White)
        if is_maximizing:
            value = float('-inf') #start with lowest possible score
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False) #simulate move
                score, _ = self.alpha_beta(new_state, depth + 1, alpha, beta, False) #repeat (recursive) with minimizing player
                if score > value:
                    value = score
                    best_move = m #Update best move
                alpha = max(alpha, value) #update alpha
                if alpha >= beta: #prune remaining branches
                    break
            return value, best_move
        else: #Minimizing player (Black)
            value = float('inf') #start with highest possible score
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False) #simulate move
                score, _ = self.alpha_beta(new_state, depth + 1, alpha, beta, True) #repeat (recursive) with maximizing player
                if score < value:
                    value = score
                    best_move = m #update best move
                beta = min(beta, value) #update beta
                if beta <= alpha: #prune remaining branches
                    break
            return value, best_move