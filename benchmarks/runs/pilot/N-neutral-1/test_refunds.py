"""Unit tests for ``refunds.refund`` (spec: refunds.md).

Every guard is exercised on its own class: idempotency, amount validation,
permission, order status, refundable balance and gateway-failure atomicity.
"""

import copy
import unittest

from refunds import GatewayError, refund

ADMIN = {"id": "adm_1", "role": "admin"}
SUPPORT = {"id": "sup_1", "role": "support"}
OWNER = {"id": "cus_1", "role": "customer"}
STRANGER = {"id": "cus_2", "role": "customer"}


class FakeGateway:
    """Test double for the payment gateway: records calls, can fail on demand."""

    def __init__(self, refund_id="re_1", error=None):
        self.refund_id = refund_id
        self.error = error
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.error is not None:
            raise self.error
        return self.refund_id


def make_order(**overrides):
    order = {
        "id": "ord_1",
        "owner_id": "cus_1",
        "charge_id": "ch_1",
        "paid": 1000,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


class RefundIdempotencyTests(unittest.TestCase):
    def test_idempotency_replay_returns_stored_result(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 400, gateway, OWNER, "key-1")
        after_first = copy.deepcopy(order)

        second = refund(order, 400, gateway, OWNER, "key-1")

        self.assertEqual(first, second)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order, after_first)

    def test_idempotency_replay_skips_later_rules(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 400, gateway, OWNER, "key-1")

        # Zero amount (rule 2), a stranger (rule 3) and, after the first refund,
        # an order that is not fully refundable (rule 5): rule 1 still wins.
        second = refund(order, 0, gateway, STRANGER, "key-1")

        self.assertEqual(first, second)
        self.assertEqual(len(gateway.calls), 1)

    def test_idempotency_replay_after_full_refund(self):
        order = make_order(paid=100)
        gateway = FakeGateway()
        first = refund(order, 100, gateway, OWNER, "key-full")
        self.assertEqual(order["status"], "refunded")

        # Rule 4 would reject a "refunded" order, but the key is already stored.
        self.assertEqual(refund(order, 100, gateway, OWNER, "key-full"), first)
        self.assertEqual(len(gateway.calls), 1)

    def test_idempotency_keys_are_independent(self):
        order = make_order()
        gateway = FakeGateway()

        refund(order, 100, gateway, OWNER, "key-a")
        refund(order, 150, gateway, OWNER, "key-b")

        self.assertEqual(order["refunded"], 250)
        self.assertEqual([amount for _, amount in gateway.calls], [100, 150])
        self.assertEqual(sorted(order["keys"]), ["key-a", "key-b"])


class RefundAmountTests(unittest.TestCase):
    def assert_amount_rejected(self, amount):
        order = make_order()
        before = copy.deepcopy(order)
        gateway = FakeGateway()

        with self.assertRaises(ValueError):
            refund(order, amount, gateway, ADMIN, "key")

        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, before)

    def test_amount_rejects_zero_and_negative_ints(self):
        for amount in (0, -1, -1000):
            with self.subTest(amount=amount):
                self.assert_amount_rejected(amount)

    def test_amount_rejects_bool(self):
        # bool is an int subclass; True must not pass as amount 1.
        for amount in (True, False):
            with self.subTest(amount=amount):
                self.assert_amount_rejected(amount)

    def test_amount_rejects_floats(self):
        for amount in (1.0, 10.5, 0.5):
            with self.subTest(amount=amount):
                self.assert_amount_rejected(amount)

    def test_amount_rejects_non_numbers(self):
        for amount in ("10", "", None, [10], {"amount": 10}):
            with self.subTest(amount=amount):
                self.assert_amount_rejected(amount)

    def test_amount_checked_before_permission(self):
        order = make_order()
        gateway = FakeGateway()

        # Rule 2 comes before rule 3: the stranger sees the amount error.
        with self.assertRaises(ValueError):
            refund(order, -5, gateway, STRANGER, "key")
        self.assertEqual(gateway.calls, [])


class RefundPermissionTests(unittest.TestCase):
    def assert_denied(self, actor, order=None):
        order = order or make_order()
        before = copy.deepcopy(order)
        gateway = FakeGateway()

        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, actor, "key")

        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, before)

    def test_permission_denies_customer_who_does_not_own_order(self):
        self.assert_denied(STRANGER)

    def test_permission_denies_unknown_role(self):
        self.assert_denied({"id": "cus_1", "role": "auditor"})

    def test_permission_denies_missing_role(self):
        self.assert_denied({"id": "cus_1"})

    def test_permission_denies_empty_actor(self):
        self.assert_denied({})

    def test_permission_allows_staff_and_owner(self):
        for actor in (ADMIN, SUPPORT, OWNER):
            with self.subTest(actor=actor["role"]):
                order = make_order()
                result = refund(order, 100, FakeGateway(), actor, "key")
                self.assertEqual(result["amount"], 100)
                self.assertEqual(order["refunded"], 100)

    def test_permission_checked_before_status(self):
        # Rule 3 comes before rule 4: a stranger gets PermissionError, not ValueError.
        self.assert_denied(STRANGER, make_order(status="cancelled"))

    def test_permission_checked_before_refundable_balance(self):
        self.assert_denied(STRANGER, make_order(paid=100, refunded=100, status="partially_refunded"))


class RefundStatusTests(unittest.TestCase):
    def assert_status_rejected(self, status):
        order = make_order(status=status)
        before = copy.deepcopy(order)
        gateway = FakeGateway()

        with self.assertRaises(ValueError):
            refund(order, 100, gateway, ADMIN, "key")

        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, before)

    def test_status_rejects_refunded(self):
        self.assert_status_rejected("refunded")

    def test_status_rejects_cancelled(self):
        self.assert_status_rejected("cancelled")

    def test_status_rejects_unknown_status(self):
        self.assert_status_rejected("pending")

    def test_status_allows_paid(self):
        order = make_order()
        result = refund(order, 100, FakeGateway(), OWNER, "key")
        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(order["status"], "partially_refunded")

    def test_status_allows_partially_refunded(self):
        order = make_order(paid=1000, refunded=400, status="partially_refunded")
        result = refund(order, 100, FakeGateway(), OWNER, "key")
        self.assertEqual(order["refunded"], 500)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(result["status"], "partially_refunded")


class RefundCapTests(unittest.TestCase):
    def assert_cap_rejected(self, order, amount):
        before = copy.deepcopy(order)
        gateway = FakeGateway()

        with self.assertRaises(ValueError):
            refund(order, amount, gateway, ADMIN, "key")

        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, before)

    def test_cap_rejects_amount_above_remaining(self):
        self.assert_cap_rejected(make_order(), 1001)

    def test_cap_rejects_one_above_remaining(self):
        order = make_order(paid=1000, refunded=400, status="partially_refunded")
        self.assert_cap_rejected(order, 601)

    def test_cap_rejects_any_amount_when_nothing_remaining(self):
        order = make_order(paid=1000, refunded=1000, status="partially_refunded")
        self.assert_cap_rejected(order, 1)

    def test_cap_allows_exact_remaining(self):
        order = make_order(paid=1000, refunded=400, status="partially_refunded")
        gateway = FakeGateway()

        result = refund(order, 600, gateway, OWNER, "key")

        self.assertEqual(gateway.calls, [("ch_1", 600)])
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(result["status"], "refunded")

    def test_cap_allows_amount_below_remaining(self):
        order = make_order(paid=1000, refunded=400, status="partially_refunded")
        result = refund(order, 500, FakeGateway(), OWNER, "key")
        self.assertEqual(order["refunded"], 900)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(result["status"], "partially_refunded")


class GatewayAtomicityTests(unittest.TestCase):
    def test_atomicity_order_unchanged_on_gateway_error(self):
        order = make_order(paid=1000, refunded=400, status="partially_refunded")
        before = copy.deepcopy(order)
        keys_before = order["keys"]
        gateway = FakeGateway(error=GatewayError("card declined"))

        with self.assertRaises(GatewayError):
            refund(order, 500, gateway, OWNER, "key-fail")

        self.assertEqual(order, before)
        self.assertIs(order["keys"], keys_before)
        self.assertEqual(order["keys"], {})

    def test_atomicity_error_propagates_unchanged(self):
        order = make_order()
        gateway = FakeGateway(error=GatewayError("network down"))

        with self.assertRaises(GatewayError) as caught:
            refund(order, 100, gateway, OWNER, "key-fail")

        self.assertEqual(str(caught.exception), "network down")

    def test_atomicity_gateway_called_once_on_failure(self):
        order = make_order()
        gateway = FakeGateway(error=GatewayError("declined"))

        with self.assertRaises(GatewayError):
            refund(order, 250, gateway, OWNER, "key-fail")

        self.assertEqual(gateway.calls, [("ch_1", 250)])

    def test_atomicity_status_unchanged_on_paid_order(self):
        order = make_order()
        gateway = FakeGateway(error=GatewayError("declined"))

        with self.assertRaises(GatewayError):
            refund(order, 1000, gateway, OWNER, "key-fail")

        self.assertEqual(order["refunded"], 0)
        self.assertEqual(order["status"], "paid")

    def test_atomicity_retry_with_same_key_succeeds(self):
        order = make_order()
        gateway = FakeGateway(error=GatewayError("declined"))

        with self.assertRaises(GatewayError):
            refund(order, 400, gateway, OWNER, "key-retry")

        # Nothing was stored, so the same key is free to be used again.
        self.assertNotIn("key-retry", order["keys"])
        gateway.error = None
        result = refund(order, 400, gateway, OWNER, "key-retry")

        self.assertEqual(order["refunded"], 400)
        self.assertEqual(result["refund_id"], "re_1")
        self.assertEqual(order["keys"]["key-retry"], result)
        self.assertEqual(len(gateway.calls), 2)


class RefundSuccessTests(unittest.TestCase):
    def test_success_records_refund_and_returns_result(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_42")

        result = refund(order, 250, gateway, OWNER, "key-1")

        self.assertEqual(
            result,
            {
                "refund_id": "re_42",
                "amount": 250,
                "status": "partially_refunded",
            },
        )
        self.assertEqual(order["refunded"], 250)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["key-1"], result)
        self.assertEqual(gateway.calls, [("ch_1", 250)])

    def test_success_full_refund_marks_order_refunded(self):
        order = make_order(paid=300, refunded=100, status="partially_refunded")
        result = refund(order, 200, FakeGateway(), OWNER, "key-1")
        self.assertEqual(order["refunded"], 300)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(result["status"], "refunded")

    def test_success_sequential_refunds_accumulate(self):
        order = make_order()
        gateway = FakeGateway()

        refund(order, 400, gateway, OWNER, "key-1")
        refund(order, 600, gateway, SUPPORT, "key-2")

        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(len(order["keys"]), 2)


if __name__ == "__main__":
    unittest.main()
