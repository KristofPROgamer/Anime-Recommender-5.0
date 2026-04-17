"""
Anime Recommender v1.0 — HTTP Server
Handles static file serving, authentication, and recommendation endpoints.
"""

import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

import logic
import auth
from config import PORT, GENRE_MAP, GLOBAL_MEAN, SCORE_WEIGHTS, SITE_URL

START_TIME = time.time()
VERSION = "1.0.0"


class RequestHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        pass  # Suppress default HTTP request logging; server.py prints its own

    def _send_json(self, status: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(body)

    def _parse_json_body(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            return None, {"error": "Invalid Content-Length header."}, 400

        if length == 0:
            return None, {"error": "Empty request body."}, 400

        try:
            body = self.rfile.read(length)
            return json.loads(body), None, None
        except json.JSONDecodeError:
            return None, {"error": "Invalid JSON in request body."}, 400

    def _get_content_type(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        return {
            ".html": "text/html",
            ".css": "text/css",
            ".js": "application/javascript",
            ".json": "application/json",
            ".svg": "image/svg+xml",
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".ico": "image/x-icon",
        }.get(ext, "application/octet-stream")

    def _serve_static_file(self, filepath: str):
        try:
            with open(filepath, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", self._get_content_type(filepath))
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except FileNotFoundError:
            self._send_json(404, {"error": "File not found."})

    # ------------------------------------------------------------------
    # GET
    # ------------------------------------------------------------------
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # Root — serve index.html with injected GENRE_MAP
        if path == "/":
            try:
                with open("frontend/index.html", "r", encoding="utf-8") as f:
                    html = f.read().replace("GENRE_MAP_PLACEHOLDER", json.dumps(GENRE_MAP))
                body = html.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            except FileNotFoundError:
                self._send_json(500, {"error": "frontend/index.html not found."})

        elif path == "/api/status":
            self._send_json(200, {
                "status": "ok",
                "version": VERSION,
                "uptime_seconds": int(time.time() - START_TIME),
                "db_entries": len(logic.ANIME_DB),
                "site_url": SITE_URL,
            })

        elif path.startswith("/api/"):
            self._send_json(404, {"error": "API endpoint not found."})

        else:
            # Static files from frontend/
            root = os.path.abspath("frontend")
            filepath = os.path.normpath(os.path.join(root, path.lstrip("/")))
            if filepath.startswith(root) and os.path.isfile(filepath):
                self._serve_static_file(filepath)
            else:
                self._send_json(404, {"error": "Not found."})

    # ------------------------------------------------------------------
    # POST
    # ------------------------------------------------------------------
    def do_POST(self):
        req, error_data, error_status = self._parse_json_body()
        if error_data:
            self._send_json(error_status, error_data)
            return

        path = self.path

        if path == "/api/register":
            data, status = auth.register_user(
                req.get("email"),
                req.get("password"),
                req.get("mal_user", ""),
                req.get("mal_api", ""),
            )
            self._send_json(status, data)

        elif path == "/api/login":
            data, status = auth.login_user(req.get("email"), req.get("password"))
            self._send_json(status, data)

        elif path == "/api/verify_manual":
            success = auth.verify_token(req.get("token", ""))
            if success:
                self._send_json(200, {"message": "Account verified successfully!"})
            else:
                self._send_json(400, {"error": "Invalid or already used token."})

        elif path == "/api/settings":
            success = auth.update_settings(
                req.get("email"),
                req.get("mal_user", ""),
                req.get("mal_api", ""),
            )
            self._send_json(200 if success else 401, {"success": success})

        elif path == "/api/recommend":
            print("\n" + "=" * 50)
            print("🚀 RECOMMENDATION REQUEST")
            print(f"   Included : {req.get('included')}")
            print(f"   Excluded : {req.get('excluded')}")
            print(f"   User     : {req.get('mal_user') or '(default)'}")
            print("=" * 50)

            results = logic.process_recommendations(
                included=req.get("included", []),
                excluded=req.get("excluded", []),
                linked_groups=req.get("linked_groups", []),
                top_x=req.get("top_x", 10),
                exclude_mal=req.get("exclude_mal", True),
                min_score=req.get("min_score", 7.0),
                logic_mode=req.get("logic_mode", "and"),
                global_mean=req.get("global_mean", GLOBAL_MEAN),
                w_score=req.get("w_score", SCORE_WEIGHTS["score"]),
                w_approval=req.get("w_approval", SCORE_WEIGHTS["approval"]),
                w_engage=req.get("w_engage", SCORE_WEIGHTS["engage"]),
                w_drop=req.get("w_drop", SCORE_WEIGHTS["drop"]),
                mal_user=req.get("mal_user"),
                mal_api=req.get("mal_api"),
            )
            self._send_json(200, results)
            print(f"✅ Sent {len(results)} results.\n")

        else:
            self._send_json(404, {"error": "Endpoint not found."})

    # ------------------------------------------------------------------
    # OPTIONS (CORS preflight)
    # ------------------------------------------------------------------
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), RequestHandler)
    print("=" * 50)
    print(f"  Anime Recommender v{VERSION}")
    print(f"  Running at: {SITE_URL}")
    print(f"  Database  : {len(logic.ANIME_DB):,} anime entries loaded")
    print("=" * 50)

    threading.Thread(target=lambda: (time.sleep(0.5), webbrowser.open(SITE_URL)), daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n⛔ Server stopped.")
        server.server_close()
