import http.server, threading, time


def make_server(handler_fn):
    """handler_fn(handler, body, headers) -> status code (may sleep)."""
    class H(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            n = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(n).decode()
            try:
                code = handler_fn(self, body, self.headers)
                self.send_response(code); self.send_header("Content-Length", "0"); self.end_headers()
            except Exception:
                pass
        def log_message(self, *a): pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    srv.daemon_threads = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_address[1]}/hook"


def wait_until(pred, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        if pred():
            return True
        time.sleep(0.05)
    return False
