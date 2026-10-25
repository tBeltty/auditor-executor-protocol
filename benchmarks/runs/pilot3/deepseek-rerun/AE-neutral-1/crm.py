"""CRM module implementing leads, opportunities and a simple round-robin owner."""

_FINAL_STAGES = ("won", "lost")
_STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_SOURCES = ("web", "referral", "event")
_BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead email, existing id: %s" % existing_id)


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
        self._waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best = None
        for user in self._users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            if best is None or (load, user["id"]) < (best[0], best[1]):
                best = (load, user["id"])
        return None if best is None else best[1]

    def _free_slot(self, user_id):
        if user_id is None or user_id not in self._users:
            return
        capacity = self._users[user_id]["capacity"]
        while self._waiting and self._load(user_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = user_id
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
        if not domain:
            raise ValueError("email must have a domain")
        if "." not in domain:
            raise ValueError("email domain must contain a dot")
        dot = domain.find(".")
        if dot == 0 or dot == len(domain) - 1:
            raise ValueError("email domain dot must not be first or last character")
        return normalized

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        domain = normalized.split("@")[1]
        score = _BASE_SCORE[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
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
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor cannot qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor cannot convert this lead")
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
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGE_ORDER and stage not in _FINAL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor cannot advance this opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost":
            current_index = _STAGE_ORDER.index(opp["stage"])
            if stage != _STAGE_ORDER[current_index + 1]:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor cannot discount this opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        new_user = self._users.get(new_owner)
        if new_user is None or new_user["role"] != "rep":
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is the current owner")
        if self._load(new_owner) >= new_user["capacity"]:
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
            weighted += opp["amount"] * _WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
