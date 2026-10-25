"""Refund processing for a single order."""

__all__ = ["GatewayError", "refund"]

_ALLOWED_STATUSES = ("paid", "partially_refunded")
_PRIVILEGED_ROLES = ("admin", "support")


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be executed."""


def _is_positive_int(value):
    """True only for genuine positive ints (bool is a subclass of int)."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _may_refund(order, actor):
    role = actor.get("role")
    if role in _PRIVILEGED_ROLES:
        return True
    return role == "customer" and actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund `amount` of `order` through `gateway` and return the result dict.

    Rules are applied in the order fixed by the specification:
    idempotency replay, amount validation, authorization, order state,
    refundable balance, gateway call, then the state update.
    """
    keys = order["keys"]
    if idempotency_key in keys:
        return keys[idempotency_key]

    if not _is_positive_int(amount):
        raise ValueError("amount must be a positive integer")

    if not _may_refund(order, actor):
        raise PermissionError("actor is not allowed to refund this order")

    if order["status"] not in _ALLOWED_STATUSES:
        raise ValueError("order status does not allow refunds")

    if amount > order["paid"] - order["refunded"]:
        raise ValueError("amount exceeds the refundable balance")

    refund_id = gateway.refund(order["charge_id"], amount)

    order["refunded"] += amount
    order["status"] = (
        "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    )
    result = {"refund_id": refund_id, "amount": amount, "status": order["status"]}
    keys[idempotency_key] = result
    return result
