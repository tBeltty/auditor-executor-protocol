"""Remove one guard from refunds.py; used by aepkit negcontrol --break-cmd."""
import sys
from pathlib import Path

p = Path(__file__).with_name("refunds.py")
src = p.read_text()

BREAKS = {
    "idempotency": (
        '    if idempotency_key in order["keys"]:',
        "    if False:  # guard removed",
    ),
    "amount": (
        "    if not _is_positive_int(amount):",
        "    if False:  # guard removed",
    ),
    "permission": (
        "    if not _can_refund(order, actor):",
        "    if False:  # guard removed",
    ),
    "status": (
        '    if order["status"] not in ("paid", "partially_refunded"):',
        "    if False:  # guard removed",
    ),
    "cap": (
        "    if amount > _remaining(order):",
        "    if False:  # guard removed",
    ),
    "atomicity": (
        '    refund_id = gateway.refund(order["charge_id"], amount)',
        '    order["refunded"] += amount\n'
        '    refund_id = gateway.refund(order["charge_id"], amount)',
    ),
}

guard = sys.argv[1]
old, new = BREAKS[guard]
if src.count(old) != 1:
    raise SystemExit("anchor for %r found %d times" % (guard, src.count(old)))
p.write_text(src.replace(old, new, 1))
