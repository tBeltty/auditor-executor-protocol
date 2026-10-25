#!/usr/bin/env python3
"""Remove exactly one guard from crm.py -- the "break" half of aepkit negcontrol.

Usage: python3 _break.py <mode>

Each mode names the guard it disables. Every replacement is asserted to match
exactly one line (or occurrence) so a silent no-op can never pass as a break.
"""

import pathlib
import re
import sys

TARGET = pathlib.Path(__file__).resolve().with_name("crm.py")

# mode -> marker comment on the guard line; the line's "raise ..." becomes "pass"
RAISE_MODES = {
    "email-type": "GC-EMAIL-TYPE",
    "email-local": "GC-EMAIL-LOCAL",
    "email-domain": "GC-EMAIL-DOMAIN",
    "name": "GC-NAME",
    "source": "GC-SOURCE",
    "duplicate": "GC-DUP",
    "permission-actor": "GC-PERM-ACTOR",
    "permission-owner": "GC-PERM-OWNER",
    "qualify-score": "GC-QUAL-SCORE",
    "stage-final": "GC-STAGE-FINAL",
    "bigdeal": "GC-BIGDEAL",
    "discount-range": "GC-DISC-RANGE",
    "discount-rep": "GC-DISC-REP",
    "discount-final": "GC-DISC-FINAL",
    "discount-floor": "GC-DISC-FLOOR",
    "transfer-manager": "GC-TRANSFER-MGR",
    "transfer-role": "GC-TRANSFER-ROLE",
    "transfer-final": "GC-TRANSFER-FINAL",
    "transfer-same": "GC-TRANSFER-SAME",
    "transfer-cap": "GC-TRANSFER-CAP",
}

# mode -> list of operations against the source text
LINE_SUBS = {
    "assign-capacity": (
        "GC-ASSIGN-CAP",
        'candidates = [self._users[rid] for rid in self._rep_ids if self.load(rid) < self._users[rid]["capacity"]]  # GC-ASSIGN-CAP',
        'candidates = [self._users[rid] for rid in self._rep_ids]  # GC-ASSIGN-CAP',
    ),
    "assign-tie": (
        "GC-ASSIGN-TIE",
        'owner = min(candidates, key=lambda u: (self.load(u["id"]), u["id"]))["id"]  # GC-ASSIGN-TIE',
        'owner = min(candidates, key=lambda u: self.load(u["id"]))["id"]  # GC-ASSIGN-TIE',
    ),
    "waiting-enqueue": (
        "GC-WAIT",
        'if owner is None: self.waiting.append(lead_id)  # GC-WAIT',
        'pass  # GC-WAIT',
    ),
    "free-capacity": (
        "GC-FREE-CAP",
        'while self.waiting and rep_id is not None and self.load(rep_id) < self._users[rep_id]["capacity"]:  # GC-FREE-CAP',
        'while self.waiting and rep_id is not None:  # GC-FREE-CAP',
    ),
    "queue-fifo": (
        "GC-WAIT-FIFO",
        'lead_id = self.waiting.pop(0)  # GC-WAIT-FIFO',
        'lead_id = self.waiting.pop()  # GC-WAIT-FIFO',
    ),
    "stage-next": (
        "GC-STAGE-NEXT",
        'if stage != "lost" and stage != following:',
        'if False:',
    ),
}

# modes that turn one validation guard into "mutate, then fail" -- the exact
# defect the atomicity rule forbids, with the success path left untouched
FULL_SUBS = {
    "atomic-id": (
        "GC-NAME",
        '        if not isinstance(name, str) or not name.strip(): raise ValueError("name must be a non-empty string")  # GC-NAME',
        '        if not isinstance(name, str) or not name.strip():\n'
        "            self._lead_seq += 1  # GC-ATOMIC-EARLY\n"
        '            raise ValueError("name must be a non-empty string")  # GC-NAME',
    ),
    "atomic-state": (
        "GC-AMOUNT",
        '        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0: raise ValueError("amount must be a positive int")  # GC-AMOUNT',
        '        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:\n'
        '            lead["status"] = "converted"  # GC-ATOMIC-EARLY\n'
        '            raise ValueError("amount must be a positive int")  # GC-AMOUNT',
    ),
    "atomic-log": (
        "GC-DISC-FLOOR",
        '        if new_amount * 100 < opp["original_amount"] * 70: raise ValueError("cumulative discount would exceed 30 percent")  # GC-DISC-FLOOR',
        '        if new_amount * 100 < opp["original_amount"] * 70:\n'
        '            self.log.append(("discount", opp_id, actor))  # GC-ATOMIC-EARLY\n'
        '            raise ValueError("cumulative discount would exceed 30 percent")  # GC-DISC-FLOOR',
    ),
}


def find_line(lines, marker):
    pattern = re.compile(r"#\s*" + re.escape(marker) + r"(?![A-Za-z0-9_-])")
    hits = [i for i, line in enumerate(lines) if pattern.search(line)]
    if len(hits) != 1:
        sys.exit("marker %s found on %d lines, expected exactly 1" % (marker, len(hits)))
    return hits[0]


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: _break.py <mode>")
    mode = sys.argv[1]
    source = TARGET.read_text()
    lines = source.splitlines(keepends=True)

    if mode in RAISE_MODES:
        marker = RAISE_MODES[mode]
        index = find_line(lines, marker)
        head, sep, _ = lines[index].partition("raise ")
        if not sep:
            sys.exit("guard %s has no raise to remove" % marker)
        lines[index] = head + "pass  # " + marker + "\n"
    elif mode in LINE_SUBS:
        marker, old, new = LINE_SUBS[mode]
        index = find_line(lines, marker)
        if old not in lines[index]:
            sys.exit("guard %s does not contain %r" % (marker, old))
        lines[index] = lines[index].replace(old, new)
    elif mode in FULL_SUBS:
        marker, old, new = FULL_SUBS[mode]
        find_line(lines, marker)
        if source.count(old) != 1:
            sys.exit("full edit for %s matched %d times" % (mode, source.count(old)))
        TARGET.write_text(source.replace(old, new))
        print("guard removed: %s" % mode)
        return
    else:
        sys.exit("unknown mode: %s" % mode)

    TARGET.write_text("".join(lines))
    print("guard removed: %s" % mode)


if __name__ == "__main__":
    main()
