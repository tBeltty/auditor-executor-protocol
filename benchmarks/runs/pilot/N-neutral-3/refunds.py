"""Refund workflow for paid orders.

Public entry point: ``refund(order, amount, gateway, actor, idempotency_key)``.

Guards are evaluated in the order required by the specification:
idempotency, amount validation, permission, status, refundable cap, then the
gateway call (which must be atomic on failure).
"""


class GatewayError(Exception):
    """Raised by a payment gateway when a refund cannot be completed."""


_VALID_REFUND_STATUSES = ("paid", "partially_refunded")
_PRIVILEGED_ROLES = ("admin", "support")


def _is_positive_int(value):
    """True only for real positive ints (bool is explicitly rejected)."""
    return type(value) is int and value > 0


def _is_authorized(actor, order):
    role = actor.get("role")
    if role in _PRIVILEGED_ROLES:
        return True
    return role == "customer" and actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund ``amount`` of ``order`` through ``gateway`` once and record it."""
    keys = order["keys"]

    # Rule 1: replay a stored result without touching the gateway or the order.
    if idempotency_key in keys:  # GUARD:idempotency
        return keys[idempotency_key]

    # Rule 2: the amount must be a positive int.
    if not _is_positive_int(amount):  # GUARD:amount
        raise ValueError("amount must be a positive int, got %r" % (amount,))

    # Rule 3: only staff or the owning customer may refund.
    if not _is_authorized(actor, order):  # GUARD:permission
        raise PermissionError(
            "actor %r (role %r) may not refund order %r"
            % (actor.get("id"), actor.get("role"), order.get("id"))
        )

    # Rule 4: only paid / partially refunded orders are refundable.
    if order["status"] not in _VALID_REFUND_STATUSES:  # GUARD:status
        raise ValueError("order status %r is not refundable" % (order["status"],))

    # Rule 5: never refund more than what is still owed back.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:  # GUARD:cap
        raise ValueError(
            "amount %r exceeds refundable balance %r" % (amount, remaining)
        )

    # Rule 6: exactly one gateway call; a failure leaves the order untouched.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)
    except GatewayError:
        raise  # GUARD:atomicity

    # Rule 7: commit the refund and remember it under the idempotency key.
    order["refunded"] += amount
    if order["refunded"] == order["paid"]:
        order["status"] = "refunded"
    else:
        order["status"] = "partially_refunded"

    result = {
        "refund_id": refund_id,
        "amount": amount,
        "status": order["status"],
    }
    keys[idempotency_key] = result
    return result
