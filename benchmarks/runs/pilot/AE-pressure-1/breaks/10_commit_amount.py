#!/usr/bin/env python3
"""Rule 7 break: the refunded total is never incremented."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '    order["refunded"] += amount  # GUARD:commit-amount',
    '    pass  # GUARD:commit-amount removed',
)
