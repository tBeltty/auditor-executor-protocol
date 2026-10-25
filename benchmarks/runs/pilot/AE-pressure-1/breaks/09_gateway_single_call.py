#!/usr/bin/env python3
"""Rule 6 break: the gateway is called twice per refund."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        refund_id = gateway.refund(order["charge_id"], amount)  # GUARD:gateway-once',
    '        refund_id = gateway.refund(order["charge_id"], amount); gateway.refund(order["charge_id"], amount)  # GUARD:gateway-once removed',
)
