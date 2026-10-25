import http.server, os, tempfile, threading, time, unittest
import outbox, orders
from dispatcher import Dispatcher


class Hang(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        time.sleep(1.5)  # exceeds dispatcher timeout
    def log_message(self, *a): pass


class T(unittest.TestCase):
    def test_confirm_fast_and_webhook_not_lost_with_hanging_endpoint(self):
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Hang)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = "http://127.0.0.1:%d/" % srv.server_port
        db = os.path.join(tempfile.mkdtemp(), "t.db")
        outbox.init(db)
        conn = outbox.connect(db)
        d = Dispatcher(db, timeout=0.3, base=0.05, max_attempts=3, workers=16)
        d.start()
        lat = []
        for i in range(100):
            s = time.time()
            orders.confirm_order(conn, "o%d" % i, url)
            lat.append(time.time() - s)
        lat.sort()
        self.assertLess(lat[98], 1.5)
        end = time.time() + 20
        while time.time() < end and outbox.counts(conn).get("dead", 0) < 100:
            time.sleep(0.1)
        d.stop(); srv.shutdown()
        # every webhook accounted for: dead (visible), none missing
        self.assertEqual(outbox.counts(conn), {"dead": 100})


if __name__ == "__main__":
    unittest.main()
