import copy
import unittest

from refunds import GatewayError, refund


class FakeGateway:
    """Records calls; optionally raises GatewayError on the Nth call."""

    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.fail:
            raise GatewayError("gateway unavailable")
        return "re_%d" % len(self.calls)


def make_order(**overrides):
    order = {
        "id": "ord_1",
        "owner_id": "cus_1",
        "charge_id": "ch_1",
        "paid": 100,
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


class RefundTests(unittest.TestCase):
    def test_partial_refund_updates_order(self):
        order, gateway = make_order(), FakeGateway()
        result = refund(order, 30, gateway, OWNER, "k1")

        self.assertEqual(result, {"refund_id": "re_1", "amount": 30, "status": "partially_refunded"})
        self.assertEqual(order["refunded"], 30)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["k1"], result)
        self.assertEqual(gateway.calls, [("ch_1", 30)])

    def test_full_refund_marks_refunded(self):
        order, gateway = make_order(paid=30, refunded=0), FakeGateway()
        result = refund(order, 30, gateway, ADMIN, "k1")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 30)
        self.assertEqual(order["status"], "refunded")

    def test_refund_from_partially_refunded_order(self):
        order, gateway = make_order(refunded=90, status="partially_refunded"), FakeGateway()
        result = refund(order, 10, gateway, SUPPORT, "k1")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 100)
        self.assertEqual(len(gateway.calls), 1)

    def test_idempotent_replay_returns_stored_result_without_gateway_call(self):
        order, gateway = make_order(), FakeGateway()
        first = refund(order, 25, gateway, OWNER, "k1")
        snapshot = copy.deepcopy(order)
        replay_gateway = FakeGateway()

        second = refund(order, 10, replay_gateway, OWNER, "k1")

        self.assertIs(second, first)
        self.assertEqual(second, first)
        self.assertEqual(order, snapshot)
        self.assertEqual(replay_gateway.calls, [])
        self.assertEqual(gateway.calls, [("ch_1", 25)])

    def test_idempotency_checked_before_amount_validation(self):
        order = make_order(keys={"k1": {"refund_id": "re_0", "amount": 5, "status": "paid"}})
        gateway = FakeGateway()

        result = refund(order, 0, gateway, STRANGER, "k1")

        self.assertEqual(result["refund_id"], "re_0")
        self.assertEqual(gateway.calls, [])

    def test_amount_must_be_positive_int(self):
        for bad in (0, -1, True, False, 1.0, "10", None):
            with self.subTest(amount=bad):
                order, gateway = make_order(), FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, bad, gateway, ADMIN, "k1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["refunded"], 0)

    def test_amount_checked_before_permission(self):
        order, gateway = make_order(), FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 0, gateway, STRANGER, "k1")
        self.assertEqual(gateway.calls, [])

    def test_permission_matrix(self):
        for actor in (ADMIN, SUPPORT, OWNER):
            with self.subTest(role=actor["role"]):
                order, gateway = make_order(), FakeGateway()
                self.assertEqual(refund(order, 1, gateway, actor, "k1")["amount"], 1)

        for actor in (STRANGER, {"id": "cus_1", "role": "auditor"}, {"id": "cus_2", "role": "admin_ish"}):
            with self.subTest(actor=actor):
                order, gateway = make_order(), FakeGateway()
                with self.assertRaises(PermissionError):
                    refund(order, 1, gateway, actor, "k1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order, make_order())

    def test_permission_checked_before_status(self):
        order, gateway = make_order(status="cancelled"), FakeGateway()
        with self.assertRaises(PermissionError):
            refund(order, 1, gateway, STRANGER, "k1")
        self.assertEqual(gateway.calls, [])

    def test_status_must_be_refundable(self):
        for status in ("refunded", "cancelled"):
            with self.subTest(status=status):
                order, gateway = make_order(status=status), FakeGateway()
                with self.assertRaises(ValueError):
                    refund(order, 1, gateway, ADMIN, "k1")
                self.assertEqual(gateway.calls, [])
                self.assertEqual(order["status"], status)

    def test_amount_cannot_exceed_refundable_cap(self):
        order, gateway = make_order(paid=100, refunded=40, status="partially_refunded"), FakeGateway()
        with self.assertRaises(ValueError):
            refund(order, 61, gateway, ADMIN, "k1")

        self.assertEqual(gateway.calls, [])
        self.assertEqual(order["refunded"], 40)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"], {})

    def test_amount_equal_to_cap_is_allowed(self):
        order, gateway = make_order(paid=100, refunded=40, status="partially_refunded"), FakeGateway()
        result = refund(order, 60, gateway, ADMIN, "k1")

        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 100)

    def test_gateway_failure_leaves_order_unchanged(self):
        order = make_order(refunded=10, status="partially_refunded")
        gateway = FakeGateway(fail=True)
        snapshot = copy.deepcopy(order)

        with self.assertRaises(GatewayError):
            refund(order, 20, gateway, OWNER, "k1")

        self.assertEqual(order, snapshot)
        self.assertEqual(len(gateway.calls), 1)
        self.assertNotIn("k1", order["keys"])

    def test_gateway_called_exactly_once_with_charge_and_amount(self):
        order, gateway = make_order(), FakeGateway()
        refund(order, 40, gateway, OWNER, "k1")
        self.assertEqual(gateway.calls, [("ch_1", 40)])

    def test_distinct_keys_accumulate(self):
        order, gateway = make_order(), FakeGateway()
        refund(order, 30, gateway, OWNER, "k1")
        refund(order, 20, gateway, OWNER, "k2")

        self.assertEqual(order["refunded"], 50)
        self.assertEqual(len(gateway.calls), 2)
        self.assertEqual(set(order["keys"]), {"k1", "k2"})


if __name__ == "__main__":
    unittest.main()
