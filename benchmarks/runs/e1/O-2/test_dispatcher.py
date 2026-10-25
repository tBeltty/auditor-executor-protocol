import os, tempfile, threading, time, unittest

import app, outbox
from dispatcher import Dispatcher


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.d.name, "t.db")
        app.init_db(self.db)
        self.ob = outbox.Outbox(self.db, lease_seconds=30)

    def tearDown(self):
        self.d.cleanup()

    def add(self, n, url="http://a.test/h"):
        conn = outbox.connect(self.db)
        for i in range(n):
            outbox.enqueue(conn, i, url, "{}")
        conn.close()

    def wait_for(self, cond, timeout=10):
        end = time.time() + timeout
        while time.time() < end:
            if cond():
                return True
            time.sleep(0.02)
        return False

    def test_delivers_all(self):
        self.add(50)
        got = []
        disp = Dispatcher(self.ob, lambda r: got.append(r["id"]), workers=8)
        disp.start()
        self.assertTrue(self.wait_for(lambda: self.ob.counts().get("done") == 50))
        disp.stop()
        self.assertEqual(len(set(got)), 50)

    def test_retry_then_success(self):
        self.add(1)
        calls = []
        def sender(r):
            calls.append(1)
            if len(calls) < 3:
                raise IOError("boom")
        disp = Dispatcher(self.ob, sender, base_backoff=0.05, max_backoff=0.1)
        disp.start()
        self.assertTrue(self.wait_for(lambda: self.ob.counts().get("done") == 1))
        disp.stop()
        self.assertEqual(len(calls), 3)

    def test_dead_after_max_attempts_is_kept(self):
        self.add(1)
        def sender(r):
            raise IOError("down")
        disp = Dispatcher(self.ob, sender, max_attempts=3, base_backoff=0.02, max_backoff=0.05)
        disp.start()
        self.assertTrue(self.wait_for(lambda: self.ob.counts().get("dead") == 1))
        disp.stop()

    def test_slow_host_does_not_starve_others(self):
        self.add(40, "http://slow.test/h")
        self.add(5, "http://fast.test/h")
        release = threading.Event()
        done_fast = []
        def sender(r):
            if r["host"] == "slow.test":
                release.wait(20)
            else:
                done_fast.append(r["id"])
        disp = Dispatcher(self.ob, sender, workers=16, per_host=4)
        disp.start()
        try:
            self.assertTrue(self.wait_for(lambda: len(done_fast) == 5, timeout=5))
        finally:
            release.set()
            disp.stop()

    def test_crash_recovery_redelivers(self):
        self.add(3)
        self.ob.lease_seconds = 0.2
        self.assertEqual(len(self.ob.claim(10)), 3)  # "crashed" worker never finished
        got = []
        disp = Dispatcher(self.ob, lambda r: got.append(r["id"]))
        time.sleep(0.3)
        disp.start()
        self.assertTrue(self.wait_for(lambda: self.ob.counts().get("done") == 3))
        disp.stop()


if __name__ == "__main__":
    unittest.main()
