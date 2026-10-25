"""Refund processing per specs/refunds.md."""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


_REFUNDABLE_STATUSES = ("paid", "partially_refunded")


def _is_valid_amount(amount):
    return isinstance(amount, int) and not isinstance(amount, bool) and amount > 0


def _is_allowed(actor, order):
    role = actor.get("role")
    if role in ("admin", "support"):
        return True
    return role == "customer" and actor.get("id") == order.get("owner_id")


def refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict:
    # 1. Idempotency: replay the stored result, do not call the gateway.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]

    # 2. Amount must be a positive int (bool is not an int here).
    if not _is_valid_amount(amount):
        raise ValueError("amount must be a positive int")

    # 3. Authorisation.
    if not _is_allowed(actor, order):
        raise PermissionError("actor may not refund this order")

    # 4. Status must allow refunds.
    if order["status"] not in _REFUNDABLE_STATUSES:
        raise ValueError("order is not refundable")

    # 5. Refundable cap.
    refundable = order["paid"] - order["refunded"]
    if amount > refundable:
        raise ValueError("amount exceeds refundable balance")

    # 6. Gateway call. Any failure leaves the order untouched (nothing has
    # been mutated yet) and propagates.
    refund_id = gateway.refund(order["charge_id"], amount)

    # 7. Success bookkeeping.
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
    order["keys"][idempotency_key] = result
    return result
