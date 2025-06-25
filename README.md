# rtsp2jpeg-http-get

> Serve a single JPEG snapshot of an RTSP(S) camera stream on HTTP GET – minimal, memory-efficient, and docker-ready.

## 🚀 Features

- On-demand snapshot of any RTSP or RTSPS stream
- HTTP GET returns a fresh `.jpg` each time
- No disk I/O (in-memory encoding with OpenCV)
- .env-based configuration or CLI override
- `uv`-friendly, Docker-ready, and installable as CLI tool
- Perfect for use with FritzBox, Home Assistant, and other snapshot-based systems

---

## 🛠️ Installation

### Using `uv` (recommended):

```bash
uv pip install -e .
```

## Configuration via .env file or environment variables

```env
PORT=8080
RTSP_URL=rtsp://user:pass@192.168.178.42:7447/abc123
SNAPSHOT_PATH=/snapshot.jpg
USE_FFMPEG=false
INVALID_CERT=false
```