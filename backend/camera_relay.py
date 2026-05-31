import cv2
import time
from flask import Flask, Response

app = Flask(__name__)

CAMERA_SOURCE = "rtsp://cctvuser:netadcctv1@192.168.1.50:554/stream2"

class CameraService:
    def __init__(self, source):
        self.source = source
        self.camera = None

    def connect(self):
        if self.camera is None or not self.camera.isOpened():
            self.camera = cv2.VideoCapture(self.source)
        return self.camera.isOpened()

    def generate_frames(self):
        retry = 0
        while True:
            try:
                if not self.connect():
                    retry += 1
                    time.sleep(min(1 * retry, 5))  # exponential backoff
                    continue

                success, frame = self.camera.read()
                if not success or frame is None:
                    if self.camera is not None:
                        self.camera.release()
                        self.camera = None
                    retry += 1
                    time.sleep(min(1 * retry, 5))
                    continue

                retry = 0
                ret, buffer = cv2.imencode(".jpg", frame)
                if not ret:
                    continue

                frame_bytes = buffer.tobytes()
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
                )

            except Exception:
                if self.camera is not None:
                    self.camera.release()
                    self.camera = None
                retry += 1
                time.sleep(min(1 * retry, 5))


camera_service = CameraService(CAMERA_SOURCE)

@app.route("/api/camera/stream")
def camera_stream():
    return Response(
        camera_service.generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)
