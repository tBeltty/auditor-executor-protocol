"""Refund processing with idempotency, validation, permissions and atomicity."""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund call fails."""


REFUNDABLE_STATUSES = ("paid", "partially_refunded")


def refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict:
    """Refund ``amount`` from ``order`` through ``gateway``.

    Guards run in the order fixed by the spec: idempotency, amount type,
    permission, order status, refundable cap, then the gateway call. The order
    is only mutated after the gateway succeeds, so a GatewayError leaves it
    untouched.
    """
    # 1. Idempotent replay: return the stored result and touch nothing.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # 2. amount must be a positive int (bool is not an acceptable int here).
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive integer")

    # 3. admin / support / the owning customer may refund.
    allowed = actor["role"] in ("admin", "support") or (
        actor["role"] == "customer" and actor["id"] == order["owner_id"]
    )
    if not allowed:
        raise PermissionError("actor is not allowed to refund this order")

    # 4. Only paid or partially refunded orders can be refunded.
    if order["status"] not in REFUNDABLE_STATUSES:
        raise ValueError("order status is not refundable")

    # 5. Never refund more than what is still refundable.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError("amount exceeds the refundable balance")

    # 6. Exactly one gateway call; nothing is mutated before it succeeds.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)
    except GatewayError:
        raise

    # 7. Commit.
    order["refunded"] += amount
    new_status = "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    order["status"] = new_status
    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    order["keys"][idempotency_key] = result
    return result
