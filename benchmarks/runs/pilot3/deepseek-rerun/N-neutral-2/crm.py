"""A small in-memory CRM: leads, opportunities, assignment and forecasting.

The module implements the behaviour described in the project specification:
every mutating method validates its input *before* touching state, and a call
that raises leaves ``leads``, ``opps``, ``log`` and internal bookkeeping
untouched.
"""

FREE_EMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGE_SEQUENCE = ("prospect", "proposal", "negotiation", "won")
VALID_STAGES = frozenset(STAGE_SEQUENCE + ("lost",))
FINAL_STAGES = frozenset({"won", "lost"})
FORECAST_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

LEAD_OPEN_STATUSES = frozenset({"new", "qualified"})


class DuplicateLeadError(Exception):
    """Raised when a lead email is already present in the CRM."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("lead email already exists with id %s" % (existing_id,))


def _lookup(mapping, key):
    """Return ``mapping[key]`` or ``None`` when the key is absent/unhashable."""
    try:
        return mapping.get(key)
    except TypeError:
        return None


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class CRM:
    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in LEAD_OPEN_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_rep(self):
        best_key = None
        best_id = None
        for user_id, user in self._users.items():
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load >= user["capacity"]:
                continue
            key = (load, user_id)
            if best_key is None or key < best_key:
                best_key = key
                best_id = user_id
        return best_id

    def _assign_waiting(self, rep_id):
        if rep_id is None or rep_id not in self._users:
            return
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not domain:
            raise ValueError("email must have a domain")
        dots = [index for index, char in enumerate(domain) if char == "."]
        if not any(0 < index < len(domain) - 1 for index in dots):
            raise ValueError("email domain must contain a valid '.'")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("unknown source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_rep()
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

        lead = _lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not (self._is_manager(actor) or lead["owner"] == actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low to qualify")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = _lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        if not (self._is_manager(actor) or lead["owner"] == actor):
            raise PermissionError("actor may not convert this lead")
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
        self._require_actor(actor)

        opp = _lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(stage, str) or stage not in VALID_STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        if not (self._is_manager(actor) or opp["owner"] == actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost":
            expected = STAGE_SEQUENCE[STAGE_SEQUENCE.index(opp["stage"]) + 1]
            if stage != expected:
                raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("large deal needs a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = _lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not _is_int(pct) or pct < 1 or pct > 30:
            raise ValueError("pct must be an integer in 1..30")
        if not (self._is_manager(actor) or opp["owner"] == actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount above 10 requires a manager")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = _lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        new_user = _lookup(self._users, new_owner)
        if new_user is None or new_user["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already belongs to that rep")
        if self._load(new_owner) >= new_user["capacity"]:
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
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * FORECAST_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
