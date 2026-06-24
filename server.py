from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

PORT = int(os.environ.get("PORT", 8080))

class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

httpd = HTTPServer(("0.0.0.0", PORT), Handler)
print(f"Server web berjalan di port {PORT}")
httpd.serve_forever()
