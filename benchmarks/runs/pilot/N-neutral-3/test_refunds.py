"""Unit tests for refunds.py, driven by an in-test fake gateway."""

import copy
import unittest

import refunds


class FakeGateway:
    """Minimal stand-in for the payment gateway."""

    def __init__(self, fail_with=None, prefix="re"):
        self.fail_with = fail_with
        self.prefix = prefix
        self.calls = []

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail_with is not None:
            raise self.fail_with
        return "%s_%d" % (self.prefix, len(self.calls))


class RefundTestCase(unittest.TestCase):
    def setUp(self):
        self.order = {
            "id": "o_1",
            "owner_id": "u_1",
            "charge_id": "ch_1",
            "paid": 1000,
            "refunded": 0,
            "status": "paid",
            "keys": {},
        }
        self.gateway = FakeGateway()
        self.actor = {"id": "u_1", "role": "customer"}

    # helpers -------------------------------------------------------------

    def run_refund(self, amount=250, actor=None, key="k1", gateway=None):
        return refunds.refund(
            self.order,
            amount,
            gateway if gateway is not None else self.gateway,
            self.actor if actor is None else actor,
            key,
        )

    def snapshot(self):
        return copy.deepcopy(self.order)

    # ---------------------------------------------------------- idempotency

    def test_idem_replay_returns_stored_result_without_gateway_call(self):
        first = self.run_refund(amount=250)
        calls_after_first = list(self.gateway.calls)
        second = self.run_refund(amount=250)
        self.assertEqual(second, first)
        self.assertEqual(self.gateway.calls, calls_after_first)
        self.assertEqual(len(self.gateway.calls), 1)

    def test_idem_replay_does_not_mutate_order(self):
        self.run_refund(amount=250)
        before = self.snapshot()
        self.run_refund(amount=250)
        self.assertEqual(self.order, before)

    def test_idem_replay_wins_over_amount_and_permission_checks(self):
        stored = {"refund_id": "re_0", "amount": 250, "status": "partially_refunded"}
        self.order["keys"]["k1"] = stored
        result = self.run_refund(
            amount=-5, actor={"id": "stranger", "role": "guest"}
        )
        self.assertEqual(result, stored)
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(
            self.order["refunded"], 0, "replay must not change the order"
        )

    def test_idem_replay_after_partial_refund(self):
        first = self.run_refund(amount=400)
        self.run_refund(amount=400)
        self.assertEqual(self.order["refunded"], 400)
        self.assertEqual(self.order["status"], "partially_refunded")
        self.assertEqual(self.order["keys"]["k1"], first)

    # ------------------------------------------------------ amount validation

    def test_amount_rejects_invalid_values(self):
        for bad in (0, -1, -250, 1.5, 0.0, True, False, "250", None):
            with self.subTest(amount=bad):
                self.gateway = FakeGateway()
                with self.assertRaises(ValueError):
                    self.run_refund(amount=bad)
                self.assertEqual(self.gateway.calls, [])
                self.assertEqual(self.order["refunded"], 0)
                self.assertEqual(self.order["keys"], {})

    def test_amount_accepts_plain_positive_int(self):
        result = self.run_refund(amount=1)
        self.assertEqual(result["amount"], 1)

    def test_amount_checked_before_permission(self):
        with self.assertRaises(ValueError):
            self.run_refund(amount=0, actor={"id": "nobody", "role": "guest"})

    # ----------------------------------------------------------- permission

    def test_perm_rejects_other_customer(self):
        with self.assertRaises(PermissionError):
            self.run_refund(actor={"id": "u_2", "role": "customer"})
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.order["refunded"], 0)

    def test_perm_rejects_unknown_role(self):
        with self.assertRaises(PermissionError):
            self.run_refund(actor={"id": "u_1", "role": "guest"})
        self.assertEqual(self.gateway.calls, [])

    def test_perm_rejects_customer_role_without_matching_id(self):
        with self.assertRaises(PermissionError):
            self.run_refund(actor={"id": "u_99", "role": "customer"})
        self.assertEqual(self.gateway.calls, [])

    def test_perm_checked_before_status(self):
        self.order["status"] = "cancelled"
        with self.assertRaises(PermissionError):
            self.run_refund(actor={"id": "u_2", "role": "customer"})

    def test_perm_allows_admin(self):
        result = self.run_refund(actor={"id": "admin_1", "role": "admin"})
        self.assertEqual(result["amount"], 250)

    def test_perm_allows_support(self):
        result = self.run_refund(actor={"id": "sup_1", "role": "support"})
        self.assertEqual(result["amount"], 250)

    def test_perm_allows_owning_customer(self):
        result = self.run_refund(actor={"id": "u_1", "role": "customer"})
        self.assertEqual(result["amount"], 250)

    # --------------------------------------------------------------- status

    def test_status_cancelled_rejected(self):
        self.order["status"] = "cancelled"
        with self.assertRaises(ValueError):
            self.run_refund()
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.order["refunded"], 0)

    def test_status_refunded_rejected(self):
        self.order["status"] = "refunded"
        self.order["refunded"] = 1000
        with self.assertRaises(ValueError):
            self.run_refund(amount=10)
        self.assertEqual(self.gateway.calls, [])
        self.assertNotIn("k1", self.order["keys"])

    def test_status_refunded_rejected_even_without_cap_breach(self):
        # The status guard must stand on its own: the amount is well inside the
        # cap, so only the status check can stop this refund.
        self.order["status"] = "refunded"
        self.order["refunded"] = 0
        with self.assertRaises(ValueError):
            self.run_refund(amount=10)
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.order["status"], "refunded")
        self.assertEqual(self.order["refunded"], 0)
        self.assertEqual(self.order["keys"], {})

    def test_status_partially_refunded_allowed(self):
        self.order["status"] = "partially_refunded"
        self.order["refunded"] = 100
        result = self.run_refund(amount=200)
        self.assertEqual(result["amount"], 200)
        self.assertEqual(self.order["refunded"], 300)

    # --------------------------------------------------------- refundable cap

    def test_cap_rejects_amount_above_remaining(self):
        with self.assertRaises(ValueError):
            self.run_refund(amount=1001)
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.order["refunded"], 0)

    def test_cap_accounts_for_previous_refunds(self):
        self.order["refunded"] = 400
        self.order["status"] = "partially_refunded"
        with self.assertRaises(ValueError):
            self.run_refund(amount=601)
        self.assertEqual(self.gateway.calls, [])
        self.assertEqual(self.order["refunded"], 400)

    def test_cap_allows_exact_remaining(self):
        self.order["refunded"] = 400
        self.order["status"] = "partially_refunded"
        result = self.run_refund(amount=600)
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(self.order["refunded"], 1000)

    def test_cap_allows_full_amount_on_paid_order(self):
        result = self.run_refund(amount=1000)
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(self.order["status"], "refunded")

    def test_cap_does_not_call_gateway_when_exceeded(self):
        self.order["paid"] = 10
        self.order["refunded"] = 10
        self.order["status"] = "partially_refunded"
        with self.assertRaises(ValueError):
            self.run_refund(amount=1)
        self.assertEqual(self.gateway.calls, [])

    # ------------------------------------------------- gateway / atomicity

    def test_gateway_failure_propagates_and_leaves_order_unchanged(self):
        self.gateway = FakeGateway(fail_with=refunds.GatewayError("boom"))
        before = self.snapshot()
        with self.assertRaises(refunds.GatewayError):
            self.run_refund(amount=250)
        self.assertEqual(self.order, before)
        self.assertEqual(self.order["refunded"], 0)
        self.assertEqual(self.order["status"], "paid")
        self.assertEqual(self.order["keys"], {})

    def test_gateway_failure_on_partial_order_leaves_state_untouched(self):
        self.order["refunded"] = 300
        self.order["status"] = "partially_refunded"
        self.gateway = FakeGateway(fail_with=refunds.GatewayError("boom"))
        before = self.snapshot()
        with self.assertRaises(refunds.GatewayError):
            self.run_refund(amount=100)
        self.assertEqual(self.order, before)
        self.assertNotIn("k1", self.order["keys"])

    def test_gateway_failure_does_not_store_key_so_retry_works(self):
        self.gateway = FakeGateway(fail_with=refunds.GatewayError("boom"))
        with self.assertRaises(refunds.GatewayError):
            self.run_refund(amount=250)
        self.gateway = FakeGateway()
        result = self.run_refund(amount=250)
        self.assertEqual(result["amount"], 250)
        self.assertEqual(len(self.gateway.calls), 1)
        self.assertEqual(self.order["refunded"], 250)

    def test_gateway_called_exactly_once_with_charge_and_amount(self):
        self.run_refund(amount=250)
        self.assertEqual(self.gateway.calls, [("ch_1", 250)])

    # -------------------------------------------------------------- success

    def test_success_result_shape_and_storage(self):
        result = self.run_refund(amount=250)
        self.assertEqual(
            result, {"refund_id": "re_1", "amount": 250, "status": "partially_refunded"}
        )
        self.assertEqual(set(result), {"refund_id", "amount", "status"})
        self.assertEqual(self.order["keys"]["k1"], result)
        self.assertEqual(self.order["refunded"], 250)
        self.assertEqual(self.order["status"], "partially_refunded")

    def test_success_full_refund_marks_order_refunded(self):
        result = self.run_refund(amount=1000)
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(self.order["status"], "refunded")
        self.assertEqual(self.order["refunded"], 1000)

    def test_success_keeps_other_keys_and_charges_untouched(self):
        self.order["keys"]["old"] = {"refund_id": "re_0", "amount": 1, "status": "x"}
        self.run_refund(amount=250, key="k1")
        self.assertIn("old", self.order["keys"])
        self.assertEqual(self.order["keys"]["old"]["refund_id"], "re_0")
        self.assertEqual(self.order["charge_id"], "ch_1")
        self.assertEqual(self.order["paid"], 1000)

    def test_success_appends_second_distinct_refund(self):
        self.run_refund(amount=250, key="k1")
        second = self.run_refund(amount=250, key="k2")
        self.assertEqual(second["refund_id"], "re_2")
        self.assertEqual(self.order["refunded"], 500)
        self.assertEqual(len(self.gateway.calls), 2)


if __name__ == "__main__":
    unittest.main()
