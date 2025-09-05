# screens/home.py
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import os

from shared.faceid import FaceIdentifier

CYAN = "#70e2ff"

class HomeScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=CYAN)
        self.app = app

        # Camera preview label (fills the screen area)
        self.preview = tk.Label(self, bg=CYAN, bd=0)
        self.preview.place(relx=0.5, rely=0.5, anchor="center",
                           relwidth=1.0, relheight=1.0)

        # Greeting bubble
        self.bubble = tk.Canvas(self, bg=CYAN, bd=0, highlightthickness=0)
        self.bubble_w, self.bubble_h = 340, 54
        self.bubble.place(relx=0.5, rely=1.0, x=0, y=-22, anchor="s",
                          width=self.bubble_w, height=self.bubble_h)
        self._rounded(self.bubble, 2, 2, self.bubble_w-2, self.bubble_h-2,
                      r=14, fill="white", outline="#e5e5e5")
        self.bubble.create_text(self.bubble_w/2, self.bubble_h/2,
                                text=f"Welcome, {self.app.name_text}",
                                font=("Segoe UI", 14))

        # --- Face ID setup ---
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        enc_path = os.path.join(project_root, "encodings.pickle")
        self.faceid = FaceIdentifier(encodings_path=enc_path, scaler=4, model="large")

        self._imgtk_cache = None
        self._loop_running = False

    def on_show(self):
        # Re-open camera when returning from Idle
        self.app.camera.open()
        self._loop_running = True
        self._render_loop()

    def on_hide(self):
        self._loop_running = False
        self.preview.configure(image="", bg=CYAN)

    def _render_loop(self):
        if not self._loop_running:
            return

        # 1) Grab a frame from the camera as a PIL RGB image
        frame = self.app.camera.read_rgb_frame()

        if frame is not None:
            # 2) Fit into current widget while keeping aspect ratio; compose onto cyan background
            w = int(self.winfo_width() or 10)
            h = int(self.winfo_height() or 10)
            if w > 10 and h > 10:
                scale = min(w / frame.width, h / frame.height)
                nw, nh = max(1, int(frame.width * scale)), max(1, int(frame.height * scale))
                img_resized = frame.resize((nw, nh))

                # 3) FACE RECOGNITION on the resized image (faster and matches drawn coords)
                boxes, names, fps = self.faceid.annotate_pil(img_resized)

                # 4) Draw boxes, labels, and FPS on the resized image
                draw = ImageDraw.Draw(img_resized)
                for (top, right, bottom, left), name in zip(boxes, names):
                    # box
                    draw.rectangle([left, top, right, bottom], outline=(244, 42, 3), width=3)
                    # label background
                    label_h = 26
                    draw.rectangle([left-3, top - label_h, right+3, top], fill=(244, 42, 3))
                    # label text (use simple draw.text; Pillow default font)
                    draw.text((left+6, top - label_h + 4), name or "Unknown", fill=(255, 255, 255))

                # FPS (top-right)
                fps_text = f"FPS: {fps:.1f}"
                tw, th = draw.textlength(fps_text), 14
                # simple black bg behind text
                draw.rectangle([img_resized.width-120, 6, img_resized.width-6, 28], fill=(0, 0, 0))
                draw.text((img_resized.width-114, 8), fps_text, fill=(0, 255, 0))

                # 5) Paste into cyan background
                from PIL import Image
                bg = Image.new("RGB", (w, h), (112, 226, 255))
                bg.paste(img_resized, ((w - nw) // 2, (h - nh) // 2))

                imgtk = ImageTk.PhotoImage(bg)
                self._imgtk_cache = imgtk
                self.preview.configure(image=imgtk, bg=CYAN)
        else:
            self.preview.configure(image="", bg=CYAN)

        # Aim ~30 fps for the UI loop
        self.after(33, self._render_loop)

    def _rounded(self, canvas, x1, y1, x2, y2, r=12, **kwargs):
        canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, **kwargs)
        canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, **kwargs)
        canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, **kwargs)
        canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, **kwargs)
        canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)
