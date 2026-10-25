"""Tiny CRM domain module."""

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCES = {"web", "referral", "event"}
STAGES = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = {"won", "lost"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {r["id"]: r for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ utils
    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self.users[actor]

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _can_act_on(self, owner, actor):
        return actor == owner or self._is_manager(actor)

    def _load(self, uid):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == uid and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == uid and opp["stage"] not in FINAL_STAGES:
                n += 1
        return n

    def _pick_rep(self):
        best = None
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            key = (load, user["id"])
            if best is None or key < best[0]:
                best = (key, user["id"])
        return best[1] if best else None

    def _assign_waiting(self, uid):
        capacity = self.users[uid]["capacity"]
        while self.waiting and self._load(uid) < capacity:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = uid
            self.log.append(("assign", lead_id, "system"))

    def _lead(self, lead_id):
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    def _opp(self, opp_id):
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp

    # ----------------------------------------------------------------- public
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("invalid email")
        if not any(
            ch == "." and 0 < i < len(domain) - 1 for i, ch in enumerate(domain)
        ):
            raise ValueError("invalid email")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        if source not in SOURCES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = {"web": 10, "referral": 30, "event": 20}[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15
        owner = self._pick_rep()
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self._lead(lead_id)
        if not self._can_act_on(lead["owner"], actor):
            raise PermissionError("not allowed to qualify lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._lead(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._can_act_on(lead["owner"], actor):
            raise PermissionError("not allowed to convert lead")
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
        opp = self._opp(opp_id)
        if stage not in STAGES and stage != "lost":
            raise ValueError("invalid stage")
        if not self._can_act_on(opp["owner"], actor):
            raise PermissionError("not allowed to advance opportunity")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost" and stage != STAGES[STAGES.index(current) + 1]:
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for large negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._opp(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not self._can_act_on(opp["owner"], actor):
            raise PermissionError("not allowed to discount opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount above 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("manager required to transfer")
        user = self.users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        previous = opp["owner"]
        if new_owner == previous:
            raise ValueError("new owner must differ")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner at capacity")

        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in FINAL_STAGES]
        weighted = sum(o["amount"] * WEIGHTS[o["stage"]] // 100 for o in open_opps)
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
