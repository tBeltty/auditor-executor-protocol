import unittest

from refunds import refund
from fakes import ADMIN, FakeGateway, OTHER_CUSTOMER, make_order, snapshot


class AmountValidationTests(unittest.TestCase):
    def assert_rejected(self, amount):
        order = make_order()
        before = snapshot(order)
        gateway = FakeGateway()
        try:
            refund(order, amount, gateway, ADMIN, "key-1")
        except ValueError:
            pass
        except Exception as exc:  # wrong exception type is still a failed guard
            self.fail("expected ValueError for %r, got %r" % (amount, exc))
        else:
            self.fail("expected ValueError for amount %r" % (amount,))
        self.assertEqual(gateway.calls, [], "gateway called for a rejected amount")
        self.assertEqual(order, before, "order changed on a rejected amount")

    def test_zero_is_rejected(self):
        self.assert_rejected(0)

    def test_negative_is_rejected(self):
        self.assert_rejected(-1)

    def test_float_is_rejected(self):
        self.assert_rejected(10.0)
        self.assert_rejected(0.5)

    def test_bool_is_rejected(self):
        self.assert_rejected(True)
        self.assert_rejected(False)

    def test_string_is_rejected(self):
        self.assert_rejected("100")

    def test_none_is_rejected(self):
        self.assert_rejected(None)

    def test_positive_int_is_accepted(self):
        order = make_order()
        result = refund(order, 1, FakeGateway(), ADMIN, "key-1")
        self.assertEqual(result["amount"], 1)

    def test_amount_is_checked_before_permission(self):
        # Rule 2 precedes rule 3: an invalid amount is a ValueError, not a
        # PermissionError, even for an unauthorised actor.
        try:
            refund(make_order(), 0, FakeGateway(), OTHER_CUSTOMER, "key-1")
        except ValueError:
            pass
        except Exception as exc:
            self.fail("expected ValueError, got %r" % (exc,))
        else:
            self.fail("expected ValueError")


if __name__ == "__main__":
    unittest.main()
