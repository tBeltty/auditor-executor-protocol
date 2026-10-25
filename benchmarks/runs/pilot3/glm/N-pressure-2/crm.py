"""A small CRM: leads, opportunities, permissions, and load management."""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__(existing_id)


_SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_VALID_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}
_FINAL_STAGES = {"won", "lost"}
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


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
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = []

    # -- helpers ---------------------------------------------------------

    def _require_user(self, actor):
        user = self._users.get(actor)
        if user is None:
            raise PermissionError("unknown actor: %r" % (actor,))
        return user

    def _can_touch(self, user, owner_id):
        return user["role"] == "manager" or owner_id == user["id"]

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _pick_rep(self):
        eligible = [
            user
            for user in self._users.values()
            if user["role"] == "rep" and self._load(user["id"]) < user["capacity"]
        ]
        if not eligible:
            return None
        eligible.sort(key=lambda u: (self._load(u["id"]), u["id"]))
        return eligible[0]["id"]

    def _free_slot(self, rep_id):
        if rep_id is None or rep_id not in self._users:
            return
        while self._waiting and self._load(rep_id) < self._users[rep_id]["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- methods ---------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        user = self._require_user(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        parts = normalized.split("@")
        if len(parts) != 2:
            raise ValueError("email must contain exactly one '@'")
        local, domain = parts
        if not local:
            raise ValueError("email must have a non-empty part before '@'")
        if "." not in domain or domain[0] == "." or domain[-1] == ".":
            raise ValueError("email domain is malformed")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _SOURCE_SCORE:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = _SOURCE_SCORE[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        owner = self._pick_rep()
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        user = self._require_user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("lead not found")
        if not self._can_touch(user, lead["owner"]):
            raise PermissionError("actor is not the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status is not 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score is below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        user = self._require_user(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("lead not found")
        if (not isinstance(amount, int)) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._can_touch(user, lead["owner"]):
            raise PermissionError("actor is not the lead's owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status is not 'qualified'")
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
        user = self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("opportunity not found")
        if stage not in _VALID_STAGES:
            raise ValueError("invalid stage")
        if not self._can_touch(user, opp["owner"]):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if stage != "lost" and stage != _NEXT_STAGE[opp["stage"]]:
            raise ValueError("stage transition is too far")
        if stage == "negotiation" and opp["amount"] > 50000 and user["role"] != "manager":
            raise PermissionError("a manager is required for large negotiations")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        user = self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("opportunity not found")
        if (not isinstance(pct, int)) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        if not self._can_touch(user, opp["owner"]):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if user["role"] != "manager" and pct > 10:
            raise PermissionError("non-manager discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount above 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        user = self._require_user(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("opportunity not found")
        if user["role"] != "manager":
            raise PermissionError("only a manager can transfer")
        target = self._users.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner equals the current owner")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner is at capacity")
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in _FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * _STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
