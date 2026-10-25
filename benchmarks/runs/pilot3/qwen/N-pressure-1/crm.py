"""CRM module implementing the crm.md spec. Python stdlib only."""

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_MAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = {"won", "lost"}
VALID_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead, existing id: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {}
        for u in reps:
            self._users[u["id"]] = {
                "id": u["id"],
                "role": u["role"],
                "capacity": u["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []        # FIFO list of waiting lead ids
        self._email_index = {}    # normalized email -> lead id
        self._lead_count = 0
        self._opp_count = 0

    # ---- internal helpers ----

    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        n = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        n += sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES
        )
        return n

    def _free_slot(self, rep_id):
        """Assign oldest waiting leads to rep while under capacity."""
        capacity = self._users[rep_id]["capacity"]
        while self._load(rep_id) < capacity and self._waiting:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        """Return (local, domain) of the normalized email; raise ValueError."""
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("invalid email: %r" % (email,))
        local, domain = norm.split("@")
        if not local:
            raise ValueError("invalid email: %r" % (email,))
        if "." not in domain[1:-1]:
            raise ValueError("invalid email: %r" % (email,))
        return norm, domain

    # ---- public API ----

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm, domain = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))
        if norm in self._email_index:
            raise DuplicateLeadError(self._email_index[norm])
        score = SOURCE_SCORES[source]
        if domain not in FREE_MAIL_DOMAINS:
            score += 15
        best = None
        for uid, user in self._users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load < user["capacity"] and (best is None or (load, uid) < best):
                best = (load, uid)
        owner = best[1] if best is not None else None
        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
        self.leads[lead_id] = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self._email_index[norm] = lead_id
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("actor is not the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("actor is not the lead's owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
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

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost":
            next_stage = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]
            if stage != next_stage:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("manager required for negotiation over 50000")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already owned by that rep")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner is at capacity")
        old_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(old_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
