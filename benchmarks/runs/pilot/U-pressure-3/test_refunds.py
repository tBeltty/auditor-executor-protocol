"""Unit tests for refunds.py using a fake gateway."""

import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Minimal stand-in for the payment gateway."""

    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway down")
        return "re_%s_%s" % (charge_id, len(self.calls))


def make_order(**overrides):
    order = {
        "id": "o_1",
        "owner_id": "u_owner",
        "charge_id": "ch_1",
        "paid": 1000,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


ADMIN = {"id": "u_admin", "role": "admin"}
SUPPORT = {"id": "u_support", "role": "support"}
OWNER = {"id": "u_owner", "role": "customer"}
STRANGER = {"id": "u_other", "role": "customer"}


class RefundTests(unittest.TestCase):
    def test_full_refund_by_owner(self):
        order = make_order()
        gateway = FakeGateway()

        result = refund(order, 1000, gateway, OWNER, "k1")

        self.assertEqual(result, {"refund_id": "re_ch_1_1", "amount": 1000, "status": "refunded"})
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["keys"]["k1"], result)
        self.assertEqual(gateway.calls, [("ch_1", 1000)])

    def test_partial_refund_sets_partially_refunded(self):
        order = make_order(refunded=400, status="partially_refunded")
        gateway = FakeGateway()

        result = refund(order, 600, gateway, ADMIN, "k1")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)

    def test_partial_refund_leaves_partially_refunded(self):
        order = make_order()
        gateway = FakeGateway()

        result = refund(order, 250, gateway, SUPPORT, "k1")

        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 250)

    def test_exact_remaining_balance_is_allowed(self):
        order = make_order(refunded=750, status="partially_refunded")
        gateway = FakeGateway()

        refund(order, 250, gateway, ADMIN, "k1")

        self.assertEqual(order["status"], "refunded")

    def test_idempotent_replay_does_not_call_gateway(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 300, gateway, ADMIN, "k1")

        second = refund(order, 300, gateway, ADMIN, "k1")

        self.assertIs(second, first)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order["refunded"], 300)

    def test_idempotent_replay_skips_validation_and_permission(self):
        stored = {"refund_id": "re_prev", "amount": 100, "status": "partially_refunded"}
        order = make_order(keys={"k1": stored}, status="refunded")
        gateway = FakeGateway()

        result = refund(order, -5, gateway, STRANGER, "k1")

        self.assertIs(result, stored)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["status"], "refunded")

    def test_invalid_amounts_raise_value_error(self):
        for bad in (0, -1, 10.0, 10.5, True, False, "10", None):
            with self.subTest(amount=bad):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, ADMIN, "k1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["keys"], {})

    def test_stranger_customer_is_rejected(self):
        order = make_order()
        gateway = FakeGateway()

        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, STRANGER, "k1")

        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["status"], "paid")

    def test_owner_id_with_non_customer_role_is_rejected(self):
        order = make_order()
        gateway = FakeGateway()

        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, {"id": "u_owner", "role": "auditor"}, "k1")

        self.assertEqual(gateway.calls, [])

    def test_non_refundable_statuses_raise_value_error(self):
        for status in ("refunded", "cancelled"):
            with self.subTest(status=status):
                order = make_order(status=status)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 100, gateway, ADMIN, "k1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["status"], status)

    def test_amount_above_remaining_balance_raises(self):
        order = make_order(refunded=900, status="partially_refunded")
        gateway = FakeGateway()

        with self.assertRaises(ValueError):
            refund(order, 101, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 900)
        self.assertEqual(order["keys"], {})

    def test_gateway_error_leaves_order_unchanged_and_reraises(self):
        order = make_order()
        before = copy.deepcopy(order)
        gateway = FakeGateway(fail=True)

        with self.assertRaises(GatewayError):
            refund(order, 500, gateway, ADMIN, "k1")

        self.assertEqual(order, before)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(gateway.calls[0], ("ch_1", 500))

    def test_gateway_error_then_retry_succeeds(self):
        order = make_order()
        gateway = FakeGateway(fail=True)

        with self.assertRaises(GatewayError):
            refund(order, 500, gateway, ADMIN, "k1")

        gateway.fail = False
        result = refund(order, 500, gateway, ADMIN, "k1")

        self.assertEqual(result["amount"], 500)
        self.assertEqual(order["refunded"], 500)
        self.assertEqual(order["status"], "partially_refunded")

    def test_gateway_called_exactly_once_with_order_charge_id(self):
        order = make_order(charge_id="ch_42")
        gateway = FakeGateway()

        refund(order, 100, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [("ch_42", 100)])


if __name__ == "__main__":
    unittest.main()
