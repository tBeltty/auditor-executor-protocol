"""crm.py -- lead / opportunity CRM as specified in specs/crm.md.

Every public method validates before it mutates, so a call that raises leaves
`leads`, `opps` and `log` exactly as they were; the log entries named in the
spec are appended only on success.

Guard markers of the form ``# G:<NAME>`` sit on the single line that enforces a
guard; they exist so a negative control can delete exactly that line.  The
``# ATOMIC-ANCHOR`` comment marks the point in `discount` where a mutation
injected before the permission check would break the all-or-nothing property:
a successful discount overwrites it, a failed one leaves it behind.
"""

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
FINAL_STAGES = {"won", "lost"}
ALL_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


def _valid_email(normalized):
    """Exactly one '@', a non-empty local part, and a '.' in the domain that is
    neither the domain's first nor its last character (spec: 'contains a . which
    is neither the first nor the last character of the domain')."""
    if normalized.count("@") != 1:
        return False
    local, domain = normalized.split("@")
    if not local:
        return False
    return any(domain[index] == "." for index in range(1, len(domain) - 1))


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead, existing id %s" % existing_id)


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_count = 0
        self._opp_count = 0
        self._email_index = {}

    # -- internals ---------------------------------------------------------

    def _require_user(self, actor):
        """Raise unless actor is a known user id."""
        # An id is a str; a non-str can never be a known user, and checking the
        # type first keeps an unhashable value from escaping as TypeError.
        if not isinstance(actor, str): raise PermissionError("unknown actor %r" % (actor,))  # G:ACTOR_TYPE
        if actor not in self.users: raise PermissionError("unknown actor %r" % (actor,))  # G:ACTOR

    def _may_act(self, actor, owner):
        return actor == owner or self.users[actor]["role"] == "manager"

    def _require_owner_or_manager(self, actor, owner):
        """Raise unless actor owns the entity or is a manager."""
        if not self._may_act(actor, owner): raise PermissionError("not owner or manager")  # G:PERM

    def _load(self, user_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _pick_assignee(self):
        available = [user_id for user_id in sorted(self.users)
                     if self.users[user_id]["role"] == "rep"  # G:REP_ONLY
                     and self._load(user_id) < self.users[user_id]["capacity"]  # G:CAPACITY
                     ]
        if not available:
            return None
        return min(available, key=lambda user_id: (self._load(user_id), user_id))  # G:LOWEST_LOAD

    def _free_slot(self, user_id):
        while self.waiting and self._load(user_id) < self.users[user_id]["capacity"]:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    # -- leads -------------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._require_user(actor)
        if not isinstance(email, str): raise ValueError("email must be a string")  # G:EMAIL_TYPE
        normalized = email.strip().lower()
        if not _valid_email(normalized): raise ValueError("invalid email %r" % (email,))  # G:EMAIL
        clean_name = name.strip() if isinstance(name, str) else ""
        if not clean_name: raise ValueError("invalid name %r" % (name,))  # G:NAME
        if not isinstance(source, str): raise ValueError("invalid source %r" % (source,))  # G:SOURCE_TYPE
        if source not in SOURCE_SCORES: raise ValueError("invalid source %r" % (source,))  # G:SOURCE
        existing = self._email_index.get(normalized)
        if existing is not None: raise DuplicateLeadError(existing)  # G:DUPLICATE
        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
        domain = normalized.rpartition("@")[2]
        score = SOURCE_SCORES.get(source, 0) + (0 if domain in FREE_EMAIL_DOMAINS else 15)
        owner = self._pick_assignee()
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": clean_name,
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self._email_index[normalized] = lead_id
        if owner is None:
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_user(actor)
        if not isinstance(lead_id, str): raise ValueError("unknown lead %r" % (lead_id,))  # G:LEAD_ID_TYPE
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead %r" % (lead_id,))
        self._require_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "new": raise ValueError("lead %s is not new" % lead_id)  # G:QUALIFY_STATUS
        if lead["score"] < 30: raise ValueError("score %d below threshold" % lead["score"])  # G:SCORE
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_user(actor)
        if not isinstance(lead_id, str): raise ValueError("unknown lead %r" % (lead_id,))  # G:CONVERT_LEAD_TYPE
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0: raise ValueError("amount must be a positive int")  # G:CONVERT_AMOUNT
        self._require_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "qualified": raise ValueError("lead %s is not qualified" % lead_id)  # G:CONVERT_STATUS
        if lead["owner"] is None: raise ValueError("lead %s has no owner" % lead_id)  # G:CONVERT_OWNER
        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
        self.opps[opp_id] = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    # -- opportunities -----------------------------------------------------

    def advance(self, opp_id, stage, actor):
        self._require_user(actor)
        if not isinstance(opp_id, str): raise ValueError("unknown opportunity %r" % (opp_id,))  # G:OPP_ID_ADV
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity %r" % (opp_id,))
        if not isinstance(stage, str): raise ValueError("invalid stage %r" % (stage,))  # G:STAGE_TYPE
        if stage not in ALL_STAGES: raise ValueError("invalid stage %r" % (stage,))  # G:STAGE_VALID
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in FINAL_STAGES: raise ValueError("opportunity already final")  # G:FINAL
        if stage != "lost" and stage != NEXT_STAGE.get(opp["stage"]): raise ValueError("illegal transition")  # G:TRANSITION
        if stage == "negotiation" and opp["amount"] > 50000 and self.users[actor]["role"] != "manager": raise PermissionError("manager approval required")  # G:BIGDEAL
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES: self._free_slot(opp["owner"])  # G:ASSIGN_ADV

    def discount(self, opp_id, pct, actor):
        self._require_user(actor)
        if not isinstance(opp_id, str): raise ValueError("unknown opportunity %r" % (opp_id,))  # G:OPP_ID_DISC
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30): raise ValueError("invalid pct %r" % (pct,))  # G:PCT_RANGE
        # ATOMIC-ANCHOR
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in FINAL_STAGES: raise ValueError("opportunity already final")  # G:DISC_FINAL
        if self.users[actor]["role"] != "manager" and pct > 10: raise PermissionError("discount above 10% needs a manager")  # G:PCT_ROLE
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70: raise ValueError("cumulative discount exceeds 30%")  # G:FLOOR
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_user(actor)
        if not isinstance(opp_id, str): raise ValueError("unknown opportunity %r" % (opp_id,))  # G:OPP_ID_XFER
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity %r" % (opp_id,))
        if self.users[actor]["role"] != "manager": raise PermissionError("only a manager may transfer")  # G:XFER_MANAGER
        if not isinstance(new_owner, str): raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_TYPE
        target = self.users.get(new_owner)
        if target is None or target["role"] != "rep": raise ValueError("target %r is not a rep" % (new_owner,))  # G:XFER_REP
        if opp["stage"] in FINAL_STAGES: raise ValueError("opportunity already final")  # G:XFER_FINAL
        if new_owner == opp["owner"]: raise ValueError("target already owns the opportunity")  # G:XFER_SAME
        if self._load(new_owner) >= target["capacity"]: raise ValueError("target %s is at capacity" % new_owner)  # G:XFER_CAPACITY
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_opps = [opp for opp in self.opps.values() if opp["stage"] not in FINAL_STAGES]  # G:FORECAST_OPEN
        weighted = sum(opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100 for opp in open_opps)
        won = sum(opp["amount"] for opp in self.opps.values() if opp["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
