import os, sys, tempfile, threading, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outbox, orders
from dispatcher import Dispatcher
from fakeserver import make_server, wait_until


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "t.db")
        self.conn = outbox.connect(self.path)
        orders.init_schema(self.conn)
        self.disp = None

    def tearDown(self):
        if self.disp: self.disp.stop()
        self.srv.shutdown(); self.srv.server_close()
        self.conn.close(); self.dir.cleanup()

    def _start(self, **kw):
        self.disp = Dispatcher(self.path, **kw); self.disp.start()

    def test_delivers_with_headers(self):
        got = []
        self.srv, url = make_server(lambda h, b, hd: (got.append((b, hd["X-Webhook-Id"])), 200)[1])
        wid = outbox.enqueue(self.conn, "o1", url, {"a": 1})
        self._start()
        self.assertTrue(wait_until(lambda: outbox.stats(self.conn)["delivered"] == 1))
        self.assertEqual(got[0][1], wid)

    def test_retry_then_success(self):
        calls = []
        def fn(h, b, hd):
            calls.append(1)
            return 500 if len(calls) < 3 else 200
        self.srv, url = make_server(fn)
        outbox.enqueue(self.conn, "o1", url, {})
        self._start(backoff_base=0.05, backoff_cap=0.2)
        self.assertTrue(wait_until(lambda: outbox.stats(self.conn)["delivered"] == 1))
        att = self.conn.execute("SELECT attempts FROM webhook_outbox").fetchone()[0]
        self.assertEqual(att, 3)

    def test_crash_recovery_in_flight(self):
        got = []
        self.srv, url = make_server(lambda h, b, hd: (got.append(1), 200)[1])
        outbox.enqueue(self.conn, "o1", url, {}, now=1)
        outbox.claim_due(self.conn, 10, 0.1)       # "crashed" worker claimed it
        self._start(lease=0.1)
        self.assertTrue(wait_until(lambda: outbox.stats(self.conn)["delivered"] == 1))

    def test_dead_after_max_attempts(self):
        self.srv, url = make_server(lambda h, b, hd: 500)
        outbox.enqueue(self.conn, "o1", url, {})
        self._start(max_attempts=2, backoff_base=0.05, backoff_cap=0.1)
        self.assertTrue(wait_until(lambda: outbox.stats(self.conn)["dead"] == 1))

    def test_burst_1000_no_loss(self):
        seen = set(); lock = threading.Lock()
        def fn(h, b, hd):
            with lock: seen.add(hd["X-Webhook-Id"])
            return 200
        self.srv, url = make_server(fn)
        self._start()
        ids = set()
        for i in range(1000):
            self.conn.execute("INSERT INTO orders(id, webhook_url) VALUES (?,?)", (f"b{i}", url))
            ids.add(orders.confirm_order(self.conn, f"b{i}"))
        self.assertTrue(wait_until(lambda: outbox.stats(self.conn)["delivered"] == 1000, 60))
        self.assertEqual(seen, ids)

    def test_bad_url_does_not_starve_good_url(self):
        import time
        good = []
        self.srv, url = make_server(lambda h, b, hd: (good.append(1), 200)[1])
        bad = "http://127.0.0.1:1/hook"   # connection refused
        for i in range(20): outbox.enqueue(self.conn, f"x{i}", bad, {})
        for i in range(20): outbox.enqueue(self.conn, f"g{i}", url, {})
        self._start(workers=4, backoff_base=30)
        self.assertTrue(wait_until(lambda: len(good) == 20, 10))


if __name__ == "__main__":
    unittest.main()
