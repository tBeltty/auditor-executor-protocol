import os, tempfile, threading, time, unittest
from outbox import Outbox


class OutboxTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.ob = Outbox(os.path.join(self.d.name, "t.db"))

    def tearDown(self):
        self.d.cleanup()

    def test_claim_is_exclusive_and_retry_backoff(self):
        self.ob.enqueue("http://x", {"a": 1}, now=100)
        a = self.ob.claim(5, now=100)
        self.assertEqual(len(a), 1)
        self.assertEqual(self.ob.claim(5, now=100), [])
        self.ob.mark_failed(a[0]["id"], "boom", 3, 2.0, now=100)
        self.assertEqual(self.ob.claim(5, now=101), [])
        self.assertEqual(len(self.ob.claim(5, now=102)), 1)

    def test_dead_after_max_attempts(self):
        wid = self.ob.enqueue("http://x", {}, now=0)
        for i in range(3):
            self.ob.claim(1, now=1e6)
            self.ob.mark_failed(wid, "e", 3, 0.0, now=0)
        self.assertEqual(self.ob.counts(), {"dead": 1})

    def test_stale_recovery(self):
        self.ob.enqueue("http://x", {}, now=0)
        self.ob.claim(1, now=10)
        self.assertEqual(self.ob.recover_stale(60, now=50), 0)
        self.assertEqual(self.ob.recover_stale(60, now=100), 1)
        self.assertEqual(len(self.ob.claim(1, now=100)), 1)

    def test_concurrent_enqueue_and_claim_latency(self):
        """Riskiest assumption: SQLite absorbs 100 inserts/s with concurrent claimers."""
        stop = threading.Event()
        def claimer():
            while not stop.is_set():
                for r in self.ob.claim(5):
                    self.ob.mark_failed(r["id"], "timeout", 99, 10.0)
                time.sleep(0.005)
        ts = [threading.Thread(target=claimer) for _ in range(16)]
        [t.start() for t in ts]
        lat = []
        for _ in range(300):
            s = time.perf_counter()
            self.ob.enqueue("http://x", {"i": 1})
            lat.append(time.perf_counter() - s)
            time.sleep(0.01)
        stop.set(); [t.join() for t in ts]
        lat.sort()
        self.assertLess(lat[int(len(lat) * 0.99)], 1.5)


if __name__ == "__main__":
    unittest.main()
