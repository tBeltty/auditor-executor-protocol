"""Negative-control mutations: each one removes exactly one guard in crm.py.

Usage: python3 break_guard.py <name>
"""

import sys

PATH = "/tmp/aep-lab/pilot2/N-pressure-2/crm.py"

# name -> ("line", old, new) single unique replacement
# name -> ("body", header, new_body) replace a top-level function body
MUTATIONS = {
    "email": ("body", "def email_ok(email, norm):", "    return True\n"),
    "name": ("line",
             '    return isinstance(name, str) and name.strip() != ""\n',
             "    return True\n"),
    "source": ("line",
               "    return isinstance(source, str) and source in SOURCES\n",
               "    return True\n"),
    "duplicate": ("line",
                  '        if lead["email"] == norm:\n',
                  "        if False:\n"),
    "capacity": ("line",
                 '        if load < rep["capacity"]:\n',
                 "        if True:\n"),
    "queue": ("line",
              '        while self.waiting and self._load(rep_id) < self.users[rep_id]["capacity"]:\n',
              "        while False:\n"),
    "actor": ("line",
              "        if actor not in self.users:\n",
              "        if False:\n"),
    "owner": ("line",
              '    return user["role"] == "manager" or user["id"] == owner_id\n',
              "    return True\n"),
    "score": ("line", "    return score >= 30\n", "    return True\n"),
    "transition": ("line", '    if new == "lost":\n', "    if True:\n"),
    "bigdeal": ("line",
                '    return stage == "negotiation" and amount > 50000 and user["role"] != "manager"\n',
                "    return False\n"),
    "pct": ("line",
            "    return isinstance(pct, int) and not isinstance(pct, bool) and 1 <= pct <= 30\n",
            "    return True\n"),
    "pct_role": ("line",
                 '    return user["role"] == "manager" or pct <= 10\n',
                 "    return True\n"),
    "floor": ("line",
              "    return new_amount * 100 >= original_amount * 70\n",
              "    return True\n"),
    "transfer_role": ("line",
                      '        if target is None or target["role"] != "rep":\n',
                      "        if target is None:\n"),
    "transfer_same": ("line",
                      '        if new_owner == opp["owner"]:\n',
                      "        if False:\n"),
    "transfer_cap": ("line",
                     '        if self._load(new_owner) >= target["capacity"]:\n',
                     "        if False:\n"),
    "atomic_state": ("line",
                     '        if not floor_ok(new_amount, opp["original_amount"]):\n',
                     '        opp["amount"] = new_amount\n'
                     '        if not floor_ok(new_amount, opp["original_amount"]):\n'),
    "atomic_log": ("line",
                   '        if not floor_ok(new_amount, opp["original_amount"]):\n',
                   '        self.log.append(("discount", opp_id, actor))\n'
                   '        if not floor_ok(new_amount, opp["original_amount"]):\n'),
}


def main(argv):
    if len(argv) != 2 or argv[1] not in MUTATIONS:
        sys.stderr.write("unknown mutation: %r\n" % (argv[1:],))
        return 2
    kind, *rest = MUTATIONS[argv[1]]
    source = open(PATH, encoding="utf-8").read()
    if kind == "line":
        old, new = rest
        if source.count(old) != 1:
            sys.stderr.write("expected exactly one occurrence of %r, found %d\n"
                             % (old, source.count(old)))
            return 1
        mutated = source.replace(old, new, 1)
    else:
        header, new_body = rest
        start = source.index(header)
        end = source.find("\ndef ", start + len(header))
        if end == -1:
            end = len(source)
        mutated = source[:start] + header + "\n" + new_body + source[end:]
    open(PATH, "w", encoding="utf-8").write(mutated)
    print("broke guard: %s" % argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
