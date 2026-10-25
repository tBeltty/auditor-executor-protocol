import unittest

from refunds import GatewayError, refund


class FakeGateway:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.error is not None:
            raise self.error
        return "re_%d" % len(self.calls)


def make_order(**overrides):
    order = {
        "id": "o1",
        "owner_id": "u1",
        "charge_id": "ch_1",
        "paid": 1000,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


ADMIN = {"id": "a1", "role": "admin"}
SUPPORT = {"id": "s1", "role": "support"}
OWNER = {"id": "u1", "role": "customer"}
STRANGER = {"id": "u2", "role": "customer"}


class RefundTests(unittest.TestCase):
    def test_partial_refund(self):
        order, gw = make_order(), FakeGateway()
        result = refund(order, 400, gw, ADMIN, "k1")
        self.assertEqual(gw.calls, [("ch_1", 400)])
        self.assertEqual(result, {"refund_id": "re_1", "amount": 400,
                                  "status": "partially_refunded"})
        self.assertEqual(order["refunded"], 400)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["k1"], result)

    def test_full_refund_sets_refunded_status(self):
        order, gw = make_order(), FakeGateway()
        result = refund(order, 1000, gw, OWNER, "k1")
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(result["status"], "refunded")

    def test_idempotent_replay_skips_gateway_and_mutation(self):
        order, gw = make_order(), FakeGateway()
        first = refund(order, 250, gw, ADMIN, "k1")
        snapshot = dict(order)
        second = refund(order, 999, gw, STRANGER, "k1")
        self.assertEqual(second, first)
        self.assertEqual(len(gw.calls), 1)
        self.assertEqual(order["refunded"], snapshot["refunded"])
        self.assertEqual(order["status"], snapshot["status"])

    def test_amount_validation(self):
        for bad in (0, -1, True, False, 1.5, "10", None):
            with self.subTest(amount=bad):
                order, gw = make_order(), FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gw, ADMIN, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order["refunded"], 0)

    def test_permissions(self):
        for actor in (STRANGER, {"id": "u1", "role": "viewer"},
                      {"id": "x", "role": "admin2"}):
            with self.subTest(actor=actor):
                order, gw = make_order(), FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 100, gw, actor, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order["keys"], {})

    def test_admin_and_support_allowed_regardless_of_owner(self):
        for actor in (ADMIN, SUPPORT):
            with self.subTest(role=actor["role"]):
                order, gw = make_order(), FakeGateway()
                refund(order, 100, gw, actor, "k")
                self.assertEqual(len(gw.calls), 1)

    def test_status_must_be_refundable(self):
        for status in ("refunded", "cancelled", "pending"):
            with self.subTest(status=status):
                order, gw = make_order(status=status), FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 100, gw, ADMIN, "k")
                self.assertEqual(gw.calls, [])

    def test_amount_cannot_exceed_remaining(self):
        order, gw = make_order(refunded=600, status="partially_refunded"), FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 401, gw, ADMIN, "k")
        self.assertEqual(gw.calls, [])
        self.assertEqual(order["refunded"], 600)

    def test_exact_remaining_allowed(self):
        order, gw = make_order(refunded=600, status="partially_refunded"), FakeGateway()
        refund(order, 400, gw, ADMIN, "k")
        self.assertEqual(order["status"], "refunded")

    def test_gateway_error_leaves_order_unchanged_and_reraises(self):
        order = make_order()
        gw = FakeGateway(error=GatewayError("boom"))
        before = {k: (dict(v) if isinstance(v, dict) else v)
                  for k, v in order.items()}
        with self.assertRaises(GatewayError):
            refund(order, 100, gw, ADMIN, "k")
        self.assertEqual(len(gw.calls), 1)
        self.assertEqual(order, before)
        self.assertNotIn("k", order["keys"])

    def test_check_order_validation_precedes_gateway(self):
        # amount validation beats authorisation
        order, gw = make_order(), FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 0, gw, STRANGER, "k")
        # authorisation beats status
        order, gw = make_order(status="cancelled"), FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gw, STRANGER, "k")
        # status beats amount-vs-remaining
        order, gw = make_order(status="cancelled", refunded=1000), FakeGateway()
        with self.assertRaises(ValueError) as ctx:
            refund(order, 500, gw, ADMIN, "k")
        self.assertIn("not refundable", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
