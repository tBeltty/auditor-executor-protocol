"""Unit tests for refunds.refund, with a hand-written fake gateway."""

import copy
import unittest

from refunds import GatewayError, refund

OWNER = "cust_1"
CHARGE = "ch_1"


def make_order(**overrides):
    order = {
        "id": "ord_1",
        "owner_id": OWNER,
        "charge_id": CHARGE,
        "paid": 10000,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


class FakeGateway:
    """Records calls; optionally raises GatewayError instead of refunding."""

    def __init__(self, refund_id="re_1", error=None):
        self.refund_id = refund_id
        self.error = error
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.error is not None:
            raise self.error
        return self.refund_id


ADMIN = {"id": "admin_1", "role": "admin"}
SUPPORT = {"id": "sup_1", "role": "support"}
OWNER_ACTOR = {"id": OWNER, "role": "customer"}


class HappyPathTests(unittest.TestCase):
    def test_admin_full_refund_marks_refunded(self):
        order = make_order()
        gateway = FakeGateway("re_full")
        result = refund(order, 10000, gateway, ADMIN, "key-1")
        self.assertEqual(
            result, {"refund_id": "re_full", "amount": 10000, "status": "refunded"}
        )
        self.assertEqual(order["refunded"], 10000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["keys"]["key-1"], result)
        self.assertIs(order["keys"]["key-1"], result)
        self.assertEqual(gateway.calls, [(CHARGE, 10000)])

    def test_support_partial_then_full_refund(self):
        order = make_order()
        gateway = FakeGateway("re_a")
        first = refund(order, 2500, gateway, SUPPORT, "key-a")
        self.assertEqual(first["status"], "partially_refunded")
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 2500)

        gateway.refund_id = "re_b"
        second = refund(order, 7500, gateway, SUPPORT, "key-b")
        self.assertEqual(second["status"], "refunded")
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["refunded"], 10000)
        self.assertEqual(gateway.calls, [(CHARGE, 2500), (CHARGE, 7500)])

    def test_owner_customer_may_refund_exact_remaining(self):
        order = make_order(refunded=1000, status="partially_refunded")
        gateway = FakeGateway()
        result = refund(order, 9000, gateway, OWNER_ACTOR, "owner-key")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(gateway.calls, [(CHARGE, 9000)])

    def test_gateway_receives_order_charge_id(self):
        order = make_order(charge_id="ch_other")
        gateway = FakeGateway()
        refund(order, 100, gateway, ADMIN, "k")
        self.assertEqual(gateway.calls, [("ch_other", 100)])


class GuardIdempotencyTests(unittest.TestCase):
    def test_idempotency_replay_does_not_call_gateway_or_mutate(self):
        order = make_order()
        gateway = FakeGateway("re_1")
        first = refund(order, 4000, gateway, ADMIN, "idem")
        snapshot = copy.deepcopy(order)

        replay = refund(order, 999, gateway, ADMIN, "idem")

        self.assertEqual(replay, first)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order, snapshot)

    def test_idempotency_takes_precedence_over_validation(self):
        order = make_order()
        gateway = FakeGateway("re_1")
        first = refund(order, 4000, gateway, ADMIN, "idem")
        snapshot = copy.deepcopy(order)

        # Invalid amount and an unauthorised actor must not matter on replay.
        replay = refund(order, -1, gateway, {"id": "x", "role": "guest"}, "idem")

        self.assertEqual(replay, first)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order, snapshot)


class GuardAmountTests(unittest.TestCase):
    def test_rejects_non_positive_bool_float_and_non_numeric_amounts(self):
        for bad in (0, -100, True, False, 1.5, 100.0, "100", None):
            with self.subTest(amount=bad):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, ADMIN, "k")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["status"], "paid")
                self.assertEqual(order["keys"], {})


class GuardPermissionTests(unittest.TestCase):
    def test_unauthorised_actors_are_rejected(self):
        for actor in (
            {"id": "cust_2", "role": "customer"},
            {"id": OWNER, "role": "guest"},
            {"id": OWNER, "role": "viewer"},
            {"id": "admin_2", "role": ""},
        ):
            with self.subTest(actor=actor):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 100, gateway, actor, "k")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["keys"], {})


class GuardStatusTests(unittest.TestCase):
    def test_non_refundable_statuses_are_rejected(self):
        for status in ("cancelled", "refunded"):
            with self.subTest(status=status):
                order = make_order(status=status)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 100, gateway, ADMIN, "k")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["status"], status)
                self.assertEqual(order["refunded"], 0)

    def test_unknown_status_is_rejected(self):
        order = make_order(status="pending")
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 100, gateway, ADMIN, "k")
        self.assertEqual(gateway.calls, [])


class GuardCapTests(unittest.TestCase):
    def test_amount_above_remaining_is_rejected(self):
        order = make_order(refunded=7000, status="partially_refunded")
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 3001, gateway, ADMIN, "k")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 7000)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"], {})


class GuardGatewayAtomicityTests(unittest.TestCase):
    def test_gateway_error_leaves_order_untouched_and_reraises(self):
        for refunded, status in ((0, "paid"), (4000, "partially_refunded")):
            with self.subTest(refunded=refunded, status=status):
                order = make_order(refunded=refunded, status=status)
                snapshot = copy.deepcopy(order)
                gateway = FakeGateway(error=GatewayError("declined"))
                with self.assertRaises(GatewayError):
                    refund(order, 1000, gateway, ADMIN, "boom-key")
                self.assertEqual(order, snapshot)
                self.assertEqual(order["refunded"], refunded)
                self.assertEqual(order["status"], status)
                self.assertEqual(order["keys"], {})
                self.assertEqual(gateway.calls, [(CHARGE, 1000)])


if __name__ == "__main__":
    unittest.main()
