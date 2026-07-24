import tkinter as tk
import random

COLORS = {
    0: ("#ccc0b3", "#776e65"),
    2: ("#eee4da", "#776e65"),
    4: ("#ede0c8", "#776e65"),
    8: ("#f2b179", "#f9f6f2"),
    16: ("#f59563", "#f9f6f2"),
    32: ("#f67c5f", "#f9f6f2"),
    64: ("#f65e3b", "#f9f6f2"),
    128: ("#edcf72", "#f9f6f2"),
    256: ("#edcc61", "#f9f6f2"),
    512: ("#edc850", "#f9f6f2"),
    1024: ("#edc53f", "#f9f6f2"),
    2048: ("#edc22e", "#f9f6f2")
}

def get_color(val):
    return COLORS.get(val, ("#3c3a32", "#f9f6f2"))

CELL_SIZE = 100
CELL_PAD = 10
ANIMATION_FRAMES = 10
ANIMATION_DUR = 150  # milliseconds

class Game2048:
    def __init__(self, root):
        self.root = root
        self.root.title("2048")
        self.root.configure(bg="#faf8ef")

        self.main_frame = tk.Frame(root, bg="#faf8ef")
        self.main_frame.pack(padx=20, pady=20)

        # Left Column: Game Board
        self.board_frame = tk.Frame(self.main_frame, bg="#bbada0", width=450, height=450)
        self.board_frame.grid(row=0, column=0, padx=10)
        self.board_frame.pack_propagate(False)

        self.canvas = tk.Canvas(self.board_frame, bg="#bbada0", width=450, height=450, highlightthickness=0)
        self.canvas.pack()

        # Right Column: Control Panel
        self.control_frame = tk.Frame(self.main_frame, bg="#faf8ef")
        self.control_frame.grid(row=0, column=1, sticky="n", padx=10)

        self.score = 0
        self.score_label = tk.Label(self.control_frame, text=f"Score\n{self.score}", font=("Helvetica", 24, "bold"), bg="#bbada0", fg="white", width=8, pady=10)
        self.score_label.pack(pady=20)

        self.restart_btn = tk.Button(self.control_frame, text="Restart", font=("Helvetica", 16, "bold"), bg="#8f7a66", fg="white", command=self.reset_game, relief="flat", padx=10, pady=5)
        self.restart_btn.pack(pady=10)

        self.board = [[0]*4 for _ in range(4)]
        self.animating = False

        self.root.bind("<Key>", self.key_pressed)

        self.reset_game()

        # Automation for testing
        self.auto_move_count = 5
        self.root.after(300, self.do_auto_move)

    def do_auto_move(self):
        if not self.root.winfo_exists(): return
        if self.auto_move_count > 0:
            moves = [
                ("Left", self.move_left),
                ("Right", self.move_right),
                ("Up", self.move_up),
                ("Down", self.move_down)
            ]
            random.shuffle(moves)
            for name, move in moves:
                if move(dry_run=True):
                    print(f"Auto-move: {name}")
                    move()
                    break
            self.auto_move_count -= 1
            if self.auto_move_count > 0:
                self.root.after(300 + ANIMATION_DUR, self.do_auto_move)
            else:
                print("Auto-moves completed. Handing over to user.")

    def draw_bg(self):
        self.canvas.delete("all")
        for r in range(4):
            for c in range(4):
                x = CELL_PAD + c * (CELL_SIZE + CELL_PAD)
                y = CELL_PAD + r * (CELL_SIZE + CELL_PAD)
                bg_color, _ = get_color(0)
                self.canvas.create_rectangle(x, y, x + CELL_SIZE, y + CELL_SIZE, fill=bg_color, outline="")

    def reset_game(self):
        if self.animating: return
        self.board = [[0]*4 for _ in range(4)]
        self.score = 0
        self.update_score()
        self.spawn_tile()
        self.spawn_tile()
        self.draw_board()

    def update_score(self):
        self.score_label.config(text=f"Score\n{self.score}")

    def spawn_tile(self):
        empty = [(r, c) for r in range(4) for c in range(4) if self.board[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.board[r][c] = 2 if random.random() < 0.9 else 4

    def draw_board(self):
        self.draw_bg()
        for r in range(4):
            for c in range(4):
                val = self.board[r][c]
                if val != 0:
                    self.create_tile(r, c, val)

    def create_tile(self, r, c, val):
        x = CELL_PAD + c * (CELL_SIZE + CELL_PAD)
        y = CELL_PAD + r * (CELL_SIZE + CELL_PAD)
        bg, fg = get_color(val)
        rect_id = self.canvas.create_rectangle(x, y, x + CELL_SIZE, y + CELL_SIZE, fill=bg, outline="")
        font_size = 36 if val < 1000 else 24
        text_id = self.canvas.create_text(x + CELL_SIZE/2, y + CELL_SIZE/2, text=str(val), font=("Helvetica", font_size, "bold"), fill=fg)
        return rect_id, text_id

    def key_pressed(self, event):
        if self.animating: return
        if self.auto_move_count > 0: return
        key = event.keysym.lower()
        if key in ["left", "a"]: self.move_left()
        elif key in ["right", "d"]: self.move_right()
        elif key in ["up", "w"]: self.move_up()
        elif key in ["down", "s"]: self.move_down()

    def generic_move(self, get_real_coords, dry_run=False):
        transitions = []
        score_diff = 0
        moved = False
        new_board = [[self.board[r][c] for c in range(4)] for r in range(4)]

        for i in range(4):
            new_line = [0, 0, 0, 0]
            merged_j = -1
            target_j = 0
            for j in range(4):
                r, c = get_real_coords(i, j)
                val = self.board[r][c]
                if val != 0:
                    if target_j > 0 and new_line[target_j - 1] == val and merged_j != target_j - 1:
                        dr, dc = get_real_coords(i, target_j - 1)
                        if not dry_run:
                            transitions.append({'val': val, 'sr': r, 'sc': c, 'dr': dr, 'dc': dc, 'merged': True})
                        new_line[target_j - 1] *= 2
                        score_diff += new_line[target_j - 1]
                        merged_j = target_j - 1
                        moved = True
                    else:
                        dr, dc = get_real_coords(i, target_j)
                        if not dry_run:
                            transitions.append({'val': val, 'sr': r, 'sc': c, 'dr': dr, 'dc': dc, 'merged': False})
                        new_line[target_j] = val
                        if target_j != j:
                            moved = True
                        target_j += 1
            if not dry_run:
                for j in range(4):
                    r, c = get_real_coords(i, j)
                    new_board[r][c] = new_line[j]

        if dry_run:
            return moved

        if moved:
            self.animate_transitions(transitions, new_board, score_diff)
        return moved

    def move_left(self, dry_run=False): return self.generic_move(lambda i, j: (i, j), dry_run)
    def move_right(self, dry_run=False): return self.generic_move(lambda i, j: (i, 3-j), dry_run)
    def move_up(self, dry_run=False): return self.generic_move(lambda i, j: (j, i), dry_run)
    def move_down(self, dry_run=False): return self.generic_move(lambda i, j: (3-j, i), dry_run)

    def animate_transitions(self, transitions, new_board, score_diff):
        self.animating = True
        self.draw_bg()

        moving_items = []
        for t in transitions:
            val = t['val']
            x1 = CELL_PAD + t['sc'] * (CELL_SIZE + CELL_PAD)
            y1 = CELL_PAD + t['sr'] * (CELL_SIZE + CELL_PAD)
            x2 = CELL_PAD + t['dc'] * (CELL_SIZE + CELL_PAD)
            y2 = CELL_PAD + t['dr'] * (CELL_SIZE + CELL_PAD)

            bg, fg = get_color(val)
            rect_id = self.canvas.create_rectangle(x1, y1, x1 + CELL_SIZE, y1 + CELL_SIZE, fill=bg, outline="")
            font_size = 36 if val < 1000 else 24
            text_id = self.canvas.create_text(x1 + CELL_SIZE/2, y1 + CELL_SIZE/2, text=str(val), font=("Helvetica", font_size, "bold"), fill=fg)

            dx = (x2 - x1) / ANIMATION_FRAMES
            dy = (y2 - y1) / ANIMATION_FRAMES

            moving_items.append({'rect': rect_id, 'text': text_id, 'dx': dx, 'dy': dy})

        def do_frame(frame):
            if not self.root.winfo_exists(): return
            if frame < ANIMATION_FRAMES:
                for item in moving_items:
                    self.canvas.move(item['rect'], item['dx'], item['dy'])
                    self.canvas.move(item['text'], item['dx'], item['dy'])
                self.root.after(ANIMATION_DUR // ANIMATION_FRAMES, do_frame, frame + 1)
            else:
                self.board = new_board
                self.score += score_diff
                self.update_score()
                self.spawn_tile()
                self.draw_board()
                self.animating = False

        do_frame(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = Game2048(root)
    root.mainloop()
