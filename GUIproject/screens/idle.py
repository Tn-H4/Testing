import tkinter as tk

class IdleScreen(tk.Frame):
    """Shown after 10s of inactivity. Any activity goes back to Home."""
    def __init__(self, parent, app):
        super().__init__(parent, bg="#d9d9d9")
        self.app = app
        self.label = tk.Label(self, text="Placeholder", bg="#d9d9d9",
                              font=("Segoe UI", 16))
        self.label.place(relx=0.5, rely=0.5, anchor="center")

    def on_show(self):
        pass

    def on_hide(self):
        pass
