"""In-memory CRM implementing the behaviour described in ``specs/crm.md``.

The module is deliberately self-contained: no I/O, no network, no third-party
imports.  All mutating calls validate everything they need before touching the
state, so a failed call leaves ``leads``, ``opps``, the waiting queue, the id
counters and ``log`` exactly as they were.
"""

STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
ALL_STAGES = STAGE_ORDER + ("lost",)
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")


def _normalize_email(email):
    """Validate ``email`` and return its normalized form or raise ValueError."""
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
    if not any(
        char == "." and index != 0 and index != len(domain) - 1
        for index, char in enumerate(domain)
    ):
        raise ValueError("email domain must contain an interior '.'")
    return normalized


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the normalized email."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


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
    def _check_actor(self, actor):
        """Unknown actors are rejected before anything else in every method."""
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        """Lowest load below capacity; ties broken by smallest id string."""
        best_id = None
        best_load = None
        for user_id in sorted(self._users):
            user = self._users[user_id]
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load >= user["capacity"]:
                continue
            if best_load is None or load < best_load:
                best_load = load
                best_id = user_id
        return best_id

    def _assign_waiting(self, user_id):
        """Fill a rep's free slots from the FIFO queue, logging each assignment."""
        user = self._users.get(user_id)
        if user is None or user["role"] != "rep":
            return
        while self._waiting and self._load(user_id) < user["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = _normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        domain = normalized.partition("@")[2]
        if domain not in FREE_EMAIL_DOMAINS:
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
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is below the qualification threshold")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        if lead["owner"] != actor and not self._is_manager(actor):
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
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost":
            current_index = STAGE_ORDER.index(opp["stage"])
            if (
                current_index + 1 >= len(STAGE_ORDER)
                or STAGE_ORDER[current_index + 1] != stage
            ):
                raise ValueError("stage is not the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("a manager is required for big deals")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("pct must be an integer between 1 and 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("a non-manager may discount at most 10 percent")
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
            raise PermissionError("only a manager may transfer an opportunity")
        target = self._users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
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
        won_total = 0
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won_total += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * weights[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
