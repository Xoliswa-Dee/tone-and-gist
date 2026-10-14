"""A small web server built on the standard library.

Routes
    GET  /                  the web app
    GET  /api/samples       bundled sample texts
    POST /api/analyze       JSON {"text": "..."}  ->  analysis
    POST /api/analyze-file  raw file bytes + X-Filename header  ->  analysis
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
from urllib.parse import unquote, urlsplit

from .analyzer import AnalysisError, analyze_text
from .readers import MAX_FILE_BYTES, UnsupportedFileError, read_text
from .samples import load_samples

WEB_DIR = Path(__file__).parent / "web"
MAX_BODY_BYTES = MAX_FILE_BYTES + 1024 * 1024

# Only these files are ever served, so there is no path to traverse.
STATIC_FILES: Dict[str, Tuple[str, str]] = {
    "/": ("index.html", "text/html; charset=utf-8"),
    "/index.html": ("index.html", "text/html; charset=utf-8"),
    "/style.css": ("style.css", "text/css; charset=utf-8"),
    "/app.js": ("app.js", "application/javascript; charset=utf-8"),
}
SECURITY_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
}


class Handler(BaseHTTPRequestHandler):
    server_version = "ToneAndGist/1.0"

    # -- helpers ---------------------------------------------------------
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        for name, value in SECURITY_HEADERS.items():
            self.send_header(name, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, status: int, payload: Any) -> None:
        self._send(status, json.dumps(payload, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def _error(self, status: int, message: str) -> None:
        self._json(status, {"error": message})

    def _read_body(self) -> Optional[bytes]:
        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self._error(411, "A Content-Length header is required.")
            return None
        if length < 0 or length > MAX_BODY_BYTES:
            self._error(413, "That request is too large. Files are limited to 15 MB.")
            return None
        return self.rfile.read(length)

    # -- routes ----------------------------------------------------------
    def do_GET(self) -> None:  # noqa: N802 (http.server naming)
        path = urlsplit(self.path).path
        if path == "/api/samples":
            self._json(200, load_samples())
        elif path in STATIC_FILES:
            filename, content_type = STATIC_FILES[path]
            self._send(200, (WEB_DIR / filename).read_bytes(), content_type)
        else:
            self._error(404, "Not found.")

    do_HEAD = do_GET  # noqa: N815

    def do_POST(self) -> None:  # noqa: N802
        path = urlsplit(self.path).path
        if path not in ("/api/analyze", "/api/analyze-file"):
            self._error(404, "Not found.")
            return
        body = self._read_body()
        if body is None:
            return
        try:
            if path == "/api/analyze":
                try:
                    payload = json.loads(body.decode("utf-8"))
                    text = payload["text"]
                except (ValueError, KeyError, TypeError):
                    raise AnalysisError('Send JSON like {"text": "..."}.')
                if not isinstance(text, str):
                    raise AnalysisError('"text" must be a string.')
            else:
                filename = unquote(self.headers.get("X-Filename", ""))
                text = read_text(filename, body)
            self._json(200, analyze_text(text).to_dict())
        except (AnalysisError, UnsupportedFileError) as error:
            self._error(422, str(error))

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        if not getattr(self.server, "quiet", False):
            super().log_message(format, *args)


def create_server(host: str = "127.0.0.1", port: int = 8000, quiet: bool = False) -> ThreadingHTTPServer:
    server = ThreadingHTTPServer((host, port), Handler)
    server.quiet = quiet  # type: ignore[attr-defined]
    return server


def serve(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = create_server(host, port)
    print(f"Tone & Gist is running at http://{host}:{port}  (press Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
