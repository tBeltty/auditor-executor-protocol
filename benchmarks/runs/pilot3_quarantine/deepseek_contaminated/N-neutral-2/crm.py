"""A small CRM module implementing leads, opportunities and conversion rules.

Only the Python standard library is used.  Every public method takes the
acting user's id as its final ``actor`` argument and checks that the actor is
a known user before doing anything else.
"""

FREE_EMAIL_DOMAINS = frozenset(("gmail.com", "yahoo.com", "outlook.com"))

SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}

STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
OPEN_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

LEAD_OPEN_STATUSES = ("new", "qualified")


class DuplicateLeadError(Exception):
    """Raised when a lead is added for an email that already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead email, existing lead: %s" % (existing_id,))


class CRM:
    """In-memory CRM with reps, leads, opportunities and an audit log."""

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
        self._lead_counter = 0
        self._opp_counter = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.reps:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self.reps[actor]["role"] == "manager"

    def _load(self, rep_id):
        """Number of open leads plus open opportunities owned by ``rep_id``."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in LEAD_OPEN_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        """Rep with the lowest load below capacity; ties by smallest id."""
        best_id = None
        best_load = None
        for rep_id in sorted(self.reps):
            rep = self.reps[rep_id]
            if rep["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load >= rep["capacity"]:
                continue
            if best_load is None or load < best_load:
                best_id = rep_id
                best_load = load
        return best_id

    def _assign_waiting(self, rep_id):
        """Fill a rep's free slots from the FIFO waiting queue."""
        capacity = self.reps[rep_id]["capacity"]
        while self.waiting and self._load(rep_id) < capacity:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must not be empty")
        if "." not in domain:
            raise ValueError("email domain must contain a '.'")
        positions = [i for i, char in enumerate(domain) if char == "."]
        if not any(0 < pos < len(domain) - 1 for pos in positions):
            raise ValueError("email domain has an invalid '.' position")
        return normalized, domain

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized, domain = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in ("web", "referral", "event"):
            raise ValueError("source must be web, referral or event")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
        score = SOURCE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15
        owner = self._pick_owner()
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
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not (self._is_manager(actor) or lead["owner"] == actor):
            raise PermissionError("actor cannot qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not (self._is_manager(actor) or lead["owner"] == actor):
            raise PermissionError("actor cannot convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        self.opps[opp_id] = opp
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not (self._is_manager(actor) or opp["owner"] == actor):
            raise PermissionError("actor cannot advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost":
            next_stage = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]
            if stage != next_stage:
                raise ValueError("illegal stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("negotiation over 50000 needs a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int between 1 and 30")
        if not (self._is_manager(actor) or opp["owner"] == actor):
            raise PermissionError("actor cannot discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount by at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        if (
            not isinstance(new_owner, str)
            or new_owner not in self.reps
            or self.reps[new_owner]["role"] != "rep"
        ):
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already belongs to new_owner")
        if self._load(new_owner) >= self.reps[new_owner]["capacity"]:
            raise ValueError("new_owner has no free capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won += opp["amount"]
            elif opp["stage"] == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * OPEN_STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
