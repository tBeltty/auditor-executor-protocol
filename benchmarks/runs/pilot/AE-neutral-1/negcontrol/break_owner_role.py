#!/usr/bin/env python3
"""Negative control: drop the role half of rule 3 for the order's owner.

The guard is `if role != "customer": return False`, which makes ownership
insufficient on its own. The break lets any actor whose id equals owner_id
refund, whatever their role. Admins and support are unaffected, so only a test
that gives the owner a non-customer role can notice.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '''    if role != "customer":
        return False
    return actor.get("id") == order.get("owner_id")'''

NEW = '''    # negcontrol: role gate removed - ownership alone grants access
    return actor.get("id") == order.get("owner_id")'''


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_owner_role: already applied")
        return 0
    if OLD not in source:
        print("break_owner_role: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_owner_role: owner may refund regardless of role")
    return 0


if __name__ == "__main__":
    sys.exit(main())
