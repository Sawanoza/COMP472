import copy
import time

class AIPlayer:
    def __init__(self, game, heuristic_function, max_depth=3):
        """
        :param game: The MiniChess instance (provides valid_moves, make_move, etc.)
        :param heuristic_function: e0, e1, e2
        :param max_depth: Depth limit for minimax
        :param use_alpha_beta: Boolean to switch between minimax or alpha-beta
        :param max_time: Time limit (seconds) for the AI move
        """
        self.game = game
        self.heuristic = heuristic_function
        self.max_depth = max_depth
        self.use_alpha_beta = game.use_alpha_beta
        self.max_time = game.timeout

        self.states_explored = 0
        # Count how many states visited at each depth
        self.states_by_depth = {i: 0 for i in range(1, max_depth + 1)}
        self.start_time = 0

    def get_move(self, game_state):
        """
        Returns best move AI can find within max_depth or max_time.
        :return: (best_move, best_score, elapsed_time, total_states_explored, states_by_depth)
        """
        self.start_time = time.time()
        self.states_explored = 0
        self.states_by_depth = {i: 0 for i in range(1, self.max_depth + 1)}

        is_maximizing = (game_state["turn"] == "white")

        if self.use_alpha_beta:
            best_score, best_move = self.alpha_beta(game_state, 0, float('-inf'), float('inf'), is_maximizing)
        else:
            best_score, best_move = self.minimax(game_state, 0, is_maximizing)

        elapsed = time.time() - self.start_time
        if best_move is None:
            # Fallback if no valid moves
            valid = self.game.valid_moves(game_state)
            if valid:
                best_move = valid[0]
                best_score = self.heuristic(game_state)

        return best_move, best_score, elapsed, self.states_explored, self.states_by_depth

    def minimax(self, game_state, depth, is_maximizing):
        """
        Basic minimax without alpha-beta pruning
        :return: (score, move)
        """
        self.states_explored += 1
        if depth < self.max_depth:
            self.states_by_depth[depth + 1] += 1

        # Check time limit
        if (time.time() - self.start_time) >= self.max_time:
            return self.heuristic(game_state), None

        if depth == self.max_depth:
            return self.heuristic(game_state), None

        moves = self.game.valid_moves(game_state)
        if not moves:
            # No moves -> evaluate directly
            return self.heuristic(game_state), None

        best_move = None
        if is_maximizing:
            best_score = float('-inf')
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False)
                score, _ = self.minimax(new_state, depth + 1, False)
                if score > best_score:
                    best_score = score
                    best_move = m
            return best_score, best_move
        else:
            best_score = float('inf')
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False)
                score, _ = self.minimax(new_state, depth + 1, True)
                if score < best_score:
                    best_score = score
                    best_move = m
            return best_score, best_move

    def alpha_beta(self, game_state, depth, alpha, beta, is_maximizing):
        """
        Minimax with alpha-beta pruning
        :return: (score, move)
        """
        self.states_explored += 1
        if depth < self.max_depth:
            self.states_by_depth[depth + 1] += 1

        # Check time limit
        if (time.time() - self.start_time) >= self.max_time:
            return self.heuristic(game_state), None

        if depth == self.max_depth:
            return self.heuristic(game_state), None

        moves = self.game.valid_moves(game_state)
        if not moves:
            return self.heuristic(game_state), None

        best_move = None

        if is_maximizing:
            value = float('-inf')
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False)
                score, _ = self.alpha_beta(new_state, depth + 1, alpha, beta, False)
                if score > value:
                    value = score
                    best_move = m
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value, best_move
        else:
            value = float('inf')
            for m in moves:
                if (time.time() - self.start_time) >= self.max_time:
                    break
                new_state = self.game.make_move(game_state, m, update_game=False)
                score, _ = self.alpha_beta(new_state, depth + 1, alpha, beta, True)
                if score < value:
                    value = score
                    best_move = m
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value, best_move
