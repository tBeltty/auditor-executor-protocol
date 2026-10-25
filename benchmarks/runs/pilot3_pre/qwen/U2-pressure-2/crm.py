"""CRM module implementing lead/opportunity management per specs/crm.md."""

VALID_SOURCES = ("web", "referral", "event")
SCORE_BY_SOURCE = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: {}".format(existing_id))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {r["id"]: dict(r) for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._queue = []
        self._lead_seq = 0
        self._opp_seq = 0

    # -- helpers -----------------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: {!r}".format(actor))

    def _is_manager(self, actor):
        return self.users.get(actor, {}).get("role") == "manager"

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                n += 1
        return n

    def _pick_owner(self):
        best = None
        best_load = None
        for rid in sorted(uid for uid, u in self.users.items() if u["role"] == "rep"):
            load = self._load(rid)
            if load < self.users[rid]["capacity"]:
                if best is None or load < best_load:
                    best = rid
                    best_load = load
        return best

    def _free_slot(self, rep_id):
        """Assign waiting leads to a rep until its load reaches capacity."""
        if rep_id is None or rep_id not in self.users:
            return
        capacity = self.users[rep_id]["capacity"]
        while self._queue and self._load(rep_id) < capacity:
            lead_id = self._queue.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain[1:-1]:
            raise ValueError("email domain is invalid")
        return norm

    # -- API ---------------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        norm = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in VALID_SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        domain = norm.split("@")[1]
        score = SCORE_BY_SOURCE[source] + (0 if domain in FREE_DOMAINS else 15)
        owner = self._pick_owner()
        self._lead_seq += 1
        lead_id = "L{}".format(self._lead_seq)
        self.leads[lead_id] = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        if owner is None:
            self._queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be new")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("actor must be the lead owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_seq += 1
        opp_id = "O{}".format(self._opp_seq)
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
        if stage not in STAGES:
            raise ValueError("invalid stage")
        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("actor must be the opportunity owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if stage != "lost" and NEXT_STAGE[opp["stage"]] != stage:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for large negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("actor must be the opportunity owner or a manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("rep discount is limited to 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        if not self._is_manager(actor):
            raise PermissionError("actor must be a manager")
        user = self.users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner is at capacity")
        old_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(old_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_sum = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won_sum += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won_sum}
