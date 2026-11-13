from __future__ import annotations

import random
import tkinter as tk
from tkinter import messagebox


CELL = 30
COLS = 10
ROWS = 20
BOARD_W = COLS * CELL
BOARD_H = ROWS * CELL
SIDE_W = 190
BG = "#10131c"
PANEL = "#191e2b"
GRID = "#242b3b"
TEXT = "#f2f5ff"
MUTED = "#9aa6bd"

SHAPES = {
    "I": ("#43d9e8", ((0, 1), (1, 1), (2, 1), (3, 1))),
    "O": ("#ffd84d", ((1, 0), (2, 0), (1, 1), (2, 1))),
    "T": ("#b56aff", ((1, 0), (0, 1), (1, 1), (2, 1))),
    "S": ("#65e572", ((1, 0), (2, 0), (0, 1), (1, 1))),
    "Z": ("#ff6278", ((0, 0), (1, 0), (1, 1), (2, 1))),
    "J": ("#5992ff", ((0, 0), (0, 1), (1, 1), (2, 1))),
    "L": ("#ffa34d", ((2, 0), (0, 1), (1, 1), (2, 1))),
}
PIECES = tuple(SHAPES)
SCORES = (0, 100, 300, 500, 800)


class Tetris:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        root.title("Tetris")
        root.configure(bg=BG)
        root.resizable(False, False)
        self.board_canvas = tk.Canvas(root, width=BOARD_W, height=BOARD_H,
                                      bg=BG, highlightthickness=0)
        self.board_canvas.grid(row=0, column=0, padx=(18, 12), pady=18)
        self.side = tk.Frame(root, bg=BG, width=SIDE_W)
        self.side.grid(row=0, column=1, sticky="ns", padx=(0, 18), pady=18)
        self.side.grid_propagate(False)

        tk.Label(self.side, text="TETRIS", font=("Segoe UI", 23, "bold"),
                 bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 12))
        self._label("SCORE")
        self.score_text = self._value("0")
        self._label("LINES")
        self.lines_text = self._value("0")
        self._label("LEVEL")
        self.level_text = self._value("1")

        self._label("HOLD (C)")
        self.hold_preview = tk.Canvas(self.side, width=150, height=90, bg=PANEL,
                                      highlightthickness=0)
        self.hold_preview.pack(anchor="w", pady=(0, 8))
        self._label("NEXT")
        self.preview = tk.Canvas(self.side, width=150, height=110, bg=PANEL,
                                 highlightthickness=0)
        self.preview.pack(anchor="w", pady=(0, 14))
        self.status = tk.Label(self.side, text="", font=("Segoe UI", 10, "bold"),
                               bg=BG, fg="#ffd84d", anchor="w")
        self.status.pack(anchor="w", pady=(0, 10))
        tk.Button(self.side, text="New game", command=self.new_game,
                  font=("Segoe UI", 10, "bold"), bg="#4659e8", fg="white",
                  activebackground="#5b6cf2", activeforeground="white",
                  relief="flat", padx=12, pady=7, cursor="hand2").pack(anchor="w", pady=(0, 14))
        self._label("CONTROLS")
        for line in ("← →   Move", "↑       Rotate", "↓       Soft drop", "Space  Hard drop", "C       Hold", "P       Pause", "R       Restart"):
            tk.Label(self.side, text=line, font=("Segoe UI", 10), bg=BG,
                     fg=MUTED, anchor="w").pack(anchor="w", pady=2)

        self.root.bind("<Left>", lambda _e: self.move(-1, 0))
        self.root.bind("<Right>", lambda _e: self.move(1, 0))
        self.root.bind("<Down>", lambda _e: self.soft_drop())
        self.root.bind("<Up>", lambda _e: self.rotate())
        self.root.bind("<space>", lambda _e: self.hard_drop())
        self.root.bind("c", lambda _e: self.hold_piece())
        self.root.bind("C", lambda _e: self.hold_piece())
        self.root.bind("p", lambda _e: self.toggle_pause())
        self.root.bind("P", lambda _e: self.toggle_pause())
        self.root.bind("r", lambda _e: self.new_game())
        self.root.bind("R", lambda _e: self.new_game())
        self.new_game()
        self.tick()

    def _label(self, text: str) -> None:
        tk.Label(self.side, text=text, font=("Segoe UI", 9, "bold"),
                 bg=BG, fg=MUTED).pack(anchor="w", pady=(6, 2))

    def _value(self, text: str) -> tk.Label:
        label = tk.Label(self.side, text=text, font=("Segoe UI", 18, "bold"),
                         bg=BG, fg=TEXT)
        label.pack(anchor="w", pady=(0, 7))
        return label

    def new_game(self) -> None:
        self.board: list[list[str | None]] = [[None for _ in range(COLS)] for _ in range(ROWS)]
        self.score = self.lines = 0
        self.paused = self.over = False
        self.held_piece: str | None = None
        self.hold_used = False
        self.bag: list[str] = []
        self.current = self._take_piece()
        self.next_piece = self._take_piece()
        self._refresh_stats()
        self.status.config(text="")
        self.draw()

    def _take_piece(self) -> dict[str, object]:
        if not self.bag:
            self.bag = list(PIECES)
            random.shuffle(self.bag)
        name = self.bag.pop()
        return {"name": name, "cells": list(SHAPES[name][1]), "x": 3, "y": 0}

    @property
    def level(self) -> int:
        return self.lines // 10 + 1

    def _refresh_stats(self) -> None:
        self.score_text.config(text=f"{self.score:,}")
        self.lines_text.config(text=str(self.lines))
        self.level_text.config(text=str(self.level))

    def _valid(self, cells: list[tuple[int, int]], x: int, y: int) -> bool:
        for dx, dy in cells:
            bx, by = x + dx, y + dy
            if bx < 0 or bx >= COLS or by >= ROWS:
                return False
            if by >= 0 and self.board[by][bx] is not None:
                return False
        return True

    def move(self, dx: int, dy: int) -> bool:
        if self.paused or self.over:
            return False
        x, y = int(self.current["x"]) + dx, int(self.current["y"]) + dy
        if self._valid(self.current["cells"], x, y):
            self.current["x"], self.current["y"] = x, y
            self.draw()
            return True
        return False

    def rotate(self) -> None:
        if self.paused or self.over:
            return
        # A square is unchanged by rotation; skipping it prevents its 2x2
        # cells from shifting inside the larger rotation grid.
        if self.current["name"] == "O":
            return
        cells = self.current["cells"]
        rotated = [(3 - y, x) for x, y in cells]
        x, y = int(self.current["x"]), int(self.current["y"])
        # Keep the anchor fixed except for the minimum shift needed at a wall.
        min_x = min(dx for dx, _ in rotated)
        max_x = max(dx for dx, _ in rotated)
        x = max(-min_x, min(x, COLS - 1 - max_x))
        if self._valid(rotated, x, y):
            self.current["cells"] = rotated
            self.current["x"] = x
        self.draw()

    def soft_drop(self) -> None:
        if self.move(0, 1):
            self.score += 1
            self._refresh_stats()
        else:
            self.lock_piece()

    def hard_drop(self) -> None:
        if self.paused or self.over:
            return
        distance = 0
        while self.move(0, 1):
            distance += 1
        self.score += distance * 2
        self.lock_piece()

    def hold_piece(self) -> None:
        if self.paused or self.over or self.hold_used:
            return
        current_name = str(self.current["name"])
        if self.held_piece is None:
            self.held_piece = current_name
            self.current = self.next_piece
            self.next_piece = self._take_piece()
        else:
            held_name = self.held_piece
            self.held_piece = current_name
            self.current = {"name": held_name, "cells": list(SHAPES[held_name][1]),
                            "x": 3, "y": 0}
        self.current["x"], self.current["y"] = 3, 0
        self.hold_used = True
        if not self._valid(self.current["cells"], 3, 0):
            self.over = True
            self.status.config(text="GAME OVER")
        self.draw()

    def lock_piece(self) -> None:
        name = str(self.current["name"])
        color = SHAPES[name][0]
        for dx, dy in self.current["cells"]:
            x, y = int(self.current["x"]) + dx, int(self.current["y"]) + dy
            if y < 0:
                self.over = True
                self.status.config(text="GAME OVER")
                self.draw()
                return
            self.board[y][x] = color
        full = [row for row in self.board if all(cell is not None for cell in row)]
        if full:
            count = len(full)
            self.board = [[None for _ in range(COLS)] for _ in range(count)] + [
                row for row in self.board if not all(cell is not None for cell in row)
            ]
            self.lines += count
            self.score += SCORES[count] * self.level
        self.current = self.next_piece
        self.next_piece = self._take_piece()
        self.hold_used = False
        self.current["x"], self.current["y"] = 3, 0
        self._refresh_stats()
        if not self._valid(self.current["cells"], 3, 0):
            self.over = True
            self.status.config(text="GAME OVER")
        self.draw()

    def toggle_pause(self) -> None:
        if self.over:
            return
        self.paused = not self.paused
        self.status.config(text="PAUSED" if self.paused else "")
        self.draw()

    def tick(self) -> None:
        if not self.paused and not self.over:
            if not self.move(0, 1):
                self.lock_piece()
        self.root.after(max(80, 650 - (self.level - 1) * 55), self.tick)

    def draw(self) -> None:
        c = self.board_canvas
        c.delete("all")
        for y in range(ROWS):
            for x in range(COLS):
                self._draw_cell(c, x, y, self.board[y][x] or BG, GRID)
        if not self.over:
            name = str(self.current["name"])
            color = SHAPES[name][0]
            ghost_y = int(self.current["y"])
            while self._valid(self.current["cells"], int(self.current["x"]), ghost_y + 1):
                ghost_y += 1
            for dx, dy in self.current["cells"]:
                x, y = int(self.current["x"]) + dx, ghost_y + dy
                if y >= 0:
                    self._draw_cell(c, x, y, color, color, stipple="gray50")
            for dx, dy in self.current["cells"]:
                x, y = int(self.current["x"]) + dx, int(self.current["y"]) + dy
                if y >= 0:
                    self._draw_cell(c, x, y, color, "#ffffff")
        if self.paused or self.over:
            c.create_rectangle(0, BOARD_H // 2 - 35, BOARD_W, BOARD_H // 2 + 35,
                               fill="#10131c", stipple="gray50", outline="")
            c.create_text(BOARD_W // 2, BOARD_H // 2, text="PAUSED" if self.paused else "GAME OVER",
                          fill=TEXT, font=("Segoe UI", 20, "bold"))
        self._draw_preview()
        self._draw_hold_preview()

    @staticmethod
    def _draw_cell(canvas: tk.Canvas, x: int, y: int, color: str, outline: str,
                   stipple: str = "") -> None:
        pad = 2
        canvas.create_rectangle(x * CELL + pad, y * CELL + pad,
                                (x + 1) * CELL - pad, (y + 1) * CELL - pad,
                                fill=color, outline=outline, width=1, stipple=stipple)

    def _draw_preview(self) -> None:
        self._draw_piece_preview(self.preview, str(self.next_piece["name"]), 150, 110)

    def _draw_hold_preview(self) -> None:
        self.hold_preview.delete("all")
        if self.held_piece is not None:
            self._draw_piece_preview(self.hold_preview, self.held_piece, 150, 90)

    @staticmethod
    def _draw_piece_preview(canvas: tk.Canvas, name: str, width: int, height: int) -> None:
        c = canvas
        c.delete("all")
        color, cells = SHAPES[name]
        min_x = min(x for x, _ in cells)
        max_x = max(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        max_y = max(y for _, y in cells)
        size = 24
        start_x = (width - (max_x - min_x + 1) * size) // 2
        start_y = (height - (max_y - min_y + 1) * size) // 2
        for x, y in cells:
            c.create_rectangle(start_x + (x - min_x) * size + 2,
                               start_y + (y - min_y) * size + 2,
                               start_x + (x - min_x + 1) * size - 2,
                               start_y + (y - min_y + 1) * size - 2,
                               fill=color, outline="white")


if __name__ == "__main__":
    window = tk.Tk()
    Tetris(window)
    window.mainloop()
