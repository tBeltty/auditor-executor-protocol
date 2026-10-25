"""Rule-precedence and success-path tests for :func:`refunds.refund`.

The specification fixes the order in which the rules are checked; these tests
pin that order down so that moving a check cannot go unnoticed.
"""

import unittest

import fixtures
from fake_gateway import FakeGateway
from refunds import GatewayError, refund


class RefundTestBase(unittest.TestCase):
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


class RulePrecedenceTests(RefundTestBase):
    def test_guard_amount_precedes_permission(self):
        stranger = fixtures.make_actor(actor_id="cus_stranger")
        with self.assertRaises(ValueError, msg="the amount is validated before authorization"):
            self.do_refund(amount=0, actor=stranger)

    def test_guard_amount_precedes_status(self):
        order = fixtures.make_order(status="cancelled")

        with self.assertRaises(ValueError) as ctx:
            self.do_refund(amount=0, order=order)

        self.assertIn("amount", str(ctx.exception))

    def test_guard_permission_precedes_status(self):
        order = fixtures.make_order(status="cancelled")
        stranger = fixtures.make_actor(actor_id="cus_stranger")

        with self.assertRaises(PermissionError, msg="authorization precedes the status check"):
            self.do_refund(amount=10, actor=stranger, order=order)

    def test_guard_permission_precedes_cap(self):
        order = fixtures.make_order(paid=100, refunded=90, status="partially_refunded")
        stranger = fixtures.make_actor(actor_id="cus_stranger")

        with self.assertRaises(PermissionError):
            self.do_refund(amount=500, actor=stranger, order=order)

    def test_guard_status_precedes_cap(self):
        order = fixtures.make_order(paid=100, refunded=0, status="cancelled")

        with self.assertRaises(ValueError) as ctx:
            self.do_refund(amount=1000, order=order)

        message = str(ctx.exception)
        self.assertIn("status", message, "the status check must run before the cap")
        self.assertNotIn("exceeds", message)

    def test_guard_idempotency_precedes_everything(self):
        stored = self.do_refund(amount=100)
        stranger = fixtures.make_actor(actor_id="cus_stranger")
        cancelled = fixtures.make_order(status="cancelled", keys={"key-1": stored})

        replayed = self.do_refund(amount=0, actor=stranger, order=cancelled)

        self.assertEqual(replayed, stored)
        self.assertEqual(cancelled["refunded"], 0)


class SuccessPathTests(RefundTestBase):
    def test_partial_refund_returns_the_documented_result(self):
        result = self.do_refund(amount=40)

        self.assertEqual(set(result), {"refund_id", "amount", "status"})
        self.assertEqual(result["amount"], 40)
        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(result["refund_id"], "re_0001")
        self.assertEqual(
            self.order,
            {
                "id": "ord_1",
                "owner_id": "cus_owner",
                "charge_id": "ch_1",
                "paid": 100,
                "refunded": 40,
                "status": "partially_refunded",
                "keys": {"key-1": result},
            },
        )

    def test_full_refund_marks_the_order_refunded(self):
        result = self.do_refund(amount=100)

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(self.order["status"], "refunded")
        self.assertEqual(self.order["refunded"], 100)

    def test_two_partial_refunds_add_up_to_refunded(self):
        first = self.do_refund(amount=30, key="key-1")
        second = self.do_refund(amount=70, key="key-2")

        self.assertEqual(first["status"], "partially_refunded")
        self.assertEqual(second["status"], "refunded")
        self.assertEqual(self.order["refunded"], 100)
        self.assertEqual(self.gateway.call_count, 2)

    def test_result_is_stored_under_the_supplied_key(self):
        result = self.do_refund(amount=25, key="idem-xyz")

        self.assertEqual(list(self.order["keys"]), ["idem-xyz"])
        self.assertEqual(self.order["keys"]["idem-xyz"], result)

    def test_paid_amount_is_never_modified(self):
        self.do_refund(amount=40)
        self.assertEqual(self.order["paid"], 100)

    def test_refund_ids_come_from_the_gateway(self):
        first = self.do_refund(amount=10, key="key-1")
        second = self.do_refund(amount=10, key="key-2")

        self.assertEqual(first["refund_id"], "re_0001")
        self.assertEqual(second["refund_id"], "re_0002")


class GatewayContractTests(RefundTestBase):
    def test_gateway_receives_charge_id_and_amount(self):
        order = fixtures.make_order(charge_id="ch_42")
        self.do_refund(amount=15, order=order)

        self.assertEqual(self.gateway.calls, [("ch_42", 15)])

    def test_gateway_is_never_called_when_a_rule_rejects_the_refund(self):
        stranger = fixtures.make_actor(actor_id="cus_stranger")
        cases = [
            ("amount", dict(amount=0)),
            ("permission", dict(amount=10, actor=stranger)),
            ("status", dict(amount=10, order=fixtures.make_order(status="cancelled"))),
            ("cap", dict(amount=101)),
        ]
        for label, kwargs in cases:
            with self.subTest(rule=label):
                # A fresh order and key per case, so one rejected attempt can
                # never be answered by the idempotency store of another.
                order = kwargs.pop("order", fixtures.make_order())
                gateway = FakeGateway()
                with self.assertRaises((ValueError, PermissionError)):
                    self.do_refund(order=order, gateway=gateway, key="key-" + label,
                                   **kwargs)
                self.assertEqual(gateway.calls, [], "the gateway must not be called")

    def test_gateway_error_is_reraised_unchanged(self):
        self.gateway.fail_every_call()

        with self.assertRaises(GatewayError) as ctx:
            self.do_refund(amount=10)

        self.assertEqual(str(ctx.exception), self.gateway.error_message)
        self.assertEqual(self.gateway.call_count, 1)


if __name__ == "__main__":
    unittest.main()
