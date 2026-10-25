"""Surgical mutations used by the aepkit negcontrol runs.

Each key removes one guard.  Usage: python3 negbreak.py <guard>
Writes crm.py in place; aepkit restores it from its own backup.
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TARGET = HERE / "crm.py"

BREAKS = {
    "email_validation": [
        ("        if not isinstance(email, str):", "        if False:"),
        ("        if len(parts) != 2 or not parts[0]:", "        if False:"),
        (
            "        if dot <= 0 or dot == len(domain) - 1:",
            "        if False:",
        ),
    ],
    "name_validation": [
        (
            "        if not isinstance(name, str) or not name.strip():",
            "        if False:",
        ),
    ],
    "source_validation": [
        ("        if source not in VALID_SOURCES:", "        if False:"),
    ],
    "duplicate_detection": [
        (
            '                raise DuplicateLeadError(lead["id"])',
            "                pass",
        ),
    ],
    "rep_assignment": [
        (
            "        owner = min(eligible)[1] if eligible else None",
            "        owner = max(eligible)[1] if eligible else None",
        ),
    ],
    "capacity_waiting_queue": [
        (
            '            if rep["role"] == "rep" and self._load(rep_id) < rep["capacity"]',
            '            if rep["role"] == "rep"',
        ),
    ],
    "permission_checks": [
        (
            '        if actor != lead["owner"] and self.reps[actor]["role"] != "manager":\n'
            '            raise PermissionError("not allowed to qualify %s" % (lead_id,))',
            '        if False:\n'
            '            raise PermissionError("not allowed to qualify %s" % (lead_id,))',
        ),
    ],
    "qualification_threshold": [
        ('        if lead["score"] < 30:', "        if False:"),
    ],
    "stage_transitions": [
        (
            '        if opp["stage"] in FINAL_STAGES:\n'
            '            raise ValueError("opportunity %s is final" % (opp_id,))\n'
            '        if stage != "lost":\n'
            '            index = STAGE_ORDER.index(opp["stage"])\n'
            "            if index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[index + 1] != stage:\n"
            '                raise ValueError("invalid transition %s -> %s" % (opp["stage"], stage))',
            "        if False:\n"
            '            index = STAGE_ORDER.index(opp["stage"])\n'
            "            if index + 1 >= len(STAGE_ORDER) or STAGE_ORDER[index + 1] != stage:\n"
            '                raise ValueError("invalid transition %s -> %s" % (opp["stage"], stage))',
        ),
    ],
    "big_deal_approval": [
        (
            "        if (\n"
            '            stage == "negotiation"\n'
            '            and opp["amount"] > 50000\n'
            '            and self.reps[actor]["role"] != "manager"\n'
            "        ):\n"
            '            raise PermissionError("deal over 50000 needs a manager")',
            "        if False:\n"
            '            raise PermissionError("deal over 50000 needs a manager")',
        ),
    ],
    "discount_limits": [
        (
            "        if isinstance(pct, bool) or not isinstance(pct, int) or pct < 1 or pct > 30:",
            "        if False:",
        ),
        (
            '        if self.reps[actor]["role"] != "manager" and pct > 10:',
            "        if False:",
        ),
    ],
    "cumulative_floor": [
        (
            '        if new_amount * 100 < opp["original_amount"] * 70:',
            "        if False:",
        ),
    ],
    "transfer_rules": [
        (
            '        if self.reps[actor]["role"] != "manager":\n'
            '            raise PermissionError("only a manager may transfer")',
            "        if False:\n"
            '            raise PermissionError("only a manager may transfer")',
        ),
        ('        if target is None or target["role"] != "rep":', "        if False:"),
        ('        if new_owner == opp["owner"]:', "        if False:"),
        (
            '        if self._load(new_owner) >= target["capacity"]:',
            "        if False:",
        ),
    ],
    "atomicity": [
        (
            "        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:\n"
            '            raise ValueError("amount must be a positive int")',
            "        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:\n"
            '            self.log.append(("convert", lead_id, actor))\n'
            '            raise ValueError("amount must be a positive int")',
        ),
    ],
}


def main():
    if len(sys.argv) != 2 or sys.argv[1] not in BREAKS:
        sys.exit("usage: python3 negbreak.py {%s}" % "|".join(sorted(BREAKS)))
    source = TARGET.read_text()
    for old, new in BREAKS[sys.argv[1]]:
        if source.count(old) != 1:
            sys.exit("snippet not found exactly once for %s" % sys.argv[1])
        source = source.replace(old, new)
    TARGET.write_text(source)
    print("broke guard: %s" % sys.argv[1])


if __name__ == "__main__":
    main()
