"""Minimal CRM module implementing the specified lead/opportunity workflow."""

_FINAL_STAGES = ("won", "lost")
_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


class CRM:
    def __init__(self, reps):
        self.reps = [
            {"id": rep["id"], "role": rep["role"], "capacity": rep["capacity"]}
            for rep in reps
        ]
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_user(self, actor):
        for rep in self.reps:
            if rep["id"] == actor:
                return rep
        raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self._require_user(actor)["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _capacity(self, rep_id):
        for rep in self.reps:
            if rep["id"] == rep_id:
                return rep["capacity"]
        return 0

    def _lead(self, lead_id):
        if not isinstance(lead_id, str):
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    def _opp(self, opp_id):
        if not isinstance(opp_id, str):
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp

    def _pick_owner(self):
        candidates = []
        for rep in self.reps:
            if rep["role"] != "rep":
                continue
            load = self._load(rep["id"])
            if load < rep["capacity"]:
                candidates.append((load, rep["id"]))
        if not candidates:
            return None
        return min(candidates)[1]

    def _assign_waiting(self, rep_id):
        while self.waiting and self._load(rep_id) < self._capacity(rep_id):
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_user(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must not be empty")
        if not domain:
            raise ValueError("email domain must not be empty")
        if "." not in domain:
            raise ValueError("email domain must contain a '.'")
        if not any(
            0 < index < len(domain) - 1
            for index, char in enumerate(domain)
            if char == "."
        ):
            raise ValueError("email domain dot must not be first or last")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(source, str) or source not in _SOURCE_SCORES:
            raise ValueError("source must be web, referral or event")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq

        score = _SOURCE_SCORES[source]
        if domain not in _FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_owner()
        if owner is None:
            self.waiting.append(lead_id)

        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_user(actor)

        lead = self._lead(lead_id)

        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")

        if lead["status"] != "new":
            raise ValueError("lead is not new")

        if lead["score"] < 30:
            raise ValueError("lead score is below 30")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_user(actor)

        lead = self._lead(lead_id)

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive integer")

        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")

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

        opp = self._opp(opp_id)

        if stage not in _ALL_STAGES:
            raise ValueError("unknown stage: %r" % (stage,))

        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")

        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")

        current_index = _STAGE_ORDER.index(opp["stage"])
        if stage != "lost" and stage != _STAGE_ORDER[current_index + 1]:
            raise ValueError("invalid stage transition")

        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in _FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_user(actor)

        opp = self._opp(opp_id)

        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an integer from 1 to 30")

        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")

        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("non-managers may discount at most 10")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_user(actor)

        opp = self._opp(opp_id)

        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")

        new_owner_rep = None
        for rep in self.reps:
            if rep["id"] == new_owner:
                new_owner_rep = rep
                break
        if new_owner_rep is None or new_owner_rep["role"] != "rep":
            raise ValueError("new owner must be a known rep")

        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if new_owner == opp["owner"]:
            raise ValueError("new owner is the current owner")

        if self._load(new_owner) >= new_owner_rep["capacity"]:
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
            if opp["stage"] in _FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * _STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
