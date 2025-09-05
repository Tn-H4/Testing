# screens/train_faces.py
import os
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox

# Heavy libs imported inside the worker thread
# to keep the UI responsive and to allow running even if not installed yet.

class TrainFacesScreen(tk.Frame):
    """
    Builds encodings.pickle from dataset/<name>/*.jpg using face_recognition.
    UI:
      - Start button
      - Progress bar + counter
      - Scrollable log
    Runs training in a background thread so Tk doesn't freeze.
    """
    def __init__(self, parent, app):
        super().__init__(parent, bg="#d9d9d9")
        self.app = app

        header = tk.Frame(self, bg="#d9d9d9")
        header.pack(fill="x", padx=14, pady=(12, 6))
        tk.Label(header, text="Train Faces", bg="#d9d9d9",
                 font=("Segoe UI", 18, "bold")).pack(side="left")
        tk.Button(header, text="Back", font=("Segoe UI", 12),
                  command=lambda: self.app.show("settings")).pack(side="right")

        body = tk.Frame(self, bg="#d9d9d9")
        body.pack(fill="both", expand=True, padx=14, pady=8)

        # Controls row
        controls = tk.Frame(body, bg="#d9d9d9")
        controls.pack(fill="x", pady=(0, 8))
        tk.Label(controls, text="Dataset:", bg="#d9d9d9",
                 font=("Segoe UI", 12)).pack(side="left")
        self.dataset_var = tk.StringVar(value="dataset")
        tk.Entry(controls, textvariable=self.dataset_var,
                 font=("Segoe UI", 12), width=32).pack(side="left", padx=8)
        tk.Button(controls, text="Start", font=("Segoe UI", 12),
                  command=self.start_training).pack(side="right")

        # Progress row
        prog_row = tk.Frame(body, bg="#d9d9d9")
        prog_row.pack(fill="x", pady=(0, 8))
        self.prog = ttk.Progressbar(prog_row, orient="horizontal", mode="determinate")
        self.prog.pack(fill="x", expand=True)
        self.count_lbl = tk.Label(prog_row, text="0 / 0", bg="#d9d9d9", font=("Segoe UI", 11))
        self.count_lbl.pack(anchor="e", pady=(4, 0))

        # Log
        log_wrap = tk.Frame(body, bg="#d9d9d9")
        log_wrap.pack(fill="both", expand=True)
        self.log = tk.Text(log_wrap, font=("Consolas", 10), height=16, wrap="word")
        self.log.pack(side="left", fill="both", expand=True)
        scroll = tk.Scrollbar(log_wrap, command=self.log.yview)
        scroll.pack(side="right", fill="y")
        self.log.configure(yscrollcommand=scroll.set)

        # threading + queue for logs
        self._worker = None
        self._q = queue.Queue()
        self._stop_flag = False
        self.after(50, self._drain_logs)

    def on_show(self):
        pass

    def on_hide(self):
        pass

    def start_training(self):
        if self._worker and self._worker.is_alive():
            messagebox.showinfo("Training", "Training is already running.")
            return
        dataset_dir = self.dataset_var.get().strip() or "dataset"
        if not os.path.isdir(dataset_dir):
            messagebox.showerror("Not Found", f"Folder not found: {dataset_dir}")
            return

        # Reset UI
        self.log.delete("1.0", "end")
        self.prog["value"] = 0
        self.count_lbl.config(text="0 / 0")

        # Start worker
        self._stop_flag = False
        self._worker = threading.Thread(
            target=self._train_worker, args=(dataset_dir,), daemon=True
        )
        self._worker.start()
        self._log("[INFO] start processing faces...")

    def _train_worker(self, dataset_dir):
        """
        Runs in background thread: scan dataset, compute encodings, save pickle.
        Mirrors your CLI script but posts progress into a Tk queue.
        """
        try:
            from imutils import paths
            import face_recognition
            import cv2
            import pickle
            import numpy as np

            imagePaths = list(paths.list_images(dataset_dir))
            total = len(imagePaths)
            self._q.put(("total", total))

            knownEncodings = []
            knownNames = []

            for (i, imagePath) in enumerate(imagePaths, start=1):
                if self._stop_flag:
                    break

                name = imagePath.split(os.path.sep)[-2]
                self._q.put(("log", f"[INFO] processing image {i}/{total}: {imagePath}"))
                self._q.put(("prog", (i, total)))

                image = cv2.imread(imagePath)
                if image is None:
                    self._q.put(("log", f"[WARN] cannot read image: {imagePath}"))
                    continue

                rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                # You can switch model="cnn" if you have dlib GPU and want accuracy over speed
                boxes = face_recognition.face_locations(rgb, model="hog")
                encodings = face_recognition.face_encodings(rgb, boxes)

                for encoding in encodings:
                    knownEncodings.append(encoding)
                    knownNames.append(name)

            # Save encodings
            data = {"encodings": knownEncodings, "names": knownNames}

            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            out_path = os.path.join(project_root, "encodings.pickle")
            with open(out_path, "wb") as f:
                import pickle
                f.write(pickle.dumps(data))

            self._q.put(("log", f"[INFO] Training complete. Encodings saved to '{out_path}'"))
            self._q.put(("done", out_path))

        except Exception as e:
            self._q.put(("error", str(e)))

    def _drain_logs(self):
        """Pump messages from the worker into the UI thread."""
        try:
            while True:
                kind, payload = self._q.get_nowait()
                if kind == "log":
                    self._log(payload)
                elif kind == "total":
                    self.prog["value"] = 0
                    self.prog["maximum"] = max(1, int(payload))
                    self.count_lbl.config(text=f"0 / {payload}")
                elif kind == "prog":
                    i, total = payload
                    self.prog["maximum"] = max(1, int(total))
                    self.prog["value"] = int(i)
                    self.count_lbl.config(text=f"{i} / {total}")
                elif kind == "done":
                    self._log("[INFO] Done.")
                    # Optional: refresh face encodings in Home if using FaceIdentifier
                    try:
                        if hasattr(self.app, "screens") and "home" in self.app.screens:
                            home = self.app.screens["home"]
                            if hasattr(home, "faceid"):
                                home.faceid.reload(payload)
                                self._log("[INFO] Home recognizer reloaded.")
                    except Exception:
                        pass
                elif kind == "error":
                    self._log(f"[ERROR] {payload}")
                    messagebox.showerror("Training Error", payload)
        except queue.Empty:
            pass
        # schedule next pump
        self.after(100, self._drain_logs)

    def _log(self, text):
        self.log.insert("end", text + "\n")
        self.log.see("end")
