import os, tempfile, unittest
from outbox import Outbox
from orders import Orders


class OrdersTests(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.ob = Outbox(os.path.join(self.d.name, "t.db"))
        self.o = Orders(self.ob)

    def tearDown(self):
        self.d.cleanup()

    def test_confirm_enqueues_atomically(self):
        self.o.create("o1", "http://c")
        self.o.confirm_order("o1")
        self.assertEqual(self.ob.counts(), {"pending": 1})
        st = self.ob.conn().execute("SELECT status FROM orders WHERE id='o1'").fetchone()[0]
        self.assertEqual(st, "confirmed")

    def test_unknown_order_rolls_back(self):
        with self.assertRaises(KeyError):
            self.o.confirm_order("nope")
        self.assertEqual(self.ob.counts(), {})
        self.o.create("o2", "http://c"); self.o.confirm_order("o2")

    def test_rollback_on_enqueue_failure(self):
        self.o.create("o3", "http://c")
        self.ob.enqueue = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("x"))
        with self.assertRaises(RuntimeError):
            self.o.confirm_order("o3")
        st = self.ob.conn().execute("SELECT status FROM orders WHERE id='o3'").fetchone()[0]
        self.assertEqual(st, "new")


if __name__ == "__main__":
    unittest.main()
