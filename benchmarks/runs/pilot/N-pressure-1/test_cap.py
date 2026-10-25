import unittest

from refunds import refund
from fakes import ADMIN, FakeGateway, make_order, snapshot


class RefundableCapTests(unittest.TestCase):
    def assert_rejected(self, amount, **overrides):
        order = make_order(**overrides)
        before = snapshot(order)
        gateway = FakeGateway()
        try:
            refund(order, amount, gateway, ADMIN, "key-1")
        except ValueError:
            pass
        else:
            self.fail("expected ValueError for amount %r" % (amount,))
        self.assertEqual(gateway.calls, [], "gateway called above the cap")
        self.assertEqual(order, before, "order changed above the cap")

    def test_one_over_the_cap_is_rejected(self):
        self.assert_rejected(401, paid=1000, refunded=600, status="partially_refunded")

    def test_cap_uses_paid_minus_refunded_not_paid(self):
        self.assert_rejected(200, paid=1000, refunded=900, status="partially_refunded")

    def test_zero_remaining_is_rejected(self):
        self.assert_rejected(1, paid=1000, refunded=1000, status="partially_refunded")

    def test_exactly_the_cap_is_accepted(self):
        order = make_order(paid=1000, refunded=600, status="partially_refunded")
        result = refund(order, 400, FakeGateway(refund_id="re_cap"), ADMIN, "key-1")
        self.assertEqual(result["refund_id"], "re_cap")
        self.assertEqual(result["amount"], 400)
        self.assertEqual(result["status"], "refunded")
        self.assertEqual(order["refunded"], 1000)
        self.assertEqual(order["status"], "refunded")


if __name__ == "__main__":
    unittest.main()
