import http.server
import socketserver
import cv2
import os
from docopt import docopt
from dotenv import load_dotenv

DOC = """
rtsp2jpeg-http-get

Usage:
  rtsp2jpeg_http_get [--port=PORT] [--url=RTSP_URL] [--path=PATH] [--ffmpeg] [--invalid-cert]

Options:
  --port=PORT         Port to listen on (overrides $PORT)
  --url=RTSP_URL      RTSP(S) stream URL (overrides $RTSP_URL)
  --path=PATH         HTTP path [default: /snapshot.jpg]
  --ffmpeg            Use FFMPEG backend for OpenCV
  --invalid-cert      Ignore invalid certificates (no effect unless using ffmpeg directly)
"""



class SnapshotHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.rtsp_url = kwargs.pop("rtsp_url")
        self.backend = kwargs.pop("backend")
        self.snapshot_path = kwargs.pop("snapshot_path")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        print(f"  Received GET request for: {self.path}")
        if self.path != self.snapshot_path:
            self.send_error(404, "Not found")
            return

        print(f"  Capturing snapshot from RTSP stream: {self.rtsp_url}")
        cap = cv2.VideoCapture(self.rtsp_url, self.backend)
        if not cap.isOpened():
            self.send_error(500, "Unable to open RTSP stream")
            return

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            self.send_error(500, "Failed to capture frame")
            return

        print("  Encoding frame to JPEG")
        success, encoded_image = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not success:
            self.send_error(500, "JPEG encoding failed")
            return

        image_bytes = encoded_image.tobytes()

        print(f"  Sending response with {len(image_bytes)} bytes")
        self.send_response(200)
        self.send_header("Content-type", "image/jpeg")
        self.send_header("Content-Length", str(len(image_bytes)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(image_bytes)
        print("  Snapshot sent successfully")

def run_server():
    load_dotenv()
    args = docopt(DOC)

    port = int(args["--port"] or os.getenv("PORT", 8080))
    rtsp_url = args["--url"] or os.getenv("RTSP_URL")
    snapshot_path = args["--path"] or os.getenv("SNAPSHOT_PATH", "/snapshot.jpg")
    use_ffmpeg = args["--ffmpeg"] or os.getenv("USE_FFMPEG", "false").lower() == "true"
    invalid_cert = args["--invalid-cert"] or os.getenv("INVALID_CERT", "false").lower() == "true"

    if not rtsp_url:
        raise ValueError("RTSP_URL must be provided via CLI or .env")

    backend = cv2.CAP_FFMPEG if use_ffmpeg else 0

    def handler(*args, **kwargs):
        return SnapshotHandler(*args, rtsp_url=rtsp_url, backend=backend, snapshot_path=snapshot_path, **kwargs)

    with socketserver.TCPServer(("", port), handler) as httpd:
        print(f"📸 http://0.0.0.0:{port}{snapshot_path}")
        print(f"🔗 Streaming from: {rtsp_url}")
        httpd.serve_forever()
