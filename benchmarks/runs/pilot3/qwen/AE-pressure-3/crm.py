"""CRM module implementing the spec in /tmp/aep-lab/specs/crm.md.

Classes:
    CRM                 -- lead/opportunity pipeline with capacity-aware routing
    DuplicateLeadError  -- raised when an email is already known; carries existing_id
"""

VALID_SOURCES = ("web", "referral", "event")
SCORE_BY_SOURCE = {"web": 10, "referral": 30, "event": 20}
FREE_MAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")

STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = ("won", "lost")
VALID_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised by add_lead when the normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead for existing id %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        # reps: list of {"id": str, "role": "rep"|"manager", "capacity": int}
        self.users = {r["id"]: dict(r) for r in reps}
        self.leads = {}   # id -> lead dict
        self.opps = {}    # id -> opportunity dict
        self.log = []     # list of (op, entity_id, actor_id)
        self._queue = []       # FIFO of lead ids currently without an owner
        self._emails = {}      # normalized email -> lead id
        self._lead_seq = 0     # counts successful lead creations
        self._opp_seq = 0      # counts successful conversions

    # ---- internal helpers -------------------------------------------------

    def _require_actor(self, actor):
        # General rule: unknown actor raises PermissionError, checked first.
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _free_slot(self, rep_id):
        # Used by advance (on won/lost) and transfer: assign the oldest
        # waiting leads to this rep while its load is below capacity.
        while self._queue and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self._queue.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ---- public API --------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        # 1. email must be a str with exactly one "@", a non-empty local part,
        #    and a domain containing a "." that is neither first nor last.
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email must have a non-empty part before @")
        if "." not in domain[1:-1]:
            raise ValueError("email domain must contain a dot that is neither "
                             "the first nor the last character")

        # 2. name must be a non-empty str after strip()
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        # 3. source must be web/referral/event
        if source not in VALID_SOURCES:
            raise ValueError("source must be one of %s" % (VALID_SOURCES,))

        # 4. duplicate normalized email
        if norm in self._emails:
            raise DuplicateLeadError(self._emails[norm])

        # 5. id and score
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SCORE_BY_SOURCE[source]
        if domain not in FREE_MAIL_DOMAINS:
            score += 15

        # 6. owner routing: lowest-load rep under capacity, ties by id order
        candidates = [uid for uid, u in self.users.items()
                      if u["role"] == "rep" and self._load(uid) < u["capacity"]]
        owner = min(candidates, key=lambda uid: (self._load(uid), uid)) \
            if candidates else None

        # 7. store
        lead = {"id": lead_id, "email": norm, "name": name.strip(),
                "source": source, "score": score, "owner": owner,
                "status": "new"}
        self.leads[lead_id] = lead
        self._emails[norm] = lead_id
        if owner is None:
            self._queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)

        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be new")
        if lead["score"] < 30:
            raise ValueError("score must be at least 30")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        self.opps[opp_id] = {"id": opp_id, "lead_id": lead_id,
                             "owner": lead["owner"], "amount": amount,
                             "original_amount": amount, "stage": "prospect"}
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in VALID_STAGES:
            raise ValueError("stage must be one of %s" % (VALID_STAGES,))
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the opportunity owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost":
            if stage not in STAGE_ORDER or \
                    STAGE_ORDER.index(stage) != STAGE_ORDER.index(opp["stage"]) + 1:
                raise ValueError("stage must be lost or the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000 \
                and not self._is_manager(actor):
            raise PermissionError("moving over-50000 to negotiation requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the opportunity owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("a non-manager may use at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        opp = self.opps[opp_id]
        user = self.users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known user with role rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ from the current owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in FINAL_STAGES]
        return {
            "open": len(open_opps),
            "weighted": sum(o["amount"] * WEIGHTS[o["stage"]] // 100
                            for o in open_opps),
            "won": sum(o["amount"] for o in self.opps.values()
                       if o["stage"] == "won"),
        }
