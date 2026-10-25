"""CRM module: lead routing, qualification, conversion and opportunity handling.

Implements the behaviour described in specs/crm.md.
"""

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})

STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = frozenset({"won", "lost"})
VALID_STAGES = frozenset(STAGE_ORDER) | {"lost"}
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

LOAD_STATUSES = frozenset({"new", "qualified"})


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id, message=None):
        if message is None:
            message = "duplicate lead, existing id: %s" % (existing_id,)
        super().__init__(message)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = rep
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []          # FIFO queue of unassigned lead ids
        self._lead_count = 0        # successful lead creations
        self._opp_count = 0         # successful conversions

    # ------------------------------------------------------------------ helpers

    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in LOAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _capacity(self, rep_id):
        return self.users[rep_id]["capacity"]

    def _has_room(self, rep_id):
        return self._load(rep_id) < self._capacity(rep_id)

    def _pick_owner(self):
        """Rep with the lowest load below capacity; ties broken by smallest id."""
        best_id = None
        best_load = None
        for rep_id in sorted(self.users):
            user = self.users[rep_id]
            if user["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load >= self._capacity(rep_id):
                continue
            if best_load is None or load < best_load:
                best_id = rep_id
                best_load = load
        return best_id

    def _drain_waiting(self, rep_id):
        """Give the oldest waiting leads to rep_id while it has room."""
        if rep_id is None or rep_id not in self.users:
            return
        if self.users[rep_id]["role"] != "rep":
            return
        while self._waiting and self._has_room(rep_id):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _check_email(email):
        """Return (normalized_email, domain) or raise ValueError."""
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@': %r" % (email,))
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part: %r" % (email,))
        # The domain must contain a '.' that is neither its first nor its last
        # character.
        if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
            raise ValueError("email domain must contain an interior '.': %r" % (email,))
        return normalized, domain

    # ------------------------------------------------------------------- API

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        normalized, domain = self._check_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
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
        if not (self._is_manager(actor) or actor == lead["owner"]):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not (self._is_manager(actor) or actor == lead["owner"]):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
        self.opps[opp_id] = {
            "id": opp_id,
            "lead_id": lead["id"],
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
        if stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        manager = self._is_manager(actor)
        if not (manager or actor == opp["owner"]):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        next_stage = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("stage must be 'lost' or %r" % (next_stage,))
        if stage == "negotiation" and opp["amount"] > 50000 and not manager:
            raise PermissionError("manager required to negotiate above 50000")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._drain_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        manager = self._is_manager(actor)
        if not (manager or actor == opp["owner"]):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if not manager and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        target = self.users.get(new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if not self._has_room(new_owner):
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._drain_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage != "lost":
                open_count += 1
                weighted += opp["amount"] * STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
