
import tkinter as tk

class SettingsScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg="#d9d9d9")
        self.app = app

        grid = tk.Frame(self, bg="#d9d9d9")
        grid.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.98, relheight=0.95)

        for r in (0, 1):
            grid.rowconfigure(r, weight=1, uniform="r")
        for c in (0, 1, 2):
            grid.columnconfigure(c, weight=1, uniform="c")

        pad = 18
        colors = ["#ffd51a", "#7CFC00", "#00F5FF", "#0047FF", "#AA00FF", "#ff9900"]

        for i, col in enumerate(colors):
            r, c = divmod(i, 3)
            cell = tk.Frame(grid, bg=col)
            cell.grid(row=r, column=c, sticky="nsew", padx=pad, pady=pad)

            if i == 0:
                tk.Label(cell, text="Language", bg=col, font=("Segoe UI", 16)).place(relx=0.05, rely=0.08, anchor="nw")
                cell.bind("<Button-1>", lambda e: self._on_language())
            #In Working    
            elif i == 1:
                tk.Label(cell, text="Capture", bg=col, font=("Segoe UI", 16)).place(relx=0.05, rely=0.08, anchor="nw")
                cell.bind("<Button-1>", lambda e: self.app.show("capture"))
            elif i == 2:
                tk.Label(cell, text="Train Faces", bg=col, font=("Segoe UI", 16)).place(relx=0.05, rely=0.08, anchor="nw")
                cell.bind("<Button-1>", lambda e: self.app.show("train"))

                
    def on_show(self):
        pass

    def on_hide(self):
        pass

    def _on_language(self):
        tk.messagebox.showinfo("Language", "Language dialog not implemented yet.")
