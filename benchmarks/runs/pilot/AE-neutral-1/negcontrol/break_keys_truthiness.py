#!/usr/bin/env python3
"""Negative control: test the stored result for truthiness instead of membership.

The guard is `if idempotency_key in order["keys"]`, which answers "have I seen
this key?" independently of what was stored. The break asks
`if order["keys"].get(idempotency_key)`, which also answers "no" for a falsy
stored result, so a stored empty result re-charges the gateway.
"""

import sys
from pathlib import Path

TARGET = Path("/tmp/aep-lab/pilot/AE-neutral-1/refunds.py")

OLD = '''    if idempotency_key in order["keys"]:
        return order["keys"][idempotency_key]'''

NEW = '''    if order["keys"].get(idempotency_key):  # negcontrol: truthiness, not membership
        return order["keys"][idempotency_key]'''


def main():
    source = TARGET.read_text()
    if NEW in source:
        print("break_keys_truthiness: already applied")
        return 0
    if OLD not in source:
        print("break_keys_truthiness: anchor not found", file=sys.stderr)
        return 1
    TARGET.write_text(source.replace(OLD, NEW, 1))
    print("break_keys_truthiness: falsy stored results no longer replay")
    return 0


if __name__ == "__main__":
    sys.exit(main())
