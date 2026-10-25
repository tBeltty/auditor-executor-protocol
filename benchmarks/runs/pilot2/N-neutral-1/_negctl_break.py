"""Negative-control helper: disable exactly one guard in crm.py.

Usage:
  python3 _negctl_break.py kill <tag> [<tag> ...]
  python3 _negctl_break.py insert <tag> <code>     # insert code before the guard line
  python3 _negctl_break.py sub <tag> <code>        # replace the guard line with code

A guard line is any line carrying a ``# @g:<tag>`` marker. ``\\n`` in <code>
starts a new line; every inserted line gets the guard line's indentation.
"""

import re
import sys
from pathlib import Path

FILE = Path(__file__).with_name("crm.py")


def marker(tag):
    return re.compile(r"#\s*@g:" + re.escape(tag) + r"(?!\w)")


def find(lines, tag):
    pattern = marker(tag)
    hits = [i for i, line in enumerate(lines) if pattern.search(line)]
    if len(hits) != 1:
        raise SystemExit("tag %r matched %d lines (need exactly 1)" % (tag, len(hits)))
    return hits[0]


def indent_of(line):
    return line[: len(line) - len(line.lstrip())]


def block(text, indent):
    return [indent + piece if piece.strip() else piece for piece in text.split("\\n")]


def main(argv):
    mode, tags = argv[1], argv[2:]
    if not tags:
        raise SystemExit("missing tag")
    lines = FILE.read_text().split("\n")
    if mode == "kill":
        for tag in tags:
            index = find(lines, tag)
            lines[index] = indent_of(lines[index]) + "if False:  # killed " + tag
    elif mode in ("insert", "sub"):
        tag, code = tags[0], tags[1]
        index = find(lines, tag)
        indent = indent_of(lines[index])
        if mode == "insert":
            lines[index:index] = block(code, indent)
        else:
            lines[index : index + 1] = block(code, indent)
    else:
        raise SystemExit("unknown mode %r" % (mode,))
    FILE.write_text("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
