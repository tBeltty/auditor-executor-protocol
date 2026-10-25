class GatewayError(Exception):
    pass

def refund(order, amount, gateway, actor, idempotency_key):
    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]
    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
        raise ValueError("amount must be a positive int")
    owner = actor.get("role") == "customer" and actor.get("id") == order["owner_id"]
    if actor.get("role") not in ("admin", "support") and not owner:
        raise PermissionError("not allowed")
    if order["status"] not in ("paid", "partially_refunded"):
        raise ValueError("order not refundable")
    if amount > order["paid"] - order["refunded"]:
        raise ValueError("exceeds refundable amount")
    rid = gateway.refund(order["charge_id"], amount)
    order["refunded"] += amount
    order["status"] = "refunded" if order["refunded"] == order["paid"] else "partially_refunded"
    result = {"refund_id": rid, "amount": amount, "status": order["status"]}
    order["keys"][idempotency_key] = result
    return result
