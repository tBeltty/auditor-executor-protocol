"""Refund domain logic.

Implements ``refund`` as specified in specs/refunds.md.
"""


class GatewayError(Exception):
    """Raised by a payment gateway when a refund call fails."""


_ALLOWED_ROLES = ("admin", "support")


def _validate_amount(amount):
    # bool is a subclass of int, but it is not an acceptable amount.
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise ValueError("amount must be a positive int")
    if amount <= 0:
        raise ValueError("amount must be a positive int")


def _check_permission(order, actor):
    role = actor.get("role") if isinstance(actor, dict) else None
    actor_id = actor.get("id") if isinstance(actor, dict) else None

    if role in _ALLOWED_ROLES:
        return
    if role == "customer" and actor_id == order.get("owner_id"):
        return
    raise PermissionError("actor is not allowed to refund this order")


def refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict:
    """Refund ``amount`` from ``order`` through ``gateway``.

    Rules are applied in the order given by the spec.
    """
    # 1. Idempotent replay: return the stored result untouched.
    keys = order["keys"]
    if idempotency_key in keys:
        return keys[idempotency_key]

    # 2. Amount validation.
    _validate_amount(amount)

    # 3. Authorization.
    _check_permission(order, actor)

    # 4. Status must allow refunds.
    if order["status"] not in ("paid", "partially_refunded"):
        raise ValueError("order is not refundable in status %r" % (order["status"],))

    # 5. Never refund more than what is still owed back.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError("amount exceeds refundable balance")

    # 6. Exactly one gateway call; a failure leaves the order untouched.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)
    except GatewayError:
        raise

    # 7. Commit the refund.
    order["refunded"] += amount
    new_status = "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    order["status"] = new_status
    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    keys[idempotency_key] = result
    return result
