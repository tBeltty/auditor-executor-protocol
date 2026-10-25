"""Negative-control breaker for the gateway-failure atomicity guard.

Rewrites the gateway call so a GatewayError still propagates but the order is
mutated first, i.e. the refund is applied even though the gateway failed.
"""

import pathlib

TARGET = pathlib.Path(__file__).with_name("refunds.py")
OLD = '    refund_id = gateway.refund(order["charge_id"], amount)\n'
NEW = (
    "    try:\n"
    '        refund_id = gateway.refund(order["charge_id"], amount)\n'
    "    except GatewayError:\n"
    '        order["refunded"] += amount\n'
    '        order["status"] = "partially_refunded"\n'
    "        raise\n"
)

source = TARGET.read_text()
if OLD not in source:
    raise SystemExit("break point not found")
TARGET.write_text(source.replace(OLD, NEW, 1))
