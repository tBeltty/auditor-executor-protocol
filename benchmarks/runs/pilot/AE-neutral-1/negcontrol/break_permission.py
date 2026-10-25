#!/usr/bin/env python3
"""Negative control: remove the permission guard (rule 3)."""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")
OLD = "    if not _actor_may_refund(order, actor):"
NEW = "    if False:  # negcontrol: permission check removed"


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_permission: already applied")
        return 0
    if OLD not in source:
        print("break_permission: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_permission: authorisation check disabled")
    return 0


if __name__ == "__main__":
    sys.exit(main())
