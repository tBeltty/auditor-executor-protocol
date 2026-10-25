"""Minimal in-memory CRM, implemented to the crm.md specification.

Public surface: ``CRM`` and ``DuplicateLeadError``.
"""

FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the normalized email."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    _BASE_SCORES = {"web": 10, "referral": 30, "event": 20}
    _SOURCES = ("web", "referral", "event")
    _STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
    _NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
    _FINAL_STAGES = ("won", "lost")
    _WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

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
        self._emails = {}
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _validate_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email local part must not be empty")
        has_inner_dot = any(
            char == "." and 0 < index < len(domain) - 1
            for index, char in enumerate(domain)
        )
        if not has_inner_dot:
            raise ValueError("email domain must contain a dot")
        return norm

    def _require_known(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _require_manager(self, actor):
        if self.users[actor]["role"] != "manager":
            raise PermissionError("manager role required")

    def _require_owner_or_manager(self, record, actor):
        if record["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("owner or manager role required")

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in self._FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best_id = None
        best_load = None
        for user_id in sorted(self.users):
            user = self.users[user_id]
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load < user["capacity"]:
                if best_load is None or load < best_load:
                    best_id, best_load = user_id, load
        return best_id

    def _assign_waiting(self, rep_id):
        if rep_id is None or rep_id not in self.users:
            return
        user = self.users[rep_id]
        if user["role"] != "rep":
            return
        while self._waiting and self._load(rep_id) < user["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # operations
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_known(actor)
        norm = self._validate_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in self._SOURCES:
            raise ValueError("source must be web, referral or event")
        domain = norm.split("@")[1]
        score = self._BASE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15
        if norm in self._emails:
            raise DuplicateLeadError(self._emails[norm])
        owner = self._pick_owner()
        lead_id = "L%d" % (self._lead_seq + 1)
        self._lead_seq += 1
        lead = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        self._emails[norm] = lead_id
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_known(actor)
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        self._require_owner_or_manager(lead, actor)
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_known(actor)
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        self._require_owner_or_manager(lead, actor)
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        opp_id = "O%d" % (self._opp_seq + 1)
        self._opp_seq += 1
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
        self._require_known(actor)
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if stage not in self._STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        self._require_owner_or_manager(opp, actor)
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage != "lost" and stage != self._NEXT.get(opp["stage"]):
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("deals above 50000 need a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self._FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_known(actor)
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("pct must be an integer from 1 to 30")
        self._require_owner_or_manager(opp, actor)
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_known(actor)
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        self._require_manager(actor)
        if not isinstance(new_owner, str) or new_owner not in self.users:
            raise ValueError("unknown user: %r" % (new_owner,))
        if self.users[new_owner]["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in self._FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new owner must differ from current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        weighted = 0
        open_count = 0
        won_total = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in self._FINAL_STAGES:
                if stage == "won":
                    won_total += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * self._WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
