# shared/faceid.py
import os, time, pickle
import numpy as np

try:
    import face_recognition
    FACE_LIB_OK = True
except Exception:
    FACE_LIB_OK = False

class FaceIdentifier:
    """
    Wraps face_recognition to detect/identify faces on a PIL RGB image.
    annotate_pil(pil_rgb) -> (boxes, names, fps)
      - boxes are (top, right, bottom, left) in the SAME resolution as the input image
      - names are matched names or "Unknown"
      - fps is a rolling FPS estimate for processing
    """
    def __init__(self, encodings_path="encodings.pickle", scaler=4, model="large"):
        self.scaler = max(1, int(scaler))
        self.model = model
        self.encodings = []
        self.names = []
        self._load_ok = False
        if FACE_LIB_OK and os.path.exists(encodings_path):
            with open(encodings_path, "rb") as f:
                data = pickle.load(f)
            self.encodings = data.get("encodings", [])
            self.names = data.get("names", [])
            self._load_ok = True

        self._f_count = 0
        self._start = time.time()
        self.fps = 0.0

    def annotate_pil(self, pil_rgb):
        """
        Run detection+recognition on a PIL.Image in RGB mode.
        Returns (upscaled_boxes, names, fps).
        If face_recognition not available or encodings missing, returns ([], [], fps).
        """
        # FPS bookkeeping
        self._f_count += 1
        elapsed = time.time() - self._start
        if elapsed >= 1.0:
            self.fps = self._f_count / elapsed
            self._f_count = 0
            self._start = time.time()

        if not (FACE_LIB_OK and self._load_ok and pil_rgb):
            return [], [], self.fps

        # Convert PIL->np RGB
        frame_rgb = np.array(pil_rgb)  # H x W x 3, RGB
        # Downscale for speed
        small = frame_rgb[::self.scaler, ::self.scaler, :]

        boxes = face_recognition.face_locations(small)
        encs = face_recognition.face_encodings(small, boxes, model=self.model)

        names = []
        for e in encs:
            if not self.encodings:
                names.append("Unknown")
                continue
            matches = face_recognition.compare_faces(self.encodings, e)
            dists = face_recognition.face_distance(self.encodings, e)
            best = int(np.argmin(dists)) if len(dists) else -1
            if best >= 0 and matches[best]:
                names.append(self.names[best])
            else:
                names.append("Unknown")

        # Upscale box coords back to original size
        scale = self.scaler
        up_boxes = [(t*scale, r*scale, b*scale, l*scale) for (t, r, b, l) in boxes]
        return up_boxes, names, self.fps

    def reload(self, encodings_path=None):
        """Reload encodings from disk."""
        import pickle, os
        if encodings_path:
            # allow override
            self_path = encodings_path
        else:
            # try the same path used at init by looking at project root
            # (adjust if you stored path elsewhere)
            import inspect, os
            project_root = os.path.dirname(os.path.dirname(inspect.getfile(type(self))))
            self_path = os.path.join(project_root, "encodings.pickle")
        if os.path.exists(self_path):
            with open(self_path, "rb") as f:
                data = pickle.load(f)
            self.encodings = data.get("encodings", [])
            self.names = data.get("names", [])
            self._load_ok = True
        else:
            self.encodings, self.names = [], []
            self._load_ok = False