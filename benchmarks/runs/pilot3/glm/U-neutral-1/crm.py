"""CRM module: leads, opportunities, and workload management.

Implements the specification in /tmp/aep-lab/specs/crm.md using only the
Python 3 standard library.
"""


class DuplicateLeadError(Exception):
    """Raised by add_lead when a lead with the same normalized email exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__(
            "a lead with this email already exists (id: %s)" % existing_id
        )


_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
_FINAL_STAGES = ("won", "lost")
_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


def _is_int(value):
    """True for genuine ints (bools excluded)."""
    return isinstance(value, int) and not isinstance(value, bool)


class CRM:
    """Customer relationship manager over reps, leads and opportunities."""

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
        self._waiting = []  # FIFO queue of lead ids with no owner
        self._emails = set()
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        user = self._users[rep_id]
        if user["role"] != "rep":
            return 0
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                total += 1
        return total

    def _has_capacity(self, rep_id):
        user = self._users[rep_id]
        return user["role"] == "rep" and self._load(rep_id) < user["capacity"]

    def _pick_rep(self):
        """Rep with the lowest load among those below capacity (ties: smallest id)."""
        best_id = None
        best_key = None
        for user_id, user in self._users.items():
            if user["role"] != "rep":
                continue
            if self._load(user_id) >= user["capacity"]:
                continue
            key = (self._load(user_id), user_id)
            if best_key is None or key < best_key:
                best_key = key
                best_id = user_id
        return best_id

    def _assign_waiting(self, rep_id):
        """Fill rep_id's free slots from the FIFO waiting queue."""
        capacity = self._users[rep_id]["capacity"]
        while self._load(rep_id) < capacity and self._waiting:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        # 1. email
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain[1:-1]:
            raise ValueError("email domain must contain an interior '.'")
        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        # 3. source
        if source not in _SOURCE_SCORES:
            raise ValueError("invalid source")
        # 4. duplicate normalized email
        if normalized in self._emails:
            for lead in self.leads.values():
                if lead["email"] == normalized:
                    raise DuplicateLeadError(lead["id"])
        # 5. id and score
        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
        score = _SOURCE_SCORES[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        # 6. owner
        owner = self._pick_rep()
        # 7. store
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
        self._emails.add(normalized)
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
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
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGES:
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        current_index = _STAGE_ORDER.index(opp["stage"])
        if stage != "lost" and stage != _STAGE_ORDER[current_index + 1]:
            raise ValueError("stage must be 'lost' or the immediate next stage")
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("moving to negotiation above 50000 needs a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            owner = opp["owner"]
            if owner is not None:
                self._assign_waiting(owner)

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not _is_int(pct) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("actor is not the owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer")
        if new_owner not in self._users or self._users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if not self._has_capacity(new_owner):
            raise ValueError("new_owner has no free capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if previous_owner is not None:
            self._assign_waiting(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won_total += opp["amount"]
            elif stage != "lost":
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
