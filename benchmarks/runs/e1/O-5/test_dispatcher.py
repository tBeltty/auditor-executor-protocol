import os, tempfile, time, unittest
import outbox, orders
from dispatcher import Dispatcher


def wait(cond, t=10):
    end = time.time() + t
    while time.time() < end:
        if cond(): return True
        time.sleep(0.02)
    return False


class T(unittest.TestCase):
    def setUp(self):
        self.db = os.path.join(tempfile.mkdtemp(), "t.db")
        outbox.init(self.db)
        self.conn = outbox.connect(self.db)

    def test_delivers_all(self):
        got = []
        d = Dispatcher(self.db, send=lambda u, b, k, t: got.append(k), workers=8)
        for i in range(50):
            orders.confirm_order(self.conn, "o%d" % i, "http://x")
        d.start()
        self.assertTrue(wait(lambda: outbox.counts(self.conn).get("delivered") == 50))
        d.stop()
        self.assertEqual(len(set(got)), 50)

    def test_retry_then_success(self):
        calls = []
        def send(u, b, k, t):
            calls.append(1)
            if len(calls) < 3: raise OSError("down")
        d = Dispatcher(self.db, send=send, base=0.01)
        orders.confirm_order(self.conn, "o", "http://x")
        d.start()
        self.assertTrue(wait(lambda: outbox.counts(self.conn).get("delivered") == 1))
        d.stop()
        self.assertEqual(len(calls), 3)

    def test_permanent_failure_goes_dead_not_lost(self):
        def send(*a): raise OSError("down")
        d = Dispatcher(self.db, send=send, base=0.001, max_attempts=3)
        orders.confirm_order(self.conn, "o", "http://x")
        d.start()
        self.assertTrue(wait(lambda: outbox.counts(self.conn).get("dead") == 1))
        d.stop()

    def test_crash_recovery_via_lease_expiry(self):
        orders.confirm_order(self.conn, "o", "http://x")
        outbox.claim(self.conn, lease=0.2)  # worker "crashes" holding lease
        got = []
        d = Dispatcher(self.db, send=lambda u, b, k, t: got.append(k))
        d.start()
        self.assertTrue(wait(lambda: outbox.counts(self.conn).get("delivered") == 1))
        d.stop()


if __name__ == "__main__":
    unittest.main()
