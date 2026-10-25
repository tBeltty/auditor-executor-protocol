import os, tempfile, threading, time, unittest
import webhooks as w


def counts(path):
    c = w.connect(path)
    r = dict(c.execute("SELECT status,COUNT(*) FROM webhook_outbox GROUP BY status"))
    c.close()
    return r


def wait_for(fn, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        if fn():
            return True
        time.sleep(0.02)
    return False


class Base(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.db = os.path.join(self.d, "t.db")
        w.init_db(self.db)
        self.conn = w.connect(self.db)

    def tearDown(self):
        self.conn.close()


class Tests(Base):
    def test_ac1_latency_with_blocking_endpoint(self):
        release = threading.Event()
        disp = w.Dispatcher(self.db, sender=lambda u, b, k: release.wait(10), workers=8)
        disp.start()
        lat = []
        for i in range(200):
            t = time.perf_counter()
            w.confirm_order(self.conn, i, "http://x", {"o": i})
            lat.append(time.perf_counter() - t)
        lat.sort()
        self.assertLess(lat[int(len(lat) * 0.99) - 1], 1.5)
        release.set()
        disp.stop()

    def test_ac2_rollback_leaves_no_row(self):
        self.conn.execute("BEGIN IMMEDIATE")
        self.conn.execute("ROLLBACK")
        with self.assertRaises(TypeError):
            w.confirm_order(self.conn, 1, "http://x", {"bad": object()})
        self.assertEqual(counts(self.db), {})

    def test_ac3_retry_then_success(self):
        n = {"c": 0}
        keys = []
        def s(u, b, k):
            n["c"] += 1; keys.append(k)
            if n["c"] <= 2:
                raise IOError("boom")
        disp = w.Dispatcher(self.db, sender=s, base_delay=0.01, poll=0.01)
        w.confirm_order(self.conn, 1, "http://x", {})
        disp.start()
        self.assertTrue(wait_for(lambda: counts(self.db).get("delivered") == 1))
        disp.stop()
        self.assertEqual(self.conn.execute("SELECT attempts FROM webhook_outbox").fetchone()[0], 3)
        self.assertEqual(set(keys), {"1"})

    def test_ac4_dead_after_max_attempts(self):
        def s(u, b, k): raise IOError("down")
        disp = w.Dispatcher(self.db, sender=s, base_delay=0.001, poll=0.01, max_attempts=3)
        w.confirm_order(self.conn, 1, "http://x", {})
        disp.start()
        self.assertTrue(wait_for(lambda: counts(self.db).get("dead") == 1))
        disp.stop()
        self.assertEqual(counts(self.db), {"dead": 1})

    def test_ac5_expired_lease_reclaimed(self):
        w.confirm_order(self.conn, 1, "http://x", {})
        rows = w.claim(self.conn, lease=0.05)   # "crashed" worker never finishes
        self.assertEqual(len(rows), 1)
        self.assertEqual(w.claim(self.conn, lease=0.05), [])  # leased, not re-claimed
        time.sleep(0.1)
        got = []
        disp = w.Dispatcher(self.db, sender=lambda u, b, k: got.append(k), poll=0.01)
        disp.start()
        self.assertTrue(wait_for(lambda: counts(self.db).get("delivered") == 1))
        disp.stop()
        self.assertEqual(got, ["1"])

    def test_ac6_burst_no_loss_no_dup(self):
        got = []
        lock = threading.Lock()
        def s(u, b, k):
            with lock: got.append(k)
        disp = w.Dispatcher(self.db, sender=s, workers=16, poll=0.01)
        disp.start()
        for i in range(1000):
            w.confirm_order(self.conn, i, "http://x", {"o": i})
        self.assertTrue(wait_for(lambda: counts(self.db).get("delivered") == 1000, 60))
        disp.stop()
        self.assertEqual(len(got), 1000)
        self.assertEqual(len(set(got)), 1000)


if __name__ == "__main__":
    unittest.main()
