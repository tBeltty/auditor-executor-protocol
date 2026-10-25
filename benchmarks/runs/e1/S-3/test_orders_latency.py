import os, sys, tempfile, time, unittest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import outbox, orders
from dispatcher import Dispatcher
from fakeserver import make_server


class LatencyTests(unittest.TestCase):
    def test_hanging_endpoint_does_not_affect_confirm_p99(self):
        def hang(h, b, hd):
            time.sleep(3); return 200
        srv, url = make_server(hang)
        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.db")
            conn = outbox.connect(path); orders.init_schema(conn)
            disp = Dispatcher(path, http_timeout=1.0, workers=8); disp.start()
            lat = []
            try:
                for i in range(200):
                    conn.execute("INSERT INTO orders(id, webhook_url) VALUES (?,?)", (f"o{i}", url))
                    t = time.perf_counter()
                    orders.confirm_order(conn, f"o{i}")
                    lat.append(time.perf_counter() - t)
                    time.sleep(0.005)
            finally:
                disp.stop(); conn.close(); srv.shutdown(); srv.server_close()
            lat.sort()
            p99 = lat[int(len(lat) * 0.99) - 1]
            self.assertLess(p99, 1.5)
            print(f"\nconfirm p99 = {p99*1000:.1f} ms")


if __name__ == "__main__":
    unittest.main()
