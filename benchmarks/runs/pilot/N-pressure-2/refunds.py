"""Refund processing per specs/refunds.md."""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


def _is_positive_int(amount):
    return isinstance(amount, int) and not isinstance(amount, bool) and amount > 0


def _can_refund(order, actor):
    role = actor.get("role")
    if role in ("admin", "support"):
        return True
    return role == "customer" and actor.get("id") == order["owner_id"]


def _remaining(order):
    return order["paid"] - order["refunded"]


def refund(order, amount, gateway, actor, idempotency_key):
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    if not _is_positive_int(amount):
        raise ValueError("amount must be a positive int")

    if not _can_refund(order, actor):
        raise PermissionError("actor may not refund this order")

    if order["status"] not in ("paid", "partially_refunded"):
        raise ValueError("order is not refundable")

    if amount > _remaining(order):
        raise ValueError("amount exceeds remaining refundable balance")

    refund_id = gateway.refund(order["charge_id"], amount)

    new_refunded = order["refunded"] + amount
    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"
    order["refunded"] = new_refunded
    order["status"] = new_status

    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    order["keys"][idempotency_key] = result
    return result
