"""CRM module per specs/crm.md."""

_FINAL_STAGES = ("won", "lost")
_NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won", "lost")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {}
        for r in reps:
            self.users[r["id"]] = r
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO of lead ids with owner None
        self._lead_n = 0
        self._opp_n = 0

    # ---- helpers -------------------------------------------------------
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _role(self, uid):
        u = self.users.get(uid)
        return u["role"] if u else None

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                n += 1
        return n

    def _pick_owner(self):
        best = None
        best_load = None
        for rid in sorted(self.users):
            u = self.users[rid]
            if u["role"] != "rep":
                continue
            load = self._load(rid)
            if load < u["capacity"]:
                if best is None or load < best_load:
                    best = rid
                    best_load = load
        return best

    def _free_slot(self, rep_id):
        u = self.users.get(rep_id)
        if not u or u["role"] != "rep":
            return
        while self._waiting and self._load(rep_id) < u["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ---- API -----------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        at = normalized.find("@")
        if at < 0 or normalized.count("@") != 1:
            raise ValueError("invalid email")
        local = normalized[:at]
        domain = normalized[at + 1:]
        if not local:
            raise ValueError("invalid email")
        dot = domain.find(".")
        if dot <= 0 or dot >= len(domain) - 1:
            raise ValueError("invalid email")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        if source not in _SOURCE_SCORE:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_n += 1
        lead_id = "L%d" % self._lead_n
        score = _SOURCE_SCORE[source]
        if domain not in _FREE_DOMAINS:
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
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and self._role(actor) != "manager":
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead")
        lead = self.leads[lead_id]
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and self._role(actor) != "manager":
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("lead must be qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_n += 1
        opp_id = "O%d" % self._opp_n
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
            raise ValueError("no such opportunity")
        opp = self.opps[opp_id]
        if stage not in _STAGE_ORDER:
            raise ValueError("invalid stage")
        if actor != opp["owner"] and self._role(actor) != "manager":
            raise PermissionError("not owner or manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        if stage != "lost" and _NEXT.get(opp["stage"]) != stage:
            raise ValueError("not the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and self._role(actor) != "manager":
            raise PermissionError("manager required for high-value negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        opp = self.opps[opp_id]
        if not isinstance(pct, int) or isinstance(pct, bool) or pct < 1 or pct > 30:
            raise ValueError("pct must be int 1..30")
        if actor != opp["owner"] and self._role(actor) != "manager":
            raise PermissionError("not owner or manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        if self._role(actor) != "manager" and pct > 10:
            raise PermissionError("rep discount exceeds 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        opp = self.opps[opp_id]
        if self._role(actor) != "manager":
            raise PermissionError("manager required")
        nu = self.users.get(new_owner)
        if not nu or nu["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self._load(new_owner) >= nu["capacity"]:
            raise ValueError("new owner at capacity")

        prev_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(prev_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in _FINAL_STAGES:
                if stage == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
