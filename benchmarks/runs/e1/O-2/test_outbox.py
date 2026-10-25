import os, tempfile, threading, time, unittest

import app, outbox
from dispatcher import Dispatcher


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.d.name, "t.db")
        app.init_db(self.db)

    def tearDown(self):
        self.d.cleanup()

    def test_claim_is_exclusive_and_lease_expires(self):
        conn = outbox.connect(self.db)
        outbox.enqueue(conn, 1, "http://h/x", "{}", now=100.0)
        conn.close()
        ob = outbox.Outbox(self.db, lease_seconds=10)
        self.assertEqual(len(ob.claim(5, now=100.0)), 1)
        self.assertEqual(len(ob.claim(5, now=105.0)), 0)   # leased
        self.assertEqual(len(ob.claim(5, now=111.0)), 1)   # crash recovery

    def test_burst_enqueue_latency_with_hung_endpoint(self):
        """Riskiest assumption: enqueue p99 stays far below 1.5 s while deliveries hang."""
        n = 1000
        conn = outbox.connect(self.db)
        for i in range(n):
            conn.execute("INSERT INTO orders(id,status,webhook_url) VALUES(?,?,?)", (i, "new", "http://slow.test/hook"))
        conn.close()
        release = threading.Event()
        disp = Dispatcher(outbox.Outbox(self.db), lambda row: release.wait(30), workers=32, per_host=16)
        disp.start()
        lat = []
        try:
            for i in range(n):  # 100/s
                t = time.perf_counter()
                app.confirm_order(self.db, i)
                lat.append(time.perf_counter() - t)
                time.sleep(0.01)
        finally:
            release.set()
            disp.stop()
        lat.sort()
        p99 = lat[int(n * 0.99) - 1]
        self.assertLess(p99, 1.5)
        counts = outbox.Outbox(self.db).counts()
        self.assertEqual(sum(counts.values()), n)  # nothing lost


if __name__ == "__main__":
    unittest.main()
