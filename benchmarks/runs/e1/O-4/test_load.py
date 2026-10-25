import os, tempfile, threading, time, unittest
from outbox import Outbox
from orders import Orders
from dispatcher import Dispatcher


class LoadTest(unittest.TestCase):
    def test_burst_with_hanging_endpoint_then_no_loss(self):
        d = tempfile.TemporaryDirectory()
        ob = Outbox(os.path.join(d.name, "t.db"))
        orders = Orders(ob)
        N = 400  # 100/s burst compressed to 4 s
        for i in range(N): orders.create(f"o{i}", "http://slow")
        state = {"up": False}
        delivered = []; lock = threading.Lock()
        def sender(url, body, headers, timeout):
            if not state["up"]:
                time.sleep(0.3)  # stands in for the 10 s hang
                raise TimeoutError()
            with lock: delivered.append(headers["Idempotency-Key"])
            return 200
        disp = Dispatcher(ob, workers=32, sender=sender, backoff_base=0.1, max_attempts=100, poll_interval=0.01)
        disp.start()
        lat = []
        t0 = time.perf_counter()
        for i in range(N):
            s = time.perf_counter()
            orders.confirm_order(f"o{i}")
            lat.append(time.perf_counter() - s)
            delay = t0 + (i + 1) / 100 - time.perf_counter()
            if delay > 0: time.sleep(delay)
        lat.sort()
        self.assertLess(lat[int(N * 0.99)], 1.5)
        state["up"] = True
        deadline = time.time() + 60
        while time.time() < deadline and ob.counts().get("done", 0) < N: time.sleep(0.1)
        disp.stop(); d.cleanup() if False else None
        self.assertEqual(ob.counts(), {"done": N})
        self.assertEqual(len(set(delivered)), N)
        d.cleanup()


if __name__ == "__main__":
    unittest.main()
