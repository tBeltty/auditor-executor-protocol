"""Refund handling for paid orders."""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


_REFUNDABLE_STATUSES = ("paid", "partially_refunded")


def _is_positive_int(amount):
    return isinstance(amount, int) and not isinstance(amount, bool) and amount > 0


def _may_refund(order, actor):
    role = actor.get("role")
    if role == "admin" or role == "support":
        return True
    if role == "customer" and actor.get("id") == order.get("owner_id"):
        return True
    return False


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund `amount` from `order` through `gateway`.

    Returns a result dict describing the refund, or the previously stored
    result when `idempotency_key` has already been used for this order.
    """
    # 1. Idempotent replay: return the stored result untouched.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # 2. Amount must be a genuine positive int (bool is not an amount).
    if not _is_positive_int(amount):
        raise ValueError("amount must be a positive int")

    # 3. Only admins, support agents, or the owning customer may refund.
    if not _may_refund(order, actor):
        raise PermissionError("actor may not refund this order")

    # 4. Only paid / partially refunded orders are refundable.
    if order["status"] not in _REFUNDABLE_STATUSES:
        raise ValueError("order is not refundable in status %r" % (order["status"],))

    # 5. Never refund more than what is still owed.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError("amount exceeds remaining refundable balance")

    # 6. Single gateway call; a failure leaves the order completely unchanged.
    refund_id = gateway.refund(order["charge_id"], amount)

    # 7. Commit the mutation only after the gateway succeeded.
    new_refunded = order["refunded"] + amount
    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"
    result = {"refund_id": refund_id, "amount": amount, "status": new_status}

    order["refunded"] = new_refunded
    order["status"] = new_status
    order["keys"][idempotency_key] = result
    return result
