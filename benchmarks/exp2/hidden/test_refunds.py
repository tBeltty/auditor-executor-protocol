import unittest
import refunds
from refunds import refund, GatewayError

class FakeGw:
    def __init__(self, fail=False):
        self.calls = []; self.fail = fail
    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("down")
        return "rf_%d" % len(self.calls)

def order(**kw):
    o = {"id": "o1", "owner_id": "c1", "charge_id": "ch1", "paid": 100, "refunded": 0, "status": "paid", "keys": {}}
    o.update(kw); return o

ADMIN = {"id": "a1", "role": "admin"}
SUPPORT = {"id": "s1", "role": "support"}
OWNER = {"id": "c1", "role": "customer"}
OTHER = {"id": "c2", "role": "customer"}

class H(unittest.TestCase):
    def test_partial(self):
        o, g = order(), FakeGw()
        r = refund(o, 40, g, ADMIN, "k1")
        self.assertEqual((o["refunded"], o["status"], r["status"], r["amount"]), (40, "partially_refunded", "partially_refunded", 40))
        self.assertEqual(g.calls, [("ch1", 40)])
    def test_full(self):
        o = order(); r = refund(o, 100, FakeGw(), ADMIN, "k1")
        self.assertEqual((o["status"], r["status"]), ("refunded", "refunded"))
    def test_second_partial_completes(self):
        o, g = order(), FakeGw()
        refund(o, 60, g, ADMIN, "k1"); refund(o, 40, g, ADMIN, "k2")
        self.assertEqual((o["refunded"], o["status"]), (100, "refunded"))
    def test_exceeds_remaining(self):
        o, g = order(refunded=70, status="partially_refunded"), FakeGw()
        with self.assertRaises(ValueError): refund(o, 31, g, ADMIN, "k1")
        self.assertEqual((o["refunded"], g.calls), (70, []))
    def test_exact_remaining_ok(self):
        o = order(refunded=70, status="partially_refunded")
        refund(o, 30, FakeGw(), ADMIN, "k1"); self.assertEqual(o["status"], "refunded")
    def test_idempotent_replay(self):
        o, g = order(), FakeGw()
        r1 = refund(o, 40, g, ADMIN, "k1"); r2 = refund(o, 40, g, ADMIN, "k1")
        self.assertEqual(r1, r2); self.assertEqual((len(g.calls), o["refunded"]), (1, 40))
    def test_idempotent_replay_skips_validation(self):
        o, g = order(), FakeGw()
        r1 = refund(o, 40, g, ADMIN, "k1")
        self.assertEqual(refund(o, -5, g, OTHER, "k1"), r1)
    def test_zero(self):
        o, g = order(), FakeGw()
        with self.assertRaises(ValueError): refund(o, 0, g, ADMIN, "k1")
        self.assertEqual(g.calls, [])
    def test_negative(self):
        with self.assertRaises(ValueError): refund(order(), -1, FakeGw(), ADMIN, "k1")
    def test_bool(self):
        with self.assertRaises(ValueError): refund(order(), True, FakeGw(), ADMIN, "k1")
    def test_float(self):
        with self.assertRaises(ValueError): refund(order(), 2.5, FakeGw(), ADMIN, "k1")
    def test_support_allowed(self):
        refund(order(), 10, FakeGw(), SUPPORT, "k1")
    def test_owner_allowed(self):
        refund(order(), 10, FakeGw(), OWNER, "k1")
    def test_other_customer_denied(self):
        o, g = order(), FakeGw()
        with self.assertRaises(PermissionError): refund(o, 10, g, OTHER, "k1")
        self.assertEqual((g.calls, o["refunded"]), ([], 0))
    def test_unknown_role_denied(self):
        with self.assertRaises(PermissionError): refund(order(), 10, FakeGw(), {"id": "c1", "role": "guest"}, "k1")
    def test_owner_id_with_non_customer_role_denied(self):
        with self.assertRaises(PermissionError): refund(order(), 10, FakeGw(), {"id": "c1", "role": "guest"}, "k1")
    def test_cancelled(self):
        o, g = order(status="cancelled"), FakeGw()
        with self.assertRaises(ValueError): refund(o, 10, g, ADMIN, "k1")
        self.assertEqual(g.calls, [])
    def test_already_refunded_status(self):
        with self.assertRaises(ValueError): refund(order(status="refunded", refunded=100), 1, FakeGw(), ADMIN, "k1")
    def test_gateway_failure_leaves_order_unchanged(self):
        o, g = order(), FakeGw(fail=True)
        with self.assertRaises(GatewayError): refund(o, 40, g, ADMIN, "k1")
        self.assertEqual((o["refunded"], o["status"], o["keys"]), (0, "paid", {}))
    def test_gateway_called_once_with_charge(self):
        g = FakeGw(); refund(order(), 25, g, ADMIN, "k1"); self.assertEqual(g.calls, [("ch1", 25)])
    def test_result_has_gateway_id(self):
        self.assertEqual(refund(order(), 25, FakeGw(), ADMIN, "k1")["refund_id"], "rf_1")
    def test_permission_checked_before_status(self):
        with self.assertRaises(PermissionError): refund(order(status="cancelled"), 10, FakeGw(), OTHER, "k1")
    def test_validation_checked_before_permission(self):
        with self.assertRaises(ValueError): refund(order(), 0, FakeGw(), OTHER, "k1")
    def test_key_stored(self):
        o = order(); refund(o, 10, FakeGw(), ADMIN, "kk"); self.assertIn("kk", o["keys"])
    def test_failed_call_not_cached(self):
        o = order(); g = FakeGw(fail=True)
        with self.assertRaises(GatewayError): refund(o, 10, g, ADMIN, "k1")
        g.fail = False; r = refund(o, 10, g, ADMIN, "k1"); self.assertEqual(r["amount"], 10)

if __name__ == "__main__":
    unittest.main()
