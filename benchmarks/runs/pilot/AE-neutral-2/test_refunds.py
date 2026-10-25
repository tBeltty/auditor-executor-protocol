"""Unit tests for the six guards of :func:`refunds.refund`.

Every test method is named ``test_guard_<guard>_...`` so that a failing run
names the guard it protects; the negative-control commands in
``negcontrol-log.md`` rely on that.
"""

import unittest

import fixtures
from fake_gateway import FakeGateway
from refunds import GatewayError, refund


class RefundTestBase(unittest.TestCase):
    """Common set-up: a fresh paid order plus a fresh fake gateway."""

    def setUp(self):
        self.order = fixtures.make_order()
        self.gateway = FakeGateway()

    def do_refund(self, amount=40, actor=None, key="key-1", gateway=None,
                  order=None):
        return refund(
            order if order is not None else self.order,
            amount,
            gateway if gateway is not None else self.gateway,
            actor if actor is not None else fixtures.make_actor(),
            key,
        )


class IdempotencyGuardTests(RefundTestBase):
    def test_guard_idempotency_replay_returns_stored_result(self):
        first = self.do_refund(amount=40)
        second = self.do_refund(amount=40)

        self.assertEqual(first, second, "a replayed key must return the stored result")
        self.assertEqual(
            self.gateway.call_count, 1,
            "a replayed idempotency key must not reach the gateway again",
        )
        self.assertEqual(self.order["refunded"], 40, "a replay must not refund twice")

    def test_guard_idempotency_replay_never_raises_on_invalid_amount(self):
        stored = self.do_refund(amount=40)

        # A replay is served before any validation, so amount 0 is irrelevant.
        replayed = self.do_refund(amount=0)

        self.assertEqual(replayed, stored)
        self.assertEqual(self.gateway.call_count, 1)

    def test_guard_idempotency_replay_skips_permission_and_status_checks(self):
        stored = self.do_refund(amount=100)
        self.assertEqual(self.order["status"], "refunded")

        stranger = fixtures.make_actor(actor_id="cus_stranger")
        replayed = self.do_refund(amount=999, actor=stranger)

        self.assertEqual(replayed, stored)
        self.assertEqual(self.gateway.call_count, 1)

    def test_guard_idempotency_replay_leaves_order_unchanged(self):
        self.do_refund(amount=40)
        before = fixtures.snapshot(self.order)

        self.do_refund(amount=40)

        self.assertEqual(self.order, before, "a replay must not change the order")

    def test_guard_idempotency_distinct_keys_refund_twice(self):
        self.do_refund(amount=30, key="key-1")
        self.do_refund(amount=30, key="key-2")

        self.assertEqual(self.gateway.call_count, 2)
        self.assertEqual(self.order["refunded"], 60)
        self.assertEqual(sorted(self.order["keys"]), ["key-1", "key-2"])


class AmountValidationGuardTests(RefundTestBase):
    def test_guard_amount_rejects_zero(self):
        with self.assertRaises(ValueError, msg="amount 0 must be rejected"):
            self.do_refund(amount=0)

    def test_guard_amount_rejects_negative(self):
        with self.assertRaises(ValueError, msg="a negative amount must be rejected"):
            self.do_refund(amount=-1)

    def test_guard_amount_rejects_float(self):
        for value in (10.0, 0.5, 10.5):
            with self.subTest(amount=value):
                with self.assertRaises(ValueError, msg="floats are not ints"):
                    self.do_refund(amount=value)

    def test_guard_amount_rejects_bool(self):
        for value in (True, False):
            with self.subTest(amount=value):
                with self.assertRaises(ValueError, msg="bools are not valid amounts"):
                    self.do_refund(amount=value)

    def test_guard_amount_rejects_non_numeric(self):
        for value in (None, "10", [10], {"amount": 10}):
            with self.subTest(amount=value):
                with self.assertRaises(ValueError, msg="only ints are valid amounts"):
                    self.do_refund(amount=value)

    def test_guard_amount_accepts_plain_positive_int(self):
        result = self.do_refund(amount=1)

        self.assertEqual(result["amount"], 1)
        self.assertEqual(self.order["refunded"], 1)

    def test_guard_amount_invalid_has_no_side_effects(self):
        before = fixtures.snapshot(self.order)

        with self.assertRaises(ValueError):
            self.do_refund(amount=0)

        self.assertEqual(self.gateway.calls, [], "the gateway must not be called")
        self.assertEqual(self.order, before)


class PermissionGuardTests(RefundTestBase):
    def test_guard_permission_allows_owning_customer(self):
        result = self.do_refund(actor=fixtures.make_actor("cus_owner", "customer"))
        self.assertEqual(result["status"], "partially_refunded")

    def test_guard_permission_allows_admin(self):
        result = self.do_refund(actor=fixtures.make_actor("adm_1", "admin"))
        self.assertEqual(result["status"], "partially_refunded")

    def test_guard_permission_allows_support(self):
        result = self.do_refund(actor=fixtures.make_actor("sup_1", "support"))
        self.assertEqual(result["status"], "partially_refunded")

    def test_guard_permission_denies_another_customer(self):
        stranger = fixtures.make_actor(actor_id="cus_stranger", role="customer")
        with self.assertRaises(PermissionError, msg="a non-owning customer must be denied"):
            self.do_refund(actor=stranger)

    def test_guard_permission_denies_unknown_role(self):
        for role in ("manager", "ops", "refund", ""):
            with self.subTest(role=role):
                with self.assertRaises(PermissionError, msg="only admin/support/owner"):
                    self.do_refund(actor=fixtures.make_actor("x_1", role))

    def test_guard_permission_denies_missing_role(self):
        with self.assertRaises(PermissionError):
            self.do_refund(actor={"id": "cus_owner"})

    def test_guard_permission_denial_has_no_side_effects(self):
        before = fixtures.snapshot(self.order)
        stranger = fixtures.make_actor(actor_id="cus_stranger", role="customer")

        with self.assertRaises(PermissionError):
            self.do_refund(actor=stranger)

        self.assertEqual(self.gateway.calls, [], "the gateway must not be called")
        self.assertEqual(self.order, before)


class StatusGuardTests(RefundTestBase):
    def test_guard_status_rejects_cancelled_order(self):
        order = fixtures.make_order(status="cancelled")

        with self.assertRaises(ValueError, msg="a cancelled order is not refundable") as ctx:
            self.do_refund(amount=50, order=order)

        self.assertIn("status", str(ctx.exception))

    def test_guard_status_rejects_fully_refunded_order(self):
        order = fixtures.make_order(paid=100, refunded=100, status="refunded")

        # The cap would reject this too, so the message pins the status guard.
        with self.assertRaises(ValueError, msg="a refunded order is not refundable") as ctx:
            self.do_refund(amount=10, order=order)

        self.assertIn("status", str(ctx.exception))

    def test_guard_status_accepts_paid_order(self):
        result = self.do_refund(amount=100)
        self.assertEqual(result["status"], "refunded")

    def test_guard_status_accepts_partially_refunded_order(self):
        order = fixtures.make_order(refunded=30, status="partially_refunded")
        result = self.do_refund(amount=20, order=order)

        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 50)

    def test_guard_status_denied_has_no_side_effects(self):
        order = fixtures.make_order(status="cancelled")
        before = fixtures.snapshot(order)

        with self.assertRaises(ValueError):
            self.do_refund(amount=50, order=order)

        self.assertEqual(self.gateway.calls, [], "the gateway must not be called")
        self.assertEqual(order, before)


class RefundableCapGuardTests(RefundTestBase):
    def test_guard_cap_accepts_exactly_the_remaining_amount(self):
        order = fixtures.make_order(paid=100, refunded=60, status="partially_refunded")
        result = self.do_refund(amount=40, order=order)

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 100)

    def test_guard_cap_rejects_one_over_the_remaining_amount(self):
        order = fixtures.make_order(paid=100, refunded=60, status="partially_refunded")

        with self.assertRaises(ValueError, msg="41 is more than the 40 still owed") as ctx:
            self.do_refund(amount=41, order=order)

        self.assertIn("exceeds", str(ctx.exception))

    def test_guard_cap_rejects_full_paid_amount_when_partly_refunded(self):
        order = fixtures.make_order(paid=100, refunded=40, status="partially_refunded")

        with self.assertRaises(ValueError, msg="the cap is paid minus refunded"):
            self.do_refund(amount=100, order=order)

    def test_guard_cap_rejects_any_amount_on_a_fully_refunded_order(self):
        order = fixtures.make_order(paid=100, refunded=100, status="partially_refunded")

        with self.assertRaises(ValueError):
            self.do_refund(amount=1, order=order)

    def test_guard_cap_rejection_has_no_side_effects(self):
        order = fixtures.make_order(paid=100, refunded=60, status="partially_refunded")
        before = fixtures.snapshot(order)

        with self.assertRaises(ValueError):
            self.do_refund(amount=41, order=order)

        self.assertEqual(self.gateway.calls, [], "the gateway must not be called")
        self.assertEqual(order, before)


class GatewayAtomicityGuardTests(RefundTestBase):
    def test_guard_atomicity_gateway_error_leaves_the_order_unchanged(self):
        order = fixtures.make_order(refunded=30, status="partially_refunded")
        before = fixtures.snapshot(order)
        self.gateway.fail_next_call()

        with self.assertRaises(GatewayError, msg="gateway failure must propagate"):
            self.do_refund(amount=20, order=order)

        self.assertEqual(order, before, "the order must be untouched after a gateway failure")

    def test_guard_atomicity_gateway_error_on_a_paid_order_leaves_it_paid(self):
        before = fixtures.snapshot(self.order)
        self.gateway.fail_next_call()

        with self.assertRaises(GatewayError):
            self.do_refund(amount=100)

        self.assertEqual(self.order, before)
        self.assertEqual(self.order["status"], "paid")
        self.assertEqual(self.order["refunded"], 0)

    def test_guard_atomicity_gateway_error_stores_no_idempotency_key(self):
        self.gateway.fail_next_call()

        with self.assertRaises(GatewayError):
            self.do_refund(amount=40)

        self.assertEqual(self.order["keys"], {},
                         "a failed refund must not be recorded as done")

    def test_guard_atomicity_failed_refund_can_be_retried_with_the_same_key(self):
        self.gateway.fail_next_call()
        with self.assertRaises(GatewayError):
            self.do_refund(amount=40)

        # Call 2 succeeds: the retry must reach the gateway and book the refund.
        result = self.do_refund(amount=40)

        self.assertEqual(self.gateway.call_count, 2)
        self.assertEqual(self.order["refunded"], 40)
        self.assertEqual(self.order["keys"]["key-1"], result)

    def test_guard_atomicity_gateway_is_called_exactly_once_on_success(self):
        self.do_refund(amount=40)

        self.assertEqual(self.gateway.call_count, 1)
        self.assertEqual(self.gateway.last_call, ("ch_1", 40))

    def test_guard_atomicity_forwards_the_order_charge_id(self):
        order = fixtures.make_order(charge_id="ch_other")
        self.do_refund(amount=10, order=order)

        self.assertEqual(self.gateway.last_call, ("ch_other", 10))


if __name__ == "__main__":
    unittest.main()
