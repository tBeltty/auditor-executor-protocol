import os, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outbox, orders


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.dir.name, "t.db")
        self.conn = outbox.connect(self.path)
        orders.init_schema(self.conn)
        self.conn.execute("INSERT INTO orders(id, webhook_url) VALUES ('o1','http://x/h')")

    def tearDown(self):
        self.conn.close(); self.dir.cleanup()

    def test_confirm_is_atomic_success(self):
        wid = orders.confirm_order(self.conn, "o1")
        self.assertIsNotNone(wid)
        self.assertEqual(self.conn.execute("SELECT status FROM orders").fetchone()[0], "confirmed")
        self.assertEqual(outbox.stats(self.conn)["pending"], 1)

    def test_confirm_rolls_back_both(self):
        orig = outbox.enqueue
        def boom(*a, **k): raise RuntimeError("fail")
        outbox.enqueue = boom
        try:
            with self.assertRaises(RuntimeError):
                orders.confirm_order(self.conn, "o1")
        finally:
            outbox.enqueue = orig
        self.assertEqual(self.conn.execute("SELECT status FROM orders").fetchone()[0], "new")
        self.assertEqual(sum(outbox.stats(self.conn).values()), 0)

    def test_claim_is_exclusive_and_lease_recovers(self):
        outbox.enqueue(self.conn, "o1", "http://x", {}, now=100)
        c2 = outbox.connect(self.path)
        a = outbox.claim_due(self.conn, 10, 30, now=101)
        b = outbox.claim_due(c2, 10, 30, now=102)
        self.assertEqual((len(a), len(b)), (1, 0))
        c = outbox.claim_due(c2, 10, 30, now=140)   # lease expired (crash recovery)
        self.assertEqual(len(c), 1)
        c2.close()

    def test_dead_and_requeue(self):
        wid = outbox.enqueue(self.conn, "o1", "http://x", {}, now=0)
        for _ in range(3):
            st, _n = outbox.mark_failed(self.conn, wid, "e", max_attempts=3, now=0)
        self.assertEqual(st, "dead")
        self.assertEqual(outbox.stats(self.conn)["dead"], 1)
        self.assertEqual(outbox.requeue_dead(self.conn), 1)
        self.assertEqual(outbox.stats(self.conn)["pending"], 1)

    def test_backoff_grows_and_caps(self):
        self.assertLess(outbox.backoff_delay(1), outbox.backoff_delay(4))
        self.assertLessEqual(outbox.backoff_delay(30, cap=900), 900 * 1.2)


if __name__ == "__main__":
    unittest.main()
