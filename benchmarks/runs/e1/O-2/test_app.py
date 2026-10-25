import json, os, tempfile, threading, time, unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import app, outbox
from dispatcher import Dispatcher


class AppTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.d.name, "t.db")
        app.init_db(self.db)

    def tearDown(self):
        self.d.cleanup()

    def order(self, i, url="http://x.test/h"):
        c = outbox.connect(self.db)
        c.execute("INSERT INTO orders(id,status,webhook_url) VALUES(?,?,?)", (i, "new", url))
        c.close()

    def test_confirm_enqueues_atomically(self):
        self.order(1)
        app.confirm_order(self.db, 1)
        c = outbox.connect(self.db)
        self.assertEqual(c.execute("SELECT status FROM orders WHERE id=1").fetchone()[0], "confirmed")
        self.assertEqual(c.execute("SELECT COUNT(*) FROM webhook_outbox").fetchone()[0], 1)
        c.close()

    def test_rollback_leaves_neither(self):
        self.order(1)
        with self.assertRaises(RuntimeError):
            app.confirm_order(self.db, 1, fail_after_enqueue=True)
        c = outbox.connect(self.db)
        self.assertEqual(c.execute("SELECT status FROM orders WHERE id=1").fetchone()[0], "new")
        self.assertEqual(c.execute("SELECT COUNT(*) FROM webhook_outbox").fetchone()[0], 0)
        c.close()

    def test_end_to_end_http_with_hanging_then_healthy_endpoint(self):
        state = {"hang": True, "got": []}
        class H(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                if state["hang"]:
                    time.sleep(1.5)  # exceeds sender timeout
                state["got"].append(json.loads(body)["order_id"])
                self.send_response(200); self.send_header("Content-Length", "0"); self.end_headers()
            def log_message(self, *a): pass
        srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://127.0.0.1:{srv.server_port}/hook"
        try:
            for i in range(5):
                self.order(i, url)
            disp = Dispatcher(outbox.Outbox(self.db), app.http_sender(timeout=0.3),
                              workers=8, base_backoff=0.1, max_backoff=0.3)
            disp.start()
            t = time.perf_counter()
            for i in range(5):
                app.confirm_order(self.db, i)
            self.assertLess(time.perf_counter() - t, 1.5)  # request path unaffected by hung endpoint
            time.sleep(0.5)
            state["hang"] = False
            end = time.time() + 10
            while time.time() < end and outbox.Outbox(self.db).counts().get("done") != 5:
                time.sleep(0.05)
            disp.stop()
            self.assertEqual(outbox.Outbox(self.db).counts().get("done"), 5)
            self.assertEqual(set(state["got"]), set(range(5)))
        finally:
            srv.shutdown()


if __name__ == "__main__":
    unittest.main()
