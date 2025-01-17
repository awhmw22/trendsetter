import tkinter as tk
from tkinter import ttk  # For themed widgets
import chess
import random
import pygame
import os

# Initialize pygame mixer for sound effects
pygame.mixer.init()

# Sound file paths
sound_files = {
    "move": "D:/My Games/sounds/move.mp3",
    "capture": "D:/My Games/sounds/capture.mp3",
    "check": "D:/My Games/sounds/move-check.mp3",
    "game_over": "D:/My Games/sounds/game-end.mp3",
    "promote": "D:/My Games/sounds/promote.mp3",
    "checkmate": "D:/My Games/sounds/checkmate.mp3",
    "win": "D:/My Games/sounds/game-win-long.mp3",
    "lose": "D:/My Games/sounds/game-lose.mp3"
}

sounds = {}
for key, filename in sound_files.items():
    try:
        if os.path.exists(filename):
            sounds[key] = pygame.mixer.Sound(filename)
        else:
            print(f"Warning: Sound file '{filename}' not found. Sound '{key}' will be disabled.")
    except Exception as e:
        print(f"Error loading sound '{filename}': {e}")

def play_sound(sound_key):
    """Play a sound if available."""
    try:
        if sound_key in sounds:
            sounds[sound_key].play()
    except Exception as e:
        print(f"Error playing sound for '{sound_key}': {e}")

# Global chess board
board = chess.Board()

def evaluate_board(board):
    piece_values = {
        chess.PAWN: 1,
        chess.KNIGHT: 3,
        chess.BISHOP: 3,
        chess.ROOK: 5,
        chess.QUEEN: 9,
        chess.KING: 0
    }
    score = 0
    for piece_type, val in piece_values.items():
        score += len(board.pieces(piece_type, chess.WHITE)) * val
        score -= len(board.pieces(piece_type, chess.BLACK)) * val
    return score

def minimax(board, depth, is_maximizing, alpha=float('-inf'), beta=float('inf')):
    """Simple minimax with alpha-beta pruning."""
    if depth == 0 or board.is_game_over():
        return evaluate_board(board)
    legal_moves = list(board.legal_moves)
    if is_maximizing:
        best_eval = float('-inf')
        for move in legal_moves:
            board.push(move)
            evaluation = minimax(board, depth - 1, False, alpha, beta)
            board.pop()
            best_eval = max(best_eval, evaluation)
            alpha = max(alpha, evaluation)
            if beta <= alpha:
                break
        return best_eval
    else:
        best_eval = float('inf')
        for move in legal_moves:
            board.push(move)
            evaluation = minimax(board, depth - 1, True, alpha, beta)
            board.pop()
            best_eval = min(best_eval, evaluation)
            beta = min(beta, evaluation)
            if beta <= alpha:
                break
        return best_eval

class ChessGUI:
    def __init__(self, root, player_color, ai_level):
        self.root = root
        self.root.title("Chess Game")
        self.player_color = player_color
        self.ai_level = ai_level

        # Configure ttk style and hover effect
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", font=("Arial", 14), padding=6)
        style.map("Hover.TButton",
                  background=[('active', '#A9A9A9')],
                  foreground=[('active', 'black')])

        # Main frame
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Canvas for board
        self.board_canvas = tk.Canvas(self.main_frame, bg="#F0D9B5")
        self.board_canvas.grid(row=0, column=0, columnspan=2, sticky="nsew")

        # Make canvas fill window
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # Undo button
        self.undo_button = ttk.Button(self.main_frame, text="Undo", command=self.undo_move, style="TButton")
        self.undo_button.grid(row=1, column=0, pady=10)
        self.add_hover_effect(self.undo_button)

        self.selected_square = None
        self.valid_moves = []

        self.piece_symbols = {
            'P': '♙', 'R': '♖', 'N': '♘', 'B': '♗', 'Q': '♕', 'K': '♔',
            'p': '♟', 'r': '♜', 'n': '♞', 'b': '♝', 'q': '♛', 'k': '♚'
        }

        self.board_canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Configure>", lambda e: self.on_resize())

        self.draw_board()
        self.update_pieces()

        # If player is Black, let AI make the first move after a delay (if you want)
        if self.player_color == chess.BLACK:
            self.root.after(1000, self.delayed_ai_move)

    def on_resize(self):
        """Redraw board and pieces on window resize."""
        self.draw_board()
        self.update_pieces()

    def get_square_size(self):
        """Compute the dynamic size of each square based on current canvas dimensions."""
        width = self.board_canvas.winfo_width()
        height = self.board_canvas.winfo_height()
        return min(width, height) / 8

    def add_hover_effect(self, widget):
        """Add a simple hover effect to a ttk button."""
        def on_enter(e): widget.configure(style="Hover.TButton")
        def on_leave(e): widget.configure(style="TButton")
        widget.bind("<Enter>", on_enter)
        widget.bind("<Leave>", on_leave)

    def draw_board(self):
        """Draw the empty squares of the board."""
        square_size = self.get_square_size()
        colors = ["#F0D9B5", "#B58863"]
        self.board_canvas.delete("square")
        for row in range(8):
            for col in range(8):
                color = colors[(row + col) % 2]
                x1, y1 = col * square_size, row * square_size
                x2, y2 = x1 + square_size, y1 + square_size
                self.board_canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="square")

    def update_pieces(self):
        """Place or re-place the pieces on the board with correct orientation."""
        square_size = self.get_square_size()
        self.board_canvas.delete("piece", "highlight", "dot", "check_msg")

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                # --- KEY CHANGE: Flip columns for BLACK to match on_click flipping ---
                if self.player_color == chess.WHITE:
                    col = chess.square_file(square)
                    row = 7 - chess.square_rank(square)
                else:
                    col = 7 - chess.square_file(square)
                    row = chess.square_rank(square)
                # ---------------------------------------------------------------------

                x = col * square_size + square_size / 2
                y = row * square_size + square_size / 2
                self.board_canvas.create_text(
                    x, y,
                    text=self.piece_symbols[piece.symbol()],
                    font=("Arial", int(square_size * 0.8)),
                    tags="piece"
                )

        # Highlight selected square if any
        if self.selected_square is not None:
            if self.player_color == chess.WHITE:
                col = chess.square_file(self.selected_square)
                row = 7 - chess.square_rank(self.selected_square)
            else:
                col = 7 - chess.square_file(self.selected_square)
                row = chess.square_rank(self.selected_square)
            x1 = col * square_size
            y1 = row * square_size
            x2 = x1 + square_size
            y2 = y1 + square_size
            self.board_canvas.create_rectangle(x1, y1, x2, y2, outline="blue", width=3, tags="highlight")

        # Mark valid moves
        for move in self.valid_moves:
            if self.player_color == chess.WHITE:
                col = chess.square_file(move.to_square)
                row = 7 - chess.square_rank(move.to_square)
            else:
                col = 7 - chess.square_file(move.to_square)
                row = chess.square_rank(move.to_square)
            x = col * square_size + square_size / 2
            y = row * square_size + square_size / 2
            self.board_canvas.create_oval(
                x - square_size * 0.15,
                y - square_size * 0.15,
                x + square_size * 0.15,
                y + square_size * 0.15,
                fill="green", tags="dot"
            )

        # Show "Check!" if king is in check
        if board.is_check():
            self.board_canvas.create_text(
                self.board_canvas.winfo_width() / 2,
                20,
                text="Check!",
                fill="red",
                font=("Arial", 24, "bold"),
                tags="check_msg"
            )

    def on_click(self, event):
        """Handle user click on the board to select/move pieces."""
        square_size = self.get_square_size()

        if self.player_color == chess.WHITE:
            col_clicked = int(event.x // square_size)
            row_clicked = 7 - int(event.y // square_size)
            clicked_square = chess.square(col_clicked, row_clicked)
        else:
            col_clicked = 7 - int(event.x // square_size)
            row_clicked = int(event.y // square_size)
            clicked_square = chess.square(col_clicked, row_clicked)

        if self.selected_square is None:
            # Select a piece if it belongs to the current player
            piece = board.piece_at(clicked_square)
            if piece and piece.color == board.turn == self.player_color:
                self.selected_square = clicked_square
                self.valid_moves = [
                    m for m in board.legal_moves if m.from_square == clicked_square
                ]
                self.update_pieces()
        else:
            # Attempt to make a move
            possible_promotions = [
                m for m in board.legal_moves
                if m.from_square == self.selected_square and
                   m.to_square == clicked_square and
                   m.promotion
            ]
            if possible_promotions:
                # Show promotion dialog
                self.show_promotion_dialog(possible_promotions[0])
            else:
                move = chess.Move(self.selected_square, clicked_square)
                if move in board.legal_moves:
                    if board.is_capture(move):
                        play_sound("capture")
                    else:
                        play_sound("move")
                    board.push(move)
                    self.finish_player_move()
                else:
                    # Invalid move
                    self.selected_square = None
                    self.valid_moves = []
                    self.update_pieces()
                    return

            self.selected_square = None
            self.valid_moves = []
            self.update_pieces()

    def show_promotion_dialog(self, move):
        """Show a dialog to choose promotion piece."""
        promotion_window = tk.Toplevel(self.root)
        promotion_window.title("Pawn Promotion")
        ttk.Label(promotion_window, text="Promote your pawn to:", font=("Arial", 14)).pack(padx=10, pady=5)

        def promote_to(piece_type):
            promotion_move = chess.Move(move.from_square, move.to_square, promotion=piece_type)
            if promotion_move in board.legal_moves:
                play_sound("promote")
                board.push(promotion_move)
                self.finish_player_move()
            promotion_window.destroy()
            self.update_pieces()

        for piece_name, piece_type in [
            ("Queen ♕", chess.QUEEN),
            ("Rook ♖", chess.ROOK),
            ("Bishop ♗", chess.BISHOP),
            ("Knight ♘", chess.KNIGHT)
        ]:
            btn = ttk.Button(promotion_window, text=piece_name, command=lambda pt=piece_type: promote_to(pt))
            btn.pack(padx=10, pady=5)
            self.add_hover_effect(btn)

        promotion_window.grab_set()
        promotion_window.lift()

    def finish_player_move(self):
        """Update the board after a player move. Check game state, then AI moves if needed."""
        self.update_pieces()
        if board.is_game_over():
            self.handle_game_over()
        else:
            self.root.after(1000, self.delayed_ai_move)

    def delayed_ai_move(self):
        """A small delay before the AI makes a move."""
        self.make_ai_move()

    def make_ai_move(self):
        """Have the AI make a move based on chosen difficulty."""
        if board.is_game_over():
            self.handle_game_over()
            return

        if self.ai_level == "Beginner":
            move = self.get_best_move(1)
        else:
            move = self.get_best_move(5)

        if move is None:
            self.handle_game_over()
            return

        if board.is_capture(move):
            play_sound("capture")
        else:
            play_sound("move")

        board.push(move)
        self.update_pieces()
        if board.is_game_over():
            self.handle_game_over()

    def handle_game_over(self):
        """Play game-over sounds and display a final message."""
        if board.is_checkmate():
            play_sound("checkmate")
        else:
            play_sound("game_over")

        if board.is_checkmate():
            msg = "You lost! Checkmate." if board.turn == self.player_color else "You won! Checkmate."
        elif board.is_stalemate():
            msg = "Draw by stalemate!"
        else:
            msg = "Game over!"
        self.display_message(msg)

    def get_best_move(self, depth):
        """Get the best move using minimax at the given depth."""
        best_move = None
        if board.turn == chess.WHITE:
            best_eval = float('-inf')
        else:
            best_eval = float('inf')

        for move in board.legal_moves:
            board.push(move)
            eval_score = minimax(board, depth - 1, not board.turn)
            board.pop()

            if board.turn == chess.WHITE and eval_score > best_eval:
                best_eval = eval_score
                best_move = move
            elif board.turn == chess.BLACK and eval_score < best_eval:
                best_eval = eval_score
                best_move = move

        return best_move

    def display_message(self, text):
        """Show a message box for game-over or other announcements."""
        msg_box = tk.Toplevel(self.root)
        msg_box.title("Game Over")
        label = ttk.Label(msg_box, text=text, font=("Arial", 18), padding=20)
        label.pack()
        ok_button = ttk.Button(msg_box, text="OK", command=lambda: [msg_box.destroy(), self.root.destroy()])
        ok_button.pack(pady=10)
        self.add_hover_effect(ok_button)

    def undo_move(self):
        """Undo the last two moves (player and AI) with move sound."""
        if len(board.move_stack) > 0:
            board.pop()
            play_sound("move")
        if len(board.move_stack) > 0:
            board.pop()
            play_sound("move")

        self.selected_square = None
        self.valid_moves = []
        self.update_pieces()

def choose_color_and_level():
    """Display a small menu to pick color and difficulty level."""
    color_choice = tk.Tk()
    color_choice.title("Choose Your Color and Level")
    ttk.Label(color_choice, text="Choose your color and AI level:", font=("Arial", 16)).pack(pady=10)
    frame = ttk.Frame(color_choice, padding="20")
    frame.pack()

    button_opts = {"width": 20, "style": "TButton"}

    style = ttk.Style()
    style.theme_use('clam')
    style.configure("TButton", font=("Arial", 14), padding=6)
    style.map("Hover.TButton",
              background=[('active', '#A9A9A9')],
              foreground=[('active', 'black')])

    def start_game(color, level):
        color_choice.destroy()
        root = tk.Tk()
        ChessGUI(root, color, level)
        root.mainloop()

    btn1 = ttk.Button(frame, text="White (Beginner)", **button_opts,
                      command=lambda: start_game(chess.WHITE, "Beginner"))
    btn2 = ttk.Button(frame, text="White (Pro)", **button_opts,
                      command=lambda: start_game(chess.WHITE, "Pro"))
    btn3 = ttk.Button(frame, text="Black (Beginner)", **button_opts,
                      command=lambda: start_game(chess.BLACK, "Beginner"))
    btn4 = ttk.Button(frame, text="Black (Pro)", **button_opts,
                      command=lambda: start_game(chess.BLACK, "Pro"))

    btn1.grid(row=0, column=0, padx=10, pady=5)
    btn2.grid(row=1, column=0, padx=10, pady=5)
    btn3.grid(row=0, column=1, padx=10, pady=5)
    btn4.grid(row=1, column=1, padx=10, pady=5)

    for btn in (btn1, btn2, btn3, btn4):
        ChessGUI.add_hover_effect(None, btn)

    color_choice.mainloop()

if __name__ == "__main__":
    choose_color_and_level()
