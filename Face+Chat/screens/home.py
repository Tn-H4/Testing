
import tkinter as tk
from PIL import Image, ImageTk

CYAN = "#70e2ff"

class HomeScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=CYAN)
        self.app = app

        self.preview = tk.Label(self, bg=CYAN, bd=0)
        self.preview.place(relx=0.5, rely=0.5, anchor="center",
                           relwidth=1.0, relheight=1.0)

        self.bubble = tk.Canvas(self, bg=CYAN, bd=0, highlightthickness=0)
        self.bubble_w, self.bubble_h = 340, 54
        self.bubble.place(relx=0.5, rely=1.0, x=0, y=-22, anchor="s",
                          width=self.bubble_w, height=self.bubble_h)
        self._rounded(self.bubble, 2, 2, self.bubble_w-2, self.bubble_h-2,
                      r=14, fill="white", outline="#e5e5e5")
        self.bubble.create_text(self.bubble_w/2, self.bubble_h/2,
                                text=f"Welcome, {self.app.name_text}",
                                font=("Segoe UI", 14))

        self._imgtk_cache = None
        self._loop_running = False

    def on_show(self):
        self._loop_running = True
        self._render_loop()

    def on_hide(self):
        self._loop_running = False
        self.preview.configure(image="", bg=CYAN)

    def _render_loop(self):
        if not self._loop_running:
            return

        frame = self.app.camera.read_rgb_frame()
        if frame is not None:
            w = int(self.winfo_width() or 10)
            h = int(self.winfo_height() or 10)
            if w > 10 and h > 10:
                scale = min(w / frame.width, h / frame.height)
                nw, nh = max(1, int(frame.width * scale)), max(1, int(frame.height * scale))
                img_resized = frame.resize((nw, nh))
                from PIL import Image
                bg = Image.new("RGB", (w, h), (112, 226, 255))
                bg.paste(img_resized, ((w - nw) // 2, (h - nh) // 2))
                imgtk = ImageTk.PhotoImage(bg)
                self._imgtk_cache = imgtk
                self.preview.configure(image=imgtk, bg=CYAN)
        else:
            self.preview.configure(image="", bg=CYAN)

        self.after(33, self._render_loop)

    def _rounded(self, canvas, x1, y1, x2, y2, r=12, **kwargs):
        canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, **kwargs)
        canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, **kwargs)
        canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, **kwargs)
        canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, **kwargs)
        canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)
