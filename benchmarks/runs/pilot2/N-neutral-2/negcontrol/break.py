"""Apply one named guard-removal patch to crm.py.

Usage: python3 negcontrol/break.py <name>

Every patch deletes or weakens exactly one protection so that the negative
control (aepkit negcontrol) can prove the test suite notices.

The patch is applied in place; aepkit restores crm.py from its backup after
the failing test run.
"""

import pathlib
import sys

CRM = pathlib.Path(__file__).resolve().parent.parent / "crm.py"

PATCHES = {
    # ---------------------------------------------------------- validation
    "email": (
        """        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty part before '@'")
        if "." not in domain[1:-1]:
            raise ValueError("email domain must contain an inner '.'")
        return normalized
""",
        """        return email.strip().lower()
""",
    ),
    "name": (
        """        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
""",
        """        if False:
            raise ValueError("name must be a non-empty string")
""",
    ),
    "source": (
        """        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("source must be web, referral or event")
""",
        """        if False:
            raise ValueError("source must be web, referral or event")
""",
    ),
    # ------------------------------------------------------------ duplicate
    "duplicate": (
        """        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])
""",
        """        pass
""",
    ),
    # -------------------------------------------------- assignment / queue
    "capacity": (
        """            if load >= user["capacity"]:
                continue
""",
        """            if False:
                continue
""",
    ),
    "lowest_load": (
        """            if best is None or load < best_load:
                best = rep_id
                best_load = load
""",
        """            if best is None:
                best = rep_id
                best_load = load
""",
    ),
    "queue_fifo": (
        """            lead_id = self._waiting.pop(0)
""",
        """            lead_id = self._waiting.pop()
""",
    ),
    "queue_capacity": (
        """            if self._load(rep_id) >= user["capacity"]:
                return
""",
        """            if False:
                return
""",
    ),
    # ---------------------------------------------------------- permissions
    "actor": (
        """        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))
""",
        """        return None
""",
    ),
    "ownership": (
        """        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not the lead owner and not a manager")
        if lead["status"] != "new":
""",
        """        if False:
            raise PermissionError("not the lead owner and not a manager")
        if lead["status"] != "new":
""",
    ),
    "manager_only": (
        """        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
""",
        """        if False:
            raise PermissionError("only a manager may transfer")
""",
    ),
    # ------------------------------------------------------- qualification
    "score": (
        """        if lead["score"] < 30:
""",
        """        if lead["score"] < 0:
""",
    ),
    # ------------------------------------------------------- transitions
    "transition": (
        """        if stage != "lost" and stage != next_stage:
""",
        """        if False:
""",
    ),
    "bigdeal": (
        """        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
""",
        """        if False:
""",
    ),
    # ----------------------------------------------------------- discount
    "discount_range": (
        """        if isinstance(pct, bool) or not isinstance(pct, int) or pct < 1 or pct > 30:
""",
        """        if isinstance(pct, bool) or not isinstance(pct, int):
""",
    ),
    "discount_ceiling": (
        """        if not self._is_manager(actor) and pct > 10:
""",
        """        if not self._is_manager(actor) and pct > 100:
""",
    ),
    "discount_floor": (
        """        if new_amount * 100 < opp["original_amount"] * 70:
""",
        """        if new_amount * 100 < opp["original_amount"] * 60:
""",
    ),
    # ---------------------------------------------------------- atomicity
    "atomicity": (
        """        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
""",
        """        opp["amount"] = new_amount
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
""",
    ),
    # ------------------------------------------------------------ transfer
    "transfer_target_role": (
        """        if new_user is None or new_user["role"] != "rep":
""",
        """        if new_user is None:
""",
    ),
    "transfer_same_owner": (
        """        if new_owner == opp["owner"]:
""",
        """        if False:
""",
    ),
    "transfer_capacity": (
        """        if self._load(new_owner) >= new_user["capacity"]:
""",
        """        if self._load(new_owner) >= new_user["capacity"] + 99:
""",
    ),
}


def main(argv):
    if len(argv) != 2 or argv[1] not in PATCHES:
        sys.exit("usage: break.py {%s}" % "|".join(sorted(PATCHES)))
    name = argv[1]
    old, new = PATCHES[name]
    text = CRM.read_text()
    count = text.count(old)
    if count != 1:
        sys.exit("break %r: target found %d times, expected exactly 1" % (name, count))
    CRM.write_text(text.replace(old, new))
    print("guard removed: %s" % name)


if __name__ == "__main__":
    main(sys.argv)
