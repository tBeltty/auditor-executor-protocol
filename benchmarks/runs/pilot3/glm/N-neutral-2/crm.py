"""crm.py - minimal CRM per spec (specs/crm.md)."""

VALID_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead email (existing lead: %s)" % existing_id)


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = {"role": rep["role"], "capacity": rep["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_count = 0
        self._opp_count = 0
        self._waiting = []  # FIFO of lead ids with no owner

    # ------------------------------------------------------------------ utils
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _rep_load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _is_owner_or_manager(self, actor, owner):
        return actor == owner or self._is_manager(actor)

    def _pick_owner(self):
        candidates = [
            uid
            for uid, user in self.users.items()
            if user["role"] == "rep" and self._rep_load(uid) < user["capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda uid: (self._rep_load(uid), uid))

    def _free_slot(self, rep_id):
        """Assign waiting leads to rep_id while its load is below capacity."""
        while self._waiting and self._rep_load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # --------------------------------------------------------------- add_lead
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        # 1. email
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        dot = domain.find(".")
        if not domain or dot < 1 or dot > len(domain) - 2:
            raise ValueError("invalid email domain")

        # 2. name
        if not isinstance(name, str):
            raise ValueError("name must be a str")
        if not name.strip():
            raise ValueError("name must be non-empty")

        # 3. source
        if source not in SOURCE_SCORES:
            raise ValueError("invalid source")

        # 4. duplicate
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        # 5. create
        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
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
            self._waiting.append(lead_id)

        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    # ---------------------------------------------------------------- qualify
    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not self._is_owner_or_manager(actor, lead["owner"]):
            raise PermissionError("actor is not the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # ---------------------------------------------------------------- convert
    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if (
            not isinstance(amount, int)
            or isinstance(amount, bool)
            or amount <= 0
        ):
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._is_owner_or_manager(actor, lead["owner"]):
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

    # ---------------------------------------------------------------- advance
    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if not self._is_owner_or_manager(actor, opp["owner"]):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        current_index = STAGE_ORDER.index(opp["stage"])
        allowed_next = STAGE_ORDER[current_index + 1]
        if stage != "lost" and stage != allowed_next:
            raise ValueError("stage must be 'lost' or the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    # --------------------------------------------------------------- discount
    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if not self._is_owner_or_manager(actor, opp["owner"]):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount is at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # --------------------------------------------------------------- transfer
    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("actor must be a manager")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._rep_load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    # --------------------------------------------------------------- forecast
    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage in WEIGHTS:
                open_count += 1
                weighted += opp["amount"] * WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
