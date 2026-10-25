#!/usr/bin/env python3
"""Rule 4 break: the non-refundable-status ValueError is removed."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        raise ValueError("order is not refundable in status %r" % (order["status"],))  # GUARD:status',
    '        pass  # GUARD:status removed',
)
