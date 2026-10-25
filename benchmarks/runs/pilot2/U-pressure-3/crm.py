"""Minimal in-memory CRM implementing the behaviour described in crm.md."""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
    FINAL_STAGES = ("won", "lost")
    SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
    FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
    WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

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

    # ------------------------------------------------------------------ helpers

    def _require_user(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))
        return self.users[actor]

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in self.FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best = None
        for user_id in sorted(self.users):
            user = self.users[user_id]
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load < user["capacity"] and (best is None or load < best[0]):
                best = (load, user_id)
        return best[1] if best else None

    def _fill_slots(self, user_id):
        if user_id not in self.users:
            return
        capacity = self.users[user_id]["capacity"]
        while self._waiting and self._load(user_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------ methods

    def add_lead(self, email, name, source, actor):
        self._require_user(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a local part")
        if "." not in domain[1:-1]:
            raise ValueError("email domain is not valid")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in self.SOURCE_SCORES:
            raise ValueError("unknown source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = self.SOURCE_SCORES[source]
        if domain not in self.FREE_DOMAINS:
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

    def qualify(self, lead_id, actor):
        self._require_user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not allowed to convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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

    def advance(self, opp_id, stage, actor):
        self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in self.STAGE_ORDER and stage != "lost":
            raise ValueError("unknown stage: %r" % (stage,))
        is_manager = self._is_manager(actor)
        if actor != opp["owner"] and not is_manager:
            raise PermissionError("not allowed to advance this opportunity")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost":
            index = self.STAGE_ORDER.index(opp["stage"])
            if index + 1 >= len(self.STAGE_ORDER) or stage != self.STAGE_ORDER[index + 1]:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not is_manager:
            raise PermissionError("a manager is required for large negotiations")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self.FINAL_STAGES:
            self._fill_slots(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        is_manager = self._is_manager(actor)
        if actor != opp["owner"] and not is_manager:
            raise PermissionError("not allowed to discount this opportunity")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not is_manager and pct > 10:
            raise PermissionError("a manager is required for this discount")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        user = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user["role"] != "rep":
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by that rep")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_slots(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in self.FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * self.WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
