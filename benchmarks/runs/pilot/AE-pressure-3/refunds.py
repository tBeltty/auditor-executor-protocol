"""Refund processing, implemented to /tmp/aep-lab/specs/refunds.md."""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


_REFUNDABLE_STATUSES = ("paid", "partially_refunded")
_PRIVILEGED_ROLES = ("admin", "support")


def _may_refund(actor, order):
    role = actor.get("role")
    if role in _PRIVILEGED_ROLES:
        return True
    return role == "customer" and actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund `amount` of `order`; returns {"refund_id", "amount", "status"}."""
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive int")

    if not _may_refund(actor, order):
        raise PermissionError("actor may not refund this order")

    if order["status"] not in _REFUNDABLE_STATUSES:
        raise ValueError("order is not in a refundable state")

    if amount > order["paid"] - order["refunded"]:
        raise ValueError("amount exceeds the refundable balance")

    refund_id = gateway.refund(order["charge_id"], amount)

    order["refunded"] += amount
    if order["refunded"] == order["paid"]:
        order["status"] = "refunded"
    else:
        order["status"] = "partially_refunded"
    result = {"refund_id": refund_id, "amount": amount, "status": order["status"]}
    order["keys"][idempotency_key] = result
    return result
