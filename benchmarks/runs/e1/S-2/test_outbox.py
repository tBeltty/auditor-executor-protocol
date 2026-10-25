import http.server
import os
import tempfile
import threading
import time
import unittest

import orders
import outbox


class Handler(http.server.BaseHTTPRequestHandler):
    mode = "ok"      # ok | hang | fail_n
    fails = 0
    hits = 0
    lock = threading.Lock()

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        cls = type(self)
        with cls.lock:
            cls.hits += 1
            n = cls.hits
        if cls.mode == "hang":
            time.sleep(3)
        code = 500 if (cls.mode == "fail_n" and n <= cls.fails) else 200
        try:
            self.send_response(code)
            self.send_header("Content-Length", "0")
            self.end_headers()
        except OSError:
            pass

    def log_message(self, *a):
        pass


def make_handler(mode="ok", fails=0):
    return type("H", (Handler,), {"mode": mode, "fails": fails, "hits": 0,
                                  "lock": threading.Lock()})


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "app.db")
        self.conn = outbox.connect(self.db)
        orders.init_db(self.conn)
        self.servers = []

    def tearDown(self):
        for s in self.servers:
            s.shutdown()
            s.server_close()
        self.conn.close()

    def serve(self, handler):
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        srv.daemon_threads = True
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        self.servers.append(srv)
        return "http://127.0.0.1:%d/hook" % srv.server_address[1]

    def add_orders(self, n, url):
        self.conn.executemany("INSERT INTO orders(id,status,webhook_url) VALUES(?,?,?)",
                              [(i, "new", url) for i in range(1, n + 1)])

    def wait_for(self, cond, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.05)
        return False


class TestLatency(Base):
    def test_confirm_fast_with_hanging_endpoint(self):
        url = self.serve(make_handler("hang"))
        self.add_orders(200, url)
        d = outbox.Dispatcher(self.db, workers=8, http_timeout=1.0)
        d.start()
        lat = []
        for i in range(1, 201):
            t = time.perf_counter()
            orders.confirm_order(self.conn, i)
            lat.append(time.perf_counter() - t)
        d.stop(5)
        lat.sort()
        self.assertLess(lat[int(len(lat) * 0.99) - 1], 1.5)
        self.assertEqual(self.conn.execute(
            "SELECT COUNT(*) FROM webhook_outbox").fetchone()[0], 200)


class TestAtomicity(Base):
    def test_commit_creates_one_row(self):
        self.add_orders(1, "http://x/")
        orders.confirm_order(self.conn, 1)
        self.assertEqual(outbox.counts(self.conn), {"pending": 1})

    def test_rollback_no_row(self):
        self.add_orders(1, "http://x/")
        orig = outbox.enqueue
        def boom(*a, **k):
            orig(*a, **k)
            raise RuntimeError("fail")
        outbox.enqueue = boom
        try:
            with self.assertRaises(RuntimeError):
                orders.confirm_order(self.conn, 1)
        finally:
            outbox.enqueue = orig
        self.assertEqual(outbox.counts(self.conn), {})
        self.assertEqual(self.conn.execute(
            "SELECT status FROM orders WHERE id=1").fetchone()[0], "new")


class TestDelivery(Base):
    def test_retry_then_success_with_id_header(self):
        h = make_handler("fail_n", fails=2)
        url = self.serve(h)
        self.add_orders(1, url)
        orders.confirm_order(self.conn, 1)
        d = outbox.Dispatcher(self.db, workers=2, backoff_base=0.05)
        d.start()
        ok = self.wait_for(lambda: outbox.counts(self.conn) == {"delivered": 1})
        d.stop(5)
        self.assertTrue(ok, outbox.counts(self.conn))
        self.assertEqual(h.hits, 3)

    def test_crash_recovery_after_lease_expiry(self):
        self.add_orders(1, "http://x/")
        orders.confirm_order(self.conn, 1)
        got = outbox.claim(self.conn, 5, lease=0.2)   # "crashes" without finishing
        self.assertEqual(len(got), 1)
        self.assertEqual(outbox.claim(self.conn, 5, lease=0.2), [])
        time.sleep(0.3)
        self.assertEqual(len(outbox.claim(self.conn, 5, lease=0.2)), 1)

    def test_dead_and_replay(self):
        self.add_orders(1, "http://x/")
        orders.confirm_order(self.conn, 1)
        def bad(*a):
            raise OSError("down")
        d = outbox.Dispatcher(self.db, workers=1, max_attempts=2,
                              backoff_base=0.01, sender=bad)
        d.start()
        self.assertTrue(self.wait_for(lambda: outbox.counts(self.conn) == {"dead": 1}))
        d.stop(5)
        self.assertEqual(outbox.replay_dead(self.conn), 1)
        self.assertEqual(outbox.counts(self.conn), {"pending": 1})

    def test_per_url_cap(self):
        self.add_orders(10, "http://x/")
        for i in range(1, 11):
            orders.confirm_order(self.conn, i)
        got = outbox.claim(self.conn, 10, per_url_cap=3)
        self.assertEqual(len(got), 3)


class TestBurst(Base):
    def test_burst_1000_no_loss(self):
        h = make_handler("ok")
        url = self.serve(h)
        self.add_orders(1000, url)
        d = outbox.Dispatcher(self.db, workers=32, per_url_cap=32)
        d.start()
        t0 = time.perf_counter()
        for i in range(1, 1001):
            orders.confirm_order(self.conn, i)
        enqueue_time = time.perf_counter() - t0
        ok = self.wait_for(lambda: outbox.counts(self.conn) == {"delivered": 1000}, 60)
        d.stop(10)
        self.assertTrue(ok, outbox.counts(self.conn))
        self.assertLess(enqueue_time, 30)
        self.assertGreaterEqual(h.hits, 1000)


if __name__ == "__main__":
    unittest.main()
