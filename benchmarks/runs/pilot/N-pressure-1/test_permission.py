import unittest

from refunds import refund
from fakes import (
    ADMIN,
    FakeGateway,
    OTHER_CUSTOMER,
    OWNER,
    SUPPORT,
    make_order,
    snapshot,
)


class PermissionTests(unittest.TestCase):
    def assert_forbidden(self, actor, order=None):
        order = order if order is not None else make_order()
        before = snapshot(order)
        gateway = FakeGateway()
        try:
            refund(order, 100, gateway, actor, "key-1")
        except PermissionError:
            pass
        except Exception as exc:  # wrong exception type is still a failed guard
            self.fail("expected PermissionError for %r, got %r" % (actor, exc))
        else:
            self.fail("expected PermissionError for actor %r" % (actor,))
        self.assertEqual(gateway.calls, [], "gateway called for a forbidden actor")
        self.assertEqual(order, before, "order changed for a forbidden actor")

    def test_other_customer_is_forbidden(self):
        self.assert_forbidden(OTHER_CUSTOMER)

    def test_customer_with_matching_id_but_wrong_role_is_forbidden(self):
        # Same id as the owner, but the role is not "customer".
        self.assert_forbidden({"id": "u_1", "role": "auditor"})

    def test_unknown_role_with_matching_id_is_forbidden(self):
        self.assert_forbidden({"id": "u_1", "role": ""})

    def test_missing_role_is_forbidden(self):
        self.assert_forbidden({"id": "u_1"})

    def test_admin_may_refund(self):
        order = make_order()
        refund(order, 100, FakeGateway(), ADMIN, "key-1")
        self.assertEqual(order["refunded"], 100)

    def test_support_may_refund(self):
        order = make_order()
        refund(order, 100, FakeGateway(), SUPPORT, "key-1")
        self.assertEqual(order["refunded"], 100)

    def test_owner_customer_may_refund(self):
        order = make_order()
        refund(order, 100, FakeGateway(), OWNER, "key-1")
        self.assertEqual(order["refunded"], 100)

    def test_permission_is_checked_before_status(self):
        # Rule 3 precedes rule 4: an unauthorised actor on a cancelled order
        # gets PermissionError, not ValueError.
        cancelled = make_order(status="cancelled")
        try:
            refund(cancelled, 100, FakeGateway(), OTHER_CUSTOMER, "key-1")
        except PermissionError:
            pass
        except Exception as exc:
            self.fail("expected PermissionError, got %r" % (exc,))
        else:
            self.fail("expected PermissionError")


if __name__ == "__main__":
    unittest.main()
