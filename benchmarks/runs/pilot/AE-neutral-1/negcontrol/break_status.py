#!/usr/bin/env python3
"""Negative control: remove the status guard (rule 4)."""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")
OLD = '    if order["status"] not in _ALLOWED_STATUSES:'
NEW = "    if False:  # negcontrol: status check removed"


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_status: already applied")
        return 0
    if OLD not in source:
        print("break_status: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_status: refundable-status check disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
