"""Simple CRM module per spec (crm.md)."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
    SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
    STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
    STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
    WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

    def __init__(self, reps):
        self.users = {u["id"]: u for u in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_count = 0
        self._opp_count = 0
        self._waiting = []  # FIFO of lead ids

    # ---- helpers -------------------------------------------------------
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _is_int(self, value):
        return isinstance(value, int) and not isinstance(value, bool)

    def _rep_load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in ("won", "lost"):
                load += 1
        return load

    def _pick_owner(self):
        candidates = [
            uid for uid, u in self.users.items()
            if u["role"] == "rep" and self._rep_load(uid) < u["capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda uid: (self._rep_load(uid), uid))

    def _fill_from_waiting(self, rep_id):
        rep = self.users[rep_id]
        while self._waiting and self._rep_load(rep_id) < rep["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ---- methods -------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        parts = normalized.split("@")
        if len(parts) != 2:
            raise ValueError("email must contain exactly one @")
        local, domain = parts
        if not local:
            raise ValueError("empty local part")
        if len(domain) < 3 or "." not in domain[1:-1]:
            raise ValueError("invalid domain")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in self.SOURCE_SCORES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
        score = self.SOURCE_SCORES[source]
        if domain not in self.FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
        if owner is None:
            self._waiting.append(lead_id)
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
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not the owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if not self._is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not the owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        if stage not in self.STAGES:
            raise ValueError("invalid stage")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not the owner or a manager")
        if opp["stage"] in ("won", "lost"):
            raise ValueError("stage is final")
        valid = {"lost"} | set(self.STAGE_ORDER)
        if stage != "lost":
            idx = self.STAGE_ORDER.index(opp["stage"])
            if stage != self.STAGE_ORDER[idx + 1]:
                raise ValueError("stage must be lost or the next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("large deals need a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in ("won", "lost") and opp["owner"] is not None:
            self._fill_from_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        if not self._is_int(pct) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int in 1..30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not the owner or a manager")
        if opp["stage"] in ("won", "lost"):
            raise ValueError("stage is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount above 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        if not self._is_manager(actor):
            raise PermissionError("only managers transfer")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in ("won", "lost"):
            raise ValueError("stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ")
        if self._rep_load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner at capacity")
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if previous is not None:
            self._fill_from_waiting(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in ("won", "lost"):
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * self.WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
