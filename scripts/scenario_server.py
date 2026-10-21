"""Independent controlled HTTP source. Not a fabricated third-party API."""

import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "data/scenarios/assessment"


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return
        if self.path in ("/http401", "/http403", "/http429", "/http500"):
            self.send_response(int(self.path[-3:]))
            self.end_headers()
            return
        status = 503 if self.path == "/unavailable" else 200
        if self.path == "/slow":
            time.sleep(3)
        if self.path == "/hold":
            # Private rehearsal probe: interrupt a real workflow before persistence.
            time.sleep(30)
        files = {
            "/calendar.ics": ("calendar.ics", "text/calendar"),
            "/records.json": ("records.json", "application/json"),
            "/malformed": ("malformed.txt", "text/plain"),
            "/hold": ("records.json", "application/json"),
        }
        if self.path not in files:
            self.send_response(status if status != 200 else 404)
            self.end_headers()
            return
        filename, content_type = files[self.path]
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.end_headers()
        try:
            self.wfile.write((ROOT / filename).read_bytes())
        except BrokenPipeError:
            pass

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", 8090), Handler).serve_forever()
