"""In-memory CRM: leads, opportunities, discounts and forecasting.

Implements exactly the behaviour described in the module specification:

* every mutating call is validated completely before any state changes, so a
  failed call leaves ``leads``, ``opps``, ``log`` and the waiting queue untouched;
* every successful call appends exactly the log entries the spec names;
* only users with role ``"rep"`` ever own work; managers never do.
"""

VALID_SOURCES = ("web", "referral", "event")

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")

# Ordered pipeline; "lost" is reachable from any non-final stage.
STAGE_FLOW = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")

FORECAST_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

COUNTED_LEAD_STATUSES = ("new", "qualified")


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the given normalized email."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__(
            "a lead with this email already exists: %r" % (existing_id,)
        )


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
        # FIFO queue of lead ids without an owner, oldest first.
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        """Return the acting user, or raise PermissionError if unknown."""
        try:
            user = self.users.get(actor)
        except TypeError:  # unhashable actor ids are simply unknown
            user = None
        if user is None:
            raise PermissionError("unknown user: %r" % (actor,))
        return user

    @staticmethod
    def _is_manager(user):
        return user["role"] == "manager"

    def _get_lead(self, lead_id):
        try:
            lead = self.leads.get(lead_id)
        except TypeError:
            lead = None
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    def _get_opp(self, opp_id):
        try:
            opp = self.opps.get(opp_id)
        except TypeError:
            opp = None
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp

    def _get_rep(self, rep_id):
        """Return the user when it is a known rep, else raise ValueError."""
        try:
            user = self.users.get(rep_id)
        except TypeError:
            user = None
        if user is None or user["role"] != "rep":
            raise ValueError("unknown rep: %r" % (rep_id,))
        return user

    def _load(self, rep_id):
        """Open leads owned plus open opportunities owned."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in COUNTED_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        """Least loaded rep below its capacity; ties broken by id string order."""
        best_id = None
        best_load = None
        for rep_id in sorted(self.users):
            user = self.users[rep_id]
            if user["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load >= user["capacity"]:
                continue
            if best_id is None or load < best_load:
                best_id = rep_id
                best_load = load
        return best_id

    def _drain_waiting(self, rep_id):
        """Assign queued leads to ``rep_id`` while it is below capacity."""
        if rep_id is None:
            return
        user = self.users.get(rep_id)
        if user is None or user["role"] != "rep":
            return
        while self.waiting and self._load(rep_id) < user["capacity"]:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        """Validate and normalize an email, returning (email, domain)."""
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email needs a non-empty local part")
        if "." not in domain:
            raise ValueError("email domain must contain a '.'")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("email domain '.' must not be first or last")
        return normalized, domain

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        normalized, domain = self._normalize_email(email)

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in VALID_SOURCES:
            raise ValueError("source must be web, referral or event")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq

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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        user = self._require_actor(actor)

        lead = self._get_lead(lead_id)

        if lead["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may qualify")

        if lead["status"] != "new":
            raise ValueError("lead is not new")

        if lead["score"] < 30:
            raise ValueError("lead score is too low to qualify")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        user = self._require_actor(actor)

        lead = self._get_lead(lead_id)

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")

        if lead["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may convert")

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
        user = self._require_actor(actor)

        opp = self._get_opp(opp_id)

        if stage not in ALL_STAGES:
            raise ValueError("unknown stage: %r" % (stage,))

        if opp["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may advance")

        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if stage != "lost":
            index = STAGE_FLOW.index(current)
            if index + 1 >= len(STAGE_FLOW) or STAGE_FLOW[index + 1] != stage:
                raise ValueError(
                    "cannot move from %r to %r" % (current, stage)
                )

        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(user)
        ):
            raise PermissionError(
                "a manager is required for negotiations above 50000"
            )

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in FINAL_STAGES:
            self._drain_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        user = self._require_actor(actor)

        opp = self._get_opp(opp_id)

        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")

        if opp["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may discount")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if not self._is_manager(user) and pct > 10:
            raise PermissionError("only a manager may discount more than 10")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        user = self._require_actor(actor)

        opp = self._get_opp(opp_id)

        if not self._is_manager(user):
            raise PermissionError("only a manager may transfer")

        target = self._get_rep(new_owner)

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")

        previous = opp["owner"]
        if new_owner == previous:
            raise ValueError("opportunity already belongs to this rep")

        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner is at capacity")

        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))

        self._drain_waiting(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in FINAL_STAGES:
                if stage == "won":
                    won_total += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * FORECAST_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
