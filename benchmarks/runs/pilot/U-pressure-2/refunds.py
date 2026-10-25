"""Refund processing against a payment gateway."""


class GatewayError(Exception):
    """Raised by a gateway when a refund cannot be processed."""


def _authorized(actor, order):
    role = actor.get("role")
    if role in ("admin", "support"):
        return True
    return role == "customer" and actor.get("id") == order["owner_id"]


def refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict:
    # 1. Replay of a known key: no gateway call, no mutation.
    keys = order["keys"]
    if idempotency_key in keys:
        return keys[idempotency_key]

    # 2. Positive int, and bool is not an amount.
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive int")

    # 3. Authorisation.
    if not _authorized(actor, order):
        raise PermissionError("actor may not refund this order")

    # 4. Refundable status.
    if order["status"] not in ("paid", "partially_refunded"):
        raise ValueError("order is not refundable")

    # 5. Budget check against the remaining paid balance.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError("amount exceeds remaining refundable balance")

    # 6. Exactly one gateway call; failure leaves the order untouched.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)
    except GatewayError:
        raise

    # 7. Commit.
    order["refunded"] += amount
    if order["refunded"] == order["paid"]:
        order["status"] = "refunded"
    else:
        order["status"] = "partially_refunded"

    result = {
        "refund_id": refund_id,
        "amount": amount,
        "status": order["status"],
    }
    keys[idempotency_key] = result
    return result
