"""Small CRM domain model (leads -> opportunities), stdlib only."""

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = {"won", "lost"}
ALL_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}
FORECAST_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
ACTIVE_LEAD_STATUSES = {"new", "qualified"}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead for email, existing lead id: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._queue = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ utils

    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        if not isinstance(actor, str):
            return False
        user = self._users.get(actor)
        return user is not None and user["role"] == "manager"

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str):
            return None
        return self.leads.get(lead_id)

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str):
            return None
        return self.opps.get(opp_id)

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ACTIVE_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _assign_waiting(self, rep_id):
        if rep_id is None:
            return
        user = self._users.get(rep_id)
        if user is None or user["role"] != "rep":
            return
        while self._queue and self._load(rep_id) < user["capacity"]:
            lead_id = self._queue.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if "." not in domain:
            raise ValueError("email domain must contain a '.'")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("email domain '.' may not be first or last")
        return normalized, domain

    # ---------------------------------------------------------------- methods

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized, domain = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("source must be web, referral or event")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        candidates = [
            user
            for user in self._users.values()
            if user["role"] == "rep" and self._load(user["id"]) < user["capacity"]
        ]
        owner = None
        if candidates:
            best = min(candidates, key=lambda user: (self._load(user["id"]), user["id"]))
            owner = best["id"]

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15
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
            self._queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self._get_lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._get_lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may convert")
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
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(stage, str) or stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may advance")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        current_index = STAGE_ORDER.index(opp["stage"])
        allowed = stage == "lost" or stage == STAGE_ORDER[current_index + 1]
        if not allowed:
            raise ValueError("illegal stage transition %s -> %s" % (opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may discount")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("a rep may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if not isinstance(new_owner, str):
            raise ValueError("new owner must be a known rep")
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ from current owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won += opp["amount"]
            elif opp["stage"] in FINAL_STAGES:
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * FORECAST_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
