"""Refund processing module.

Implements a single public entry point, :func:`refund`, which validates the
request, delegates the money movement to the payment gateway exactly once, and
mutates the order only after the gateway succeeds.
"""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed."""


def _validate_amount(amount):
    # bool is a subclass of int, but True/False are not valid amounts.
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise ValueError("amount must be a positive int")
    if amount <= 0:
        raise ValueError("amount must be a positive int")


def _authorize(order, actor):
    role = actor.get("role")
    if role in ("admin", "support"):
        return
    if role == "customer" and actor.get("id") == order.get("owner_id"):
        return
    raise PermissionError("actor is not allowed to refund this order")


def refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict:
    """Refund ``amount`` from ``order`` via ``gateway``.

    The order is left untouched on any validation failure or gateway error.
    """
    # 1. Replay of an already-processed key: return the stored result as-is.
    keys = order["keys"]
    if idempotency_key in keys:
        return keys[idempotency_key]

    # 2. Amount must be a positive int (bool/float/zero/negative are rejected).
    _validate_amount(amount)

    # 3. Authorization.
    _authorize(order, actor)

    # 4. Refundable status.
    if order["status"] not in ("paid", "partially_refunded"):
        raise ValueError("order is not refundable in status %r" % (order["status"],))

    # 5. Cannot refund more than remains.
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError("amount exceeds refundable remainder")

    # 6. Gateway call happens exactly once, before any local mutation.
    refund_id = gateway.refund(order["charge_id"], amount)

    # 7. Commit the result.
    order["refunded"] += amount
    new_status = "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    order["status"] = new_status

    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    keys[idempotency_key] = result
    return result
