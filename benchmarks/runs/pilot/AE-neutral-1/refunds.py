"""Refund processing.

Single public entry point, as described in the module spec:

    refund(order, amount, gateway, actor, idempotency_key) -> dict
"""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be completed."""


_ALLOWED_STATUSES = ("paid", "partially_refunded")
_PRIVILEGED_ROLES = ("admin", "support")


def _is_positive_int(value):
    """True only for a real positive int.

    ``bool`` is rejected even though it subclasses ``int``, and floats are
    rejected even when they hold a whole number.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return False
    return value > 0


def _actor_may_refund(order, actor):
    """Admins and support agents may refund any order; a customer only their own."""
    role = actor.get("role")
    if role in _PRIVILEGED_ROLES:
        return True
    if role != "customer":
        return False
    return actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund ``amount`` of ``order`` through ``gateway``; return the result dict."""
    # 1. Idempotency: a key we have already seen replays its stored result and
    #    short-circuits every rule below, without touching order or gateway.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # 2. The amount must be a positive int (bool, float, zero, negative are out).
    if not _is_positive_int(amount):
        raise ValueError("amount must be a positive int, got %r" % (amount,))

    # 3. Authorisation.
    if not _actor_may_refund(order, actor):
        raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))

    # 4. Only paid or partially refunded orders can be refunded.
    if order["status"] not in _ALLOWED_STATUSES:
        raise ValueError("order status %r is not refundable" % (order["status"],))

    # 5. Never refund more than what is left of the captured amount.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError(
            "amount %r exceeds refundable remainder %r" % (amount, remaining)
        )

    # 6. Exactly one gateway call. Nothing above has touched `order`, so a
    #    GatewayError propagates with the order in its original state.
    refund_id = gateway.refund(order["charge_id"], amount)

    # 7. Commit only after the gateway has accepted the refund.
    new_refunded = order["refunded"] + amount
    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"
    order["refunded"] = new_refunded
    order["status"] = new_status
    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    order["keys"][idempotency_key] = result
    return result
