#!/usr/bin/env python3
"""
RNGenius – The Button-Based Random Number Revolution
Test Fixture Implementation (Tkinter, single file, with confetti)

This playful app is only for use as a test document source for Escarabajo.
Do not confuse with actual production software.

Functional Characteristics (per spec):
- Button labeled "I'm Feeling Chaotic".
- Click or Enter generates a random 64-bit signed integer.
- Displays the number in large font.
- Copy-to-clipboard.
- Stores last 5 results (session).
- Keyboard-accessible (Enter / Space).
- Delight factor: playful window titles + confetti animation.
"""

import tkinter as tk
from tkinter import messagebox
import random
import time

# 64-bit signed integer bounds
MAX_INT64 = 2**63 - 1
MIN_INT64 = -(2**63)

class RNGeniusApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("RNGenius — Button-Based Random Number Revolution")
        self.root.geometry("560x460")
        self.root.minsize(520, 420)

        self.history = []              # last 5 numbers
        self.current_value = None
        self.confetti_particles = []   # animation state
        self.confetti_active = False

        # ====== Top area (title + message) ======
        top = tk.Frame(root)
        top.pack(fill="x", pady=(10, 0))
        self.title_label = tk.Label(top, text="RNGenius", font=("Helvetica", 20, "bold"))
        self.title_label.pack()

        self.msg_label = tk.Label(
            root,
            text="Press the button to summon entropy!",
            font=("Helvetica", 12),
            fg="#555",
        )
        self.msg_label.pack(pady=(2, 8))

        # ====== Central area (display + canvas overlay for confetti) ======
        center = tk.Frame(root)
        center.pack(expand=True, fill="both", padx=16)

        # big number label
        self.number_label = tk.Label(
            center,
            text="",
            font=("Courier New", 28, "bold"),
            wraplength=520,
            justify="center"
        )
        self.number_label.pack(pady=(16, 8), fill="x")

        # a thin canvas overlay for confetti
        self.canvas = tk.Canvas(center, highlightthickness=0, bg=self.root.cget("bg"))
        self.canvas.pack(expand=True, fill="both")

        # ====== Controls ======
        controls = tk.Frame(root)
        controls.pack(pady=10)

        self.button = tk.Button(
            controls,
            text="I'm Feeling Chaotic",
            font=("Helvetica", 14, "bold"),
            bg="#f7b733",
            activebackground="#f4a300",
            command=self.generate_number
        )
        self.button.grid(row=0, column=0, padx=8)

        self.copy_button = tk.Button(
            controls,
            text="Copy to Clipboard",
            command=self.copy_to_clipboard,
            state="disabled"
        )
        self.copy_button.grid(row=0, column=1, padx=8)

        # ====== History ======
        self.history_label = tk.Label(
            root,
            text="Last 5 results: (none yet)",
            font=("Courier New", 10),
            justify="left"
        )
        self.history_label.pack(pady=(10, 14))

        # ====== Keyboard bindings for accessibility ======
        # Enter / Space on the window should act like pressing the main button
        root.bind("<Return>", lambda e: self.generate_number())
        root.bind("<space>", lambda e: self.generate_number())
        # Focus traversal
        self.button.focus_set()

        # update canvas size tracking
        self.canvas.bind("<Configure>", self._on_canvas_resize)

    # ---------- Core actions ----------
    def generate_number(self):
        value = random.randint(MIN_INT64, MAX_INT64)
        self.current_value = value
        self.number_label.config(text=str(value))
        self.copy_button.config(state="normal")

        # update history
        self.history.insert(0, value)
        self.history = self.history[:5]
        self.history_label.config(
            text="Last 5 results:\n" + "\n".join(str(n) for n in self.history)
        )

        # Delight factor: playful title
        self.root.title("RNGenius — " + random.choice([
            "Entropy unleashed!",
            "Destiny digit delivered!",
            "Pure chaos, fresh for you!",
            "As random as your mood!",
            "Giggles per click: achieved!"
        ]))

        # Confetti
        self._burst_confetti()

    def copy_to_clipboard(self):
        number_text = self.number_label.cget("text").strip()
        if not number_text:
            messagebox.showwarning("Nothing to copy", "No number has been generated yet.")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(number_text)
        messagebox.showinfo("Copied", f"Number {number_text} copied to clipboard!")

    # ---------- Confetti animation ----------
    def _on_canvas_resize(self, _event):
        # keep background consistent with window theme
        self.canvas.configure(bg=self.root.cget("bg"))

    def _burst_confetti(self):
        """
        Create a short-lived confetti burst.
        - ~80 particles
        - colored dots with random velocities
        - gravity + fade
        - auto-stops after ~1.5s
        """
        if self.confetti_active:
            # if an animation is already running, add a smaller burst
            num = 40
        else:
            num = 80
            self.confetti_particles.clear()

        self.confetti_active = True
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)

        # Spawn around top-center region
        origin_x = w // 2
        origin_y = int(h * 0.15)

        colors = [
            "#ff595e", "#ffca3a", "#8ac926", "#1982c4",
            "#6a4c93", "#f72585", "#4cc9f0", "#e76f51"
        ]

        for _ in range(num):
            r = random.randint(2, 4)
            vx = random.uniform(-3.0, 3.0)
            vy = random.uniform(-0.5, 1.0)
            life = 1.5  # seconds
            created = time.time()
            c = random.choice(colors)
            item = self.canvas.create_oval(
                origin_x - r, origin_y - r, origin_x + r, origin_y + r,
                fill=c, outline=""
            )
            self.confetti_particles.append({
                "id": item, "x": origin_x, "y": origin_y,
                "r": r, "vx": vx, "vy": vy,
                "g": 0.18,           # gravity
                "drag": 0.995,       # slight air resistance
                "life": life, "t0": created
            })

        # Start or continue animation loop
        self._animate_confetti()

    def _animate_confetti(self):
        if not self.confetti_particles:
            self.confetti_active = False
            return

        now = time.time()
        w = max(self.canvas.winfo_width(), 1)
        h = max(self.canvas.winfo_height(), 1)

        alive = []
        for p in self.confetti_particles:
            t = now - p["t0"]
            if t > p["life"]:
                # remove particle
                self.canvas.delete(p["id"])
                continue

            # physics
            p["vy"] += p["g"]
            p["vx"] *= p["drag"]
            p["vy"] *= p["drag"]
            p["x"] += p["vx"]
            p["y"] += p["vy"]

            # boundary bounce at bottom
            if p["y"] > h - p["r"]:
                p["y"] = h - p["r"]
                p["vy"] *= -0.55
                p["vx"] *= 0.9

            # update drawing
            x, y, r = p["x"], p["y"], p["r"]
            self.canvas.coords(p["id"], x - r, y - r, x + r, y + r)

            # fade out near end of life by shrinking
            remaining = max(0.0, p["life"] - t)
            if remaining < 0.4:
                sr = r * (remaining / 0.4)
                sr = max(0.1, sr)
                self.canvas.coords(p["id"], x - sr, y - sr, x + sr, y + sr)

            alive.append(p)

        self.confetti_particles = alive
        # schedule next frame (~60 FPS)
        self.root.after(16, self._animate_confetti)

def main():
    root = tk.Tk()
    app = RNGeniusApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
