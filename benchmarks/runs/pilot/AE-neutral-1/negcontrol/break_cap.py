#!/usr/bin/env python3
"""Negative control: remove the refundable-cap guard (rule 5)."""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")
OLD = "    if amount > remaining:"
NEW = "    if False:  # negcontrol: refundable cap removed"


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_cap: already applied")
        return 0
    if OLD not in source:
        print("break_cap: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_cap: paid-minus-refunded cap disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
