"""
TectonicWeb 统一入口(端口 8090)
- 静态页面(从 TectonicWeb/)
- API 反代(/api/* → 127.0.0.1:5189)
这样 8090 跟 5189 行为一致,任一端口都能用,数据来自同一份 construction.db
"""
import http.server
import urllib.request
from pathlib import Path

STATIC_DIR = Path(__file__).parent.parent / "TectonicWeb"
API_TARGET = "http://127.0.0.1:5189"
PORT = 8090


class UnifiedHandler(http.server.SimpleHTTPRequestHandler):
    # 让 SimpleHTTPRequestHandler 把 STATIC_DIR 当根目录
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(STATIC_DIR), **kwargs)

    def do_GET(self):
        # /api/* 转发到 5189
        if self.path.startswith("/api/"):
            self._proxy()
            return
        # 根路径 → index.html
        if self.path == "/" or self.path == "":
            self.path = "/index.html"
        # 其它路径走静态文件(SimpleHTTPRequestHandler 默认会处理)
        return super().do_GET()

    def end_headers(self):
        # 静态文件加 no-cache 头(HTML/CSS/JS 一改就生效)
        if not self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_POST(self):
        if self.path.startswith("/api/"):
            self._proxy()
            return
        self.send_error(405)

    def _proxy(self):
        url = API_TARGET + self.path
        try:
            # 透传 body(POST 用)
            body = None
            if self.command == "POST":
                length = int(self.headers.get("Content-Length", "0") or 0)
                body = self.rfile.read(length) if length > 0 else None
            req = urllib.request.Request(url, data=body, method=self.command)
            with urllib.request.urlopen(req, timeout=15) as r:
                data = r.read()
                self.send_response(r.status)
                # 透传 content-type,去掉 flask 加的 Connection: close 让长连接不频繁重建
                ct = r.headers.get("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            body = e.read()
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            msg = f'{{"error": "proxy failed: {e}"}}'.encode("utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)

    def log_message(self, fmt, *args):
        # 静默日志
        pass


if __name__ == "__main__":
    print(f"TectonicWeb 统一入口")
    print(f"  页面: http://127.0.0.1:{PORT}/")
    print(f"  API:  /api/*  →  {API_TARGET}")
    print(f"  静态: {STATIC_DIR}")
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), UnifiedHandler)
    server.serve_forever()
