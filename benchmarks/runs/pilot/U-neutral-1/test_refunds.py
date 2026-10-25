import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Records calls; optionally fails or returns a scripted id."""

    def __init__(self, refund_id="re_1", fail=False):
        self.refund_id = refund_id
        self.fail = fail
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway refused")
        return self.refund_id


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
NO_ROLE = {"id": "u_owner", "role": "guest"}


class TestIdempotency(unittest.TestCase):
    def test_replay_returns_stored_result_without_gateway_call(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 400, gateway, OWNER, "k1")
        snapshot = copy.deepcopy(order)

        second = refund(order, 400, gateway, OWNER, "k1")

        self.assertEqual(second, first)
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order, snapshot)

    def test_replay_wins_over_invalid_amount(self):
        stored = {"refund_id": "re_old", "amount": 50, "status": "partially_refunded"}
        order = make_order(refunded=50, status="partially_refunded", keys={"k1": stored})
        gateway = FakeGateway()

        self.assertIs(refund(order, -5, gateway, STRANGER, "k1"), stored)
        self.assertEqual(gateway.calls, [])

    def test_replay_of_already_refunded_order_is_allowed(self):
        order = make_order()
        gateway = FakeGateway()
        refund(order, 1000, gateway, ADMIN, "k1")
        self.assertEqual(order["status"], "refunded")

        result = refund(order, 1000, gateway, ADMIN, "k1")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order["refunded"], 1000)

    def test_distinct_keys_are_independent(self):
        order = make_order()
        gateway = FakeGateway()
        refund(order, 100, gateway, ADMIN, "k1")
        refund(order, 100, gateway, ADMIN, "k2")

        self.assertEqual(len(gateway.calls), 2)
        self.assertEqual(set(order["keys"]), {"k1", "k2"})


class TestAmountValidation(unittest.TestCase):
    def test_rejects_non_positive_and_non_int(self):
        bad_amounts = [0, -1, -100, True, False, 1.0, 2.5, "100", None]
        for amount in bad_amounts:
            with self.subTest(amount=amount):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, amount, gateway, ADMIN, "k")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order, make_order())

    def test_amount_checked_before_permission(self):
        with self.assertRaises(ValueError):
            refund(make_order(), 0, FakeGateway(), STRANGER, "k")

    def test_amount_checked_before_status(self):
        order = make_order(status="cancelled")
        with self.assertRaises(ValueError) as ctx:
            refund(order, -3, FakeGateway(), ADMIN, "k")
        self.assertIn("positive", str(ctx.exception))


class TestPermissions(unittest.TestCase):
    def test_allowed_actors(self):
        for actor in (ADMIN, SUPPORT, OWNER):
            with self.subTest(actor=actor):
                order = make_order()
                gateway = FakeGateway()
                refund(order, 100, gateway, actor, "k")
                self.assertEqual(len(gateway.calls), 1)

    def test_denied_actors(self):
        for actor in (STRANGER, NO_ROLE, {"id": "u_owner", "role": "admin_ish"}):
            with self.subTest(actor=actor):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 100, gateway, actor, "k")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order, make_order())

    def test_unknown_role_denied_even_for_owner_id(self):
        actor = {"id": "u_owner", "role": "janitor"}
        with self.assertRaises(PermissionError):
            refund(make_order(), 100, FakeGateway(), actor, "k")


class TestStatusRules(unittest.TestCase):
    def test_rejects_non_refundable_statuses(self):
        for status in ("refunded", "cancelled", "pending", ""):
            with self.subTest(status=status):
                order = make_order(status=status)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 10, gateway, ADMIN, "k")
                self.assertEqual(gateway.calls, [])

    def test_partially_refunded_order_can_be_refunded_again(self):
        order = make_order(refunded=300, status="partially_refunded")
        gateway = FakeGateway()
        result = refund(order, 200, gateway, ADMIN, "k")

        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 500)

    def test_status_checked_after_permission(self):
        order = make_order(status="cancelled")
        with self.assertRaises(PermissionError):
            refund(order, 10, FakeGateway(), STRANGER, "k")


class TestLimits(unittest.TestCase):
    def test_rejects_amount_above_remaining(self):
        order = make_order(refunded=400, status="partially_refunded")
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 601, gateway, ADMIN, "k")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 400)
        self.assertEqual(order["keys"], {})

    def test_exact_remaining_is_allowed(self):
        order = make_order(refunded=400, status="partially_refunded")
        result = refund(order, 600, FakeGateway(), ADMIN, "k")

        self.assertEqual(result["amount"], 600)
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")

    def test_limit_checked_before_gateway_call(self):
        order = make_order()
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 1001, gateway, ADMIN, "k")
        self.assertEqual(gateway.calls, [])


class TestGatewayBehaviour(unittest.TestCase):
    def test_success_mutates_order_and_stores_result(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_42")
        result = refund(order, 250, gateway, SUPPORT, "key-1")

        self.assertEqual(gateway.calls, [("ch_1", 250)])
        self.assertEqual(result, {"refund_id": "re_42", "amount": 250, "status": "partially_refunded"})
        self.assertEqual(order["refunded"], 250)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["key-1"], result)

    def test_full_refund_marks_order_refunded(self):
        order = make_order()
        result = refund(order, 1000, FakeGateway(), OWNER, "k")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)

    def test_gateway_error_leaves_order_unchanged(self):
        order = make_order(refunded=200, status="partially_refunded")
        gateway = FakeGateway(fail=True)
        before = copy.deepcopy(order)

        with self.assertRaises(GatewayError):
            refund(order, 100, gateway, ADMIN, "k")

        self.assertEqual(order, before)
        self.assertEqual(gateway.calls, [("ch_1", 100)])

    def test_gateway_called_exactly_once(self):
        gateway = FakeGateway()
        refund(make_order(), 10, gateway, ADMIN, "k")
        self.assertEqual(len(gateway.calls), 1)

    def test_gateway_error_is_retryable_with_same_key(self):
        order = make_order()
        failing = FakeGateway(fail=True)
        with self.assertRaises(GatewayError):
            refund(order, 100, failing, ADMIN, "k")

        ok = FakeGateway(refund_id="re_ok")
        result = refund(order, 100, ok, ADMIN, "k")

        self.assertEqual(result["refund_id"], "re_ok")
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(len(ok.calls), 1)


if __name__ == "__main__":
    unittest.main()
