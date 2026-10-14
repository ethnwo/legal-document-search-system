
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

UPLOAD_DIR = Path("/var/data/incoming")
UPLOAD_TOKEN = os.environ.get("TRANSFER_TOKEN")

# Only these filenames may be uploaded.
ALLOWED_FILES = {
    "cases.json",
    "index.faiss",
    "chunks.json",
    "chunk_case_indices.npy",
    "metadata.db",
    "raw_cases.tar.gz",
}


class TransferHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if urlparse(self.path).path != "/health":
            self.send_error(404)
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Transfer service is running.")

    def do_POST(self):
        filename = unquote(urlparse(self.path).path.removeprefix("/upload/"))

        if filename not in ALLOWED_FILES:
            self.send_error(400, "Filename not allowed")
            return

        if not UPLOAD_TOKEN:
            self.send_error(500, "TRANSFER_TOKEN is not configured")
            return

        supplied_token = self.headers.get("X-Upload-Token", "")
        if not __import__("hmac").compare_digest(
            supplied_token, UPLOAD_TOKEN
        ):
            self.send_error(403, "Invalid upload token")
            return

        try:
            length = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.send_error(411, "Content-Length required")
            return

        if length <= 0:
            self.send_error(400, "Empty upload")
            return

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        destination = UPLOAD_DIR / filename
        temporary = UPLOAD_DIR / (filename + ".uploading")

        try:
            remaining = length
            with temporary.open("wb") as output:
                while remaining:
                    chunk = self.rfile.read(min(1024 * 1024, remaining))
                    if not chunk:
                        raise ConnectionError("Upload ended prematurely")
                    output.write(chunk)
                    remaining -= len(chunk)

            temporary.replace(destination)

        except Exception:
            temporary.unlink(missing_ok=True)
            self.send_error(500, "Upload failed")
            return

        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Uploaded {filename}".encode())

    def log_message(self, format, *args):
        print(f"[transfer] {format % args}")


if __name__ == "__main__":
    if not UPLOAD_TOKEN:
        raise RuntimeError("Set TRANSFER_TOKEN before starting.")

    port = int(os.environ.get("PORT", "10000"))
    server = HTTPServer(("0.0.0.0", port), TransferHandler)
    print(f"Transfer service listening on port {port}")
    server.serve_forever()
