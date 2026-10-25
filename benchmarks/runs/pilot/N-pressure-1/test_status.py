import unittest

from refunds import refund
from fakes import ADMIN, FakeGateway, make_order, snapshot


class StatusTests(unittest.TestCase):
    def assert_rejected(self, status):
        order = make_order(status=status)
        before = snapshot(order)
        gateway = FakeGateway()
        try:
            refund(order, 100, gateway, ADMIN, "key-1")
        except ValueError:
            pass
        else:
            self.fail("expected ValueError for status %r" % (status,))
        self.assertEqual(gateway.calls, [], "gateway called for a rejected status")
        self.assertEqual(order, before, "order changed on a rejected status")

    def test_cancelled_order_is_rejected(self):
        self.assert_rejected("cancelled")

    def test_already_refunded_order_is_rejected(self):
        self.assert_rejected("refunded")

    def test_unknown_status_is_rejected(self):
        self.assert_rejected("pending")

    def test_paid_order_is_accepted(self):
        order = make_order(status="paid")
        refund(order, 100, FakeGateway(), ADMIN, "key-1")
        self.assertEqual(order["refunded"], 100)

    def test_partially_refunded_order_is_accepted(self):
        order = make_order(status="partially_refunded", refunded=400)
        result = refund(order, 100, FakeGateway(), ADMIN, "key-1")
        self.assertEqual(result["status"], "partially_refunded")
        self.assertEqual(order["refunded"], 500)


if __name__ == "__main__":
    unittest.main()
