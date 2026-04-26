"""Tiny HTTP preview server — see what the webcam is sending Gemini.

Routes:
  /          HTML page that auto-refreshes the live view
  /live.jpg  Most recent webcam frame (fresh, captured on demand)
  /last.jpg  Last frame actually sent to Gemini (set by Camera.capture_jpeg)

Open http://<pi-ip>:8080/ from any device on the same network.
"""
from __future__ import annotations
import logging
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

log = logging.getLogger(__name__)

INDEX_HTML = b"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<title>PalAI camera preview</title>
<style>
  body { background:#0a0a0b; color:#e5e7eb; font-family:system-ui, sans-serif;
         margin:0; padding:1.5rem; }
  h1 { font-size:1.1rem; margin:0 0 1rem; font-weight:600; }
  .row { display:grid; gap:1rem; grid-template-columns:1fr; }
  @media (min-width:900px){ .row { grid-template-columns:1fr 1fr; } }
  .card { background:#18181b; border:1px solid #27272a; border-radius:.75rem;
          padding:.75rem; }
  .card h2 { font-size:.85rem; color:#a1a1aa; margin:0 0 .5rem; font-weight:500;
             text-transform:uppercase; letter-spacing:.05em; }
  img { width:100%; border-radius:.5rem; display:block; background:#000; }
  small { color:#71717a; }
</style>
</head>
<body>
<h1>PalAI camera preview</h1>
<div class="row">
  <div class="card">
    <h2>Live (refreshes every second)</h2>
    <img id="live" src="/live.jpg" alt="live" />
    <small>This is what Scan would capture right now.</small>
  </div>
  <div class="card">
    <h2>Last sent to Gemini</h2>
    <img id="last" src="/last.jpg" alt="last" onerror="this.style.opacity=.3" />
    <small>Updates every time you tap Scan in the webapp.</small>
  </div>
</div>
<script>
  const live = document.getElementById('live');
  const last = document.getElementById('last');
  setInterval(() => { live.src = '/live.jpg?t=' + Date.now(); }, 1000);
  setInterval(() => { last.src = '/last.jpg?t=' + Date.now(); }, 2000);
</script>
</body>
</html>
"""


def make_handler(camera, last_frame_path: str):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args, **_kwargs):
            # Quiet — don't spam stdout with every refresh.
            return

        def _send_jpeg(self, data: bytes):
            try:
                self.send_response(200)
                self.send_header("Content-Type", "image/jpeg")
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                # Browser closed the connection mid-response. Harmless.
                pass

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            if path in ("/", "/index.html"):
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(INDEX_HTML)))
                self.end_headers()
                self.wfile.write(INDEX_HTML)
                return
            if path == "/live.jpg":
                try:
                    data = camera.grab_jpeg()
                except Exception as e:
                    log.warning("live grab failed: %s", e)
                    self.send_error(500, "camera error")
                    return
                self._send_jpeg(data)
                return
            if path == "/last.jpg":
                try:
                    with open(last_frame_path, "rb") as f:
                        data = f.read()
                except FileNotFoundError:
                    self.send_error(404, "no scan yet")
                    return
                self._send_jpeg(data)
                return
            self.send_error(404)

    return Handler


def start(camera, host: str = "0.0.0.0", port: int = 8080) -> ThreadingHTTPServer:
    from camera import LAST_FRAME_PATH
    handler = make_handler(camera, LAST_FRAME_PATH)
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(
        target=server.serve_forever, name="preview", daemon=True
    )
    thread.start()
    log.info("📺 preview server: http://%s:%d/  (open on any device on the LAN)",
             _get_lan_ip() or host, port)
    return server


def _get_lan_ip() -> str | None:
    """Best-effort: connect a UDP socket to find the local IP."""
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None
