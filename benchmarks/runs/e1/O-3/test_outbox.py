import os, tempfile, threading, time, unittest
import outbox


def newdb():
    d = tempfile.mkdtemp()
    p = os.path.join(d, "t.db")
    c = outbox.connect(p)
    return p, c


def count(c, state=None):
    if state:
        return c.execute("SELECT COUNT(*) FROM webhook_outbox WHERE state=?", (state,)).fetchone()[0]
    return c.execute("SELECT COUNT(*) FROM webhook_outbox").fetchone()[0]


def wait_for(fn, t=15):
    end = time.time() + t
    while time.time() < end:
        if fn():
            return True
        time.sleep(0.05)
    return False


class TestEnqueue(unittest.TestCase):
    def test_atomic_with_order(self):
        p, c = newdb()
        c.execute("INSERT INTO orders(id,status) VALUES(1,'new')")
        outbox.confirm_order(c, 1, "http://x/h", {"a": 1})
        self.assertEqual(count(c, "pending"), 1)
        self.assertEqual(c.execute("SELECT status FROM orders WHERE id=1").fetchone()[0], "confirmed")

    def test_rollback_leaves_no_row(self):
        p, c = newdb()
        c.execute("INSERT INTO orders(id,status) VALUES(1,'new')")
        c.execute("BEGIN IMMEDIATE")
        outbox.enqueue(c, 1, "http://x", {})
        c.execute("ROLLBACK")
        self.assertEqual(count(c), 0)


class TestBurst(unittest.TestCase):
    def test_burst_latency_and_no_loss(self):
        p, c = newdb()
        for i in range(1, 1001):
            c.execute("INSERT INTO orders(id,status) VALUES(?, 'new')", (i,))
        delivered = []
        lock = threading.Lock()

        def slow(url, body):
            time.sleep(0.2)
            with lock:
                delivered.append(body)

        d = outbox.Dispatcher(p, workers=8, sender=slow, poll=0.05)
        d.start()
        lat = []

        def one(i):
            conn = outbox.connect(p)
            t = time.perf_counter()
            outbox.confirm_order(conn, i, "http://cust%d/h" % (i % 5), {})
            lat.append(time.perf_counter() - t)
            conn.close()

        threads = []
        for i in range(1, 301):          # 100/s for 3 s
            th = threading.Thread(target=one, args=(i,)); th.start(); threads.append(th)
            time.sleep(0.01)
        for th in threads:
            th.join()
        lat.sort()
        p99 = lat[int(len(lat) * 0.99) - 1]
        self.assertLess(p99, 1.5)
        self.assertTrue(wait_for(lambda: count(c, "delivered") == 300, 60))
        d.stop()
        self.assertEqual(count(c), 300)
        self.assertGreaterEqual(len(delivered), 300)


class TestDelivery(unittest.TestCase):
    def test_retry_backoff_and_dead(self):
        p, c = newdb()
        outbox.enqueue(c, 1, "http://x", {}, now=0)
        rid, url, payload, att = outbox.claim(c, now=1)[0]
        outbox.mark_failed(c, rid, att, "boom", now=1)
        self.assertEqual(outbox.claim(c, now=1.5), [])
        self.assertEqual(len(outbox.claim(c, now=1 + outbox.backoff(1) + 0.1)), 1)
        outbox.mark_failed(c, rid, outbox.MAX_ATTEMPTS - 1, "boom")
        self.assertEqual(count(c, "dead"), 1)

    def test_delivered_not_reclaimed(self):
        p, c = newdb()
        outbox.enqueue(c, 1, "http://x", {}, now=0)
        rid = outbox.claim(c, now=1)[0][0]
        outbox.mark_delivered(c, rid)
        self.assertEqual(outbox.claim(c, now=100), [])


class TestRecovery(unittest.TestCase):
    def test_stale_claim_recovered(self):
        p, c = newdb()
        outbox.enqueue(c, 1, "http://x", {}, now=0)
        outbox.claim(c, now=10)
        self.assertEqual(outbox.recover_stale(c, 60, now=30), 0)
        self.assertEqual(outbox.recover_stale(c, 60, now=100), 1)
        self.assertEqual(len(outbox.claim(c, now=101)), 1)

    def test_breaker(self):
        t = [0]
        b = outbox.CircuitBreaker(2, 10, clock=lambda: t[0])
        b.fail("http://h/a"); b.fail("http://h/b")
        self.assertEqual(b.open_hosts(), {"h"})
        t[0] = 11
        self.assertEqual(b.open_hosts(), set())


class TestDispatcher(unittest.TestCase):
    def test_failure_then_success(self):
        p, c = newdb()
        outbox.enqueue(c, 1, "http://x", {"k": 1})
        calls = []

        def flaky(url, body):
            calls.append(1)
            if len(calls) == 1:
                raise IOError("down")

        d = outbox.Dispatcher(p, workers=2, sender=flaky, poll=0.05,
                              breaker=outbox.CircuitBreaker(99))
        d.start()
        # first attempt fails; backoff is 2 s, then succeeds
        self.assertTrue(wait_for(lambda: count(c, "delivered") == 1, 15))
        d.stop()
        self.assertEqual(len(calls), 2)

    def test_restart_recovers_claimed(self):
        p, c = newdb()
        outbox.enqueue(c, 1, "http://x", {})
        outbox.claim(c)  # simulated crash: claimed, never finished
        d = outbox.Dispatcher(p, workers=1, sender=lambda u, b: None, poll=0.05)
        d.start()
        self.assertTrue(wait_for(lambda: count(c, "delivered") == 1))
        d.stop()


class TestConfirmOrder(unittest.TestCase):
    def test_hanging_endpoint_does_not_block(self):
        p, c = newdb()
        for i in range(1, 21):
            c.execute("INSERT INTO orders(id,status) VALUES(?,'new')", (i,))
        release = threading.Event()
        d = outbox.Dispatcher(p, workers=4, sender=lambda u, b: release.wait(20), poll=0.05)
        d.start()
        t = time.perf_counter()
        for i in range(1, 21):
            outbox.confirm_order(c, i, "http://hang/h", {})
        self.assertLess(time.perf_counter() - t, 1.5)
        release.set()
        self.assertTrue(wait_for(lambda: count(c, "delivered") == 20, 30))
        d.stop()


if __name__ == "__main__":
    unittest.main()
