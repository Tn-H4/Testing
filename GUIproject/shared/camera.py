try:
    import cv2
    OPENCV_OK = True
except Exception:
    OPENCV_OK = False
    cv2 = None

from PIL import Image

class CameraManager:
    def __init__(self, index=0, width=1280, height=720): #change to index 1 if using USB camera
        self.index = index
        self.width = width
        self.height = height
        self.cap = None
        self.open()

    def open(self):
        if not OPENCV_OK:
            return
        if self.cap and self.cap.isOpened():
            return
        try:
            self.cap = cv2.VideoCapture(self.index)
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        except Exception:
            self.cap = None

    def read_rgb_frame(self):
        if not self.cap or not self.cap.isOpened():
            return None
        ok, frame = self.cap.read()
        if not ok:
            return None
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        return Image.fromarray(frame)

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = None