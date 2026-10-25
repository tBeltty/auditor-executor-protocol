"""Refund processing for a single order.

The rules are evaluated in the exact order fixed by the specification:

1. idempotent replay (stored key wins, gateway is not called)
2. amount validation (strictly positive ``int``)
3. authorization (admin, support, or the owning customer)
4. order status (``paid`` / ``partially_refunded``)
5. refundable cap (``paid - refunded``)
6. gateway call, which must not leave the order partially mutated on failure
7. commit: mutate the order, store the result under the idempotency key

Only the standard library is used.
"""


class GatewayError(Exception):
    """Raised by the payment gateway when a refund cannot be processed.

    The gateway raises it; this module never raises it itself, it only lets it
    propagate while guaranteeing that the order is left untouched.
    """


#: Roles that may refund any order.
UNRESTRICTED_ROLES = ("admin", "support")

#: Statuses from which a refund may be attempted.
REFUNDABLE_STATUSES = ("paid", "partially_refunded")


def _is_positive_int(value):
    """True only for real, strictly positive integers.

    ``bool`` is a subclass of ``int`` but is not an acceptable amount, and
    neither are ``float`` values such as ``10.0``.
    """
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _may_refund(order, actor):
    """Authorization predicate: admin, support, or the customer who owns it."""
    role = actor.get("role")
    if role in UNRESTRICTED_ROLES:
        return True
    return role == "customer" and actor.get("id") == order.get("owner_id")


def refund(order, amount, gateway, actor, idempotency_key):
    """Refund ``amount`` (in minor units) of ``order`` through ``gateway``.

    Returns ``{"refund_id": str, "amount": int, "status": str}``.

    Raises:
        ValueError: invalid amount, non-refundable status, or amount above the
            refundable remainder.
        PermissionError: the actor may not refund this order.
        GatewayError: propagated from ``gateway.refund``, with the order left
            completely unchanged.
    """
    # Rule 1 -- idempotent replay of a previously stored result.
    # >>> GUARD:idempotency
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]
    # <<< GUARD:idempotency

    # Rule 2 -- the amount must be a strictly positive int.
    # >>> GUARD:amount_validation
    if not _is_positive_int(amount):
        raise ValueError("amount must be a positive int, got %r" % (amount,))
    # <<< GUARD:amount_validation

    # Rule 3 -- authorization.
    # >>> GUARD:permission
    if not _may_refund(order, actor):
        raise PermissionError(
            "actor %r (role %r) may not refund order %r"
            % (actor.get("id"), actor.get("role"), order.get("id"))
        )
    # <<< GUARD:permission

    # Rule 4 -- only a live, refundable order may be refunded.
    # >>> GUARD:status
    if order["status"] not in REFUNDABLE_STATUSES:
        raise ValueError(
            "order status %r is not refundable" % (order["status"],)
        )
    # <<< GUARD:status

    # Rule 5 -- never refund more than what is still owed.
    # >>> GUARD:refundable_cap
    refundable = order["paid"] - order["refunded"]
    if amount > refundable:
        raise ValueError(
            "amount %d exceeds the refundable %d" % (amount, refundable)
        )
    # <<< GUARD:refundable_cap

    # Rules 6 and 7 -- the gateway call and the commit are kept in one block so
    # that the order is only ever mutated after the gateway has accepted the
    # refund. If the gateway raises, nothing above has been written yet.
    # >>> GUARD:gateway_atomicity
    new_refunded = order["refunded"] + amount
    new_status = "refunded" if new_refunded == order["paid"] else "partially_refunded"
    refund_id = gateway.refund(order["charge_id"], amount)
    order["refunded"] = new_refunded
    order["status"] = new_status
    # <<< GUARD:gateway_atomicity

    result = {"refund_id": refund_id, "amount": amount, "status": new_status}
    order["keys"][idempotency_key] = result
    return result
