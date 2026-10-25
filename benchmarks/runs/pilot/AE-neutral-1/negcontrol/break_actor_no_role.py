#!/usr/bin/env python3
"""Negative control: make a missing actor role fail open.

The guard is `role = actor.get("role")`, which yields None for an actor that
carries no role, and None is neither privileged nor "customer", so the request
is denied. The break defaults the role to "admin", so an actor dict with only
an id - or with nothing at all - is treated as privileged.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '    role = actor.get("role")'
NEW = '    role = actor.get("role", "admin")  # negcontrol: missing role defaults to admin'


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_actor_no_role: already applied")
        return 0
    if OLD not in source:
        print("break_actor_no_role: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_actor_no_role: missing role defaults to admin")
    return 0


if __name__ == "__main__":
    sys.exit(main())
