import http.server, os, sqlite3, tempfile, threading, time, unittest
import webhooks as w


class Stub:
    """Local HTTP server. mode: ok | hang | flaky(n failures first)."""
    def __init__(self, mode="ok", fail_first=0):
        self.mode, self.fail_first = mode, fail_first
        self.ids, self.calls, self.lock = [], 0, threading.Lock()
        stub = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                with stub.lock:
                    stub.calls += 1
                    n = stub.calls
                if stub.mode == "hang":
                    time.sleep(3)
                    return
                code = 500 if n <= stub.fail_first else 200
                if code == 200:
                    with stub.lock:
                        stub.ids.append(self.headers["X-Webhook-Id"])
                self.send_response(code); self.send_header("Content-Length", "0"); self.end_headers()

            def log_message(self, *a): pass

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
        self.srv.daemon_threads = True
        self.url = "http://127.0.0.1:%d/hook" % self.srv.server_port
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def close(self):
        self.srv.shutdown(); self.srv.server_close()


def wait_for(cond, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        if cond():
            return True
        time.sleep(0.05)
    return False


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.dir.name, "t.db")
        w.init_db(self.db)
        self.stubs = []

    def tearDown(self):
        for s in self.stubs: s.close()
        self.dir.cleanup()

    def stub(self, *a, **k):
        s = Stub(*a, **k); self.stubs.append(s); return s


class TestWebhooks(Base):
    def test_ac1_latency_with_hanging_endpoint(self):
        s = self.stub("hang")
        d = w.Dispatcher(self.db, workers=8, http_timeout=1.0, max_attempts=2)
        d.start()
        lat = []
        conn = w.connect(self.db)
        for i in range(1000):
            t = time.perf_counter(); w.confirm_order(self.db, i, s.url, conn); lat.append(time.perf_counter() - t)
        d.stop()
        lat.sort()
        self.assertLess(lat[int(0.99 * len(lat))], 1.5)
        self.assertEqual(sum(w.stats(self.db).values()), 1000)

    def test_ac2_atomic(self):
        conn = w.connect(self.db)
        conn.execute("CREATE TRIGGER boom BEFORE INSERT ON webhook_outbox BEGIN SELECT RAISE(ABORT,'x'); END")
        with self.assertRaises(sqlite3.Error):
            w.confirm_order(self.db, 1, "http://x", conn)
        self.assertEqual(conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 0)

    def test_ac3_retry_then_success(self):
        s = self.stub(fail_first=2)
        w.confirm_order(self.db, 1, s.url)
        d = w.Dispatcher(self.db, workers=2, http_timeout=2, backoff_base=0.05, poll_interval=0.05)
        d.start()
        self.assertTrue(wait_for(lambda: w.stats(self.db).get("delivered") == 1))
        d.stop()
        self.assertEqual(len(s.ids), 1)
        a = sqlite3.connect(self.db).execute("SELECT attempts FROM webhook_outbox").fetchone()[0]
        self.assertEqual(a, 3)

    def test_ac4_expired_lease_recovered(self):
        s = self.stub()
        wid = w.confirm_order(self.db, 1, s.url)
        c = w.connect(self.db)
        c.execute("UPDATE webhook_outbox SET status='in_progress', lease_until=? WHERE id=?", (time.time() - 1, wid))
        d = w.Dispatcher(self.db, poll_interval=0.05); d.start()
        self.assertTrue(wait_for(lambda: w.stats(self.db).get("delivered") == 1))
        d.stop()
        self.assertEqual(s.ids, [wid])

    def test_ac5_dead_and_replay(self):
        s = self.stub(fail_first=10**6)
        w.confirm_order(self.db, 1, s.url)
        d = w.Dispatcher(self.db, max_attempts=2, backoff_base=0.01, poll_interval=0.05); d.start()
        self.assertTrue(wait_for(lambda: w.stats(self.db).get("dead") == 1))
        self.assertEqual(w.replay_dead(self.db), 1)
        self.assertEqual(w.stats(self.db), {"pending": 1})
        s.fail_first = 0
        self.assertTrue(wait_for(lambda: w.stats(self.db).get("delivered") == 1))
        d.stop()

    def test_ac6_burst_no_loss(self):
        s = self.stub()
        d = w.Dispatcher(self.db, workers=32, poll_interval=0.05); d.start()
        conn = w.connect(self.db)
        ids = {w.confirm_order(self.db, i, s.url, conn) for i in range(1000)}
        self.assertTrue(wait_for(lambda: w.stats(self.db).get("delivered") == 1000, 60))
        d.stop()
        self.assertEqual(set(s.ids), ids)


if __name__ == "__main__":
    unittest.main()
