import os
import cv2
import time
from flask import Flask, Response, abort, request
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

CAMERA_SOURCE = os.getenv("CAMERA_SOURCE")
RELAY_TOKEN = os.getenv("RELAY_TOKEN", "change-this-token")

os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;tcp"


def generate_frames():
    cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_FFMPEG)

    while True:
        if not cap.isOpened():
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_FFMPEG)
            continue

        success, frame = cap.read()

        if not success:
            cap.release()
            time.sleep(2)
            cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_FFMPEG)
            continue

        ok, buffer = cv2.imencode(".jpg", frame)

        if not ok:
            continue

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" +
            buffer.tobytes() +
            b"\r\n"
        )


@app.route("/camera-stream")
def camera_stream():
    token = request.args.get("token")

    if token != RELAY_TOKEN:
        abort(403)

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )


@app.route("/camera-status")
def camera_status():
    token = request.args.get("token")

    if token != RELAY_TOKEN:
        abort(403)

    cap = cv2.VideoCapture(CAMERA_SOURCE, cv2.CAP_FFMPEG)
    online = cap.isOpened()
    cap.release()

    return {
        "status": "ONLINE" if online else "OFFLINE"
    }


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)