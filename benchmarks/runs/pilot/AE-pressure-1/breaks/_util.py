"""Shared helper for the aepkit negcontrol break scripts.

Each script removes exactly one protection from refunds.py by an exact string
replacement. The anchor must occur exactly once, otherwise the script aborts
loudly instead of silently breaking nothing.
"""

import pathlib

REFUNDS = pathlib.Path("/tmp/aep-lab/pilot/AE-pressure-1/refunds.py")


def mutate(old, new):
    src = REFUNDS.read_text()
    count = src.count(old)
    assert count == 1, "break anchor found %d times (want 1): %r" % (count, old)
    REFUNDS.write_text(src.replace(old, new))
