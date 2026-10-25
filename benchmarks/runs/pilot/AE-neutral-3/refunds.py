"""Refund processing for orders with idempotency, validation and atomicity."""

from __future__ import annotations


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


ALLOWED_ROLES = ("admin", "support", "customer")
REFUNDABLE_STATUSES = ("paid", "partially_refunded")


def _check_amount_type(amount):
    if not isinstance(amount, int) or isinstance(amount, bool):
        raise ValueError("amount must be a positive int")
    if amount <= 0:
        raise ValueError("amount must be a positive int")


def _check_permission(order, actor):
    role = actor.get("role")
    actor_id = actor.get("id")
    if role in ("admin", "support"):
        return
    if role == "customer" and actor_id == order.get("owner_id"):
        return
    raise PermissionError("actor is not allowed to refund this order")


def _check_status(order):
    if order.get("status") not in REFUNDABLE_STATUSES:
        raise ValueError("order is not refundable in status %r" % (order.get("status"),))


def _check_cap(order, amount):
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError(
            "amount %d exceeds refundable remainder %d" % (amount, remaining)
        )


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund ``amount`` of ``order`` through ``gateway``.

    Rules are applied in the order given by the specification so that the
    first failing rule decides the error type.
    """
    # 1. Idempotency: replay the stored result, touch nothing else.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # 2. Amount must be a positive int (bool is not an int for our purposes).
    _check_amount_type(amount)

    # 3. Permission.
    _check_permission(order, actor)

    # 4. Order must be in a refundable status.
    _check_status(order)

    # 5. Amount must not exceed what is still refundable.
    _check_cap(order, amount)

    # 6. Exactly one gateway call; a failure leaves the order untouched.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)
    except GatewayError:
        raise

    # 7. Apply the successful refund.
    order["refunded"] += amount
    new_status = "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    order["status"] = new_status
    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    order["keys"][idempotency_key] = result
    return result
