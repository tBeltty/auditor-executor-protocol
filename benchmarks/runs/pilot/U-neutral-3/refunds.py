"""Refund handling for orders, with idempotency, permission and balance checks."""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


_ALLOWED_STATUSES = ("paid", "partially_refunded")


def _is_legitimate_amount(amount) -> bool:
    """True only for a real, positive int (bools are not amounts)."""
    if isinstance(amount, bool):
        return False
    if not isinstance(amount, int):
        return False
    return amount > 0


def _is_authorised(actor, order) -> bool:
    role = actor.get("role")
    if role in ("admin", "support"):
        return True
    if role == "customer" and actor.get("id") == order.get("owner_id"):
        return True
    return False


def refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict:
    """Refund `amount` of `order` through `gateway`.

    Checks run in the order mandated by the specification, so an idempotent
    replay short-circuits everything else.
    """
    keys = order["keys"]

    # 1. Idempotent replay: never touch the gateway or the order.
    if idempotency_key in keys:
        return keys[idempotency_key]

    # 2. Amount must be a positive int.
    if not _is_legitimate_amount(amount):
        raise ValueError("amount must be a positive int")

    # 3. Only admins, support agents, or the owning customer may refund.
    if not _is_authorised(actor, order):
        raise PermissionError("actor is not allowed to refund this order")

    # 4. Only refundable statuses.
    if order["status"] not in _ALLOWED_STATUSES:
        raise ValueError("order is not in a refundable state: %r" % (order["status"],))

    # 5. Cannot refund more than remains.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError("amount exceeds refundable balance")

    # 6. Exactly one gateway call; on failure the order stays untouched.
    refund_id = gateway.refund(order["charge_id"], amount)

    # 7. Commit the refund.
    order["refunded"] = order["refunded"] + amount
    if order["refunded"] == order["paid"]:
        order["status"] = "refunded"
    else:
        order["status"] = "partially_refunded"

    result = {"refund_id": refund_id, "amount": amount, "status": order["status"]}
    keys[idempotency_key] = result
    return result
