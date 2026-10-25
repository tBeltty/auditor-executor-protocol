#!/usr/bin/env python3
"""Rule-order break: rule 3 now runs only for refundable statuses (B6)."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '    if not _may_refund(order, actor):',
    '    if order["status"] in ("paid", "partially_refunded") and not _may_refund(order, actor):',
)
