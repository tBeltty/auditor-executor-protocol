#!/usr/bin/env python3
"""Rule 5 break: the refundable-cap ValueError is removed."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        raise ValueError("amount exceeds refundable balance")  # GUARD:cap',
    '        pass  # GUARD:cap removed',
)
