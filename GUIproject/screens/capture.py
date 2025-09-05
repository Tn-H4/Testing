# screens/capture.py
import os
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

CYAN = "#70e2ff"

class CaptureScreen(tk.Frame):
    """
    Photo capture screen:
    - Live camera preview
    - Name input
    - Capture button (and Space key)
    - Saves to dataset/<name>/<name>_YYYYmmdd_HHMMSS.jpg
    """
    def __init__(self, parent, app):
        super().__init__(parent, bg=CYAN)
        self.app = app

        # --- Top title row ---
        topbar = tk.Frame(self, bg=CYAN)
        topbar.pack(fill="x", pady=(10, 2))
        tk.Label(topbar, text="Photo Capture", bg=CYAN, font=("Segoe UI", 18, "bold")).pack(side="left", padx=12)

        # --- Name + buttons row ---
        toolbar = tk.Frame(self, bg=CYAN)
        toolbar.pack(fill="x", pady=(2, 10))

        tk.Label(toolbar, text="Name:", bg=CYAN, font=("Segoe UI", 12)).pack(side="left", padx=(12, 6))
        self.name_var = tk.StringVar(value="Subject1")
        self.name_entry = tk.Entry(toolbar, textvariable=self.name_var, font=("Segoe UI", 12), width=24)
        self.name_entry.pack(side="left", padx=(0, 12), ipady=2)

        self.count_lbl = tk.Label(toolbar, text="Saved: 0", bg=CYAN, font=("Segoe UI", 12))
        self.count_lbl.pack(side="left", padx=8)

        tk.Button(toolbar, text="Capture (Space)", font=("Segoe UI", 12), command=self.capture).pack(side="right", padx=(6, 12))
        tk.Button(toolbar, text="Back", font=("Segoe UI", 12), command=lambda: self.app.show("settings")).pack(side="right")

        # --- Preview area ---
        self.preview = tk.Label(self, bg=CYAN, bd=0)
        self.preview.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        # state
        self._imgtk_cache = None
        self._loop_running = False
        self._saved_count = 0
        self._last_frame_pil = None  # keep last grabbed frame (PIL RGB)

        # Key binding for Space capture (bound when shown)
        self._space_binding_added = False

    # lifecycle
    def on_show(self):
        # ensure camera is on
        self.app.camera.open()
        self._loop_running = True
        self._render_loop()
        # focus name on first open
        self.after(50, lambda: self.name_entry.focus_set())
        if not self._space_binding_added:
            self.bind_all("<space>", self._on_space, add="+")
            self._space_binding_added = True

    def on_hide(self):
        self._loop_running = False
        self.preview.configure(image="", bg=CYAN)

    # preview loop
    def _render_loop(self):
        if not self._loop_running:
            return
        frame = self.app.camera.read_rgb_frame()  # PIL.Image (RGB) or None
        if frame is not None:
            self._last_frame_pil = frame  # keep latest for saving
            w = max(10, int(self.preview.winfo_width() or 10))
            h = max(10, int(self.preview.winfo_height() or 10))
            if w > 10 and h > 10:
                scale = min(w / frame.width, h / frame.height)
                nw, nh = max(1, int(frame.width * scale)), max(1, int(frame.height * scale))
                img_resized = frame.resize((nw, nh))
                from PIL import Image
                bg = Image.new("RGB", (w, h), (112, 226, 255))
                bg.paste(img_resized, ((w - nw) // 2, (h - nh) // 2))
                imgtk = ImageTk.PhotoImage(bg)
                self._imgtk_cache = imgtk
                self.preview.configure(image=imgtk)
        self.after(33, self._render_loop)

    # saving
    def _ensure_folder(self, name):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # project root
        folder = os.path.join(base, "dataset", name)
        os.makedirs(folder, exist_ok=True)
        return folder

    def capture(self):
        name = self.name_var.get().strip() or "Subject1"
        if self._last_frame_pil is None:
            messagebox.showwarning("No Frame", "No camera frame available yet.")
            return
        folder = self._ensure_folder(name)

        # Construct filename
        from datetime import datetime
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{ts}.jpg"
        path = os.path.join(folder, filename)

        # Save image; prefer OpenCV (BGR) if available to match your previous script
        try:
            import cv2
            import numpy as np
            rgb = np.array(self._last_frame_pil)               # RGB
            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            ok = cv2.imwrite(path, bgr)
            if not ok:
                raise RuntimeError("cv2.imwrite returned False")
        except Exception:
            # fallback to PIL save
            try:
                self._last_frame_pil.save(path, format="JPEG", quality=95)
            except Exception as e:
                messagebox.showerror("Save Failed", f"Could not save image:\n{e}")
                return

        self._saved_count += 1
        self.count_lbl.config(text=f"Saved: {self._saved_count}")

    def _on_space(self, event):
        # Capture on spacebar
        self.capture()

    # util
    def _rounded(self, canvas, x1, y1, x2, y2, r=12, **kwargs):
        canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90, extent=90, **kwargs)
        canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0, extent=90, **kwargs)
        canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, **kwargs)
        canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, **kwargs)
        canvas.create_rectangle(x1+r, y1, x2-r, y2, **kwargs)
        canvas.create_rectangle(x1, y1+r, x2, y2-r, **kwargs)
