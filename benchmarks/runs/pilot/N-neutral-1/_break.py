"""Negative-control harness: remove exactly one guard from refunds.py in place.

Usage: ``python3 _break.py <guard>`` where guard is one of the keys of BREAKS.
``aepkit negcontrol`` backs refunds.py up before running this and restores it
byte-identically afterwards, so the tree is left green.

Each entry is an exact snippet of refunds.py replaced by a version that no
longer enforces that guard. The replacement is always syntactically valid: it
disables the check rather than deleting code, so the tests fail with the
assertion that the guard exists, never with a SyntaxError or ImportError.
"""

import sys
from pathlib import Path

TARGET = Path(__file__).with_name("refunds.py")

BREAKS = {
    # Rule 1: skip the stored-result lookup, so a replay re-runs the refund.
    "idempotency": (
        '    if idempotency_key in order["keys"]:',
        "    if False:  # guard removed: a replayed key is treated as new",
    ),
    # Rule 2: accept any amount the caller passes.
    "amount": (
        "    if not _is_positive_int(amount):",
        "    if False:  # guard removed: amount shape is no longer checked",
    ),
    # Rule 3: let every actor refund every order.
    "permission": (
        "    if _may_refund(actor, order):",
        "    if True:  # guard removed: every actor is authorised",
    ),
    # Rule 4: refund regardless of the order status.
    "status": (
        '    if order["status"] not in REFUNDABLE_STATUSES:',
        "    if False:  # guard removed: order status is no longer checked",
    ),
    # Rule 5: ignore the refundable balance.
    "cap": (
        "    if amount > remaining:",
        "    if False:  # guard removed: the refundable balance is not checked",
    ),
    # Rule 6: write the refund to the order before the gateway accepts it, and
    # keep the write when the gateway raises (the success path is unchanged).
    "gateway_atomicity": (
        '    refund_id = _charge(gateway, order["charge_id"], amount)\n'
        "\n"
        "    return _record(order, amount, refund_id, idempotency_key)",
        '    order["refunded"] += amount\n'
        "    order[\"status\"] = (\n"
        '        "refunded" if order["refunded"] == order["paid"] else "partially_refunded"\n'
        "    )\n"
        '    refund_id = _charge(gateway, order["charge_id"], amount)\n'
        '    result = {"refund_id": refund_id, "amount": amount, "status": order["status"]}\n'
        '    order["keys"][idempotency_key] = result\n'
        "    return result",
    ),
}


def main(argv):
    if len(argv) != 2 or argv[1] not in BREAKS:
        names = ", ".join(sorted(BREAKS))
        print(f"usage: {argv[0]} <guard>  (one of: {names})", file=sys.stderr)
        return 2
    guard = argv[1]
    old, new = BREAKS[guard]
    source = TARGET.read_text()
    occurrences = source.count(old)
    if occurrences != 1:
        print(
            f"error: guard {guard!r} matched {occurrences} times in {TARGET}",
            file=sys.stderr,
        )
        return 1
    TARGET.write_text(source.replace(old, new))
    print(f"broke guard {guard!r} in {TARGET}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
