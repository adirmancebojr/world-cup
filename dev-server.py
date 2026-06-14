"""Local preview server for docs/ that disables caching, so edits to
style.css / main.js show up on a plain reload. Threaded so parallel asset
fetches (module + geojson + JSON) don't block each other. Dev-only — the
production host (GitHub Pages) serves docs/ with its own headers."""
import functools
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8377
DIRECTORY = sys.argv[2] if len(sys.argv) > 2 else "docs"


class Handler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        super().end_headers()


handler = functools.partial(Handler, directory=DIRECTORY)
with ThreadingHTTPServer(("", PORT), handler) as httpd:
    print(f"serving {DIRECTORY}/ on http://localhost:{PORT} (no-cache, threaded)")
    httpd.serve_forever()
