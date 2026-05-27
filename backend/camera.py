import cv2
import time
import os


class CameraService:
    def __init__(self, source=0):
        self.source = int(source) if str(source).isdigit() else source
        self.camera = None

        # Helps RTSP cameras like Tapo use TCP instead of UDP
        os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"

    def connect(self):
        if self.camera is not None and self.camera.isOpened():
            return True

        self.camera = cv2.VideoCapture(self.source, cv2.CAP_FFMPEG)

        if not self.camera.isOpened():
            self.camera.release()
            self.camera = None
            return False

        return True

    def generate_frames(self):
        while True:
            try:
                if not self.connect():
                    time.sleep(2)
                    continue

                success, frame = self.camera.read()

                if not success:
                    self.release()
                    time.sleep(2)
                    continue

                ret, buffer = cv2.imencode(".jpg", frame)

                if not ret:
                    continue

                frame_bytes = buffer.tobytes()

                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" +
                    frame_bytes +
                    b"\r\n"
                )

            except Exception as error:
                print("Camera error:", error)
                self.release()
                time.sleep(2)

    def release(self):
        if self.camera is not None:
            self.camera.release()
            self.camera = None