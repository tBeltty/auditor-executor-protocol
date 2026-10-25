"""Unit tests for refunds.refund, using a local fake gateway (no network)."""

import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Records every refund call; optionally raises GatewayError."""

    def __init__(self, fail=False, refund_id="re_1"):
        self.fail = fail
        self.refund_id = refund_id
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway declined")
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


ADMIN = {"id": "admin_1", "role": "admin"}
SUPPORT = {"id": "sup_1", "role": "support"}
OWNER = {"id": "cust_1", "role": "customer"}
OTHER = {"id": "cust_2", "role": "customer"}


class HappyPathTests(unittest.TestCase):
    def test_partial_refund_updates_order_and_returns_result(self):
        order = make_order()
        gw = FakeGateway(refund_id="re_42")
        result = refund(order, 300, gw, OWNER, "key-1")

        self.assertEqual(
            result, {"refund_id": "re_42", "amount": 300, "status": "partially_refunded"}
        )
        self.assertEqual(order["refunded"], 300)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["key-1"], result)
        self.assertEqual(gw.calls, [("ch_1", 300)])  # exactly once, right args

    def test_full_refund_marks_order_refunded(self):
        order = make_order(refunded=400, status="partially_refunded")
        gw = FakeGateway()
        result = refund(order, 600, gw, ADMIN, "key-2")

        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(len(gw.calls), 1)

    def test_support_and_admin_and_owner_may_refund(self):
        for actor in (ADMIN, SUPPORT, OWNER):
            with self.subTest(role=actor["role"]):
                order = make_order()
                refund(order, 100, FakeGateway(), actor, "k-%s" % actor["role"])
                self.assertEqual(order["refunded"], 100)


class IdempotencyTests(unittest.TestCase):
    def test_replay_returns_stored_result_without_gateway_call(self):
        order = make_order()
        gw = FakeGateway()
        first = refund(order, 250, gw, OWNER, "same-key")
        snapshot = copy.deepcopy(order)

        second = refund(order, 250, gw, OWNER, "same-key")

        self.assertEqual(second, first)
        self.assertEqual(len(gw.calls), 1)  # no second gateway call
        self.assertEqual(order, snapshot)  # order not changed again

    def test_replay_ignores_new_amount_and_actor(self):
        order = make_order()
        gw = FakeGateway()
        first = refund(order, 250, gw, OWNER, "same-key")
        snapshot = copy.deepcopy(order)

        # Different amount, and an actor with no permission: replay wins.
        second = refund(order, 999, gw, OTHER, "same-key")

        self.assertEqual(second, first)
        self.assertEqual(len(gw.calls), 1)
        self.assertEqual(order, snapshot)

    def test_replay_beats_amount_validation(self):
        order = make_order()
        gw = FakeGateway()
        first = refund(order, 100, gw, OWNER, "k")
        self.assertEqual(refund(order, -5, gw, OWNER, "k"), first)
        self.assertEqual(len(gw.calls), 1)

    def test_replay_precedes_status_guard(self):
        # Rule 1 is checked before rule 4: a stored key replays its result even
        # when the order is no longer refundable, and the order stays untouched.
        def cancelled_after_partial():
            order = make_order()
            gw = FakeGateway()
            refund(order, 100, gw, OWNER, "k")
            order["status"] = "cancelled"
            return order, gw

        def fully_refunded():
            order = make_order()
            gw = FakeGateway()
            refund(order, 1000, gw, OWNER, "k")  # status becomes "refunded"
            return order, gw

        for name, build in (("cancelled", cancelled_after_partial),
                            ("refunded", fully_refunded)):
            with self.subTest(order_state=name):
                order, gw = build()
                stored = order["keys"]["k"]
                snapshot = copy.deepcopy(order)
                self.assertEqual(order["status"], name)
                self.assertEqual(len(gw.calls), 1)

                # Different amount, same actor: only rule 4 could reject this.
                replay = refund(order, 500, gw, OWNER, "k")

                self.assertEqual(replay, stored)
                self.assertEqual(order, snapshot)
                self.assertEqual(len(gw.calls), 1)  # no second gateway call

    def test_distinct_keys_refund_separately(self):
        order = make_order()
        gw = FakeGateway()
        refund(order, 100, gw, OWNER, "a")
        refund(order, 100, gw, OWNER, "b")
        self.assertEqual(order["refunded"], 200)
        self.assertEqual(len(gw.calls), 2)
        self.assertEqual(set(order["keys"]), {"a", "b"})


class AmountValidationTests(unittest.TestCase):
    def test_invalid_amounts_raise_value_error(self):
        for bad in (0, -1, -100, True, False, 1.5, 10.0, "10", None, [1]):
            with self.subTest(amount=bad):
                order = make_order()
                gw = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gw, ADMIN, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["keys"], {})

    def test_amount_validation_precedes_permission_check(self):
        # Rule order: invalid amount raises ValueError even for a stranger.
        order = make_order()
        with self.assertRaises(ValueError):
            refund(order, 0, FakeGateway(), OTHER, "k")


class PermissionTests(unittest.TestCase):
    def test_stranger_cannot_refund(self):
        order = make_order()
        gw = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gw, OTHER, "k")
        self.assertEqual(gw.calls, [])
        self.assertEqual(order["refunded"], 0)
        self.assertEqual(order["keys"], {})

    def test_unknown_or_missing_roles_are_denied(self):
        for actor in (
            {"id": "x", "role": "intern"},
            {"id": "cust_1"},                      # owner id, no role
            {},                                    # nothing at all
            {"id": "cust_1", "role": "Customer"},  # role match is case-sensitive
            {"id": "cust_1", "role": "customer "}, # no accidental strip
        ):
            # Note: owner id alone is not enough; the role must be customer.
            with self.subTest(actor=actor):
                order = make_order()
                gw = FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 100, gw, actor, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order["refunded"], 0)

    def test_permission_precedes_status_guard(self):
        # Rule 3 is checked before rule 4: an unauthorized actor on a dead order
        # gets PermissionError, never the status ValueError, and nothing moves.
        dead_orders = {
            "cancelled": make_order(status="cancelled", refunded=0),
            "refunded": make_order(status="refunded", refunded=1000),
        }
        for status, order in dead_orders.items():
            with self.subTest(status=status):
                snapshot = copy.deepcopy(order)
                gw = FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 100, gw, OTHER, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order, snapshot)

    def test_non_dict_actor_is_denied(self):
        # Malformed actors are denied with PermissionError, not AttributeError.
        for actor in (None, "admin", ["admin"], 42):
            with self.subTest(actor=actor):
                order = make_order()
                snapshot = copy.deepcopy(order)
                gw = FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 100, gw, actor, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order, snapshot)

    def test_admin_with_foreign_id_allowed(self):
        order = make_order(owner_id="someone-else")
        refund(order, 100, FakeGateway(), ADMIN, "k")

    def test_owner_role_must_match_exactly(self):
        order = make_order()
        with self.assertRaises(PermissionError):
            refund(order, 100, FakeGateway(), {"id": "cust_1", "role": "support_lead"}, "k")


class StatusTests(unittest.TestCase):
    def test_non_refundable_statuses_raise_value_error(self):
        cases = (
            ("cancelled", {"refunded": 0}),
            # Real fully-refunded shape: paid == refunded, not the contrived 0.
            ("refunded", {"refunded": 1000}),
            ("pending", {"refunded": 0}),
            ("", {"refunded": 0}),
        )
        for status, overrides in cases:
            with self.subTest(status=status):
                order = make_order(status=status, **overrides)
                gw = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 100, gw, ADMIN, "k")
                self.assertEqual(gw.calls, [])
                self.assertEqual(order["refunded"], overrides["refunded"])
                self.assertEqual(order["keys"], {})

    def test_status_check_precedes_cap_check(self):
        # cancelled order, amount over balance: still ValueError from status
        order = make_order(status="cancelled")
        with self.assertRaises(ValueError):
            refund(order, 99999, FakeGateway(), ADMIN, "k")
        self.assertEqual(order["refunded"], 0)


class RefundableCapTests(unittest.TestCase):
    def test_amount_over_remaining_balance_rejected(self):
        order = make_order(paid=1000, refunded=900, status="partially_refunded")
        gw = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 101, gw, ADMIN, "k")
        self.assertEqual(gw.calls, [])
        self.assertEqual(order["refunded"], 900)
        self.assertEqual(order["keys"], {})

    def test_exact_remaining_balance_allowed(self):
        order = make_order(paid=1000, refunded=900, status="partially_refunded")
        refund(order, 100, FakeGateway(), ADMIN, "k")
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")

    def test_second_refund_cannot_exceed_remaining(self):
        order = make_order(paid=500)
        gw = FakeGateway()
        refund(order, 300, gw, ADMIN, "a")
        with self.assertRaises(ValueError):
            refund(order, 300, gw, ADMIN, "b")
        self.assertEqual(order["refunded"], 300)
        self.assertEqual(len(gw.calls), 1)
        self.assertEqual(set(order["keys"]), {"a"})

    def test_no_refund_on_fully_refunded_amount(self):
        order = make_order(paid=100, refunded=100, status="refunded")
        with self.assertRaises(ValueError):
            refund(order, 1, FakeGateway(), ADMIN, "k")


class GatewayFailureAtomicityTests(unittest.TestCase):
    def test_gateway_error_leaves_order_completely_unchanged(self):
        order = make_order(paid=1000, refunded=250, status="partially_refunded")
        snapshot = copy.deepcopy(order)
        gw = FakeGateway(fail=True)

        with self.assertRaises(GatewayError):
            refund(order, 100, gw, ADMIN, "boom")

        self.assertEqual(order, snapshot)  # refunded/status/keys untouched
        self.assertEqual(order["refunded"], 250)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"], {})
        self.assertEqual(len(gw.calls), 1)

    def test_failed_refund_can_be_retried_after_recovery(self):
        order = make_order()
        gw = FakeGateway(fail=True)
        with self.assertRaises(GatewayError):
            refund(order, 100, gw, ADMIN, "same-key")
        self.assertEqual(order["keys"], {})

        gw.fail = False
        result = refund(order, 100, gw, ADMIN, "same-key")
        self.assertEqual(result["amount"], 100)
        self.assertEqual(order["refunded"], 100)
        self.assertEqual(len(gw.calls), 2)

    def test_gateway_error_is_not_swallowed_or_rewrapped(self):
        order = make_order()
        gw = FakeGateway(fail=True)
        with self.assertRaises(GatewayError) as ctx:
            refund(order, 100, gw, ADMIN, "k")
        self.assertIsInstance(ctx.exception, GatewayError)
        self.assertEqual(str(ctx.exception), "gateway declined")

    def test_non_gateway_error_leaves_order_unchanged(self):
        # Spec-silent, but the commit must sit after the gateway call for any
        # exception, not only GatewayError: nothing is written, nothing stored.
        class ExplodingGateway:
            def __init__(self):
                self.calls = []

            def refund(self, charge_id, amount):
                self.calls.append((charge_id, amount))
                raise RuntimeError("socket closed")

        order = make_order()
        snapshot = copy.deepcopy(order)
        gw = ExplodingGateway()

        with self.assertRaises(RuntimeError):
            refund(order, 100, gw, ADMIN, "k")

        self.assertEqual(order, snapshot)
        self.assertEqual(order["refunded"], 0)
        self.assertEqual(order["keys"], {})
        self.assertEqual(len(gw.calls), 1)


if __name__ == "__main__":
    unittest.main()
