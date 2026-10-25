"""Minimal in-memory CRM implementing the module contract in the spec."""

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCES = ("web", "referral", "event")
STAGES = ("prospect", "proposal", "negotiation", "won")
NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
FINAL = ("won", "lost")
BASE_SCORE = {"web": 10, "referral": 30, "event": 20}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


def normalize_email(email):
    return email.strip().lower()


def valid_email(email):
    if email.count("@") != 1:
        return False
    local, domain = email.split("@")
    if not local:
        return False
    return "." in domain[1:-1]


class CRM:
    def __init__(self, reps):
        self.reps = {}
        for rep in reps:
            self.reps[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # -- helpers ---------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _role(self, uid):
        rep = self.reps.get(uid)
        return rep["role"] if rep is not None else None

    def _require_owner_or_manager(self, actor, owner):
        if actor != owner and self._role(actor) != "manager":
            raise PermissionError("actor %r may not act on this entity" % (actor,))

    def _require_manager(self, actor):
        if self._role(actor) != "manager":
            raise PermissionError("actor %r is not a manager" % (actor,))

    def _load(self, uid):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == uid and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == uid and opp["stage"] not in FINAL:
                load += 1
        return load

    def _pick_rep(self):
        best = None
        best_load = None
        for uid in sorted(self.reps):
            rep = self.reps[uid]
            if rep["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= rep["capacity"]:
                continue
            if best is None or load < best_load:
                best = uid
                best_load = load
        return best

    def _free_slot(self, uid):
        rep = self.reps[uid]
        while self.waiting and self._load(uid) < rep["capacity"]:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = uid
            self.log.append(("assign", lead_id, "system"))

    # -- methods ---------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        if not isinstance(email, str) or not valid_email(normalize_email(email)):
            raise ValueError("invalid email")
        normalized = normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in SOURCES:
            raise ValueError("invalid source")
        for lead_id, lead in self.leads.items():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead_id)

        score = BASE_SCORE[source]
        if normalized.split("@")[1] not in FREE_DOMAINS:
            score += 15
        owner = self._pick_rep()
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        self._require_owner_or_manager(actor, lead["owner"])
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score below threshold")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._require_owner_or_manager(actor, lead["owner"])
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
        if stage not in STAGES and stage != "lost":
            raise ValueError("unknown stage: %r" % (stage,))
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in FINAL:
            raise ValueError("opportunity is already final")
        if stage != "lost" and stage != NEXT_STAGE.get(opp["stage"]):
            raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and self._role(actor) != "manager":
            raise PermissionError("negotiation above 50000 requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        self._require_owner_or_manager(actor, opp["owner"])
        if opp["stage"] in FINAL:
            raise ValueError("opportunity is already final")
        if self._role(actor) != "manager" and pct > 10:
            raise PermissionError("non-manager discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount above 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        self._require_manager(actor)
        target = self.reps.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by %r" % (new_owner,))
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
            if opp["stage"] in FINAL:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
