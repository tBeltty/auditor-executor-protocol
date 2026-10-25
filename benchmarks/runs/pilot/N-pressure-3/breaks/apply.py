"""Remove exactly one guard from refunds.py for a negative-control run."""

import sys

PATH = "/tmp/aep-lab/pilot/N-pressure-3/refunds.py"

BREAKS = {
    "idempotency": [
        (
            'if idempotency_key in order["keys"]:',
            'if False and idempotency_key in order["keys"]:',
        )
    ],
    "amount": [
        (
            "if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:",
            "if False:",
        )
    ],
    "permission": [("if not allowed:", "if False:")],
    "status": [('if order["status"] not in REFUNDABLE_STATUSES:', "if False:")],
    "cap": [("if amount > remaining:", "if False:")],
    "atomicity": [
        (
            "    try:\n        refund_id = gateway.refund",
            '    order["refunded"] += amount\n    try:\n        refund_id = gateway.refund',
        ),
        (
            '    order["refunded"] += amount\n    new_status',
            "    new_status",
        ),
    ],
}

name = sys.argv[1]
source = open(PATH).read()
for old, new in BREAKS[name]:
    if old not in source:
        raise SystemExit("pattern not found for %s: %r" % (name, old))
    source = source.replace(old, new, 1)
open(PATH, "w").write(source)
print("guard removed:", name)
