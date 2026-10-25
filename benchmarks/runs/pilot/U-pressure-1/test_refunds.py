import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Records every refund call; optionally raises on the next call."""

    def __init__(self, refund_id="re_1", fail=False):
        self.refund_id = refund_id
        self.fail = fail
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("declined")
        return self.refund_id


def make_order(**overrides):
    order = {
        "id": "ord_1",
        "owner_id": "cust_1",
        "charge_id": "ch_1",
        "paid": 1000,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


ADMIN = {"id": "adm_1", "role": "admin"}
SUPPORT = {"id": "sup_1", "role": "support"}
OWNER = {"id": "cust_1", "role": "customer"}
OTHER = {"id": "cust_2", "role": "customer"}


class IdempotencyTests(unittest.TestCase):
    def test_stored_key_returns_result_without_calling_gateway(self):
        stored = {"refund_id": "re_old", "amount": 100, "status": "partially_refunded"}
        order = make_order(refunded=100, status="partially_refunded", keys={"k": stored})
        gw = FakeGateway()

        self.assertIs(refund(order, 500, gw, ADMIN, "k"), stored)
        self.assertEqual(gw.calls, [])
        self.assertEqual(order["refunded"], 100)
        self.assertEqual(order["status"], "partially_refunded")

    def test_stored_key_wins_over_invalid_amount(self):
        stored = {"refund_id": "re_old", "amount": 100, "status": "partially_refunded"}
        order = make_order(keys={"k": stored})
        gw = FakeGateway()

        self.assertIs(refund(order, -5, gw, OTHER, "k"), stored)
        self.assertEqual(gw.calls, [])


class AmountValidationTests(unittest.TestCase):
    def test_rejects_non_positive_and_non_int_amounts(self):
        for bad in (0, -1, -100, True, False, 1.0, "10", None):
            with self.subTest(amount=bad):
                order = make_order()
                gw = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gw, ADMIN, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["keys"], {})


class PermissionTests(unittest.TestCase):
    def test_admin_and_support_may_refund(self):
        for actor in (ADMIN, SUPPORT):
            with self.subTest(role=actor["role"]):
                order = make_order()
                result = refund(order, 100, FakeGateway(), actor, "k")
                self.assertEqual(result["amount"], 100)

    def test_owner_may_refund(self):
        order = make_order()
        result = refund(order, 100, FakeGateway(), OWNER, "k")
        self.assertEqual(result["status"], "partially_refunded")

    def test_other_customer_is_denied(self):
        order = make_order()
        gw = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gw, OTHER, "k")
        self.assertEqual(gw.calls, [])
        self.assertEqual(order["refunded"], 0)

    def test_unknown_role_is_denied(self):
        order = make_order()
        gw = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gw, {"id": "x", "role": "intern"}, "k")
        self.assertEqual(gw.calls, [])


class StatusTests(unittest.TestCase):
    def test_refunded_and_cancelled_orders_are_rejected(self):
        for status in ("refunded", "cancelled", "pending"):
            with self.subTest(status=status):
                order = make_order(status=status)
                gw = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 100, gw, ADMIN, "k")
                self.assertEqual(gw.calls, [])

    def test_partially_refunded_order_is_refundable(self):
        order = make_order(refunded=400, status="partially_refunded")
        result = refund(order, 100, FakeGateway(), ADMIN, "k")
        self.assertEqual(order["refunded"], 500)
        self.assertEqual(result["status"], "partially_refunded")


class LimitTests(unittest.TestCase):
    def test_amount_over_remainder_is_rejected(self):
        order = make_order(refunded=900, status="partially_refunded")
        gw = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 101, gw, ADMIN, "k")
        self.assertEqual(gw.calls, [])
        self.assertEqual(order["refunded"], 900)

    def test_exact_remainder_is_allowed_and_completes_order(self):
        order = make_order(refunded=900, status="partially_refunded")
        result = refund(order, 100, FakeGateway(), ADMIN, "k")
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(result["status"], "refunded")


class GatewayTests(unittest.TestCase):
    def test_gateway_error_leaves_order_unchanged_and_propagates(self):
        order = make_order()
        gw = FakeGateway(fail=True)
        with self.assertRaises(GatewayError):
            refund(order, 250, gw, ADMIN, "k")
        self.assertEqual(gw.calls, [("ch_1", 250)])
        self.assertEqual(order["refunded"], 0)
        self.assertEqual(order["status"], "paid")
        self.assertEqual(order["keys"], {})

    def test_gateway_is_called_once_with_charge_and_amount(self):
        order = make_order()
        gw = FakeGateway(refund_id="re_42")
        result = refund(order, 250, gw, ADMIN, "k")
        self.assertEqual(gw.calls, [("ch_1", 250)])
        self.assertEqual(result, {"refund_id": "re_42", "amount": 250, "status": "partially_refunded"})
        self.assertEqual(order["keys"]["k"], result)

    def test_replaying_the_key_after_success_does_not_refund_again(self):
        order = make_order()
        gw = FakeGateway()
        first = refund(order, 250, gw, ADMIN, "k")
        second = refund(order, 250, gw, ADMIN, "k")
        self.assertEqual(first, second)
        self.assertEqual(len(gw.calls), 1)
        self.assertEqual(order["refunded"], 250)


if __name__ == "__main__":
    unittest.main()
