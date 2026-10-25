"""crm.py — minimal CRM with lead routing, opportunities, and permissions."""

_VALID_SOURCES = {"web", "referral", "event"}
_COMMON_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_FINAL_STAGES = ("won", "lost")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__(
            "duplicate lead email (existing lead: {})".format(existing_id)
        )


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
        self._lead_counter = 0
        self._opp_counter = 0
        self._waiting = []  # FIFO queue of lead ids with no owner

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #
    def _check_actor(self, actor):
        """Unknown actor: PermissionError. Checked first in every method."""
        if actor not in self._users:
            raise PermissionError("unknown actor: {}".format(actor))

    def _load(self, rep_id):
        """Load of a rep: active leads (new/qualified) + open opportunities."""
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                total += 1
        return total

    def _can_act(self, actor, owner):
        """Owner or any manager may act."""
        return owner == actor or self._users[actor]["role"] == "manager"

    def _assign_waiting(self, rep_id):
        """Fill the rep's freed slot from the FIFO waiting queue."""
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------ #
    # add_lead
    # ------------------------------------------------------------------ #
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        # 1. email validation
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email domain")

        # 2. name validation
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        # 3. source validation
        if source not in _VALID_SOURCES:
            raise ValueError("invalid source")

        # 4. duplicate email
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(existing_id=lead["id"])

        # 5. id + score
        self._lead_counter += 1
        lead_id = "L{}".format(self._lead_counter)
        score = _SOURCE_SCORE[source]
        if domain not in _COMMON_DOMAINS:
            score += 15

        # 6. owner assignment (lowest load below capacity; ties: smallest id)
        candidates = [
            (self._load(uid), uid)
            for uid, user in sorted(self._users.items())
            if user["role"] == "rep" and self._load(uid) < user["capacity"]
        ]
        owner = min(candidates)[1] if candidates else None
        if owner is None:
            self._waiting.append(lead_id)

        # 7. create + log
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
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    # ------------------------------------------------------------------ #
    # qualify
    # ------------------------------------------------------------------ #
    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        if not self._can_act(actor, lead["owner"]):
            raise PermissionError("not the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead is not in 'new' status")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # ------------------------------------------------------------------ #
    # convert
    # ------------------------------------------------------------------ #
    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._can_act(actor, lead["owner"]):
            raise PermissionError("not the lead's owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_counter += 1
        opp_id = "O{}".format(self._opp_counter)
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

    # ------------------------------------------------------------------ #
    # advance
    # ------------------------------------------------------------------ #
    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if stage not in _STAGES:
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        if not self._can_act(actor, opp["owner"]):
            raise PermissionError("not the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        current_index = _STAGE_ORDER.index(opp["stage"])
        if stage != "lost" and stage != _STAGE_ORDER[current_index + 1]:
            raise ValueError("invalid stage transition")
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and self._users[actor]["role"] != "manager"
        ):
            raise PermissionError("moving to negotiation requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    # ------------------------------------------------------------------ #
    # discount
    # ------------------------------------------------------------------ #
    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if not self._can_act(actor, opp["owner"]):
            raise PermissionError("not the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if self._users[actor]["role"] != "manager" and pct > 10:
            raise PermissionError("non-manager discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ------------------------------------------------------------------ #
    # transfer
    # ------------------------------------------------------------------ #
    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        if self._users[actor]["role"] != "manager":
            raise PermissionError("only a manager may transfer")
        if (
            new_owner not in self._users
            or self._users[new_owner]["role"] != "rep"
        ):
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner equals current owner")
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    # ------------------------------------------------------------------ #
    # forecast
    # ------------------------------------------------------------------ #
    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in _FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
