import os, tempfile, time, unittest
from outbox import Outbox
from dispatcher import Dispatcher


class DispatcherTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.ob = Outbox(os.path.join(self.d.name, "t.db"))

    def tearDown(self):
        self.d.cleanup()

    def test_success_sends_idempotency_key(self):
        seen = []
        def sender(url, body, headers, timeout):
            seen.append((url, headers, timeout)); return 200
        wid = self.ob.enqueue("http://c", {"k": 1})
        d = Dispatcher(self.ob, sender=sender, timeout=3)
        self.assertTrue(d.deliver_one())
        self.assertEqual(self.ob.counts(), {"done": 1})
        self.assertEqual(seen[0][1]["Idempotency-Key"], wid)
        self.assertEqual(seen[0][2], 3)
        self.assertFalse(d.deliver_one())

    def test_failure_retries_then_dead(self):
        def sender(*a): raise TimeoutError("t")
        self.ob.enqueue("http://c", {})
        d = Dispatcher(self.ob, sender=sender, max_attempts=2, backoff_base=0.0)
        d.deliver_one(); self.assertEqual(self.ob.counts(), {"pending": 1})
        d.deliver_one(); self.assertEqual(self.ob.counts(), {"dead": 1})

    def test_non_2xx_is_failure(self):
        self.ob.enqueue("http://c", {})
        d = Dispatcher(self.ob, sender=lambda *a: 500, max_attempts=5, backoff_base=100)
        d.deliver_one()
        self.assertEqual(self.ob.counts(), {"pending": 1})

    def test_background_workers_deliver_after_recovery(self):
        state = {"up": False}
        def sender(*a):
            if not state["up"]: raise TimeoutError()
            return 204
        for _ in range(20): self.ob.enqueue("http://c", {})
        d = Dispatcher(self.ob, workers=4, sender=sender, backoff_base=0.05, max_attempts=50, poll_interval=0.01)
        d.start(); time.sleep(0.3); state["up"] = True
        deadline = time.time() + 10
        while time.time() < deadline and self.ob.counts().get("done", 0) < 20: time.sleep(0.05)
        d.stop()
        self.assertEqual(self.ob.counts(), {"done": 20})


if __name__ == "__main__":
    unittest.main()
