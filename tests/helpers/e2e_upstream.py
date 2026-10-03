from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._respond()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        if length:
            self.rfile.read(length)
        self._respond()

    def _respond(self):
        body = json.dumps({
            "upstream": True,
            "path": self.path,
            "decision": self.headers.get("X-SL-Decision"),
            "score": self.headers.get("X-SL-Score"),
            "gateway_processing_ms": self.headers.get("X-SL-Latency-Ms"),
            "gateway_stages_ms": {stage: self.headers.get(f"X-SL-{stage}-Latency-Ms") for stage in ("WAF", "Behavior", "Risk")},
            "gateway_degraded": self.headers.get("X-SL-Degraded"),
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        if self.path == "/safe":
            self.send_header("X-SL-Gateway-Processing-Ms", "999999")
            self.send_header("X-SL-Gateway-Degraded", "true")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return


if __name__ == "__main__":
    port = int(os.getenv("E2E_UPSTREAM_PORT", "18080"))
    class CapacityServer(ThreadingHTTPServer):
        # The default five-connection accept queue produced baseline connect
        # timeouts at 32 clients, independently of gateway processing.
        request_queue_size = 128

    CapacityServer(("127.0.0.1", port), Handler).serve_forever()
