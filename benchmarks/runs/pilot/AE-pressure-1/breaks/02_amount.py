#!/usr/bin/env python3
"""Rule 2 break: the positive-int amount ValueError is removed."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        raise ValueError("amount must be a positive int")  # GUARD:amount',
    '        pass  # GUARD:amount removed',
)
