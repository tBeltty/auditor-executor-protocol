#!/usr/bin/env python3
"""Negative-control helper: remove exactly one guard from crm.py.

Each mutation replaces one contiguous, unique snippet of crm.py with a version
that no longer enforces the corresponding rule. ``crm.py`` is rewritten in
place; ``aepkit negcontrol --file crm.py`` restores it from its backup
afterwards. Run with ``--check`` to verify every anchor matches exactly once.
"""

import sys
from pathlib import Path

TARGET = Path(__file__).with_name("crm.py")

MUTATIONS = {
    # 1. email / name / source validation
    "validation": (
        """        norm = self._validate_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in self._SOURCES:
            raise ValueError("source must be web, referral or event")
        domain = norm.split("@")[1]
        score = self._BASE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15""",
        """        norm = email.strip().lower() if isinstance(email, str) else ""
        domain = norm.split("@")[-1]
        name = name if isinstance(name, str) else ""
        score = self._BASE_SCORES.get(source, 10) if isinstance(source, str) else 10
        if domain and domain not in FREE_EMAIL_DOMAINS:
            score += 15""",
    ),
    # 2. duplicate detection
    "duplicate": (
        """        if norm in self._emails:
            raise DuplicateLeadError(self._emails[norm])""",
        """        if False:
            raise DuplicateLeadError(self._emails.get(norm))""",
    ),
    # 3a. capacity limit when picking an owner
    "capacity": (
        """            if load < user["capacity"]:""",
        """            if True:""",
    ),
    # 3b. stop draining the queue at capacity
    "queue_drain": (
        """        while self._waiting and self._load(rep_id) < user["capacity"]:""",
        """        while self._waiting and True:""",
    ),
    # 3c. FIFO order of the waiting queue
    "fifo": (
        """            lead_id = self._waiting.pop(0)""",
        """            lead_id = self._waiting.pop()""",
    ),
    # 4a. unknown actor rejected first
    "unknown_actor": (
        """        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))""",
        """        if False:
            raise PermissionError("unknown actor: %r" % (actor,))""",
    ),
    # 4b. owner-or-manager permission check
    "owner_or_manager": (
        """        if record["owner"] != actor and not self._is_manager(actor):""",
        """        if False:""",
    ),
    # 4c. manager-only operations
    "require_manager": (
        """        if self.users[actor]["role"] != "manager":""",
        """        if False:""",
    ),
    # 5. qualification score threshold
    "score_threshold": (
        """        if lead["score"] < 30:""",
        """        if False:""",
    ),
    # 6a. immediate-next-stage rule
    "stage_next": (
        """        if stage != "lost" and stage != self._NEXT.get(opp["stage"]):""",
        """        if False:""",
    ),
    # 6b. final stages are immutable
    "stage_final": (
        """        self._require_owner_or_manager(opp, actor)
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and stage != self._NEXT.get(opp["stage"]):""",
        """        self._require_owner_or_manager(opp, actor)
        if False:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and stage != self._NEXT.get(opp["stage"]):""",
    ),
    # 7. big-deal approval
    "big_deal": (
        """        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):""",
        """        if False:""",
    ),
    # 8a. discount percentage range / integer type
    "pct_range": (
        """        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):""",
        """        if False:""",
    ),
    # 8b. non-manager discount cap
    "pct_rep_limit": (
        """        if not self._is_manager(actor) and pct > 10:""",
        """        if False:""",
    ),
    # 8c. cumulative 30 percent floor
    "discount_floor": (
        """        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")""",
        """        new_amount = opp["amount"] * (100 - pct) // 100
        if False:
            raise ValueError("cumulative discount exceeds 30 percent")""",
    ),
    # 9a. new owner capacity on transfer
    "transfer_capacity": (
        """        if self._load(new_owner) >= self.users[new_owner]["capacity"]:""",
        """        if False:""",
    ),
    # 9b. new owner must be a rep
    "transfer_role": (
        """        if self.users[new_owner]["role"] != "rep":""",
        """        if False:""",
    ),
    # 11a. email validation only (attributable split of "validation")
    "validation_email": (
        """        norm = self._validate_email(email)
        if not isinstance(name, str) or not name.strip():""",
        """        norm = email.strip().lower() if isinstance(email, str) else ""
        if not isinstance(name, str) or not name.strip():""",
    ),
    # 11b. name validation only
    "validation_name": (
        """        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")""",
        """        if False:
            raise ValueError("name must be a non-empty string")""",
    ),
    # 11c. source validation only
    "validation_source": (
        """        if source not in self._SOURCES:
            raise ValueError("source must be web, referral or event")""",
        """        if False:
            raise ValueError("source must be web, referral or event")""",
    ),
    # 12a. qualify: unknown lead id (check 1)
    "qualify_unknown": (
        """        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        self._require_owner_or_manager(lead, actor)""",
        """        lead = self.leads.get(lead_id)
        self._require_owner_or_manager(lead, actor)""",
    ),
    # 12b. qualify: status must be "new" (check 3)
    "qualify_status": (
        """        if lead["status"] != "new":
            raise ValueError("lead is not new")""",
        """        if False:
            raise ValueError("lead is not new")""",
    ),
    # 12c. convert: unknown lead id (check 1)
    "convert_unknown": (
        """        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:""",
        """        lead = self.leads.get(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:""",
    ),
    # 12d. convert: lead must have an owner (check 5)
    "convert_ownerless": (
        """        if lead["owner"] is None:
            raise ValueError("lead has no owner")""",
        """        if False:
            raise ValueError("lead has no owner")""",
    ),
    # 12e. convert: amount must be a positive non-bool int
    "convert_amount": (
        """        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive integer")""",
        """        if False:
            raise ValueError("amount must be a positive integer")""",
    ),
    # 12f. a failed convert must not consume an opportunity id
    "opp_id_consumed": (
        """        lead = self.leads[lead_id]
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:""",
        """        lead = self.leads[lead_id]
        self._opp_seq += 1
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:""",
    ),
    # 12g. a rejected duplicate must not consume a lead id
    "lead_id_consumed": (
        """        if norm in self._emails:
            raise DuplicateLeadError(self._emails[norm])
        owner = self._pick_owner()
        lead_id = "L%d" % (self._lead_seq + 1)
        self._lead_seq += 1""",
        """        self._lead_seq += 1
        if norm in self._emails:
            raise DuplicateLeadError(self._emails[norm])
        owner = self._pick_owner()
        lead_id = "L%d" % self._lead_seq""",
    ),
    # 12h. advance: unknown opportunity id (check 1)
    "advance_unknown": (
        """        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if stage not in self._STAGES:""",
        """        opp = self.opps.get(opp_id)
        if stage not in self._STAGES:""",
    ),
    # 12i. discount: unknown opportunity id (check 1)
    "discount_unknown": (
        """        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):""",
        """        opp = self.opps.get(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):""",
    ),
    # 12j. transfer: unknown opportunity id (check 1)
    "transfer_unknown_opp": (
        """        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        self._require_manager(actor)""",
        """        opp = self.opps.get(opp_id)
        self._require_manager(actor)""",
    ),
    # 12k. atomicity: failed duplicate must not write a lead record
    "atomic_add_lead": (
        """        if norm in self._emails:
            raise DuplicateLeadError(self._emails[norm])""",
        """        if norm in self._emails:
            self.leads["Lghost"] = {"id": "Lghost", "email": norm}
            raise DuplicateLeadError(self._emails[norm])""",
    ),
    # 12l. atomicity: failed discount must not change the amount
    "atomic_discount": (
        """        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount""",
        """        new_amount = opp["amount"] * (100 - pct) // 100
        opp["amount"] = new_amount
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")""",
    ),
    # 13a. assignment tie-break is string order, not numeric id order
    "tiebreak_numeric": (
        """        for user_id in sorted(self.users):""",
        """        for user_id in sorted(self.users, key=lambda value: int(value[1:]) if value[1:].isdigit() else 0):""",
    ),
    # 13b. assignment tie-break direction
    "tiebreak_reverse": (
        """        for user_id in sorted(self.users):""",
        """        for user_id in sorted(self.users, reverse=True):""",
    ),
    # 13c. corporate-domain score bonus
    "score_bonus": (
        """        if domain not in FREE_EMAIL_DOMAINS:
            score += 15""",
        """        if False:
            score += 15""",
    ),
    # 13d. discount rejects a final stage (check 4)
    "discount_final": (
        """        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:""",
        """        if False:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:""",
    ),
    # 13e. advance frees the owner's slot and drains the queue
    "advance_assign": (
        """        if stage in self._FINAL_STAGES:
            self._assign_waiting(opp["owner"])""",
        """        if False:
            self._assign_waiting(opp["owner"])""",
    ),
    # 13f. add_lead success log entry
    "add_lead_log": (
        """        self.log.append(("add_lead", lead_id, actor))""",
        """        pass""",
    ),
    # 13g. transfer rejects the current owner (check 5)
    "transfer_self": (
        """        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ from current owner")""",
        """        if False:
            raise ValueError("new owner must differ from current owner")""",
    ),
    # 13h. transfer rejects a final stage (check 4)
    "transfer_final": (
        """        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:""",
        """        if False:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:""",
    ),
    # 13i. transfer rejects an unknown new_owner (check 3)
    "transfer_unknown_user": (
        """        if not isinstance(new_owner, str) or new_owner not in self.users:
            raise ValueError("unknown user: %r" % (new_owner,))""",
        """        if False:
            raise ValueError("unknown user: %r" % (new_owner,))""",
    ),
    # 13j. big-deal threshold reads the current amount, not the original
    "big_deal_original": (
        """        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):""",
        """        if stage == "negotiation" and opp["original_amount"] > 50000 and not self._is_manager(actor):""",
    ),
    # 13k. forecast is pure: no log entry
    "forecast_log": (
        """    def forecast(self):
        weighted = 0""",
        """    def forecast(self):
        self.log.append(("forecast", None, None))
        weighted = 0""",
    ),
    # 10a. atomicity: mutate before the failing check
    "atomic_qualify": (
        """        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified\"""",
        """        lead["status"] = "qualified"
        if lead["score"] < 30:
            raise ValueError("lead score below 30")""",
    ),
    # 10b. atomicity: log before the failing check
    "atomic_transfer_log": (
        """        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")""",
        """        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            self.log.append(("transfer", opp_id, actor))
            raise ValueError("new owner is at capacity")""",
    ),
}


def check():
    text = TARGET.read_text()
    failed = False
    for name, (old, new) in MUTATIONS.items():
        count = text.count(old)
        status = "ok" if count == 1 and old != new else "BAD"
        if status == "BAD":
            failed = True
        print("%-22s matches=%d %s" % (name, count, status))
    return 1 if failed else 0


def main(argv):
    if len(argv) != 2 or argv[1] in ("-h", "--help"):
        print("usage: negcontrol_break.py <mutation>|--check|--list")
        return 2
    if argv[1] == "--check":
        return check()
    if argv[1] == "--list":
        print("\n".join(sorted(MUTATIONS)))
        return 0
    if argv[1] not in MUTATIONS:
        print("unknown mutation: %s" % argv[1], file=sys.stderr)
        print("known: %s" % ", ".join(sorted(MUTATIONS)), file=sys.stderr)
        return 2
    old, new = MUTATIONS[argv[1]]
    text = TARGET.read_text()
    if text.count(old) != 1:
        print(
            "ERROR: anchor for %r matched %d times (expected 1)"
            % (argv[1], text.count(old)),
            file=sys.stderr,
        )
        return 1
    TARGET.write_text(text.replace(old, new, 1))
    print("broke guard: %s" % argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
