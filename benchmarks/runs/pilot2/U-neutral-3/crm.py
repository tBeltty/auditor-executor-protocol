"""A small in-memory CRM: leads, opportunities, rep loads and a waiting queue."""

VALID_SOURCES = ("web", "referral", "event")
FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


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
        self._waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _is_rep(self, actor):
        return self.users[actor]["role"] == "rep"

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _has_capacity(self, user_id):
        return self._load(user_id) < self.users[user_id]["capacity"]

    def _pick_owner(self):
        best = None
        best_load = None
        for user_id in sorted(self.users):
            user = self.users[user_id]
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load >= user["capacity"]:
                continue
            if best is None or load < best_load:
                best = user_id
                best_load = load
        return best

    def _assign_waiting(self, rep_id):
        while self._waiting and self._has_capacity(rep_id):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # commands
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized_email = email.strip().lower()
        if normalized_email.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized_email.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not domain:
            raise ValueError("email must have a domain")
        if "." not in domain[1:-1]:
            raise ValueError("email domain must contain an inner '.'")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized_email:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_owner()
        if owner is None:
            self._waiting.append(lead_id)

        lead = {
            "id": lead_id,
            "email": normalized_email,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)

        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]

        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed to qualify lead")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)

        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")

        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed to convert lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        self.opps[opp_id] = opp
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]

        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))

        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed to advance opportunity")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")

        current = opp["stage"]
        if stage != "lost":
            next_stage = STAGE_ORDER[STAGE_ORDER.index(current) + 1]
            if stage != next_stage:
                raise ValueError("invalid stage transition")

        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for large negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]

        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int between 1 and 30")

        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed to discount opportunity")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")

        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)

        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]

        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")

        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new owner must be a rep")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")

        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")

        if not self._has_capacity(new_owner):
            raise ValueError("new owner has no capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in FINAL_STAGES:
                if stage == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
