"""Unit tests for refunds.refund (see specs/refunds.md)."""

import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """In-memory stand-in for the payment gateway."""

    def __init__(self, refund_id="re_1"):
        self.refund_id = refund_id
        self.calls = []
        self.fail = False

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway unavailable")
        return self.refund_id


def make_order(**overrides):
    order = {
        "id": "ord_1",
        "owner_id": "cust_1",
        "charge_id": "ch_1",
        "paid": 100,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


ADMIN = {"id": "adm_1", "role": "admin"}
SUPPORT = {"id": "sup_1", "role": "support"}
OWNER = {"id": "cust_1", "role": "customer"}
OTHER_CUSTOMER = {"id": "cust_2", "role": "customer"}

class HappyPathTests(unittest.TestCase):
    def setUp(self):
        self.order = make_order()
        self.gateway = FakeGateway()

    def test_partial_refund_updates_order_and_returns_result(self):
        result = refund(self.order, 40, self.gateway, ADMIN, "key-1")

        self.assertEqual(
            result,
            {"refund_id": "re_1", "amount": 40, "status": "partially_refunded"},
        )
        self.assertEqual(self.order["refunded"], 40)
        self.assertEqual(self.order["status"], "partially_refunded")
        self.assertIs(self.order["keys"]["key-1"], result)

    def test_gateway_called_exactly_once_with_charge_and_amount(self):
        refund(self.order, 25, self.gateway, SUPPORT, "key-1")

        self.assertEqual(self.gateway.calls, [("ch_1", 25)])

    def test_second_refund_completes_the_order(self):
        refund(self.order, 40, self.gateway, ADMIN, "key-1")
        result = refund(self.order, 60, self.gateway, OWNER, "key-2")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(result["amount"], 60)
        self.assertEqual(self.order["refunded"], 100)
        self.assertEqual(self.order["status"], "refunded")
        self.assertEqual(len(self.gateway.calls), 2)

    def test_full_refund_in_one_call_is_marked_refunded(self):
        result = refund(self.order, 100, self.gateway, ADMIN, "key-1")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(self.order["status"], "refunded")
        self.assertEqual(self.order["refunded"], 100)

    def test_each_successful_refund_is_stored_under_its_key(self):
        first = refund(self.order, 10, self.gateway, ADMIN, "a")
        second = refund(self.order, 20, self.gateway, ADMIN, "b")

        self.assertIs(self.order["keys"]["a"], first)
        self.assertIs(self.order["keys"]["b"], second)
        self.assertEqual(set(self.order["keys"]), {"a", "b"})


class IdempotencyGuardTests(unittest.TestCase):
    def test_repeat_key_returns_stored_result_without_touching_anything(self):
        stored = {"refund_id": "re_old", "amount": 30, "status": "partially_refunded"}
        order = make_order(refunded=30, status="partially_refunded", keys={"k": stored})
        gateway = FakeGateway(refund_id="re_new")
        snapshot = copy.deepcopy(order)

        result = refund(order, 30, gateway, ADMIN, "k")

        self.assertIs(result, stored)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_idempotency_is_checked_before_every_other_rule(self):
        stored = {"refund_id": "re_old", "amount": 5, "status": "partially_refunded"}
        order = make_order(refunded=5, status="partially_refunded", keys={"k": stored})
        gateway = FakeGateway()
        snapshot = copy.deepcopy(order)

        # Invalid amount, unauthorized actor and over-cap amount: the stored
        # result still wins because rule 1 runs first.
        self.assertIs(refund(order, -5, gateway, OTHER_CUSTOMER, "k"), stored)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_repeat_of_completed_refund_returns_stored_result(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 100, gateway, ADMIN, "k")
        snapshot = copy.deepcopy(order)

        self.assertIs(refund(order, 1, gateway, OWNER, "k"), first)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order, snapshot)


class AmountValidationGuardTests(unittest.TestCase):
    def setUp(self):
        self.order = make_order()
        self.gateway = FakeGateway()
        self.snapshot = copy.deepcopy(self.order)

    def assert_rejected(self, amount):
        with self.assertRaises(ValueError):
            refund(self.order, amount, self.gateway, ADMIN, "key-1")
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.order, self.snapshot)

    def test_zero_is_rejected(self):
        self.assert_rejected(0)

    def test_negative_is_rejected(self):
        self.assert_rejected(-1)

    def test_bool_true_is_rejected(self):
        self.assert_rejected(True)

    def test_bool_false_is_rejected(self):
        self.assert_rejected(False)

    def test_float_is_rejected(self):
        self.assert_rejected(10.0)

    def test_numeric_string_is_rejected(self):
        self.assert_rejected("10")

    def test_positive_int_is_accepted(self):
        result = refund(self.order, 1, self.gateway, ADMIN, "key-1")
        self.assertEqual(result["amount"], 1)

    def test_amount_is_validated_before_permission(self):
        order = make_order()
        with self.assertRaises(ValueError):
            refund(order, 0, self.gateway, OTHER_CUSTOMER, "key-1")
        self.assertEqual(self.gateway.calls, [])


class PermissionGuardTests(unittest.TestCase):
    def setUp(self):
        self.order = make_order()
        self.gateway = FakeGateway()
        self.snapshot = copy.deepcopy(self.order)

    def assert_denied(self, actor):
        with self.assertRaises(PermissionError):
            refund(self.order, 10, self.gateway, actor, "key-1")
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.order, self.snapshot)

    def test_admin_may_refund(self):
        result = refund(self.order, 10, self.gateway, ADMIN, "key-1")
        self.assertEqual(result["amount"], 10)

    def test_support_may_refund(self):
        result = refund(self.order, 10, self.gateway, SUPPORT, "key-1")
        self.assertEqual(result["amount"], 10)

    def test_owning_customer_may_refund(self):
        result = refund(self.order, 10, self.gateway, OWNER, "key-1")
        self.assertEqual(result["amount"], 10)

    def test_other_customer_is_denied(self):
        self.assert_denied(OTHER_CUSTOMER)

    def test_customer_role_with_matching_wrong_id_is_denied(self):
        self.assert_denied({"id": "cust_2", "role": "customer"})

    def test_matching_id_with_unknown_role_is_denied(self):
        self.assert_denied({"id": "cust_1", "role": "guest"})

    def test_empty_actor_is_denied(self):
        self.assert_denied({})

    def test_missing_role_is_denied(self):
        self.assert_denied({"id": "cust_1"})

    def test_permission_is_checked_before_status(self):
        order = make_order(status="cancelled")
        with self.assertRaises(PermissionError):
            refund(order, 10, self.gateway, OTHER_CUSTOMER, "key-1")
        self.assertEqual(self.gateway.calls, [])


class StatusGuardTests(unittest.TestCase):
    def setUp(self):
        self.gateway = FakeGateway()

    def assert_rejected(self, status):
        order = make_order(status=status)
        snapshot = copy.deepcopy(order)
        with self.assertRaises(ValueError):
            refund(order, 10, self.gateway, ADMIN, "key-1")
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_cancelled_order_is_rejected(self):
        self.assert_rejected("cancelled")

    def test_already_refunded_order_is_rejected(self):
        self.assert_rejected("refunded")

    def test_paid_order_is_accepted(self):
        order = make_order(status="paid")
        result = refund(order, 10, self.gateway, ADMIN, "key-1")
        self.assertEqual(result["status"], "partially_refunded")

    def test_partially_refunded_order_is_accepted(self):
        order = make_order(paid=100, refunded=20, status="partially_refunded")
        result = refund(order, 10, self.gateway, ADMIN, "key-1")
        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 30)


class RefundableCapGuardTests(unittest.TestCase):
    def setUp(self):
        self.gateway = FakeGateway()

    def test_exact_remainder_is_allowed(self):
        order = make_order(paid=100, refunded=70, status="partially_refunded")
        result = refund(order, 30, self.gateway, ADMIN, "key-1")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 100)

    def test_one_over_remainder_is_rejected(self):
        order = make_order(paid=100, refunded=70, status="partially_refunded")
        snapshot = copy.deepcopy(order)
        with self.assertRaises(ValueError):
            refund(order, 31, self.gateway, ADMIN, "key-1")
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_full_paid_amount_is_allowed_when_nothing_refunded(self):
        order = make_order(paid=100, refunded=0, status="paid")
        result = refund(order, 100, self.gateway, ADMIN, "key-1")
        self.assertEqual(result["status"], "refunded")

    def test_any_amount_is_rejected_when_nothing_remains(self):
        order = make_order(paid=100, refunded=100, status="partially_refunded")
        snapshot = copy.deepcopy(order)
        with self.assertRaises(ValueError):
            refund(order, 1, self.gateway, ADMIN, "key-1")
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(order, snapshot)


class GatewayFailureAtomicityGuardTests(unittest.TestCase):
    def setUp(self):
        self.order = make_order(refunded=40, status="partially_refunded")
        self.gateway = FakeGateway()
        self.snapshot = copy.deepcopy(self.order)

    def test_gateway_error_is_reraised(self):
        self.gateway.fail = True
        with self.assertRaises(GatewayError):
            refund(self.order, 10, self.gateway, ADMIN, "key-1")

    def test_order_is_completely_unchanged_after_gateway_error(self):
        self.gateway.fail = True
        with self.assertRaises(GatewayError):
            refund(self.order, 10, self.gateway, ADMIN, "key-1")

        self.assertEqual(self.order, self.snapshot)
        self.assertEqual(self.order["refunded"], 40)
        self.assertEqual(self.order["status"], "partially_refunded")
        self.assertNotIn("key-1", self.order["keys"])

    def test_failed_refund_does_not_poison_a_later_retry(self):
        self.gateway.fail = True
        with self.assertRaises(GatewayError):
            refund(self.order, 10, self.gateway, ADMIN, "key-1")
        self.gateway.fail = False

        result = refund(self.order, 10, self.gateway, ADMIN, "key-1")

        self.assertEqual(result["amount"], 10)
        self.assertEqual(self.order["refunded"], 50)
        self.assertEqual(self.order["status"], "partially_refunded")
        self.assertEqual(self.order["keys"]["key-1"], result)
        self.assertEqual(self.gateway.calls, [("ch_1", 10), ("ch_1", 10)])

    def test_gateway_error_on_full_refund_leaves_status_and_total(self):
        order = make_order()
        snapshot = copy.deepcopy(order)
        self.gateway.fail = True
        with self.assertRaises(GatewayError):
            refund(order, 100, self.gateway, ADMIN, "key-1")

        self.assertEqual(order, snapshot)
        self.assertEqual(order["status"], "paid")


if __name__ == "__main__":
    unittest.main()
