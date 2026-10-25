#!/usr/bin/env python3
"""Rule-order break: rule 1 now runs only for refundable statuses (B7)."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '    if idempotency_key in order["keys"]:',
    '    if order["status"] in ("paid", "partially_refunded") and idempotency_key in order["keys"]:',
)
