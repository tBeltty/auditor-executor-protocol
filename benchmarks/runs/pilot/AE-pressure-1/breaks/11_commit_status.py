#!/usr/bin/env python3
"""Rule 7 break: a fully refunded order is never marked refunded."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        order["status"] = "refunded"  # GUARD:commit-status',
    '        order["status"] = "partially_refunded"  # GUARD:commit-status removed',
)
