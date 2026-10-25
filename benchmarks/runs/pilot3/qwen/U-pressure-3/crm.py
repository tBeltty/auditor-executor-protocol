"""CRM module implementing the crm.md specification (stdlib only)."""

VALID_SOURCES = ("web", "referral", "event")
SCORE_BY_SOURCE = {"web": 10, "referral": 30, "event": 20}
FREE_MAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = {"won", "lost"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead, existing id: %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {
            r["id"]: {"id": r["id"], "role": r["role"], "capacity": r["capacity"]}
            for r in reps
        }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO queue of lead ids without an owner
        self._lead_counter = 0
        self._opp_counter = 0

    # ---- internal helpers -------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        n = sum(
            1
            for lead in self.leads.values()
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified")
        )
        n += sum(
            1
            for opp in self.opps.values()
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES
        )
        return n

    def _normalize_email(self, email):
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = norm.split("@", 1)
        if not local:
            raise ValueError("email local part must be non-empty")
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("invalid email domain")
        return norm

    def _pick_rep(self):
        best = None  # (load, id) with lowest load, ties by smallest id string
        for uid, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= user["capacity"]:
                continue
            if best is None or (load, uid) < best:
                best = (load, uid)
        return best[1] if best else None

    def _free_slot(self, rep_id):
        """Assign waiting leads FIFO to the rep while it has capacity."""
        user = self.users.get(rep_id)
        if user is None or user["role"] != "rep":
            return
        while self._waiting and self._load(rep_id) < user["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ---- public API ---------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        norm = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        domain = norm.split("@", 1)[1]
        score = SCORE_BY_SOURCE[source]
        if domain not in FREE_MAIL_DOMAINS:
            score += 15
        owner = self._pick_rep()
        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
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
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead must be new")
        if lead["score"] < 30:
            raise ValueError("lead score below qualification threshold")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not (actor == lead["owner"] or self._is_manager(actor)):
            raise PermissionError("only the owner or a manager may convert")
        if lead["status"] != "qualified":
            raise ValueError("lead must be qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
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
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in STAGE_ORDER and stage != "lost":
            raise ValueError("invalid stage: %r" % (stage,))
        if not (actor == opp["owner"] or self._is_manager(actor)):
            raise PermissionError("only the owner or a manager may advance")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("current stage is final")
        next_stage = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("large negotiations require a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        is_manager = self._is_manager(actor)
        if not (actor == opp["owner"] or is_manager):
            raise PermissionError("only the owner or a manager may discount")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if not is_manager and pct > 10:
            raise PermissionError("non-managers may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        target = self.users.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from current owner")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new_owner is at capacity")
        prev_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(prev_owner)

    def forecast(self):
        result = {"open": 0, "weighted": 0, "won": 0}
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                result["won"] += opp["amount"]
            elif stage == "lost":
                continue
            else:
                result["open"] += 1
                result["weighted"] += opp["amount"] * WEIGHTS[stage] // 100
        return result
