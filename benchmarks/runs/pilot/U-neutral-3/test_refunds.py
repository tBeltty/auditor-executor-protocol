"""Unit tests for refunds.refund()."""

import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Records every refund call, optionally raising GatewayError."""

    def __init__(self, refund_id="rf_1", error=None):
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


ADMIN = {"id": "adm_1", "role": "admin"}
SUPPORT = {"id": "sup_1", "role": "support"}
OWNER = {"id": "cus_1", "role": "customer"}
OTHER_CUSTOMER = {"id": "cus_2", "role": "customer"}
UNKNOWN_ROLE = {"id": "adm_1", "role": "intern"}


class HappyPathTests(unittest.TestCase):
    def test_partial_refund_updates_order_and_calls_gateway_once(self):
        order = make_order()
        gateway = FakeGateway(refund_id="rf_abc")

        result = refund(order, 400, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [("ch_1", 400)])
        self.assertEqual(order["refunded"], 400)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(
            result, {"refund_id": "rf_abc", "amount": 400, "status": "partially_refunded"}
        )

    def test_full_refund_marks_order_refunded(self):
        order = make_order(refunded=250, status="partially_refunded")
        gateway = FakeGateway(refund_id="rf_full")

        result = refund(order, 750, gateway, SUPPORT, "k1")

        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(result["refund_id"], "rf_full")
        self.assertEqual(len(gateway.calls), 1)

    def test_single_call_for_the_whole_paid_amount(self):
        order = make_order(paid=500)
        gateway = FakeGateway()

        result = refund(order, 500, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [("ch_1", 500)])
        self.assertEqual(order["refunded"], 500)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(result["amount"], 500)

    def test_owner_customer_may_refund(self):
        order = make_order()
        gateway = FakeGateway()

        refund(order, 100, gateway, OWNER, "k1")

        self.assertEqual(gateway.calls, [("ch_1", 100)])

    def test_admin_may_refund_order_they_do_not_own(self):
        order = make_order(owner_id="cus_9")
        gateway = FakeGateway()

        refund(order, 100, gateway, ADMIN, "k1")

        self.assertEqual(order["refunded"], 100)

    def test_support_may_refund_order_they_do_not_own(self):
        order = make_order(owner_id="cus_9")
        gateway = FakeGateway()

        refund(order, 100, gateway, SUPPORT, "k1")

        self.assertEqual(order["refunded"], 100)

    def test_successful_refund_is_stored_for_replay(self):
        order = make_order()
        gateway = FakeGateway(refund_id="rf_store")

        result = refund(order, 200, gateway, ADMIN, "k1")

        self.assertIn("k1", order["keys"])
        self.assertEqual(order["keys"]["k1"], result)


class IdempotencyTests(unittest.TestCase):
    def test_replay_returns_stored_result_without_gateway_call(self):
        stored = {"refund_id": "rf_old", "amount": 100, "status": "partially_refunded"}
        order = make_order(refunded=100, status="partially_refunded", keys={"k1": stored})
        gateway = FakeGateway()

        result = refund(order, 100, gateway, ADMIN, "k1")

        self.assertIs(result, stored)
        self.assertEqual(gateway.calls, [])

    def test_replay_does_not_change_order(self):
        stored = {"refund_id": "rf_old", "amount": 100, "status": "partially_refunded"}
        order = make_order(refunded=100, status="partially_refunded", keys={"k1": stored})
        before = copy.deepcopy(order)

        refund(order, 100, FakeGateway(), ADMIN, "k1")

        self.assertEqual(order, before)

    def test_replay_wins_over_invalid_amount(self):
        stored = {"refund_id": "rf_old", "amount": 100, "status": "partially_refunded"}
        order = make_order(refunded=100, status="partially_refunded", keys={"k1": stored})
        gateway = FakeGateway()

        self.assertIs(refund(order, -5, gateway, ADMIN, "k1"), stored)
        self.assertEqual(gateway.calls, [])

    def test_replay_wins_over_unauthorised_actor(self):
        stored = {"refund_id": "rf_old", "amount": 100, "status": "partially_refunded"}
        order = make_order(refunded=100, status="partially_refunded", keys={"k1": stored})

        self.assertIs(refund(order, 100, FakeGateway(), OTHER_CUSTOMER, "k1"), stored)

    def test_replay_wins_over_non_refundable_status(self):
        stored = {"refund_id": "rf_old", "amount": 100, "status": "refunded"}
        order = make_order(paid=100, refunded=100, status="refunded", keys={"k1": stored})

        self.assertIs(refund(order, 100, FakeGateway(), ADMIN, "k1"), stored)

    def test_replay_does_not_consume_other_keys(self):
        stored = {"refund_id": "rf_old", "amount": 100, "status": "partially_refunded"}
        order = make_order(refunded=100, status="partially_refunded", keys={"k1": stored})
        gateway = FakeGateway(refund_id="rf_new")

        result = refund(order, 100, gateway, ADMIN, "k2")

        self.assertEqual(result["refund_id"], "rf_new")
        self.assertEqual(order["refunded"], 200)
        self.assertEqual(order["keys"]["k1"], stored)

    def test_second_identical_call_after_success_is_a_replay(self):
        order = make_order()
        gateway = FakeGateway(refund_id="rf_first")

        first = refund(order, 300, gateway, ADMIN, "k1")
        second = refund(order, 300, gateway, ADMIN, "k1")

        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(first, second)
        self.assertEqual(order["refunded"], 300)


class AmountValidationTests(unittest.TestCase):
    def test_zero_rejected(self):
        order = make_order()
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 0, gateway, ADMIN, "k1")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 0)

    def test_negative_rejected(self):
        with self.assertRaises(ValueError):
            refund(make_order(), -1, FakeGateway(), ADMIN, "k1")

    def test_float_rejected(self):
        with self.assertRaises(ValueError):
            refund(make_order(), 10.0, FakeGateway(), ADMIN, "k1")

    def test_bool_rejected(self):
        for value in (True, False):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    refund(make_order(), value, FakeGateway(), ADMIN, "k1")

    def test_string_rejected(self):
        with self.assertRaises(ValueError):
            refund(make_order(), "100", FakeGateway(), ADMIN, "k1")

    def test_none_rejected(self):
        with self.assertRaises(ValueError):
            refund(make_order(), None, FakeGateway(), ADMIN, "k1")

    def test_no_key_stored_on_invalid_amount(self):
        order = make_order()
        with self.assertRaises(ValueError):
            refund(order, -1, FakeGateway(), ADMIN, "k1")
        self.assertEqual(order["keys"], {})


class PermissionTests(unittest.TestCase):
    def test_other_customer_rejected(self):
        order = make_order()
        gateway = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, OTHER_CUSTOMER, "k1")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["keys"], {})

    def test_unknown_role_rejected(self):
        with self.assertRaises(PermissionError):
            refund(make_order(), 100, FakeGateway(), UNKNOWN_ROLE, "k1")

    def test_owner_id_with_other_role_rejected(self):
        actor = {"id": "cus_1", "role": "intern"}
        order = make_order()
        gateway = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, actor, "k1")
        self.assertEqual(gateway.calls, [])

    def test_support_role_allowed_regardless_of_ownership(self):
        order = make_order(owner_id="someone_else")
        refund(order, 100, FakeGateway(), {"id": "cus_1", "role": "support"}, "k1")
        self.assertEqual(order["refunded"], 100)

    def test_id_match_but_role_customer_of_other_order_rejected(self):
        order = make_order(owner_id="cus_2")
        with self.assertRaises(PermissionError):
            refund(order, 100, FakeGateway(), OWNER, "k1")

    def test_missing_role_rejected(self):
        with self.assertRaises(PermissionError):
            refund(make_order(), 100, FakeGateway(), {"id": "cus_1"}, "k1")

    def test_amount_checked_before_permission(self):
        """Rule 2 precedes rule 3, so a bad amount wins over a bad actor."""
        with self.assertRaises(ValueError):
            refund(make_order(), 0, FakeGateway(), OTHER_CUSTOMER, "k1")

    def test_permission_checked_before_status(self):
        """Rule 3 precedes rule 4, so the permission error wins."""
        order = make_order(status="cancelled")
        with self.assertRaises(PermissionError):
            refund(order, 100, FakeGateway(), OTHER_CUSTOMER, "k1")


class StatusTests(unittest.TestCase):
    def test_cancelled_rejected(self):
        order = make_order(status="cancelled")
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 100, gateway, ADMIN, "k1")
        self.assertEqual(gateway.calls, [])

    def test_refunded_rejected(self):
        order = make_order(paid=1000, refunded=1000, status="refunded")
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 100, gateway, ADMIN, "k1")
        self.assertEqual(gateway.calls, [])

    def test_unknown_status_rejected(self):
        with self.assertRaises(ValueError):
            refund(make_order(status="pending"), 100, FakeGateway(), ADMIN, "k1")

    def test_status_checked_before_balance(self):
        """Rule 4 precedes rule 5: a cancelled order fails on status."""
        order = make_order(status="cancelled")
        with self.assertRaises(ValueError) as ctx:
            refund(order, 10_000, FakeGateway(), ADMIN, "k1")
        self.assertNotIn("balance", str(ctx.exception))


class BalanceTests(unittest.TestCase):
    def test_over_refund_rejected(self):
        order = make_order()
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 1001, gateway, ADMIN, "k1")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["status"], "paid")
        self.assertEqual(order["keys"], {})

    def test_over_remaining_after_previous_refund_rejected(self):
        order = make_order(paid=1000, refunded=900, status="partially_refunded")
        with self.assertRaises(ValueError):
            refund(order, 101, FakeGateway(), ADMIN, "k1")
        self.assertEqual(order["refunded"], 900)

    def test_exact_remaining_allowed(self):
        order = make_order(paid=1000, refunded=900, status="partially_refunded")
        gateway = FakeGateway()

        result = refund(order, 100, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [("ch_1", 100)])
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(result["status"], "refunded")


class GatewayFailureTests(unittest.TestCase):
    def test_gateway_error_propagates(self):
        order = make_order()
        gateway = FakeGateway(error=GatewayError("declined"))

        with self.assertRaises(GatewayError):
            refund(order, 100, gateway, ADMIN, "k1")

    def test_order_untouched_and_key_not_stored_on_gateway_error(self):
        order = make_order(refunded=200, status="partially_refunded")
        before = copy.deepcopy(order)
        gateway = FakeGateway(error=GatewayError("declined"))

        with self.assertRaises(GatewayError):
            refund(order, 100, gateway, ADMIN, "k1")

        self.assertEqual(order, before)
        self.assertNotIn("k1", order["keys"])
        self.assertEqual(len(gateway.calls), 1)

    def test_gateway_called_with_charge_id_and_amount(self):
        order = make_order(charge_id="ch_zzz")
        gateway = FakeGateway()

        refund(order, 123, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [("ch_zzz", 123)])

    def test_gateway_failure_then_retry_with_same_key_succeeds(self):
        order = make_order()
        failing = FakeGateway(error=GatewayError("declined"))
        with self.assertRaises(GatewayError):
            refund(order, 100, failing, ADMIN, "k1")

        gateway = FakeGateway(refund_id="rf_retry")
        result = refund(order, 100, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [("ch_1", 100)])
        self.assertEqual(result["refund_id"], "rf_retry")
        self.assertEqual(order["refunded"], 100)

    def test_gateway_error_class_is_exception_subclass(self):
        self.assertTrue(issubclass(GatewayError, Exception))

    def test_gateway_raising_other_error_propagates_without_mutation(self):
        order = make_order()
        before = copy.deepcopy(order)

        class Boom(Exception):
            pass

        class Exploding:
            def refund(self, charge_id, amount):
                raise Boom("kaboom")

        with self.assertRaises(Boom):
            refund(order, 100, Exploding(), ADMIN, "k1")

        self.assertEqual(order, before)


class ResultShapeTests(unittest.TestCase):
    def test_result_has_exactly_the_specified_fields(self):
        order = make_order()
        result = refund(order, 250, FakeGateway(refund_id="rf_x"), ADMIN, "k1")

        self.assertEqual(
            sorted(result), ["amount", "refund_id", "status"]
        )
        self.assertIsInstance(result["refund_id"], str)
        self.assertEqual(result["amount"], 250)

    def test_stored_key_is_the_returned_result(self):
        order = make_order()
        result = refund(order, 250, FakeGateway(), ADMIN, "k1")

        self.assertIs(order["keys"]["k1"], result)


if __name__ == "__main__":
    unittest.main()
