"""A tiny in-memory CRM: leads, opportunities, ownership and load balancing.

The module implements the behaviour described in the project specification:
users are either ``rep`` or ``manager``; only reps receive work; every
mutating call is atomic (a failing call leaves the CRM untouched) and every
successful call records exactly the log entries the specification names.
"""

STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = ("won", "lost")
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}

OPEN_LEAD_STATUSES = ("new", "qualified")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

SYSTEM_ACTOR = "system"


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead email; existing lead is %r" % (existing_id,))


class CRM:
    def __init__(self, reps):
        self.reps = [dict(rep) for rep in reps]
        self.users = {rep["id"]: rep for rep in self.reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        # FIFO queue of unowned lead ids, in creation order.
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ helpers

    def _user(self, actor):
        """Return the user record for ``actor`` or raise PermissionError."""
        try:
            user = self.users.get(actor)
        except TypeError:  # unhashable actor, e.g. a list
            user = None
        if user is None:
            raise PermissionError("unknown user: %r" % (actor,))
        return user

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    @staticmethod
    def _lookup(mapping, entity_id):
        """Dict lookup that treats any non-str id as simply unknown."""
        return mapping.get(entity_id) if isinstance(entity_id, str) else None

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in OPEN_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_rep(self):
        """Rep with the lowest load below capacity; ties go to the smallest id."""
        candidates = []
        for rep in self.reps:
            if rep["role"] != "rep":
                continue
            load = self._load(rep["id"])
            if load < rep["capacity"]:
                candidates.append((load, rep["id"]))
        if not candidates:
            return None
        return min(candidates)[1]

    def _assign_waiting(self, rep_id):
        """Hand waiting leads to ``rep_id`` while it still has spare capacity."""
        capacity = self.users[rep_id]["capacity"]
        while self.waiting and self._load(rep_id) < capacity:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, SYSTEM_ACTOR))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        # A dot that is neither the first nor the last character of the domain.
        if not any(domain[i] == "." for i in range(1, len(domain) - 1)):
            raise ValueError("email domain must contain an inner '.'")
        return normalized, domain

    # ----------------------------------------------------------------- methods

    def add_lead(self, email, name, source, actor):
        self._user(actor)
        normalized, domain = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("source must be one of %s" % (sorted(SOURCE_SCORES),))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_rep()
        self._lead_seq += 1
        lead_id = "L%d" % (self._lead_seq,)
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
        self._user(actor)
        lead = self._lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead status is %r" % (lead["status"],))
        if lead["score"] < 30:
            raise ValueError("lead score %d is too low" % (lead["score"],))

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._user(actor)
        lead = self._lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status is %r" % (lead["status"],))
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % (self._opp_seq,)
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
        self._user(actor)
        opp = self._lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        index = STAGE_ORDER.index(opp["stage"])
        if stage != "lost" and stage != STAGE_ORDER[index + 1]:
            raise ValueError("cannot move from %r to %r" % (opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for large negotiations")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._user(actor)
        opp = self._lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int between 1 and 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("only a manager may discount more than 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        user = self._user(actor)
        opp = self._lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if user["role"] != "manager":
            raise PermissionError("only a manager may transfer opportunities")
        new_user = self._lookup(self.users, new_owner)
        if new_user is None or new_user["role"] != "rep":
            raise ValueError("new_owner must be a rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner already owns this opportunity")
        if self._load(new_owner) >= new_user["capacity"]:
            raise ValueError("new_owner has no spare capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in FINAL_STAGES:
                if stage == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
