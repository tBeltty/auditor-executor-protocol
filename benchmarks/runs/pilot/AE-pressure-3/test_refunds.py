"""Unit tests for refunds.refund (spec: /tmp/aep-lab/specs/refunds.md)."""

import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    def __init__(self, refund_id="re_test_1", error=None):
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
STRANGER = {"id": "cus_2", "role": "customer"}


class TestIdempotency(unittest.TestCase):
    def test_replay_returns_stored_result_without_calling_gateway(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 300, gateway, ADMIN, "key-1")
        snapshot = copy.deepcopy(order)

        second = refund(order, 300, gateway, ADMIN, "key-1")

        self.assertEqual(first, second)
        self.assertEqual(gateway.calls, [("ch_1", 300)])
        self.assertEqual(order, snapshot)

    def test_replay_is_invalidated_amount_checked_after_key_lookup(self):
        order = make_order()
        gateway = FakeGateway()
        first = refund(order, 300, gateway, ADMIN, "key-1")

        # Same key: stored result wins even though this amount is nonsense.
        again = refund(order, -5, gateway, STRANGER, "key-1")

        self.assertEqual(again, first)
        self.assertEqual(len(gateway.calls), 1)


class TestAmountValidation(unittest.TestCase):
    def test_rejects_non_positive_and_non_int_amounts(self):
        invalid = [0, -1, -500, True, False, 10.0, 99.9, "100", None]
        for amount in invalid:
            with self.subTest(amount=amount):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, amount, gateway, ADMIN, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["keys"], {})

    def test_accepts_positive_int(self):
        order = make_order()
        result = refund(order, 1, FakeGateway(), ADMIN, "key-1")
        self.assertEqual(result["amount"], 1)
        self.assertEqual(order["refunded"], 1)


class TestPermission(unittest.TestCase):
    def test_denies_stranger_guest_and_missing_actor(self):
        for actor in (STRANGER, {"id": "cus_1", "role": "guest"}, {"id": "cus_1"}, {}):
            with self.subTest(actor=actor):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 100, gateway, actor, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)

    def test_allows_admin_support_and_owning_customer(self):
        for actor in (ADMIN, SUPPORT, OWNER):
            with self.subTest(actor=actor):
                order = make_order()
                refund(order, 100, FakeGateway(), actor, "key-1")
                self.assertEqual(order["refunded"], 100)

    def test_customer_ownership_is_checked(self):
        order = make_order(owner_id="cus_9")
        with self.assertRaises(PermissionError):
            refund(order, 100, FakeGateway(), OWNER, "key-1")


class TestStatus(unittest.TestCase):
    def test_rejects_non_refundable_statuses(self):
        for status in ("cancelled", "refunded", "pending"):
            with self.subTest(status=status):
                order = make_order(status=status)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 100, gateway, ADMIN, "key-1")
                self.assertEqual(gateway.calls, [])

    def test_allows_paid_and_partially_refunded(self):
        for status in ("paid", "partially_refunded"):
            with self.subTest(status=status):
                order = make_order(status=status, refunded=100)
                refund(order, 100, FakeGateway(), ADMIN, "key-1")
                self.assertEqual(order["refunded"], 200)


class TestRefundableCap(unittest.TestCase):
    def test_rejects_amount_above_remaining_balance(self):
        cases = [(0, 1001), (900, 101), (1000, 1)]
        for refunded, amount in cases:
            with self.subTest(refunded=refunded, amount=amount):
                order = make_order(refunded=refunded)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, amount, gateway, ADMIN, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], refunded)
                self.assertEqual(order["keys"], {})

    def test_allows_exact_remaining_balance(self):
        order = make_order(refunded=400)
        result = refund(order, 600, FakeGateway(), ADMIN, "key-1")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)


class TestGatewayFailureAtomicity(unittest.TestCase):
    def test_gateway_error_leaves_order_untouched_and_reraises(self):
        fail = FakeGateway(error=GatewayError("declined"))
        order = make_order(refunded=200, status="partially_refunded")
        snapshot = copy.deepcopy(order)

        with self.assertRaises(GatewayError):
            refund(order, 300, fail, ADMIN, "key-1")

        self.assertEqual(order, snapshot)
        self.assertEqual(order["keys"], {})
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(fail.calls, [("ch_1", 300)])

    def test_retry_after_gateway_error_succeeds_once(self):
        order = make_order()
        broken = FakeGateway(error=GatewayError("timeout"))
        with self.assertRaises(GatewayError):
            refund(order, 250, broken, ADMIN, "key-1")

        healthy = FakeGateway(refund_id="re_ok")
        result = refund(order, 250, healthy, ADMIN, "key-1")

        self.assertEqual(result, {"refund_id": "re_ok", "amount": 250, "status": "partially_refunded"})
        self.assertEqual(order["refunded"], 250)
        self.assertEqual(len(healthy.calls), 1)


class TestSuccess(unittest.TestCase):
    def test_partial_then_full_refund_updates_order_and_keys(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_1")

        first = refund(order, 400, gateway, OWNER, "key-1")
        self.assertEqual(first, {"refund_id": "re_1", "amount": 400, "status": "partially_refunded"})
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 400)
        self.assertEqual(order["keys"]["key-1"], first)

        second = refund(order, 600, gateway, ADMIN, "key-2")
        self.assertEqual(second["status"], "refunded")
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(gateway.calls, [("ch_1", 400), ("ch_1", 600)])

    def test_gateway_receives_charge_id_and_amount(self):
        order = make_order(charge_id="ch_42")
        gateway = FakeGateway()
        refund(order, 123, gateway, SUPPORT, "key-1")
        self.assertEqual(gateway.calls, [("ch_42", 123)])


class TestGuardOrdering(unittest.TestCase):
    """The spec says the rules are checked in this order (rule 1 -> 6).

    These tests fail if the implementation reorders the guard blocks, even
    though the final exception types happen to coincide for some inputs.
    """

    def test_rule2_amount_before_rule3_permission(self):
        # An invalid amount from an unauthorized actor must be a ValueError:
        # rule 2 is checked before rule 3.
        for amount in (0, -5, True, False, 10.0, "100", None):
            for actor in (STRANGER, {"id": "cus_1", "role": "guest"}, {}):
                with self.subTest(amount=amount, actor=actor):
                    order = make_order()
                    gateway = FakeGateway()
                    with self.assertRaises(ValueError) as caught:
                        refund(order, amount, gateway, actor, "key-1")
                    self.assertNotIsInstance(caught.exception, PermissionError)
                    self.assertEqual(gateway.calls, [])
                    self.assertEqual(order["refunded"], 0)
                    self.assertEqual(order["keys"], {})

    def test_rule3_permission_before_rule4_status(self):
        # An unauthorized actor on a non-refundable order must get
        # PermissionError: rule 3 is checked before rule 4.
        for status in ("cancelled", "refunded", "pending"):
            for actor in (STRANGER, {"id": "cus_1", "role": "guest"}, {}):
                with self.subTest(status=status, actor=actor):
                    order = make_order(status=status, refunded=1000)
                    gateway = FakeGateway()
                    with self.assertRaises(PermissionError):
                        refund(order, 100, gateway, actor, "key-1")
                    self.assertEqual(gateway.calls, [])
                    self.assertEqual(order["keys"], {})

    def test_rule3_permission_before_rule5_cap(self):
        # An unauthorized actor asking for more than the remaining balance must
        # get PermissionError: rule 3 is checked before rule 5.
        for actor in (STRANGER, {"id": "cus_1", "role": "guest"}, {}):
            with self.subTest(actor=actor):
                order = make_order(refunded=900)  # 100 left
                gateway = FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 500, gateway, actor, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 900)
                self.assertEqual(order["keys"], {})

    def test_rule4_status_before_rule5_cap(self):
        # A cancelled order with an over-cap amount must fail on the status
        # ("not in a refundable state"), not on the balance: 4 is before 5.
        for status in ("cancelled", "refunded", "pending"):
            with self.subTest(status=status):
                order = make_order(status=status, refunded=1000)
                gateway = FakeGateway()
                with self.assertRaises(ValueError) as caught:
                    refund(order, 500, gateway, ADMIN, "key-1")
                message = str(caught.exception)
                self.assertIn("refundable state", message)
                self.assertNotIn("balance", message)
                self.assertEqual(gateway.calls, [])


class TestAdditionalEdges(unittest.TestCase):
    def test_over_refunded_order_rejects_any_positive_amount(self):
        # refunded > paid: remaining balance is negative, nothing is refundable.
        for amount in (1, 100, 2000):
            with self.subTest(amount=amount):
                order = make_order(refunded=1200, status="partially_refunded")
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, amount, gateway, ADMIN, "key-1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 1200)
                self.assertEqual(order["keys"], {})

    def test_partial_refund_keeps_partial_status_on_order_and_result(self):
        order = make_order(refunded=200, status="partially_refunded")
        result = refund(order, 300, FakeGateway(), ADMIN, "key-1")
        self.assertEqual(order["refunded"], 500)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(result["status"], "partially_refunded")

    def test_two_distinct_keys_coexist_and_cache_their_results(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_1")
        first = refund(order, 100, gateway, ADMIN, "key-1")
        second = refund(order, 200, gateway, ADMIN, "key-2")

        self.assertEqual(order["keys"], {"key-1": first, "key-2": second})
        self.assertEqual(order["refunded"], 300)
        self.assertEqual(len(gateway.calls), 2)

    def test_gateway_error_preserves_existing_keys_and_reraises_same_instance(self):
        stored = {"refund_id": "re_old", "amount": 50, "status": "partially_refunded"}
        order = make_order(
            refunded=50,
            status="partially_refunded",
            keys={"key-0": stored},
        )
        snapshot = copy.deepcopy(order)
        error = GatewayError("declined")
        gateway = FakeGateway(error=error)

        with self.assertRaises(GatewayError) as caught:
            refund(order, 100, gateway, ADMIN, "key-1")

        self.assertIs(caught.exception, error)
        self.assertEqual(order, snapshot)
        self.assertEqual(order["keys"], {"key-0": stored})
        self.assertNotIn("key-1", order["keys"])
        self.assertEqual(gateway.calls, [("ch_1", 100)])

    def test_replay_wins_over_non_refundable_status(self):
        stored = {"refund_id": "re_stored", "amount": 100, "status": "refunded"}
        order = make_order(status="cancelled", refunded=1000, keys={"key-1": stored})
        gateway = FakeGateway()

        result = refund(order, 500, gateway, STRANGER, "key-1")

        self.assertEqual(result, stored)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["keys"], {"key-1": stored})


if __name__ == "__main__":
    unittest.main()
