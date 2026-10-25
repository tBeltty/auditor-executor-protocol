"""Refund processing for a single order (spec: refunds.md, module ``refunds.py``).

The public entry point is :func:`refund`. The seven rules are applied in the
order the specification lists them, so an earlier rule always wins over a later
one (a replayed idempotency key never re-validates anything, a bad amount is
reported before a permission problem, and so on).

Each rule lives in its own small helper: the ordering stays readable in one
screen and every guard can be pointed at individually.
"""

REFUNDABLE_STATUSES = ("paid", "partially_refunded")
STAFF_ROLES = ("admin", "support")

_MISSING = object()


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be applied."""


def refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict:
    """Refund ``amount`` from ``order`` and return the recorded result.

    Returns ``{"refund_id": str, "amount": int, "status": str}`` and stores it in
    ``order["keys"][idempotency_key]``. Raises ``ValueError`` for an invalid
    amount, an unrefundable status or an amount above the refundable balance,
    ``PermissionError`` for an actor that may not refund, and ``GatewayError``
    (with the order untouched) when the gateway refuses the refund.
    """
    stored = _stored_result(order, idempotency_key)
    if stored is not _MISSING:
        return stored

    _require_positive_int(amount)
    _require_permission(actor, order)
    _require_refundable_status(order)
    _require_within_refundable(order, amount)

    # The gateway is called before anything on the order is written, so a
    # GatewayError leaves the order untouched by construction. If the call
    # raises, nothing below runs and the exception propagates unchanged.
    refund_id = _charge(gateway, order["charge_id"], amount)

    return _record(order, amount, refund_id, idempotency_key)


def _stored_result(order, idempotency_key):
    """Rule 1: a replayed key returns the stored result, gateway untouched."""
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]
    return _MISSING


def _is_positive_int(value):
    # bool is a subclass of int, so it has to be excluded explicitly.
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _require_positive_int(amount):
    """Rule 2: the amount is a positive int, and nothing else."""
    if not _is_positive_int(amount):
        raise ValueError(f"amount must be a positive int, got {amount!r}")


def _may_refund(actor, order):
    if actor.get("role") in STAFF_ROLES:
        return True
    return actor.get("role") == "customer" and actor.get("id") == order["owner_id"]


def _require_permission(actor, order):
    """Rule 3: staff may refund any order, a customer only their own."""
    if _may_refund(actor, order):
        return
    raise PermissionError(f"actor {actor.get('id')!r} may not refund this order")


def _require_refundable_status(order):
    """Rule 4: only paid and partially refunded orders can be refunded."""
    if order["status"] not in REFUNDABLE_STATUSES:
        raise ValueError(f"order status {order['status']!r} is not refundable")


def _require_within_refundable(order, amount):
    """Rule 5: the refund may not exceed what is still refundable."""
    remaining = order["paid"] - order["refunded"]
    if amount > remaining:
        raise ValueError(
            f"amount {amount} exceeds refundable balance {remaining}"
        )


def _charge(gateway, charge_id, amount):
    """Rule 6: one gateway call; GatewayError propagates unchanged."""
    return gateway.refund(charge_id, amount)


def _record(order, amount, refund_id, idempotency_key):
    """Rule 7: apply the successful refund and memoize its result."""
    order["refunded"] += amount
    order["status"] = (
        "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    )
    result = {
        "refund_id": refund_id,
        "amount": amount,
        "status": order["status"],
    }
    order["keys"][idempotency_key] = result
    return result
