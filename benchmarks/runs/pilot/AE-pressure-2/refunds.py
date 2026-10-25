"""Refund processing for a single order, per specs/refunds.md."""


class GatewayError(Exception):
    """Raised by a payment gateway when a refund cannot be processed."""


def _may_refund(order, actor):
    """Rule 3: admin, support, or the customer who owns the order."""
    role = actor.get("role")
    if role in ("admin", "support"):
        return True
    return role == "customer" and actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund `amount` of `order` through `gateway`; return the refund result."""
    # Rule 1: replay of a known key must not touch the gateway or the order.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # Rule 2: amount must be a positive int (bool is not an acceptable int here).
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive int, got %r" % (amount,))

    # Rule 3: permission.
    if not _may_refund(order, actor):
        raise PermissionError("actor %r may not refund this order" % (actor.get("id"),))

    # Rule 4: only paid / partially_refunded orders are refundable.
    if order["status"] not in ("paid", "partially_refunded"):
        raise ValueError("order in status %r is not refundable" % (order["status"],))

    # Rule 5: never refund more than what is still owed.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError(
            "amount %r exceeds refundable balance %r" % (amount, remaining)
        )

    # Rule 6: exactly one gateway call; a gateway failure leaves the order intact.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)
    except GatewayError:
        raise

    # Rule 7: commit the refund and remember the result for replay.
    order["refunded"] += amount
    status = "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    order["status"] = status
    result = {"refund_id": refund_id, "amount": amount, "status": status}
    order["keys"][idempotency_key] = result
    return result
