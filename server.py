#!/usr/bin/env python3
"""Development server for Codex II Chat Garden.

This module serves the static frontend and provides a stub `/api/chat` endpoint
so caretakers can verify the UI without wiring up a full model backend. The
handler echoes the latest user message while keeping the last assistant reply in
memory so the interface stays responsive.

Run with:
    python server.py --port 8000
"""

from __future__ import annotations

import argparse
import json
import os
import posixpath
from http import HTTPStatus
from http.server import ThreadingHTTPServer
from typing import Dict, List, Tuple

try:
    from http.server import SimpleHTTPRequestHandler
except ImportError:  # pragma: no cover - Python always ships http.server
    raise

RepositoryDir = os.path.dirname(os.path.abspath(__file__))
StaticDir = RepositoryDir


class ChatGardenHandler(SimpleHTTPRequestHandler):
    """Serve static files and handle `/api/chat` JSON POST requests."""

    server_version = "ChatGardenHTTP/1.0"

    def __init__(self, *args, directory: str = StaticDir, **kwargs) -> None:  # type: ignore[override]
        super().__init__(*args, directory=directory, **kwargs)

    def do_POST(self) -> None:  # noqa: N802  (http.server API uses camelCase)
        if self.path.rstrip("/") != "/api/chat":
            self.send_error(HTTPStatus.NOT_FOUND, "Unknown endpoint")
            return

        content_length = int(self.headers.get("Content-Length", 0))
        raw_body = self.rfile.read(content_length) if content_length else b""

        try:
            payload = json.loads(raw_body.decode("utf-8")) if raw_body else {}
        except json.JSONDecodeError:
            self.send_error(HTTPStatus.BAD_REQUEST, "Request body must be valid JSON")
            return

        message = _coerce_text(payload.get("message"))
        persona = _coerce_text(payload.get("persona"))
        history = payload.get("history")

        if not isinstance(history, list):
            history = []

        reply = build_reply(message=message, persona=persona, history=history)
        response = {"reply": reply}

        response_body = json.dumps(response).encode("utf-8")

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_body)))
        self.end_headers()
        self.wfile.write(response_body)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - mirrors base signature
        """Keep default logging but include method and path for POST calls."""
        super().log_message(format, *args)

    def translate_path(self, path: str) -> str:
        """Restrict static file lookups to the repository directory."""
        # `SimpleHTTPRequestHandler` attempts to walk the filesystem. Constrain
        # lookups so `/..` cannot escape the project root.
        path = posixpath.normpath(path)
        parts = [part for part in path.split("/") if part]
        full_path = StaticDir
        for part in parts:
            full_path = os.path.join(full_path, part)
        return full_path


def _coerce_text(value: object) -> str:
    return value if isinstance(value, str) else ""


def build_reply(message: str, persona: str, history: List[Dict[str, str]]) -> str:
    """Return a friendly placeholder response for local development."""

    if not message:
        return (
            "I'm online and ready to chat once you send a message. "
            "Wire me up to your local model when you're ready to go deeper!"
        )

    prefix_parts: List[str] = []
    if persona:
        prefix_parts.append("Persona active")
    if history:
        prefix_parts.append(f"History has {len(history)} entries")
    prefix = " (" + ", ".join(prefix_parts) + ")" if prefix_parts else ""

    return f"Echoing your last prompt{prefix}: {message}"


def parse_args() -> Tuple[str, int]:
    parser = argparse.ArgumentParser(description="Serve Codex II with a demo chat backend.")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="Port number (default: 8000)")
    args = parser.parse_args()
    return args.host, args.port


def main() -> None:
    host, port = parse_args()
    server = ThreadingHTTPServer((host, port), ChatGardenHandler)
    print(f"Serving Codex II on http://{host}:{port} (press Ctrl+C to quit)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
