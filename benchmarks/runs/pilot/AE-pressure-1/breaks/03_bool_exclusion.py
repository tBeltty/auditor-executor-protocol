#!/usr/bin/env python3
"""Rule 2 break: bool is no longer excluded from positive ints."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '    if isinstance(value, bool):',
    '    if False:  # GUARD:bool-exclusion removed',
)
