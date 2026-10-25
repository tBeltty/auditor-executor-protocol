#!/usr/bin/env python3
"""Negative control: remove the amount-validation guard (rule 2)."""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")
OLD = "    if not _is_positive_int(amount):"
NEW = "    if False:  # negcontrol: amount validation removed"


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_amount: already applied")
        return 0
    if OLD not in source:
        print("break_amount: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_amount: positive-int check disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
