import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway down")
        return "re_%d" % len(self.calls)


def make_order(**overrides):
    order = {
        "id": "o1",
        "owner_id": "u1",
        "charge_id": "ch_1",
        "paid": 100,
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


class TestRefund(unittest.TestCase):
    def test_success_partial_then_full(self):
        order = make_order()
        gw = FakeGateway()

        first = refund(order, 40, gw, OWNER, "k1")
        self.assertEqual(first, {"refund_id": "re_1", "amount": 40, "status": "partially_refunded"})
        self.assertEqual(order["refunded"], 40)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertIn("k1", order["keys"])

        second = refund(order, 60, gw, ADMIN, "k2")
        self.assertEqual(second["status"], "refunded")
        self.assertEqual(order["refunded"], 100)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(gw.calls, [("ch_1", 40), ("ch_1", 60)])

    def test_admin_and_support_allowed(self):
        for actor in (ADMIN, SUPPORT):
            order = make_order()
            self.assertEqual(refund(order, 10, FakeGateway(), actor, "k")["amount"], 10)

    def test_idempotent_replay_returns_stored_result_without_gateway(self):
        order = make_order()
        gw = FakeGateway()
        first = refund(order, 30, gw, OWNER, "k1")
        snapshot = copy.deepcopy(order)

        replay = refund(order, 999, gw, STRANGER, "k1")

        self.assertIs(replay, first)
        self.assertEqual(gw.calls, [("ch_1", 30)])
        self.assertEqual(order, snapshot)

    def test_idempotency_checked_before_amount_validation(self):
        stored = {"refund_id": "re_old", "amount": 10, "status": "partially_refunded"}
        order = make_order(refunded=10, status="partially_refunded", keys={"k1": stored})
        gw = FakeGateway()

        self.assertIs(refund(order, 0, gw, STRANGER, "k1"), stored)
        self.assertEqual(gw.calls, [])

    def test_amount_must_be_positive_int(self):
        for bad in (0, -1, -100, True, False, 1.5, "10", None):
            order = make_order()
            gw = FakeGateway()
            with self.assertRaises(ValueError, msg=repr(bad)):
                refund(order, bad, gw, ADMIN, "k")
            self.assertEqual(gw.calls, [])
            self.assertEqual(order["refunded"], 0)
            self.assertEqual(order["keys"], {})

    def test_amount_validation_precedes_permission(self):
        with self.assertRaises(ValueError):
            refund(make_order(), 0, FakeGateway(), STRANGER, "k")

    def test_stranger_and_unknown_role_denied(self):
        for actor in (STRANGER, {"id": "u1", "role": "viewer"}, {"id": "u1"}):
            order = make_order()
            gw = FakeGateway()
            with self.assertRaises(PermissionError):
                refund(order, 10, gw, actor, "k")
            self.assertEqual(gw.calls, [])

    def test_permission_checked_before_status(self):
        order = make_order(status="cancelled")
        with self.assertRaises(PermissionError):
            refund(order, 10, FakeGateway(), STRANGER, "k")

    def test_non_refundable_status_rejected(self):
        for status in ("cancelled", "refunded"):
            order = make_order(status=status)
            gw = FakeGateway()
            with self.assertRaises(ValueError):
                refund(order, 10, gw, ADMIN, "k")
            self.assertEqual(gw.calls, [])
            self.assertEqual(order["status"], status)

    def test_amount_cannot_exceed_remaining(self):
        order = make_order(paid=100, refunded=90, status="partially_refunded")
        gw = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 11, gw, ADMIN, "k")
        self.assertEqual(gw.calls, [])
        self.assertEqual(order["refunded"], 90)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"], {})

    def test_amount_equal_to_remaining_allowed(self):
        order = make_order(paid=100, refunded=90, status="partially_refunded")
        result = refund(order, 10, FakeGateway(), ADMIN, "k")
        self.assertEqual(result["status"], "refunded")

    def test_gateway_failure_leaves_order_unchanged_and_reraises(self):
        order = make_order(refunded=20, status="partially_refunded")
        gw = FakeGateway(fail=True)
        snapshot = copy.deepcopy(order)

        with self.assertRaises(GatewayError):
            refund(order, 30, gw, OWNER, "k1")

        self.assertEqual(order, snapshot)
        self.assertEqual(gw.calls, [("ch_1", 30)])
        self.assertNotIn("k1", order["keys"])


if __name__ == "__main__":
    unittest.main()
