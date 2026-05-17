from __future__ import annotations

import json
import sys
from http.server import BaseHTTPRequestHandler
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fusion_material_ai import screen_candidates  # noqa: E402
from server import DEFAULT_PROMPT  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def _send_json(self, payload: object, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(length).decode("utf-8") if length else "{}"
            payload = json.loads(raw_body or "{}")
            prompt = str(payload.get("prompt") or DEFAULT_PROMPT)
            samples = max(100, min(10000, int(payload.get("samples", 2500))))
            top = max(5, min(100, int(payload.get("top", 25))))
            self._send_json(screen_candidates(prompt, samples=samples, top_n=top))
        except Exception as exc:
            self._send_json({"error": str(exc)}, 500)

    def do_GET(self) -> None:
        self._send_json({"error": "POST required"}, 405)
