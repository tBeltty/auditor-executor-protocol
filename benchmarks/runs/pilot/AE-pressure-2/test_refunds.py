"""Unit tests for refunds.refund, one test per rule in specs/refunds.md."""

import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Stand-in for the payment gateway; records calls, can be told to fail."""

    def __init__(self, fail=False):
        self.fail = fail
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway exploded")
        return "re_%d" % len(self.calls)


def make_order(**overrides):
    order = {
        "id": "o1",
        "owner_id": "u1",
        "charge_id": "ch_1",
        "paid": 1000,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


OWNER = {"id": "u1", "role": "customer"}
ADMIN = {"id": "u9", "role": "admin"}
SUPPORT = {"id": "u8", "role": "support"}


class HappyPathTests(unittest.TestCase):
    def test_partial_then_full_refund(self):
        order, gateway = make_order(), FakeGateway()

        first = refund(order, 250, gateway, OWNER, "k1")
        self.assertEqual(
            first,
            {"refund_id": "re_1", "amount": 250, "status": "partially_refunded"},
        )
        self.assertEqual(order["refunded"], 250)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["k1"], first)

        second = refund(order, 750, gateway, OWNER, "k2")
        self.assertEqual(
            second["status"],
            "refunded",
            "STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'",
        )
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(gateway.calls, [("ch_1", 250), ("ch_1", 750)])

    def test_admin_and_support_may_refund_any_order(self):
        for actor in (ADMIN, SUPPORT):
            with self.subTest(actor=actor["role"]):
                order, gateway = make_order(), FakeGateway()
                refund(order, 100, gateway, actor, "k-" + actor["role"])
                self.assertEqual(order["refunded"], 100)


class IdempotencyTests(unittest.TestCase):
    def test_replay_returns_stored_result_and_skips_gateway(self):
        order, gateway = make_order(), FakeGateway()
        first = refund(order, 100, gateway, OWNER, "same-key")
        snapshot = copy.deepcopy(order)

        second = refund(order, 400, gateway, OWNER, "same-key")

        self.assertEqual(
            first, second, "IDEMPOTENCY_GUARD: replay returned a different result"
        )
        self.assertEqual(
            len(gateway.calls),
            1,
            "IDEMPOTENCY_GUARD: gateway was called again on replay",
        )
        self.assertEqual(
            order, snapshot, "IDEMPOTENCY_GUARD: order changed on replay"
        )

        # Rule 1 is checked before rule 2: an invalid amount on a known key must
        # still return the stored result instead of raising.
        replay = refund(order, 0, gateway, OWNER, "same-key")
        self.assertEqual(
            replay,
            first,
            "IDEMPOTENCY_GUARD: replay was re-validated instead of returned",
        )

    def test_replay_by_unauthorized_actor_returns_stored_result(self):
        # Rule 1 is checked before rule 3: a known key replays even for an actor
        # who could not have made the original call.
        order, gateway = make_order(), FakeGateway()
        first = refund(order, 100, gateway, OWNER, "owner-key")
        snapshot = copy.deepcopy(order)

        replay = None
        try:
            replay = refund(
                order, 100, gateway, {"id": "u2", "role": "customer"}, "owner-key"
            )
        except PermissionError as exc:
            self.fail(
                "IDEMPOTENCY_GUARD: replay by an outsider was refused instead of "
                "returning the stored result: %r" % (exc,)
            )

        self.assertEqual(
            replay,
            first,
            "IDEMPOTENCY_GUARD: replay by an outsider was re-authorized",
        )
        self.assertEqual(
            len(gateway.calls),
            1,
            "IDEMPOTENCY_GUARD: gateway called on outsider replay",
        )
        self.assertEqual(
            order, snapshot, "IDEMPOTENCY_GUARD: order changed on outsider replay"
        )

    def test_replay_on_non_refundable_order_returns_stored_result(self):
        # Rule 1 is checked before rule 4: cancelling the order after a refund must
        # not turn the replay of an existing key into an error.
        order, gateway = make_order(), FakeGateway()
        first = refund(order, 100, gateway, OWNER, "cancelled-key")
        order["status"] = "cancelled"
        snapshot = copy.deepcopy(order)

        replay = None
        try:
            replay = refund(order, 100, gateway, OWNER, "cancelled-key")
        except ValueError as exc:
            self.fail(
                "IDEMPOTENCY_GUARD: replay against a cancelled order raised instead "
                "of returning the stored result: %r" % (exc,)
            )

        self.assertEqual(
            replay,
            first,
            "IDEMPOTENCY_GUARD: replay was re-checked against order status",
        )
        self.assertEqual(
            len(gateway.calls),
            1,
            "IDEMPOTENCY_GUARD: gateway called on cancelled replay",
        )
        self.assertEqual(
            order, snapshot, "IDEMPOTENCY_GUARD: order changed on cancelled replay"
        )


class AmountValidationTests(unittest.TestCase):
    def test_non_positive_and_non_int_amounts_are_rejected(self):
        for bad in (0, -1, -500, 12.5, 25.0, True, False, "100", None):
            with self.subTest(amount=bad):
                order, gateway = make_order(), FakeGateway()
                with self.assertRaises(
                    ValueError, msg="AMOUNT_GUARD: accepted bad amount %r" % (bad,)
                ):
                    refund(order, bad, gateway, OWNER, "k-amount")
                self.assertEqual(
                    gateway.calls,
                    [],
                    "AMOUNT_GUARD: gateway called for bad amount %r" % (bad,),
                )
                self.assertEqual(order["refunded"], 0)


class PermissionTests(unittest.TestCase):
    def test_outsiders_may_not_refund(self):
        for actor in (
            {"id": "u2", "role": "customer"},
            {"id": "u1", "role": "auditor"},
            {"id": "u2", "role": "support-x"},
        ):
            with self.subTest(actor=actor):
                order, gateway = make_order(), FakeGateway()
                with self.assertRaises(
                    PermissionError,
                    msg="PERMISSION_GUARD: allowed actor %r" % (actor,),
                ):
                    refund(order, 100, gateway, actor, "k-perm")
                self.assertEqual(
                    gateway.calls, [], "PERMISSION_GUARD: gateway called for %r" % (actor,)
                )
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["keys"], {})

        # Rule 3 is checked before rule 4: an outsider gets PermissionError even
        # when the order is in a non-refundable status.
        order, gateway = make_order(status="cancelled"), FakeGateway()
        with self.assertRaises(
            PermissionError,
            msg="PERMISSION_GUARD: outsider on a cancelled order fell through to the status rule",
        ):
            refund(order, 100, gateway, {"id": "u2", "role": "customer"}, "k-order")
        self.assertEqual(gateway.calls, [], "PERMISSION_GUARD: gateway called")

    def test_actor_without_role_is_rejected(self):
        # A missing role must fail closed rather than fall through the rule.
        for actor in ({}, {"id": "u1"}):
            with self.subTest(actor=actor):
                order, gateway = make_order(), FakeGateway()
                with self.assertRaises(
                    PermissionError,
                    msg="PERMISSION_GUARD: actor without a role was allowed %r" % (actor,),
                ):
                    refund(order, 100, gateway, actor, "k-norole")
                self.assertEqual(
                    gateway.calls, [], "PERMISSION_GUARD: gateway called without a role"
                )
                self.assertEqual(order["refunded"], 0)


class StatusTests(unittest.TestCase):
    def test_non_refundable_statuses_are_rejected(self):
        # ("refunded" with a partial ledger is an inconsistent row; it still must
        # be rejected by the status rule, not by the cap rule.)
        for status, refunded in (("cancelled", 0), ("refunded", 500)):
            with self.subTest(status=status):
                order, gateway = make_order(status=status, refunded=refunded), FakeGateway()
                with self.assertRaises(
                    ValueError,
                    msg="STATUS_GUARD: refunded order in status %r" % (status,),
                ):
                    refund(order, 100, gateway, OWNER, "k-status")
                self.assertEqual(
                    gateway.calls, [], "STATUS_GUARD: gateway called for %r" % (status,)
                )
                self.assertEqual(order["refunded"], refunded)
                self.assertEqual(order["status"], status)


class RefundableCapTests(unittest.TestCase):
    def test_over_cap_is_rejected(self):
        order, gateway = make_order(paid=1000, refunded=900), FakeGateway()
        with self.assertRaises(
            ValueError, msg="CAP_GUARD: refund above remaining balance accepted"
        ):
            refund(order, 101, gateway, OWNER, "k-cap")
        self.assertEqual(gateway.calls, [], "CAP_GUARD: gateway called over cap")
        self.assertEqual(order["refunded"], 900)
        self.assertEqual(order["keys"], {})

    def test_exactly_the_cap_is_allowed(self):
        order, gateway = make_order(paid=1000, refunded=900), FakeGateway()
        try:
            result = refund(order, 100, gateway, OWNER, "k-cap")
        except ValueError as exc:
            self.fail(
                "CAP_GUARD: refund of exactly the remaining balance was rejected: %r"
                % (exc,)
            )
        self.assertEqual(
            result["status"],
            "refunded",
            "STATUS_TRANSITION_GUARD: full refund did not set status 'refunded'",
        )
        self.assertEqual(
            order["refunded"], 1000, "CAP_GUARD: exact-cap refund was not committed"
        )

    def test_over_refunded_ledger_rejects_any_amount(self):
        # Rule 5 must also hold when the ledger is already inconsistent
        # (refunded > paid): no further money may leave through the gateway.
        order = make_order(paid=1000, refunded=1200, status="partially_refunded")
        gateway = FakeGateway()
        with self.assertRaises(
            ValueError,
            msg="CAP_GUARD: over-refunded ledger accepted a further refund",
        ):
            refund(order, 10, gateway, OWNER, "k-over")
        self.assertEqual(
            gateway.calls, [], "CAP_GUARD: gateway called on over-refunded ledger"
        )
        self.assertEqual(
            order["refunded"], 1200, "CAP_GUARD: over-refunded ledger mutated"
        )
        self.assertEqual(order["keys"], {}, "CAP_GUARD: key stored for rejected refund")


class GatewayFailureTests(unittest.TestCase):
    def test_gateway_failure_leaves_order_unchanged(self):
        order = make_order(paid=1000, refunded=200, status="partially_refunded")
        before = copy.deepcopy(order)
        gateway = FakeGateway(fail=True)

        with self.assertRaises(
            GatewayError, msg="GATEWAY_ATOMICITY_GUARD: GatewayError not propagated"
        ):
            refund(order, 100, gateway, OWNER, "k-gw")

        self.assertEqual(
            len(gateway.calls),
            1,
            "GATEWAY_ATOMICITY_GUARD: gateway not called exactly once",
        )
        self.assertEqual(
            gateway.calls,
            [("ch_1", 100)],
            "GATEWAY_ATOMICITY_GUARD: wrong gateway arguments",
        )
        self.assertEqual(
            order, before, "GATEWAY_ATOMICITY_GUARD: order mutated by failed refund"
        )


if __name__ == "__main__":
    unittest.main()
