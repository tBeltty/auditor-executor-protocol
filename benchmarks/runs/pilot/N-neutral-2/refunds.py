"""Refund processing.

Implements the contract described in specs/refunds.md.
"""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


_ALLOWED_STATUSES = ("paid", "partially_refunded")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund ``amount`` for ``order`` through ``gateway``.

    Returns ``{"refund_id", "amount", "status"}`` and records the result under
    ``idempotency_key``.  Raises ValueError for bad input, PermissionError for
    unauthorized actors and re-raises GatewayError without touching the order.
    """
    # Rule 1: a repeated key returns the stored result, no gateway call.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # Rule 2: amount must be a positive int (bool and float are rejected).
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive int")

    # Rule 3: admins, support agents and the owning customer may refund.
    role = actor.get("role")
    authorized = role in ("admin", "support") or (
        role == "customer" and actor.get("id") == order["owner_id"]
    )
    if not authorized:
        raise PermissionError("actor is not allowed to refund this order")

    # Rule 4: only paid or partially refunded orders can be refunded.
    if order["status"] not in _ALLOWED_STATUSES:
        raise ValueError("order status %r is not refundable" % (order["status"],))

    # Rule 5: never refund more than the remaining paid amount.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError("amount exceeds refundable remainder")

    # Rule 6: call the gateway exactly once.  The order is mutated only after
    # the call succeeds, so a GatewayError leaves it completely unchanged.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)
    except GatewayError:
        raise

    # Rule 7: commit the refund.
    order["refunded"] += amount
    if order["refunded"] == order["paid"]:
        new_status = "refunded"
    else:
        new_status = "partially_refunded"
    order["status"] = new_status
    result = {
        "refund_id": refund_id,
        "amount": amount,
        "status": new_status,
    }
    order["keys"][idempotency_key] = result
    return result
