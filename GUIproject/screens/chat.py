import tkinter as tk

class ChatScreen(tk.Frame):
    def __init__(self, parent, app, assistant):
        super().__init__(parent, bg="#d9d9d9")
        self.app = app
        self.assistant = assistant  #preloaded bot from main.py
        self._greeted = False 

        # === Outer wrapper (centered in screen) ===
        wrapper = tk.Frame(self, bg="#d9d9d9")
        wrapper.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.9, relheight=0.9)

        # Messages area (scrollable)
        container = tk.Frame(wrapper, bg="#d9d9d9")
        container.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(container, bg="#d9d9d9", highlightthickness=0)
        self.scroll = tk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.msg_frame = tk.Frame(self.canvas, bg="#d9d9d9")

        self.msg_frame.grid_columnconfigure(0, weight=1)   # left lane
        self.msg_frame.grid_columnconfigure(1, weight=0, minsize=24)  # gutter
        self.msg_frame.grid_columnconfigure(2, weight=1)   # right lane

        self.msg_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas_win = self.canvas.create_window((0, 0), window=self.msg_frame, anchor="nw", width=1)
        self.canvas.configure(yscrollcommand=self.scroll.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scroll.pack(side="right", fill="y")

        # Input bar
        input_bar = tk.Frame(wrapper, bg="#d9d9d9")
        input_bar.pack(fill="x", pady=6)

        self.entry = tk.Entry(input_bar, font=("Segoe UI", 13))
        self.entry.pack(side="left", fill="both", expand=True, padx=(0,10), pady=6)
        self.entry.bind("<Return>", self._on_send)

        self.send_btn = tk.Button(input_bar, text="Send", font=("Segoe UI", 12), command=self._on_send)
        self.send_btn.pack(side="right", padx=(0,0), pady=6)

        container.bind("<Configure>", lambda e: self._resize_canvas_window())

    def on_show(self):
        self.after(50, lambda: self.entry.focus_set())

        if not self._greeted:
            self.add_message("bot", "Hello, what can I help you?")
            self._greeted = True

    def on_hide(self):
        # nothing to clean up yet
        pass

    # --- bubble helpers (two lanes meeting in middle) ---
    def add_message(self, sender, text):
        bubble_bg = "#ffffff" if sender == "user" else "#f6f6f6"
        bubble = tk.Frame(self.msg_frame, bg=bubble_bg, padx=10, pady=6)

        # Wrap to ~38% of canvas width so each side fits nicely
        wrap = max(180, int(self.canvas.winfo_width() * 0.38))
        label = tk.Label(bubble, text=text, bg=bubble_bg, font=("Segoe UI", 12),
                         wraplength=wrap, justify="left")
        label.pack()

        row = self.msg_frame.grid_size()[1]
        if sender == "user":
            bubble.grid(row=row, column=2, sticky="e", padx=8, pady=6)  # right lane
        else:
            bubble.grid(row=row, column=0, sticky="w", padx=8, pady=6)  # left lane

        self.after(0, self._scroll_to_bottom)

    def _scroll_to_bottom(self):
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)
        self._resize_canvas_window()

    def _resize_canvas_window(self):
        width = self.canvas.winfo_width()
        if width > 0:
            self.canvas.itemconfig(self.canvas_win, width=width)

    # --- send handler: call your model and post reply ---
    def _on_send(self, event=None):
        text = self.entry.get().strip()
        if not text:
            return
        self.entry.delete(0, "end")
        self.add_message("user", text)

        def bot_reply():
            if not self.assistant:
                self.add_message("bot", "Loading my brain… please try again in a moment.")
                return
            reply = self.assistant.reply(text)
            self.add_message("bot", reply)

        # Non-blocking so UI stays responsive
        self.after(10, bot_reply)
