"""Shared fixtures for the refund unit tests (not a test module)."""

import copy


def make_order(**overrides):
    """A paid order for 100 minor units, owned by ``cus_owner``."""
    order = {
        "id": "ord_1",
        "owner_id": "cus_owner",
        "charge_id": "ch_1",
        "paid": 100,
        "refunded": 0,
        "status": "paid",
        "keys": {},
    }
    order.update(overrides)
    return order


def make_actor(actor_id="cus_owner", role="customer"):
    return {"id": actor_id, "role": role}


def snapshot(order):
    """Deep copy of an order, used to prove nothing was mutated."""
    return copy.deepcopy(order)
