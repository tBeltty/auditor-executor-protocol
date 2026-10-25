"""Unit tests for refunds.refund, one group per spec rule."""

import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """In-memory stand-in for the payment gateway."""

    def __init__(self, refund_id="re_123", fail_times=0):
        self.refund_id = refund_id
        self.fail_times = fail_times
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if len(self.calls) <= self.fail_times:
            raise GatewayError("gateway unavailable")
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


OWNER = {"id": "cus_1", "role": "customer"}
ADMIN = {"id": "adm_1", "role": "admin"}
SUPPORT = {"id": "sup_1", "role": "support"}
OTHER_CUSTOMER = {"id": "cus_2", "role": "customer"}
AUDITOR = {"id": "aud_1", "role": "auditor"}


class TestIdempotency(unittest.TestCase):
    """Rule 1: a seen key replays the stored result and changes nothing."""

    def test_replay_returns_stored_result_without_second_charge(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_first")
        first = refund(order, 400, gateway, OWNER, "key-1")
        snapshot = copy.deepcopy(order)

        second = refund(order, 400, gateway, OWNER, "key-1")

        self.assertEqual(second, first)
        self.assertEqual(second["refund_id"], "re_first")
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order, snapshot)
        self.assertEqual(len(order["keys"]), 1)

    def test_replay_ignores_a_different_amount_and_does_not_recharge(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 400, gateway, OWNER, "key-1")
        snapshot = copy.deepcopy(order)

        second = refund(order, 999, gateway, OWNER, "key-1")

        self.assertEqual(second, first)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order["refunded"], 400)
        self.assertEqual(order, snapshot)

    def test_replay_wins_over_every_other_rule(self):
        """Rule 1 precedes rules 2-5: bad amount, wrong actor, dead status."""
        stored = {"refund_id": "re_old", "amount": 250, "status": "partially_refunded"}
        order = make_order(
            refunded=250,
            status="cancelled",
            keys={"key-old": stored},
        )
        snapshot = copy.deepcopy(order)
        gateway = FakeGateway()

        result = refund(order, 0, gateway, AUDITOR, "key-old")

        self.assertEqual(result, stored)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_replay_uses_membership_not_truthiness(self):
        """Rule 1 keys on membership: a stored falsy result must still replay.

        A lookup like ``if order["keys"].get(key):`` would treat an empty stored
        result as "no key" and charge the gateway a second time.
        """
        stored = {}
        order = make_order(keys={"key-empty": stored})
        snapshot = copy.deepcopy(order)
        gateway = FakeGateway()

        result = refund(order, 100, gateway, OWNER, "key-empty")

        self.assertIs(result, stored)
        self.assertEqual(result, {})
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, snapshot)
        self.assertEqual(order["refunded"], 0)

    def test_distinct_keys_each_charge_once(self):
        order = make_order()
        gateway = FakeGateway()
        refund(order, 300, gateway, OWNER, "key-1")
        refund(order, 200, gateway, OWNER, "key-2")
        self.assertEqual(len(gateway.calls), 2)
        self.assertEqual(order["refunded"], 500)
        self.assertEqual(sorted(order["keys"]), ["key-1", "key-2"])


class TestAmountValidation(unittest.TestCase):
    """Rule 2: only a positive int is accepted."""

    def test_rejects_non_positive_ints(self):
        for bad in (0, -1, -1000):
            with self.subTest(amount=bad):
                order = make_order()
                snapshot = copy.deepcopy(order)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, OWNER, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order, snapshot)

    def test_rejects_floats_even_when_whole(self):
        for bad in (1.0, 2.5, 0.0):
            with self.subTest(amount=bad):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, OWNER, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)

    def test_rejects_bools(self):
        for bad in (True, False):
            with self.subTest(amount=bad):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, OWNER, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)

    def test_rejects_non_numeric_amounts(self):
        for bad in ("100", None, [100], {"amount": 100}):
            with self.subTest(amount=bad):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, OWNER, "key-1")
                self.assertEqual(gateway.calls, [])

    def test_accepts_one(self):
        order = make_order()
        gateway = FakeGateway()
        result = refund(order, 1, gateway, OWNER, "key-1")
        self.assertEqual(result["amount"], 1)
        self.assertEqual(order["refunded"], 1)

    def test_amount_is_checked_before_permission_and_status(self):
        order = make_order(status="cancelled")
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 0, gateway, AUDITOR, "key-1")
        self.assertEqual(gateway.calls, [])


class TestPermission(unittest.TestCase):
    """Rule 3: admin, support, or the owning customer."""

    def _assert_allowed(self, actor):
        order = make_order()
        gateway = FakeGateway()
        result = refund(order, 100, gateway, actor, "key-1")
        self.assertEqual(result["amount"], 100)
        self.assertEqual(len(gateway.calls), 1)

    def _assert_denied(self, actor):
        order = make_order()
        snapshot = copy.deepcopy(order)
        gateway = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, actor, "key-1")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_owner_customer_is_allowed(self):
        self._assert_allowed(OWNER)

    def test_admin_is_allowed(self):
        self._assert_allowed(ADMIN)

    def test_support_is_allowed(self):
        self._assert_allowed(SUPPORT)

    def test_admin_and_support_need_not_own_the_order(self):
        self._assert_allowed({"id": "adm_other", "role": "admin"})
        self._assert_allowed({"id": "sup_other", "role": "support"})

    def test_other_customer_is_denied(self):
        self._assert_denied(OTHER_CUSTOMER)

    def test_unknown_role_is_denied(self):
        self._assert_denied(AUDITOR)
        self._assert_denied({"id": "x", "role": "guest"})

    def test_customer_without_matching_id_is_denied(self):
        self._assert_denied({"id": "", "role": "customer"})
        self._assert_denied({"role": "customer"})

    def test_owner_with_non_customer_role_is_denied(self):
        """Rule 3 grants the *customer* who owns the order, not any matching id."""
        self._assert_denied({"id": "cus_1", "role": "auditor"})
        self._assert_denied({"id": "cus_1", "role": "guest"})
        self._assert_denied({"id": "cus_1", "role": "support_readonly"})

    def test_actor_without_a_role_is_denied(self):
        """A missing role must fail closed, never default to a privileged one."""
        self._assert_denied({})
        self._assert_denied({"id": "cus_1"})
        self._assert_denied({"id": "adm_1"})

    def test_permission_is_checked_before_status(self):
        order = make_order(status="cancelled")
        gateway = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, OTHER_CUSTOMER, "key-1")
        self.assertEqual(gateway.calls, [])


class TestStatus(unittest.TestCase):
    """Rule 4: only paid / partially_refunded orders are refundable."""

    def test_cancelled_order_is_rejected(self):
        order = make_order(status="cancelled")
        snapshot = copy.deepcopy(order)
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 100, gateway, OWNER, "key-1")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_refunded_order_is_rejected_even_with_room_on_the_clock(self):
        order = make_order(status="refunded", refunded=0)
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 100, gateway, OWNER, "key-1")
        self.assertEqual(gateway.calls, [])

    def test_unknown_status_is_rejected(self):
        for status in ("pending", "authorized", "", "PAID"):
            with self.subTest(status=status):
                order = make_order(status=status)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 100, gateway, OWNER, "key-1")
                self.assertEqual(gateway.calls, [])

    def test_paid_order_is_accepted(self):
        order = make_order(status="paid")
        gateway = FakeGateway()
        refund(order, 100, gateway, OWNER, "key-1")
        self.assertEqual(len(gateway.calls), 1)

    def test_partially_refunded_order_is_accepted(self):
        order = make_order(status="partially_refunded", refunded=300)
        gateway = FakeGateway()
        result = refund(order, 100, gateway, OWNER, "key-1")
        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 400)


class TestRefundableCap(unittest.TestCase):
    """Rule 5: amount may not exceed paid - refunded."""

    def test_amount_above_remaining_is_rejected(self):
        order = make_order(status="partially_refunded", refunded=600)
        snapshot = copy.deepcopy(order)
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 401, gateway, OWNER, "key-1")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order, snapshot)

    def test_amount_equal_to_paid_is_rejected_once_partly_refunded(self):
        order = make_order(status="partially_refunded", refunded=1)
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 1000, gateway, OWNER, "key-1")
        self.assertEqual(gateway.calls, [])

    def test_over_refunded_order_rejects_any_amount(self):
        """A negative remainder must still reject every amount, not skip the cap."""
        order = make_order(paid=100, refunded=150, status="partially_refunded")
        snapshot = copy.deepcopy(order)
        for amount in (1, 2, 100):
            with self.subTest(amount=amount):
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, amount, gateway, OWNER, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order, snapshot)

    def test_exact_remaining_is_allowed(self):
        order = make_order(status="partially_refunded", refunded=600)
        gateway = FakeGateway()
        result = refund(order, 400, gateway, OWNER, "key-1")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(gateway.calls, [("ch_1", 400)])

    def test_full_refund_of_untouched_order_is_allowed(self):
        order = make_order()
        gateway = FakeGateway()
        result = refund(order, 1000, gateway, OWNER, "key-1")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["status"], "refunded")


class TestGatewayFailureAtomicity(unittest.TestCase):
    """Rule 6: one gateway call, and a GatewayError leaves the order untouched."""

    def test_failed_refund_leaves_order_completely_unchanged(self):
        order = make_order(status="partially_refunded", refunded=250)
        order["keys"]["old"] = {"refund_id": "re_old", "amount": 250,
                                "status": "partially_refunded"}
        snapshot = copy.deepcopy(order)
        gateway = FakeGateway(fail_times=1)

        with self.assertRaises(GatewayError):
            refund(order, 500, gateway, OWNER, "key-new")

        self.assertEqual(order, snapshot)
        self.assertNotIn("key-new", order["keys"])
        self.assertEqual(order["refunded"], 250)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(len(gateway.calls), 1)

    def test_failed_refund_does_not_poison_a_retry(self):
        order = make_order()
        snapshot = copy.deepcopy(order)
        failing = FakeGateway(fail_times=1)

        with self.assertRaises(GatewayError):
            refund(order, 1000, failing, OWNER, "key-1")
        self.assertEqual(order, snapshot)
        self.assertEqual(order["status"], "paid")

        retry = FakeGateway(refund_id="re_retry")
        result = refund(order, 1000, retry, OWNER, "key-1")
        self.assertEqual(result["refund_id"], "re_retry")
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["keys"]["key-1"], result)

    def test_gateway_is_called_exactly_once_per_refund(self):
        order = make_order()
        gateway = FakeGateway()
        refund(order, 250, gateway, OWNER, "key-1")
        self.assertEqual(gateway.calls, [("ch_1", 250)])

    def test_gateway_receives_the_order_charge_id(self):
        """Rule 6: the gateway is charged the order's own charge id, not a fixed one."""
        order = make_order(charge_id="ch_other", paid=500)
        gateway = FakeGateway(refund_id="re_other")
        result = refund(order, 200, gateway, OWNER, "key-1")

        self.assertEqual(gateway.calls, [("ch_other", 200)])
        self.assertEqual(result["refund_id"], "re_other")
        self.assertEqual(order["charge_id"], "ch_other")

    def test_gateway_is_never_called_when_a_rule_rejects(self):
        cases = [
            (make_order(status="cancelled"), 100, OWNER),
            (make_order(), 0, OWNER),
            (make_order(), 100, AUDITOR),
            (make_order(status="partially_refunded", refunded=900), 500, OWNER),
        ]
        for order, amount, actor in cases:
            with self.subTest(order=order, amount=amount, actor=actor):
                gateway = FakeGateway()
                with self.assertRaises((ValueError, PermissionError)):
                    refund(order, amount, gateway, actor, "key-1")
                self.assertEqual(gateway.calls, [])


class TestSuccessBookkeeping(unittest.TestCase):
    """Rule 7: state and result after a successful refund."""

    def test_partial_refund_result_and_state(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_777")
        result = refund(order, 400, gateway, OWNER, "key-1")

        self.assertEqual(
            result,
            {"refund_id": "re_777", "amount": 400, "status": "partially_refunded"},
        )
        self.assertEqual(order["refunded"], 400)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["key-1"], result)

    def test_result_has_exactly_the_specified_fields(self):
        order = make_order()
        result = refund(order, 100, FakeGateway(), OWNER, "key-1")
        self.assertEqual(sorted(result), ["amount", "refund_id", "status"])

    def test_two_partial_refunds_then_fully_refunded(self):
        order = make_order()
        gateway = FakeGateway()
        refund(order, 300, gateway, OWNER, "key-1")
        result = refund(order, 700, gateway, OWNER, "key-2")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["refunded"], order["paid"])

    def test_full_refund_sets_status_refunded(self):
        """Rule 7: the terminal transition is exactly `refunded`, and it is stored."""
        order = make_order()
        gateway = FakeGateway(refund_id="re_full")
        result = refund(order, 1000, gateway, OWNER, "key-full")

        self.assertEqual(
            result,
            {"refund_id": "re_full", "amount": 1000, "status": "refunded"},
        )
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["refunded"], order["paid"])
        self.assertEqual(order["keys"]["key-full"], result)
        self.assertEqual(gateway.calls, [("ch_1", 1000)])

    def test_untouched_order_fields_are_preserved(self):
        order = make_order()
        refund(order, 100, FakeGateway(), OWNER, "key-1")
        self.assertEqual(order["id"], "ord_1")
        self.assertEqual(order["owner_id"], "cus_1")
        self.assertEqual(order["charge_id"], "ch_1")
        self.assertEqual(order["paid"], 1000)


if __name__ == "__main__":
    unittest.main()
