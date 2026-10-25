"""A small in-memory CRM implementing the behaviour described in the spec."""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead email (existing lead id: %r)" % (existing_id,))


_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_FINAL_STAGES = ("won", "lost")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
_SOURCES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")


class CRM:
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
        self.waiting = []  # FIFO queue of lead ids without an owner
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ helpers

    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _lead(self, lead_id):
        """Look up a lead, treating non-string ids as simply unknown."""
        return self.leads.get(lead_id) if isinstance(lead_id, str) else None

    def _opp(self, opp_id):
        """Look up an opportunity, treating non-string ids as simply unknown."""
        return self.opps.get(opp_id) if isinstance(opp_id, str) else None

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best = None
        best_load = None
        for uid, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= user["capacity"]:
                continue
            if best is None or load < best_load or (load == best_load and uid < best):
                best = uid
                best_load = load
        return best

    def _assign_waiting(self, rep_id):
        capacity = self.users[rep_id]["capacity"]
        while self.waiting and self._load(rep_id) < capacity:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ----------------------------------------------------------------- methods

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not any(ch == "." and i != 0 and i != len(domain) - 1
                   for i, ch in enumerate(domain)):
            raise ValueError("email domain must contain a dot that is neither first nor last")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        stripped_name = name.strip()

        if not isinstance(source, str) or source not in _SOURCES:
            raise ValueError("invalid source: %r" % (source,))

        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])

        score = _SOURCES[source]
        if domain not in _FREE_DOMAINS:
            score += 15

        owner = self._pick_owner()
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        lead = {
            "id": lead_id,
            "email": normalized,
            "name": stripped_name,
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
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
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
        self._require_actor(actor)
        opp = self._opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGE_ORDER and stage != "lost":
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        next_stage = _STAGE_ORDER[_STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("invalid transition: %s -> %s" % (opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("a manager is required for this amount")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("a non-manager may use at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        target = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")
        if self._load(new_owner) >= target["capacity"]:
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
            weighted += opp["amount"] * _WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
