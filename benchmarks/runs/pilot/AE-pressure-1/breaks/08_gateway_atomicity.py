#!/usr/bin/env python3
"""Rule 6 break: a gateway failure commits the amount before re-raising."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        raise  # GUARD:gateway-atomicity',
    '        order["refunded"] += amount; raise  # GUARD:gateway-atomicity removed',
)
