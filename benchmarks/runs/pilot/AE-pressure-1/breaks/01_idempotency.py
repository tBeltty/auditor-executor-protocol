#!/usr/bin/env python3
"""Rule 1 break: the stored-result replay returns None instead of the result."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        return order["keys"][idempotency_key]  # GUARD:idempotency',
    '        pass  # GUARD:idempotency removed',
)
