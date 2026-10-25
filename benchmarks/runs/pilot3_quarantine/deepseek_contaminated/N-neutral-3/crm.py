"""CRM lead / opportunity management module (spec: specs/crm.md)."""

FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")

SOURCES = ("web", "referral", "event")

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGES = ("prospect", "proposal", "negotiation", "won")

FINAL_STAGES = ("won", "lost")

WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id=None, message=None):
        self.existing_id = existing_id
        if message is None:
            message = "duplicate lead email (existing id: %r)" % (existing_id,)
        super().__init__(message)


class CRM:
    def __init__(self, reps):
        self.reps = {}
        for rep in reps or ():
            record = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
            self.reps[record["id"]] = record
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting_queue = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ utils
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        user = self.reps.get(actor)
        return user is not None and user["role"] == "manager"

    def _load(self, rep_id):
        lead_load = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        opp_load = sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES
        )
        return lead_load + opp_load

    def _capacity(self, rep_id):
        user = self.reps.get(rep_id)
        if user is None:
            return 0
        return user["capacity"]

    def _assign_waiting(self, rep_id):
        while self.waiting_queue and self._load(rep_id) < self._capacity(rep_id):
            lead_id = self.waiting_queue.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # --------------------------------------------------------------- add_lead
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not self._valid_domain(domain):
            raise ValueError("email domain is not valid")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(source, str) or source not in SOURCES:
            raise ValueError("source must be one of %s" % (", ".join(SOURCES),))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        candidates = [
            (self._load(rep_id), rep_id)
            for rep_id, user in self.reps.items()
            if user["role"] == "rep" and self._load(rep_id) < self._capacity(rep_id)
        ]
        owner = None
        if candidates:
            owner = min(candidates)[1]

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        lead = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        if owner is None:
            self.waiting_queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    @staticmethod
    def _valid_domain(domain):
        if not domain:
            return False
        length = len(domain)
        for index, char in enumerate(domain):
            if char == "." and 0 < index < length - 1:
                return True
        return False

    # ----------------------------------------------------------------- qualify
    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self._get_lead(lead_id)
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def _get_lead(self, lead_id):
        try:
            return self.leads[lead_id]
        except (KeyError, TypeError):
            raise ValueError("unknown lead: %r" % (lead_id,))

    def _get_opp(self, opp_id):
        try:
            return self.opps[opp_id]
        except (KeyError, TypeError):
            raise ValueError("unknown opportunity: %r" % (opp_id,))

    # ----------------------------------------------------------------- convert
    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._get_lead(lead_id)

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")

        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may convert")

        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")

        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
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

    # ----------------------------------------------------------------- advance
    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)

        if not isinstance(stage, str) or stage not in STAGES + ("lost",):
            raise ValueError("invalid stage: %r" % (stage,))

        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may advance")

        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")

        if stage != "lost" and stage != self._next_stage(current):
            raise ValueError("illegal stage transition %r -> %r" % (current, stage))

        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    @staticmethod
    def _next_stage(current):
        index = STAGES.index(current)
        if index + 1 >= len(STAGES):
            return None
        return STAGES[index + 1]

    # ---------------------------------------------------------------- discount
    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)

        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")

        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may discount")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")

        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("a rep may discount at most 10 percent")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ---------------------------------------------------------------- transfer
    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)

        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")

        target = self.reps.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a known rep")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")

        if new_owner == opp["owner"]:
            raise ValueError("opportunity already belongs to new_owner")

        if self._load(new_owner) >= self._capacity(new_owner):
            raise ValueError("new_owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    # ---------------------------------------------------------------- forecast
    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
