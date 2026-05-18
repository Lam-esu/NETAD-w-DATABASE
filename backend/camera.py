import cv2
import time


class CameraService:
    def __init__(self, source=0):
        self.source = int(source) if str(source).isdigit() else source
        self.camera = None

    def connect(self):
        if self.camera is None or not self.camera.isOpened():
            self.camera = cv2.VideoCapture(self.source)
        return self.camera.isOpened()

    def generate_frames(self):
        while True:
            try:
                if not self.connect():
                    time.sleep(2)
                    continue

                success, frame = self.camera.read()

                if not success:
                    self.camera.release()
                    self.camera = None
                    time.sleep(2)
                    continue

                ret, buffer = cv2.imencode(".jpg", frame)

                if not ret:
                    continue

                frame_bytes = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )

            except Exception:
                time.sleep(2)