import os, tempfile, threading, time, unittest
import outbox, orders


class T(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.mkdtemp()
        self.db = os.path.join(self.d, "t.db")
        outbox.init(self.db)
        self.conn = outbox.connect(self.db)

    def test_rollback_leaves_no_row(self):
        orig = outbox.enqueue
        def boom(*a, **k):
            orig(*a, **k); raise RuntimeError("x")
        outbox.enqueue = boom
        try:
            with self.assertRaises(RuntimeError):
                orders.confirm_order(self.conn, "o1", "http://x")
        finally:
            outbox.enqueue = orig
        self.assertEqual(outbox.counts(self.conn), {})
        self.assertIsNone(self.conn.execute("SELECT 1 FROM orders").fetchone())

    def test_claim_lease_and_reclaim(self):
        orders.confirm_order(self.conn, "o1", "http://x")
        now = time.time()
        self.assertEqual(len(outbox.claim(self.conn, lease=10, now=now)), 1)
        self.assertEqual(outbox.claim(self.conn, lease=10, now=now + 1), [])
        self.assertEqual(len(outbox.claim(self.conn, lease=10, now=now + 11)), 1)

    def test_backoff_then_dead(self):
        oid = outbox.enqueue(self.conn, "o", "http://x", {})
        for i in range(3):
            outbox.mark_failed(self.conn, oid, i, "e", max_attempts=3, now=100)
        self.assertEqual(outbox.counts(self.conn), {"dead": 1})

    def test_load_100_per_sec_concurrent_claims(self):
        stop = threading.Event()
        def claimer():
            c = outbox.connect(self.db)
            while not stop.is_set():
                for it in outbox.claim(c, 20, lease=30):
                    outbox.mark_delivered(c, it["id"])
                time.sleep(0.01)
        th = threading.Thread(target=claimer); th.start()
        lat = []
        t0 = time.time()
        for i in range(1000):
            s = time.time()
            orders.confirm_order(self.conn, "o%d" % i, "http://x")
            lat.append(time.time() - s)
            nxt = t0 + (i + 1) / 100.0
            time.sleep(max(0, nxt - time.time()))
        stop.set(); th.join()
        lat.sort()
        self.assertLess(lat[int(len(lat) * 0.99)], 0.5)
        self.assertEqual(self.conn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0], 1000)


if __name__ == "__main__":
    unittest.main()
