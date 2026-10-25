import os, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webhooks


def make_server(behavior):
    got = []

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            eid = self.headers["X-Webhook-Id"]
            n = int(self.headers.get("Content-Length", 0)); self.rfile.read(n)
            code = behavior(eid, got)
            if code is None:  # hang to force client timeout
                time.sleep(1.5); code = 200
            self.send_response(code); self.send_header("Content-Length", "0"); self.end_headers()
            if code == 200: got.append(eid)
        def log_message(self, *a): pass
    s = ThreadingHTTPServer(("127.0.0.1", 0), H); s.daemon_threads = True
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s, got, "http://127.0.0.1:%d/" % s.server_address[1]


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp(); self.db = os.path.join(self.d, "t.db")
        webhooks.init_db(self.db); self.conn = webhooks.connect(self.db)

    def add_orders(self, n, url):
        self.conn.execute("BEGIN")
        for i in range(1, n + 1):
            self.conn.execute("INSERT INTO orders(id,webhook_url) VALUES(?,?)", (i, url))
        self.conn.execute("COMMIT")

    def counts(self):
        return dict(self.conn.execute("SELECT status,COUNT(*) FROM outbox GROUP BY status"))

    def wait_all(self, n, t=30):
        end = time.time() + t
        while time.time() < end:
            if self.counts().get("delivered", 0) == n: return True
            time.sleep(0.05)
        return False


class TestOutbox(Base):
    def test_confirm_enqueues_atomically(self):
        self.add_orders(1, "http://x/")
        webhooks.confirm_order(self.conn, 1)
        self.assertEqual(self.conn.execute("SELECT status FROM orders").fetchone()[0], "confirmed")
        self.assertEqual(self.counts(), {"pending": 1})

    def test_unknown_order_rolls_back(self):
        with self.assertRaises(KeyError): webhooks.confirm_order(self.conn, 99)
        self.assertEqual(self.counts(), {})

    def test_claim_is_exclusive_and_lease_expiry_recovers(self):
        self.add_orders(1, "http://x/"); webhooks.confirm_order(self.conn, 1)
        self.assertIsNotNone(webhooks.claim(self.conn, lease=10))
        self.assertIsNone(webhooks.claim(self.conn, lease=10))          # held
        self.assertIsNotNone(webhooks.claim(self.conn, lease=10, now=time.time() + 11))  # crash recovery


class TestDelivery(Base):
    def test_slow_endpoint_p99_and_no_loss(self):
        srv, got, url = make_server(lambda eid, g: None)  # always hangs 1.5s; client timeout 0.3s
        self.add_orders(200, url)
        disp = webhooks.Dispatcher(self.db, workers=16, timeout=0.3, backoff_base=0.05, backoff_cap=0.2)
        disp.start()
        lat = []
        for i in range(1, 201):
            t = time.perf_counter(); webhooks.confirm_order(self.conn, i); lat.append(time.perf_counter() - t)
        lat.sort(); p99 = lat[int(len(lat) * 0.99) - 1]
        self.assertLess(p99, 1.5, p99)
        # endpoint recovers: now accept everything
        srv.shutdown()
        srv2, got2, url2 = make_server(lambda e, g: 200)
        self.conn.execute("UPDATE outbox SET url=? WHERE status!='delivered'", (url2,))
        self.assertTrue(self.wait_all(200)); disp.stop()
        self.assertEqual(self.counts(), {"delivered": 200})

    def test_retry_until_success_burst(self):
        seen = {}
        def beh(eid, g):
            seen[eid] = seen.get(eid, 0) + 1
            return 500 if seen[eid] == 1 else 200   # every event fails once
        srv, got, url = make_server(beh)
        self.add_orders(300, url)
        disp = webhooks.Dispatcher(self.db, workers=16, timeout=2, backoff_base=0.05, backoff_cap=0.2)
        disp.start()
        for i in range(1, 301): webhooks.confirm_order(self.conn, i)
        self.assertTrue(self.wait_all(300)); disp.stop(); srv.shutdown()
        self.assertEqual(len(set(got)), 300)

    def test_dead_letter_retained(self):
        srv, got, url = make_server(lambda e, g: 500)
        self.add_orders(1, url); webhooks.confirm_order(self.conn, 1)
        disp = webhooks.Dispatcher(self.db, max_attempts=2, backoff_base=0.01)
        while self.counts().get("dead", 0) == 0:
            disp.process_one(self.conn); time.sleep(0.02)
        srv.shutdown()
        self.assertEqual(self.counts(), {"dead": 1})


if __name__ == "__main__":
    unittest.main()
