"""Test doubles and fixtures shared by the refunds tests."""

import copy


class FakeGateway:
    """Records calls; optionally raises a given error instead of refunding."""

    def __init__(self, refund_id="re_1", error=None):
        self.calls = []
        self.refund_id = refund_id
        self.error = error

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        if self.error is not None:
            raise self.error
        return self.refund_id


class LoudGateway(FakeGateway):
    """Fails the test if it is called at all."""

    def refund(self, charge_id, amount):
        self.calls.append((charge_id, amount))
        raise AssertionError("gateway must not be called")


def make_order(**overrides):
    order = {
        "id": "o_1",
        "owner_id": "u_1",
        "charge_id": "ch_1",
        "paid": 1000,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


def snapshot(order):
    return copy.deepcopy(order)


ADMIN = {"id": "u_admin", "role": "admin"}
SUPPORT = {"id": "u_support", "role": "support"}
OWNER = {"id": "u_1", "role": "customer"}
OTHER_CUSTOMER = {"id": "u_2", "role": "customer"}
