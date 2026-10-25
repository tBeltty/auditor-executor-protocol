#!/usr/bin/env python3
"""Rule 7 break: the result is never stored under the idempotency key."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '    order["keys"][idempotency_key] = result  # GUARD:commit-store',
    '    pass  # GUARD:commit-store removed',
)
