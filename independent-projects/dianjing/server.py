"""Point-and-guess playground. Serve the same files used by the GitHub Pages demo."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATIC = Path(__file__).resolve().parent / "static"


class GameHandler(SimpleHTTPRequestHandler):
    extensions_map = {**SimpleHTTPRequestHandler.extensions_map, ".mjs": "text/javascript; charset=utf-8"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def list_directory(self, path):
        self.send_error(404, "Directory listing is disabled")


def create_server(host="127.0.0.1", port=6951):
    return ThreadingHTTPServer((host, port), GameHandler)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="点睛 · 你画我猜")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=6951)
    args = parser.parse_args()
    with create_server(args.host, args.port) as server:
        print(f"点睛已启动：http://{args.host}:{args.port} / Ctrl+C 停止")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
