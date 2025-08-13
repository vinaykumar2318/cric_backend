# api/classify_image.py
import json
import sys
import io
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Make root imports work (so we can import util/wavelet)
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

import util  # loads artifacts on import

def _json_response(handler, status_code, payload_dict):
    body = json.dumps(payload_dict).encode("utf-8")
    handler.send_response(status_code)
    handler.send_header("Content-Type", "application/json")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")
    handler.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS, GET")
        self.end_headers()

    def do_GET(self):
        _json_response(self, 200, {"status": "ok", "message": "Use POST with image_data"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)

            ctype = (self.headers.get("Content-Type") or "").lower()

            image_data = None

            if "application/json" in ctype:
                body = json.loads(raw.decode("utf-8"))
                image_data = body.get("image_data") or body.get("image")
            elif "application/x-www-form-urlencoded" in ctype:
                parsed = urllib.parse.parse_qs(raw.decode("utf-8"))
                # jQuery $.post sends fields url-encoded
                vals = parsed.get("image_data") or parsed.get("image")
                if vals:
                    image_data = vals[0]
            else:
                # Try raw text (base64 data URL posted as text/plain)
                text = raw.decode("utf-8", errors="ignore")
                if text.strip().startswith("{"):
                    body = json.loads(text)
                    image_data = body.get("image_data") or body.get("image")
                else:
                    image_data = text.strip()

            if not image_data:
                return _json_response(self, 400, {"error": "image_data missing"})

            result = util.classify_image(image_data)
            return _json_response(self, 200, result)

        except Exception as e:
            return _json_response(self, 500, {"error": str(e)})
