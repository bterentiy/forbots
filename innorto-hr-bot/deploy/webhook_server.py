import hmac
import hashlib
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler

GITHUB_SECRET = b"ЗАМЕНИ_НА_СВОЙ_СЕКРЕТ"
BOT_SERVICE = "innorto-hr-bot"
REPO_DIR = "/root/forbots"


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/deploy":
            self.send_response(404)
            self.end_headers()
            return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        sig = self.headers.get("X-Hub-Signature-256", "")
        expected = "sha256=" + hmac.new(GITHUB_SECRET, body, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            self.send_response(403)
            self.end_headers()
            return

        subprocess.run(["git", "-C", REPO_DIR, "pull"], check=True)
        subprocess.run(["systemctl", "restart", BOT_SERVICE], check=True)

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 9000), WebhookHandler)
    print("Webhook listening on :9000/deploy")
    server.serve_forever()
