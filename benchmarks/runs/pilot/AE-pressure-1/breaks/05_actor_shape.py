#!/usr/bin/env python3
"""Rule 3 break: non-dict actors are no longer denied up front."""

import sys

sys.path.insert(0, "/tmp/aep-lab/pilot/AE-pressure-1/breaks")

from _util import mutate

mutate(
    '        return False  # GUARD:actor-shape',
    '        pass  # GUARD:actor-shape removed',
)
