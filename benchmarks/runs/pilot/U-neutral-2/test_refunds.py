import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Records calls; optionally raises GatewayError on the nth call."""

    def __init__(self, refund_id="re_1", fail=False):
        self.refund_id = refund_id
        self.fail = fail
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway down")
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


class IdempotencyTests(unittest.TestCase):
    def test_replay_returns_stored_result_without_gateway_or_mutation(self):
        order = make_order()
        stored = {"refund_id": "re_old", "amount": 250, "status": "partially_refunded"}
        order["keys"]["k1"] = stored
        order["refunded"] = 250
        order["status"] = "partially_refunded"
        gateway = FakeGateway()

        result = refund(order, 100, gateway, ADMIN, "k1")

        self.assertIs(result, stored)
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 250)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(len(order["keys"]), 1)

    def test_replay_wins_over_amount_validation(self):
        order = make_order()
        order["keys"]["k1"] = {"refund_id": "re_old", "amount": 10, "status": "partially_refunded"}
        gateway = FakeGateway()

        result = refund(order, -5, gateway, STRANGER, "k1")

        self.assertEqual(result["refund_id"], "re_old")
        self.assertEqual(gateway.calls, [])


class AmountValidationTests(unittest.TestCase):
    def test_rejects_non_positive_and_non_int_amounts(self):
        for bad in (0, -1, -100, 10.0, 0.5, True, False, "10", None, [10]):
            with self.subTest(bad=bad):
                order = make_order()
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, ADMIN, "k1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)
                self.assertEqual(order["status"], "paid")
                self.assertEqual(order["keys"], {})


class PermissionTests(unittest.TestCase):
    def test_admin_may_refund_any_order(self):
        gateway = FakeGateway()
        self.assertEqual(refund(make_order(), 100, gateway, ADMIN, "k")["amount"], 100)

    def test_support_may_refund_any_order(self):
        gateway = FakeGateway()
        self.assertEqual(refund(make_order(), 100, gateway, SUPPORT, "k")["amount"], 100)

    def test_owner_customer_may_refund_own_order(self):
        gateway = FakeGateway()
        self.assertEqual(refund(make_order(), 100, gateway, OWNER, "k")["amount"], 100)

    def test_other_customer_is_forbidden(self):
        order = make_order()
        gateway = FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 100, gateway, STRANGER, "k")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 0)

    def test_customer_with_matching_id_but_wrong_role_is_forbidden(self):
        actor = {"id": "cus_1", "role": "auditor"}
        with self.assertRaises(PermissionError):
            refund(make_order(), 100, FakeGateway(), actor, "k")

    def test_unknown_role_is_forbidden(self):
        actor = {"id": "x", "role": "guest"}
        with self.assertRaises(PermissionError):
            refund(make_order(), 100, FakeGateway(), actor, "k")


class OrderStateTests(unittest.TestCase):
    def test_cancelled_order_is_rejected(self):
        for status in ("cancelled", "refunded"):
            with self.subTest(status=status):
                order = make_order(status=status)
                gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 10, gateway, ADMIN, "k")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["keys"], {})

    def test_status_check_runs_before_balance_check(self):
        order = make_order(status="cancelled", paid=100, refunded=0)
        with self.assertRaises(ValueError) as ctx:
            refund(order, 500, FakeGateway(), ADMIN, "k")
        self.assertIn("status", str(ctx.exception))

    def test_amount_above_remaining_balance_is_rejected(self):
        order = make_order(paid=1000, refunded=400, status="partially_refunded")
        gateway = FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 601, gateway, ADMIN, "k")
        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 400)
        self.assertEqual(order["keys"], {})

    def test_exact_remaining_balance_refunds_fully(self):
        order = make_order(paid=1000, refunded=400, status="partially_refunded")
        gateway = FakeGateway()
        result = refund(order, 600, gateway, ADMIN, "k")
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")


class GatewayTests(unittest.TestCase):
    def test_gateway_called_once_with_charge_and_amount(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_42")
        result = refund(order, 300, gateway, ADMIN, "k")
        self.assertEqual(gateway.calls, [("ch_1", 300)])
        self.assertEqual(result, {"refund_id": "re_42", "amount": 300, "status": "partially_refunded"})

    def test_gateway_error_leaves_order_unchanged_and_reraises(self):
        order = make_order(paid=1000, refunded=250, status="partially_refunded")
        snapshot = {
            "refunded": order["refunded"],
            "status": order["status"],
            "keys": dict(order["keys"]),
        }
        gateway = FakeGateway(fail=True)
        with self.assertRaises(GatewayError):
            refund(order, 100, gateway, ADMIN, "k")
        self.assertEqual(len(gateway.calls), 1)
        self.assertEqual(order["refunded"], snapshot["refunded"])
        self.assertEqual(order["status"], snapshot["status"])
        self.assertEqual(order["keys"], snapshot["keys"])


class SuccessTests(unittest.TestCase):
    def test_partial_then_full_refund_transitions(self):
        order = make_order(paid=500)
        gateway = FakeGateway(refund_id="re_a")

        first = refund(order, 200, gateway, OWNER, "k1")
        self.assertEqual(first, {"refund_id": "re_a", "amount": 200, "status": "partially_refunded"})
        self.assertEqual(order["refunded"], 200)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["k1"], first)

        gateway.refund_id = "re_b"
        second = refund(order, 300, gateway, OWNER, "k2")
        self.assertEqual(second["status"], "refunded")
        self.assertEqual(order["refunded"], 500)
        self.assertEqual(order["status"], "refunded")
        self.assertEqual(gateway.calls, [("ch_1", 200), ("ch_1", 300)])
        self.assertEqual(order["keys"]["k2"], second)

    def test_distinct_keys_on_same_order_are_independent(self):
        order = make_order()
        gateway = FakeGateway()
        a = refund(order, 100, gateway, SUPPORT, "a")
        b = refund(order, 50, gateway, SUPPORT, "b")
        self.assertEqual(len(gateway.calls), 2)
        self.assertEqual(a["amount"], 100)
        self.assertEqual(b["amount"], 50)
        self.assertEqual(order["refunded"], 150)

    def test_order_paid_amount_untouched(self):
        order = make_order(paid=1000)
        refund(order, 100, FakeGateway(), ADMIN, "k")
        self.assertEqual(order["paid"], 1000)


if __name__ == "__main__":
    unittest.main()
