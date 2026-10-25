"""Refund processing for a single order.

Implements the contract in specs/refunds.md. Every business guard -- and every
step of the rule-7 commit -- is marked ``GUARD:<name>`` so that each protection
can be removed in isolation by an ``aepkit negcontrol`` break command
(see ``breaks/`` for the one script per control).
"""


class GatewayError(Exception):
    """Raised by a payment gateway when a refund call fails."""


def _is_positive_int(value):
    """True for ints > 0, excluding bool (bool is an int subclass)."""
    if isinstance(value, bool):
        return False  # GUARD:bool-exclusion
    return isinstance(value, int) and value > 0


def _may_refund(order, actor):
    """True if the actor is an admin, support agent, or the owning customer."""
    if not isinstance(actor, dict):
        return False  # GUARD:actor-shape
    role = actor.get("role")
    if role in ("admin", "support"):
        return True
    return role == "customer" and actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund ``amount`` from ``order`` and return the stored result dict."""

    # Rule 1: replay a previously stored result without touching the gateway.
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]  # GUARD:idempotency

    # Rule 2: amount must be a strictly positive int (bool/float rejected).
    if not _is_positive_int(amount):
        raise ValueError("amount must be a positive int")  # GUARD:amount

    # Rule 3: only admin, support, or the owning customer may refund.
    if not _may_refund(order, actor):
        raise PermissionError("actor may not refund this order")  # GUARD:permission

    # Rule 4: only paid / partially_refunded orders are refundable.
    if order["status"] not in ("paid", "partially_refunded"):
        raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status

    # Rule 5: never refund more than the remaining paid balance.
    if amount > order["paid"] - order["refunded"]:
        raise ValueError("amount exceeds refundable balance")  # GUARD:cap

    # Rule 6: exactly one gateway call; a failure must leave the order intact.
    try:
        refund_id = gateway.refund(order["charge_id"], amount)  # GUARD:gateway-once
    except GatewayError:
        raise  # GUARD:gateway-atomicity

    # Rule 7: commit the refund only after the gateway succeeded.
    order["refunded"] += amount  # GUARD:commit-amount
    if order["refunded"] == order["paid"]:
        order["status"] = "refunded"  # GUARD:commit-status
    else:
        order["status"] = "partially_refunded"
    result = {
        "refund_id": refund_id,
        "amount": amount,
        "status": order["status"],
    }
    order["keys"][idempotency_key] = result  # GUARD:commit-store
    return result
