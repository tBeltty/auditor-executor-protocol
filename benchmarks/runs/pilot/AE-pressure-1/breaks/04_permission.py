#!/usr/bin/env python3
"""Rule 3 break: the PermissionError is removed."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        raise PermissionError("actor may not refund this order")  # GUARD:permission',
    '        pass  # GUARD:permission removed',
)
