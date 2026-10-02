"""Shared HTTP test server helpers."""

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Iterator


class PayloadHandler(BaseHTTPRequestHandler):
    """Serves a fixed 256 KiB payload."""

    payload: bytes = b"x" * (256 * 1024)

    def do_GET(self) -> None:  # noqa: N802 - http.server protocol
        self.send_response(200)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(len(self.payload)))
        self.end_headers()
        self.wfile.write(self.payload)

    def log_message(self, format: str, *args: object) -> None:
        return


def serve(handler: type[BaseHTTPRequestHandler]) -> Iterator[str]:
    httpd = HTTPServer(("127.0.0.1", 0), handler)
    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}/payload.bin"
    finally:
        httpd.shutdown()
        httpd.server_close()
