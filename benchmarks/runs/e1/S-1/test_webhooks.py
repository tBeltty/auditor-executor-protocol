import os
import sqlite3
import tempfile
import threading
import time
import unittest

import webhooks as w


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "app.db")
        w.init_db(self.path)
        self.conn = w.connect(self.path)

    def tearDown(self):
        self.conn.close()
        self.dir.cleanup()

    def counts(self):
        c = w.connect(self.path)
        r = dict(c.execute("SELECT status,COUNT(*) FROM webhook_outbox GROUP BY status"))
        c.close()
        return r

    def wait_for(self, pred, timeout=20):
        end = time.time() + timeout
        while time.time() < end:
            if pred():
                return True
            time.sleep(0.05)
        return False


class TestLatency(Base):
    def test_confirm_not_blocked_by_hung_endpoint(self):  # AC1
        release = threading.Event()
        d = w.Dispatcher(self.path, sender=lambda u, b, e: release.wait(10), workers=4)
        d.start()
        lat = []
        for i in range(100):
            t = time.perf_counter()
            w.confirm_order(self.conn, "o%d" % i, "http://x", {"i": i})
            lat.append(time.perf_counter() - t)
        release.set()
        d.stop()
        lat.sort()
        self.assertLess(lat[98], 1.5)
        self.assertLess(lat[98], 0.5)


class TestBurst(Base):
    def test_burst_100_concurrent_none_lost(self):  # AC2
        seen, lock = set(), threading.Lock()

        def sender(url, body, eid):
            with lock:
                seen.add(eid)

        d = w.Dispatcher(sender=sender, path=self.path, workers=8)
        d.start()
        ids = []

        def work(i):
            c = w.connect(self.path)
            ids.append(w.confirm_order(c, "o%d" % i, "http://x", {"i": i}))
            c.close()

        ts = [threading.Thread(target=work, args=(i,)) for i in range(100)]
        [t.start() for t in ts]
        [t.join() for t in ts]
        self.assertTrue(self.wait_for(lambda: self.counts().get("delivered") == 100))
        d.stop()
        self.assertEqual(len(ids), 100)
        self.assertEqual(seen, set(ids))


class TestRetry(Base):
    def test_retry_then_success(self):  # AC3
        calls = []

        def sender(url, body, eid):
            calls.append(eid)
            if len(calls) <= 2:
                raise TimeoutError("boom")

        d = w.Dispatcher(self.path, sender=sender, workers=1, backoff_base=0.05)
        d.start()
        w.confirm_order(self.conn, "o1", "http://x", {})
        self.assertTrue(self.wait_for(lambda: self.counts().get("delivered") == 1))
        d.stop()
        a = self.conn.execute("SELECT attempts FROM webhook_outbox").fetchone()[0]
        self.assertEqual(a, 3)
        self.assertEqual(len(set(calls)), 1)  # same idempotency key

    def test_dead_letter_kept(self):  # AC5
        def sender(url, body, eid):
            raise ConnectionError("down")

        d = w.Dispatcher(self.path, sender=sender, workers=1, max_attempts=3,
                         backoff_base=0.01)
        d.start()
        w.confirm_order(self.conn, "o1", "http://x", {})
        self.assertTrue(self.wait_for(lambda: self.counts().get("dead") == 1))
        d.stop()
        row = self.conn.execute("SELECT attempts,last_error FROM webhook_outbox").fetchone()
        self.assertEqual(row[0], 3)
        self.assertIn("down", row[1])


class TestRecovery(Base):
    def test_expired_lease_is_redelivered(self):  # AC4
        w.confirm_order(self.conn, "o1", "http://x", {})
        self.conn.execute("UPDATE webhook_outbox SET status='in_flight', lease_until=?",
                          (time.time() - 1,))
        got = []
        d = w.Dispatcher(self.path, sender=lambda u, b, e: got.append(e), workers=1)
        d.start()
        self.assertTrue(self.wait_for(lambda: self.counts().get("delivered") == 1))
        d.stop()
        self.assertEqual(len(got), 1)

    def test_live_lease_not_stolen(self):
        w.confirm_order(self.conn, "o1", "http://x", {})
        self.conn.execute("UPDATE webhook_outbox SET status='in_flight', lease_until=?",
                          (time.time() + 100,))
        d = w.Dispatcher(self.path, sender=lambda u, b, e: None)
        self.assertEqual(d.process_once(self.conn), 0)


class TestAtomic(Base):
    def test_rollback_leaves_no_outbox(self):  # AC6
        with self.assertRaises(TypeError):
            w.confirm_order(self.conn, "o1", "http://x", {"bad": object()})
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM webhook_outbox").fetchone()[0], 0)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
