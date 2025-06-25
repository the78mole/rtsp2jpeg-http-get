import http.server
import socketserver
import os
import cv2
from io import BytesIO
from dotenv import load_dotenv
from docopt import docopt

DOC = """
rtsp2jpeg-http-get

Usage:
  rtsp2jpeg_http_get [--port=PORT] [--ffmpeg] [--invalid-cert]

Options:
  --port=PORT         Port to listen on
  --ffmpeg            Use FFMPEG backend for OpenCV
  --invalid-cert      Ignore invalid certificates (no effect unless using ffmpeg directly)
"""

def load_snapshot_routes_from_env():
    routes = {}
    for key, value in os.environ.items():
        if key.startswith("SNAPSHOT_") and "::" in value:
            path, url = value.split("::", 1)
            routes[path.strip()] = url.strip()
    return routes

class MultiSnapshotHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.routes = kwargs.pop("routes")
        self.backend = kwargs.pop("backend")
        super().__init__(*args, **kwargs)

    def do_GET(self):
        print(f"  Received request for {self.path}")
        rtsp_url = self.routes.get(self.path)
        if not rtsp_url:
            self.send_error(404, f"Snapshot path '{self.path}' not configured")
            return

        print(f"  Fetching snapshot from {rtsp_url}")
        cap = cv2.VideoCapture(rtsp_url, self.backend)
        if not cap.isOpened():
            self.send_error(500, f"Unable to open RTSP stream for path '{self.path}'")
            return

        print(f"  Capturing frame from {rtsp_url}")
        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            self.send_error(500, f"Failed to capture frame from '{self.path}'")
            return

        print(f"  Encoding frame to JPEG for {self.path}")
        success, encoded_image = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
        if not success:
            self.send_error(500, "JPEG encoding failed")
            return

        image_bytes = encoded_image.tobytes()

        print(f"  Sending response for {self.path} ({len(image_bytes)} bytes)")
        self.send_response(200)
        self.send_header("Content-type", "image/jpeg")
        self.send_header("Content-Length", str(len(image_bytes)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(image_bytes)
        print(f"  Response sent for {self.path}")

def run_server():
    load_dotenv()
    args = docopt(DOC)

    port = int(args["--port"] or os.getenv("PORT", 8080))
    use_ffmpeg = args["--ffmpeg"] or os.getenv("USE_FFMPEG", "false").lower() == "true"
    invalid_cert = args["--invalid-cert"] or os.getenv("INVALID_CERT", "false").lower() == "true"

    backend = cv2.CAP_FFMPEG if use_ffmpeg else 0
    routes = load_snapshot_routes_from_env()

    if not routes:
        raise ValueError("No snapshot paths configured. Define SNAPSHOT_CAMx entries in .env")

    print(f"🚀 Starting rtsp2jpeg-http-get on 0.0.0.0:{port}")
    for path, url in routes.items():
        print(f"📸 Serving {path} → {url}")

    def handler(*args, **kwargs):
        return MultiSnapshotHandler(*args, routes=routes, backend=backend, **kwargs)

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("0.0.0.0", port), handler) as httpd:
        httpd.serve_forever()
