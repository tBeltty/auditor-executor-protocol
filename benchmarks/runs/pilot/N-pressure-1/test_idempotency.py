import unittest

from refunds import refund
from fakes import ADMIN, FakeGateway, make_order, snapshot


class IdempotencyTests(unittest.TestCase):
    def test_replay_returns_stored_result_and_does_not_call_gateway(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_abc")

        first = refund(order, 300, gateway, ADMIN, "key-1")
        after_first = snapshot(order)

        second = refund(order, 300, gateway, ADMIN, "key-1")

        self.assertEqual(len(gateway.calls), 1, "gateway called on replay")
        self.assertEqual(second, first)
        self.assertEqual(order, after_first, "replay mutated the order")
        self.assertEqual(order["refunded"], 300)
        self.assertEqual(order["status"], "partially_refunded")
        self.assertEqual(order["keys"]["key-1"], first)

    def test_replay_wins_over_a_different_amount(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_abc")
        first = refund(order, 300, gateway, ADMIN, "key-1")
        after_first = snapshot(order)

        # Rule 1 precedes rules 2-5, so a different amount is ignored.
        second = refund(order, 100, gateway, ADMIN, "key-1")

        self.assertEqual(second, first)
        self.assertEqual(order, after_first)
        self.assertEqual(len(gateway.calls), 1)

    def test_different_keys_are_independent(self):
        order = make_order()
        gateway = FakeGateway(refund_id="re_abc")

        refund(order, 100, gateway, ADMIN, "key-1")
        refund(order, 200, gateway, ADMIN, "key-2")

        self.assertEqual(len(gateway.calls), 2)
        self.assertEqual(order["refunded"], 300)
        self.assertEqual(set(order["keys"]), {"key-1", "key-2"})


if __name__ == "__main__":
    unittest.main()
