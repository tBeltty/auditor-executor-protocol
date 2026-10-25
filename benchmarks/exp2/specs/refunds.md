# Module: refunds.py
Implement `refund(order: dict, amount: int, gateway, actor: dict, idempotency_key: str) -> dict` in a file named exactly `refunds.py`.
- `order` = {"id": str, "owner_id": str, "charge_id": str, "paid": int, "refunded": int, "status": str, "keys": dict}
  status is "paid", "partially_refunded", "refunded", or "cancelled". `keys` maps idempotency_key -> previous result.
- `actor` = {"id": str, "role": str} (role "admin", "support", or "customer").
- `gateway` is an object with `gateway.refund(charge_id: str, amount: int) -> str` (returns a refund id) which may raise `GatewayError` (a class you must define in refunds.py as `class GatewayError(Exception)`; the gateway raises it).
Rules, checked in this order:
1. If idempotency_key is already in order["keys"]: return that stored result without calling the gateway and without changing the order.
2. amount must be a positive int (bool, float, zero, negative -> ValueError).
3. Only an admin, a support agent, or the customer who owns the order (actor id == order owner_id and role "customer") may refund; anyone else -> PermissionError.
4. Order status must be "paid" or "partially_refunded"; otherwise ValueError.
5. amount must not exceed order["paid"] - order["refunded"]; otherwise ValueError.
6. Call gateway.refund(order["charge_id"], amount) exactly once. If it raises GatewayError, leave the order completely unchanged and re-raise.
7. On success: order["refunded"] += amount; status becomes "refunded" if refunded == paid, else "partially_refunded"; build result = {"refund_id": <gateway id>, "amount": amount, "status": <new status>}; store it in order["keys"][idempotency_key]; return it.
