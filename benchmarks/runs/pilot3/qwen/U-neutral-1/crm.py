"""Tiny CRM: lead intake, routing, qualification, conversion and pipeline ops.

Implements the module contract in /tmp/aep-lab/specs/crm.md using only the
Python 3 standard library.
"""

_SOURCES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_VALID_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_FINAL_STAGES = ("won", "lost")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
_VALID_SOURCES = ("web", "referral", "event")


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead for existing id %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {}
        for user in reps:
            self.users[user["id"]] = {"role": user["role"], "capacity": user["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        # FIFO list of lead ids whose owner is None (waiting for a free slot).
        self._waiting = []
        self._lead_counter = 0
        self._opp_counter = 0

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #

    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _pick_rep(self):
        best = None
        for uid, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load < user["capacity"]:
                if best is None or (load, uid) < best:
                    best = (load, uid)
        return None if best is None else best[1]

    def _free_slots(self, rep_id):
        """Assign oldest waiting leads to rep_id while it has capacity."""
        user = self.users[rep_id]
        while self._waiting and self._load(rep_id) < user["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _validate_email(email):
        """Return (normalized_email, domain) or raise ValueError."""
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain[1:-1]:
            raise ValueError("email domain needs a '.' that is not first or last")
        return normalized, domain

    def _get_lead(self, lead_id):
        lead = self.leads.get(lead_id) if isinstance(lead_id, str) else None
        if lead is None:
            raise ValueError("unknown lead id: %r" % (lead_id,))
        return lead

    def _get_opp(self, opp_id):
        opp = self.opps.get(opp_id) if isinstance(opp_id, str) else None
        if opp is None:
            raise ValueError("unknown opportunity id: %r" % (opp_id,))
        return opp

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized, domain = self._validate_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _VALID_SOURCES:
            raise ValueError("source must be web, referral or event")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        score = _SOURCES[source] + (0 if domain in _FREE_DOMAINS else 15)
        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
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
        self._check_actor(actor)
        lead = self._get_lead(lead_id)
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self._get_lead(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
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
        opp = self._get_opp(opp_id)
        if stage not in _VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed")
        next_stage = _STAGE_ORDER[_STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("invalid stage transition to %r" % (stage,))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager approval required above 50000")
        owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slots(owner)

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("actor must be the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may apply at most 10 percent discount")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("actor must be a manager")
        user = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be the id of a rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the current owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new_owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slots(previous_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
