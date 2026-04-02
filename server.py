import json
import os
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
import logic
import auth
from config import PORT, GENRE_MAP, GLOBAL_MEAN, SCORE_WEIGHTS, SITE_URL
from urllib.parse import urlparse, parse_qs

START_TIME = time.time()

class RequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress default HTTP logging
        
    def _send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def _parse_json_body(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
        except ValueError:
            return None, {"error": "Invalid Content-Length header."}, 400

        if content_length == 0:
            return None, {"error": "Empty request body."}, 400
        try:
            body = self.rfile.read(content_length)
            return json.loads(body), None, None
        except json.JSONDecodeError:
            return None, {"error": "Invalid JSON request body."}, 400

    def _get_content_type(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return {
            '.html': 'text/html',
            '.css': 'text/css',
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.svg': 'image/svg+xml',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg'
        }.get(ext, 'application/octet-stream')

    def _serve_static_file(self, filepath, content_type=None):
        try:
            with open(filepath, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type or self._get_content_type(filepath))
                self.end_headers()
                self.wfile.write(f.read())
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)

        if parsed_path.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            with open('frontend/index.html', 'r', encoding='utf-8') as f:
                html = f.read().replace("GENRE_MAP_PLACEHOLDER", json.dumps(GENRE_MAP))
                self.wfile.write(html.encode('utf-8'))

        elif parsed_path.path == '/api/status':
            uptime = int(time.time() - START_TIME)
            self._send_json_response(200, {
                'status': 'ok',
                'uptime_seconds': uptime,
                'version': '1.0',
                'site_url': SITE_URL
            })

        elif parsed_path.path == '/api/verify':
            query_params = parse_qs(parsed_path.query)
            token = query_params.get('token', [None])[0]
            verified = bool(token and auth.verify_token(token))

            self.send_response(200 if verified else 400)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()

            if verified:
                self.wfile.write(b"<h1>Email verified successfully! You can now close this tab and log in.</h1>")
            else:
                self.wfile.write(b"<h1>Invalid or expired verification link.</h1>")

        elif parsed_path.path.startswith('/api/'):
            self._send_json_response(404, {'error': 'API endpoint not found.'})

        else:
            root_dir = os.path.abspath('frontend')
            filepath = os.path.normpath(os.path.join(root_dir, parsed_path.path.lstrip('/')))
            if filepath.startswith(root_dir) and os.path.isfile(filepath):
                self._serve_static_file(filepath)
            else:
                self.send_response(404)
                self.end_headers()

    def do_POST(self):
        req, error_data, error_status = self._parse_json_body()
        if error_data:
            self._send_json_response(error_status, error_data)
            return

        if self.path == '/api/register':
            response_data, status = auth.register_user(
                req.get('email'), 
                req.get('password'),
                req.get('mal_user', ''),
                req.get('mal_api', '')
            )
            self._send_json_response(status, response_data)

        elif self.path == '/api/login':
            response_data, status = auth.login_user(req.get('email'), req.get('password'))
            self._send_json_response(status, response_data)
            
        elif self.path == '/api/verify_manual':
            success = auth.verify_token(req.get('token', ''))
            if success:
                self._send_json_response(200, {"message": "Account verified successfully!"})
            else:
                self._send_json_response(400, {"error": "Invalid or already used token."})

        elif self.path == '/api/settings':
            success = auth.update_settings(req.get('email'), req.get('mal_user'), req.get('mal_api'))
            self._send_json_response(200 if success else 401, {"success": success})

        elif self.path == '/api/recommend':
            print(f"\n" + "="*50)
            print(f"🚀 NEW RECOMMENDATION REQUEST RECEIVED")
            print(f"Included: {req.get('included')} | Excluded: {req.get('excluded')}")
            print(f"Targeting MAL User: {req.get('mal_user')}")
            print("="*50)
            
            results = logic.process_recommendations(
                included=req.get('included', []),
                excluded=req.get('excluded', []),
                linked_groups=req.get('linked_groups', []),
                top_x=req.get('top_x', 10),
                exclude_mal=req.get('exclude_mal', True),
                min_score=req.get('min_score', 7.0),
                logic_mode=req.get('logic_mode', 'and'),
                global_mean=req.get('global_mean', GLOBAL_MEAN),
                w_score=req.get('w_score', SCORE_WEIGHTS['score']),
                w_approval=req.get('w_approval', SCORE_WEIGHTS['approval']),
                w_engage=req.get('w_engage', SCORE_WEIGHTS['engage']),
                w_drop=req.get('w_drop', SCORE_WEIGHTS['drop']),
                mal_user=req.get('mal_user'), 
                mal_api=req.get('mal_api')    
            )
            
            self._send_json_response(200, results)
            print("\n✅ Results sent to UI!\n")
        else:
            self._send_json_response(404, {"error": "Endpoint not found."})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

if __name__ == "__main__":
    server = HTTPServer(('0.0.0.0', PORT), RequestHandler)
    print("=" * 50)
    print(f"🚀 SERVER RUNNING AT: {SITE_URL}")
    print("✨ Modular Architecture Active - Waiting for Authentication Requests")
    print("=" * 50)
    
    threading.Thread(target=lambda: webbrowser.open(SITE_URL)).start()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.server_close()