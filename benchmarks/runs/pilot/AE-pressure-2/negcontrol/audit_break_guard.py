"""Auditor-side negative controls: remove one guard the Executor never controlled.

Companion to `break_guard.py` (Executor's six controls). Each entry removes a
*finer-grained* protection than the Executor's coarse control for that rule, or
probes an ordering/boundary guarantee that has no test at all. The target text
must appear exactly once, so a control can never pass by breaking nothing.

Usage: python3 audit_break_guard.py <name>
Exit status 1 if the anchor is missing/ambiguous; 2 on bad usage.
"""

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().parent.parent / "refunds.py"

# Two-step breaks are expressed as a tuple of (old, new) pairs applied in order.
BREAKS = {
    # Rule 3: the "customer who owns the order" half of the permission test.
    "rule3-owner-only": (
        (
            '    return role == "customer" and actor.get("id") == order.get("owner_id")\n',
            '    return role == "customer"\n',
        ),
    ),
    # Rule 2: the bool half of the "positive int" test (True/False are ints in Python).
    "rule2-bool": (
        (
            "    if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:\n",
            "    if not isinstance(amount, int) or amount <= 0:\n",
        ),
    ),
    # Rule 7: remembering the result for replay (the key store, which rule 1 reads).
    "rule7-store": (
        (
            '    order["keys"][idempotency_key] = result\n',
            "    pass\n",
        ),
    ),
    # Rule 7: full-refund status transition.
    "rule7-status": (
        (
            '    status = "refunded" if order["refunded"] == order["paid"] else "partially_refunded"\n',
            '    status = "partially_refunded"\n',
        ),
    ),
    # Rule 5: the inclusive boundary (refunding exactly the remaining balance).
    "rule5-boundary": (
        (
            "    if amount > remaining:\n",
            "    if amount >= remaining:\n",
        ),
    ),
    # Probe: rule 1 is checked before rule 3. Require permission on the replay path too, so
    # an outsider replaying a known key is refused instead of handed the stored result.
    # If no test notices, rule 1's precedence over rule 3 is unpinned.
    "rule1-permission-clause": (
        (
            '    if idempotency_key in order["keys"]:\n'
            '        return order["keys"][idempotency_key]\n',
            '    if idempotency_key in order["keys"] and _may_refund(order, actor):\n'
            '        return order["keys"][idempotency_key]\n',
        ),
    ),
    # Probe: rule 1 is checked before rule 4. Require a refundable status on the replay
    # path too, so a replay against a now-cancelled order raises instead of returning the
    # stored result. If no test notices, rule 1's precedence over rule 4 is unpinned.
    "rule1-status-clause": (
        (
            '    if idempotency_key in order["keys"]:\n'
            '        return order["keys"][idempotency_key]\n',
            '    if idempotency_key in order["keys"] and order["status"] in ("paid", "partially_refunded"):\n'
            '        return order["keys"][idempotency_key]\n',
        ),
    ),
    # Probe: rule 5 when the ledger is already over-refunded (remaining < 0). The cap
    # must still reject; no test builds such a row.
    "rule5-negative-remaining": (
        (
            '    remaining = order["paid"] - order["refunded"]\n    if amount > remaining:\n',
            '    remaining = order["paid"] - order["refunded"]\n    if remaining > 0 and amount > remaining:\n',
        ),
    ),
}


def main(argv):
    if len(argv) != 2 or argv[1] not in BREAKS:
        sys.stderr.write("usage: audit_break_guard.py {%s}\n" % "|".join(BREAKS))
        return 2
    source = TARGET.read_text()
    for old, new in BREAKS[argv[1]]:
        if source.count(old) != 1:
            sys.stderr.write(
                "anchor for %r not found exactly once in %s: %r\n"
                % (argv[1], TARGET, old)
            )
            return 1
        source = source.replace(old, new)
    TARGET.write_text(source)
    print("guard removed: %s" % argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
