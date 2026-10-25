"""Negative-control helper: remove one guard from refunds.py.

The guards in ``refunds.py`` are delimited by ``# >>> GUARD:<name>`` and
``# <<< GUARD:<name>`` markers, so a guard can be taken out with a mechanical
edit instead of hand-editing the file.

Usage:
    python3 _negcontrol.py <guard> [--swap]

    <guard>   one of idempotency, amount_validation, permission, status,
              refundable_cap, gateway_atomicity
    --swap    keep the block but reorder it so that the order is mutated
              *before* the gateway call (the atomicity mutation). Only valid
              for gateway_atomicity.

Without ``--swap`` the whole guarded block is deleted, which is the mutation
"the check is simply not there".

``aepkit negcontrol --file refunds.py`` restores the original file afterwards.
"""

import pathlib
import sys

TARGET = pathlib.Path(__file__).resolve().with_name("refunds.py")

GUARDS = (
    "idempotency",
    "amount_validation",
    "permission",
    "status",
    "refundable_cap",
    "gateway_atomicity",
)

START = "    # >>> GUARD:%s\n"
END = "    # <<< GUARD:%s\n"


def swap_commit_before_gateway(lines):
    """Move the ``gateway.refund`` call after the two order mutations."""
    opening, inner, closing = lines[0], lines[1:-1], lines[-1]
    call_index = next(
        index for index, line in enumerate(inner) if "gateway.refund(" in line
    )
    call = inner.pop(call_index)
    inner.append(call)
    return [opening] + inner + [closing]


def main(argv):
    args = argv[1:]
    target = TARGET
    if "--file" in args:
        index = args.index("--file")
        try:
            target = pathlib.Path(args[index + 1]).resolve()
        except IndexError:
            sys.stderr.write("--file needs a path\n")
            return 2
        del args[index:index + 2]

    if not args or args[0] not in GUARDS:
        sys.stderr.write("usage: _negcontrol.py {%s} [--swap] [--file PATH]\n" % "|".join(GUARDS))
        return 2

    guard = args[0]
    swap = "--swap" in args[1:]
    if swap and guard != "gateway_atomicity":
        sys.stderr.write("--swap is only meaningful for gateway_atomicity\n")
        return 2

    text = target.read_text()
    start = START % guard
    end = END % guard
    if text.count(start) != 1 or text.count(end) != 1:
        sys.stderr.write("guard markers for %r are missing or duplicated in %s\n" % (guard, target))
        return 3

    head = text.index(start)
    tail = text.index(end) + len(end)
    block = text[head:tail].splitlines(keepends=True)

    if swap:
        replacement = "".join(swap_commit_before_gateway(block))
        action = "reordered (commit before gateway call)"
    else:
        replacement = ""
        action = "deleted"

    target.write_text(text[:head] + replacement + text[tail:])
    print("[negcontrol] guard %r %s in %s (%d line(s) affected)"
          % (guard, action, target, len(block) - 2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
