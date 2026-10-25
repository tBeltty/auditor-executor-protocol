"""Remove one guard from crm.py by name (used only by negative controls)."""
import os
import re
import sys

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crm.py")

# Replacement text for a guard block. An empty string deletes the block; a
# non-empty stub keeps the module importable so the failure is a test failure.
STUBS = {
    "email": "        norm = str(email).strip().lower()\n        domain = norm.split('@')[-1]\n",
    "permission": "        return None\n",
}

SWAPS = {
    # -- check-order permutations (spec: "Checks run in the order listed") --
    "order-advance-stage": (
        "        # >>> guard:stage-name\n"
        "        if not isinstance(stage, str) or stage not in ALL_STAGES:\n"
        "            raise ValueError(\"unknown stage: %r\" % (stage,))\n"
        "        # <<< guard:stage-name\n"
        "        self._allowed(opp[\"owner\"], actor)\n",
        "        self._allowed(opp[\"owner\"], actor)\n"
        "        # >>> guard:stage-name\n"
        "        if not isinstance(stage, str) or stage not in ALL_STAGES:\n"
        "            raise ValueError(\"unknown stage: %r\" % (stage,))\n"
        "        # <<< guard:stage-name\n",
    ),
    "order-advance-final": (
        "        self._allowed(opp[\"owner\"], actor)\n"
        "        # >>> guard:transition\n"
        "        if opp[\"stage\"] in FINAL_STAGES:\n"
        "            raise ValueError(\"opportunity is already in a final stage\")\n"
        "        nxt = STAGE_ORDER[STAGE_ORDER.index(opp[\"stage\"]) + 1]\n"
        "        if stage != \"lost\" and stage != nxt:\n"
        "            raise ValueError(\"illegal stage transition\")\n"
        "        # <<< guard:transition\n",
        "        # >>> guard:transition\n"
        "        if opp[\"stage\"] in FINAL_STAGES:\n"
        "            raise ValueError(\"opportunity is already in a final stage\")\n"
        "        nxt = STAGE_ORDER[STAGE_ORDER.index(opp[\"stage\"]) + 1]\n"
        "        if stage != \"lost\" and stage != nxt:\n"
        "            raise ValueError(\"illegal stage transition\")\n"
        "        # <<< guard:transition\n"
        "        self._allowed(opp[\"owner\"], actor)\n",
    ),
    "order-convert-amount": (
        "        # >>> guard:amount\n"
        "        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:\n"
        "            raise ValueError(\"amount must be a positive int\")\n"
        "        # <<< guard:amount\n"
        "        self._allowed(lead[\"owner\"], actor)\n",
        "        self._allowed(lead[\"owner\"], actor)\n"
        "        # >>> guard:amount\n"
        "        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:\n"
        "            raise ValueError(\"amount must be a positive int\")\n"
        "        # <<< guard:amount\n",
    ),
    "order-discount-pct": (
        "        # >>> guard:pct-range\n"
        "        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:\n"
        "            raise ValueError(\"pct must be an int between 1 and 30\")\n"
        "        # <<< guard:pct-range\n"
        "        self._allowed(opp[\"owner\"], actor)\n",
        "        self._allowed(opp[\"owner\"], actor)\n"
        "        # >>> guard:pct-range\n"
        "        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:\n"
        "            raise ValueError(\"pct must be an int between 1 and 30\")\n"
        "        # <<< guard:pct-range\n",
    ),
    "order-discount-permission": (
        "        self._allowed(opp[\"owner\"], actor)\n"
        "        if opp[\"stage\"] in FINAL_STAGES:\n"
        "            raise ValueError(\"opportunity is already in a final stage\")\n"
        "        # >>> guard:rep-cap\n"
        "        if not self._is_manager(actor) and pct > 10:\n"
        "            raise PermissionError(\"reps may discount at most 10 percent\")\n"
        "        # <<< guard:rep-cap\n",
        "        if opp[\"stage\"] in FINAL_STAGES:\n"
        "            raise ValueError(\"opportunity is already in a final stage\")\n"
        "        # >>> guard:rep-cap\n"
        "        if not self._is_manager(actor) and pct > 10:\n"
        "            raise PermissionError(\"reps may discount at most 10 percent\")\n"
        "        # <<< guard:rep-cap\n"
        "        self._allowed(opp[\"owner\"], actor)\n",
    ),
    "order-discount-final": (
        "        if opp[\"stage\"] in FINAL_STAGES:\n"
        "            raise ValueError(\"opportunity is already in a final stage\")\n"
        "        # >>> guard:rep-cap\n"
        "        if not self._is_manager(actor) and pct > 10:\n"
        "            raise PermissionError(\"reps may discount at most 10 percent\")\n"
        "        # <<< guard:rep-cap\n",
        "        # >>> guard:rep-cap\n"
        "        if not self._is_manager(actor) and pct > 10:\n"
        "            raise PermissionError(\"reps may discount at most 10 percent\")\n"
        "        # <<< guard:rep-cap\n"
        "        if opp[\"stage\"] in FINAL_STAGES:\n"
        "            raise ValueError(\"opportunity is already in a final stage\")\n",
    ),
    "order-transfer-target": (
        "        # >>> guard:transfer-manager\n"
        "        if not self._is_manager(actor):\n"
        "            raise PermissionError(\"only managers may transfer opportunities\")\n"
        "        # <<< guard:transfer-manager\n"
        "        # >>> guard:transfer-target\n"
        "        target = self.users.get(new_owner) if isinstance(new_owner, str) else None\n"
        "        if target is None or target[\"role\"] != \"rep\":\n"
        "            raise ValueError(\"new owner must be a rep\")\n"
        "        # <<< guard:transfer-target\n",
        "        # >>> guard:transfer-target\n"
        "        target = self.users.get(new_owner) if isinstance(new_owner, str) else None\n"
        "        if target is None or target[\"role\"] != \"rep\":\n"
        "            raise ValueError(\"new owner must be a rep\")\n"
        "        # <<< guard:transfer-target\n"
        "        # >>> guard:transfer-manager\n"
        "        if not self._is_manager(actor):\n"
        "            raise PermissionError(\"only managers may transfer opportunities\")\n"
        "        # <<< guard:transfer-manager\n",
    ),
    "order-add-source": (
        "        # >>> guard:source\n"
        "        if not isinstance(source, str) or source not in SOURCE_SCORES:\n"
        "            raise ValueError(\"source must be web, referral or event\")\n"
        "        # <<< guard:source\n"
        "        # >>> guard:duplicate\n"
        "        for existing in self.leads.values():\n"
        "            if existing[\"email\"] == norm:\n"
        "                raise DuplicateLeadError(existing[\"id\"])\n"
        "        # <<< guard:duplicate\n",
        "        # >>> guard:duplicate\n"
        "        for existing in self.leads.values():\n"
        "            if existing[\"email\"] == norm:\n"
        "                raise DuplicateLeadError(existing[\"id\"])\n"
        "        # <<< guard:duplicate\n"
        "        # >>> guard:source\n"
        "        if not isinstance(source, str) or source not in SOURCE_SCORES:\n"
        "            raise ValueError(\"source must be web, referral or event\")\n"
        "        # <<< guard:source\n",
    ),
}

SPECIAL = {
    "atomicity": (
        "        # >>> guard:bigdeal\n"
        "        if stage == \"negotiation\" and opp[\"amount\"] > 50000 and not self._is_manager(actor):\n"
        "            raise PermissionError(\"manager approval required for deals above 50000\")\n"
        "        # <<< guard:bigdeal\n"
        "        opp[\"stage\"] = stage\n"
        "        self.log.append((\"advance\", opp_id, actor))\n",
        "        opp[\"stage\"] = stage\n"
        "        if stage == \"negotiation\" and opp[\"amount\"] > 50000 and not self._is_manager(actor):\n"
        "            raise PermissionError(\"manager approval required for deals above 50000\")\n"
        "        self.log.append((\"advance\", opp_id, actor))\n",
    ),
    "atomicity-add": (
        "    def add_lead(self, email, name, source, actor):\n"
        "        self._actor(actor)\n",
        "    def add_lead(self, email, name, source, actor):\n"
        "        self._actor(actor)\n"
        "        self._lead_seq += 1\n",
    ),
}


def main(name):
    with open(PATH, encoding="utf-8") as handle:
        source = handle.read()

    if name in SPECIAL or name in SWAPS:
        table = SWAPS if name in SWAPS else SPECIAL
        old, new = table[name]
        if source.count(old) != 1:
            raise SystemExit("break %r: anchor not unique" % name)
        broken = source.replace(old, new)
    else:
        pattern = re.compile(
            r"(?m)^[ \t]*# >>> guard:%s\n.*?^[ \t]*# <<< guard:%s\n" % (name, name),
            re.S,
        )
        broken, hits = pattern.subn(STUBS.get(name, ""), source)
        if hits != 1:
            raise SystemExit("break %r: found %d guard blocks" % (name, hits))

    if broken == source:
        raise SystemExit("break %r: source unchanged" % name)

    with open(PATH, "w", encoding="utf-8") as handle:
        handle.write(broken)


if __name__ == "__main__":
    main(sys.argv[1])
