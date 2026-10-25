import unittest

from refunds import GatewayError, refund
from fakes import ADMIN, FakeGateway, make_order, snapshot


class GatewayFailureTests(unittest.TestCase):
    def test_gateway_error_propagates_and_leaves_order_untouched(self):
        order = make_order(paid=1000, refunded=100, status="partially_refunded")
        before = snapshot(order)
        gateway = FakeGateway(error=GatewayError("declined"))

        with self.assertRaises(GatewayError):
            refund(order, 250, gateway, ADMIN, "key-fail")

        self.assertEqual(gateway.calls, [("ch_1", 250)])
        self.assertEqual(order, before, "failed refund mutated the order")
        self.assertEqual(order["keys"], {})
        self.assertEqual(order["refunded"], 100)
        self.assertEqual(order["status"], "partially_refunded")

    def test_no_result_is_cached_for_the_failed_key(self):
        order = make_order()
        failing = FakeGateway(error=GatewayError("timeout"))

        with self.assertRaises(GatewayError):
            refund(order, 100, failing, ADMIN, "key-fail")

        # The same key must be retryable, and the order must still be intact.
        self.assertNotIn("key-fail", order["keys"])
        result = refund(order, 100, FakeGateway(refund_id="re_retry"), ADMIN, "key-fail")
        self.assertEqual(result["refund_id"], "re_retry")
        self.assertEqual(order["refunded"], 100)
        self.assertEqual(order["status"], "partially_refunded")

    def test_gateway_called_once_with_charge_and_amount(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_once")

        result = refund(order, 700, gateway, ADMIN, "key-1")

        self.assertEqual(gateway.calls, [("ch_1", 700)])
        self.assertEqual(result, {
            "refund_id": "re_once",
            "amount": 700,
            "status": "partially_refunded",
        })
        self.assertEqual(order["keys"]["key-1"], result)


if __name__ == "__main__":
    unittest.main()
