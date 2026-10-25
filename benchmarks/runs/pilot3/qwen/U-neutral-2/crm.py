"""CRM module implementing the sales pipeline described in specs/crm.md."""

_STAGE_NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_VALID_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_FINAL_STAGES = ("won", "lost")
_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_FREE_MAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_FORECAST_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id=None):
        super().__init__("duplicate lead (existing id: %r)" % (existing_id,))
        self.existing_id = existing_id


def _normalize_email(email):
    """Return the normalized email, or None when the address is invalid."""
    if not isinstance(email, str):
        return None
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        return None
    local, domain = normalized.split("@", 1)
    if not local:
        return None
    # The domain must contain a "." that is neither its first nor last char.
    if "." not in domain[1:-1]:
        return None
    return normalized


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = rep
        self.leads = {}
        self.opps = {}
        self.log = []
        self._queue = []  # FIFO of waiting lead ids with no owner
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ core

    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor_id):
        user = self.users.get(actor_id)
        return user is not None and user.get("role") == "manager"

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
        """Lowest-load rep below capacity; ties broken by smallest id."""
        best = None
        best_key = None
        for user in self.users.values():
            if user.get("role") != "rep":
                continue
            rep_id = user["id"]
            load = self._load(rep_id)
            if load < user["capacity"]:
                key = (load, rep_id)
                if best_key is None or key < best_key:
                    best_key = key
                    best = rep_id
        return best

    def _free_slot(self, rep_id):
        """Assign the oldest waiting leads to rep_id while it has capacity."""
        capacity = self.users[rep_id]["capacity"]
        while self._load(rep_id) < capacity and self._queue:
            lead_id = self._queue.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ----------------------------------------------------------------- leads

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = _normalize_email(email)
        if normalized is None:
            raise ValueError("invalid email: %r" % (email,))
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        domain = normalized.split("@", 1)[1]
        score = _SOURCE_SCORES[source]
        if domain not in _FREE_MAIL_DOMAINS:
            score += 15
        owner = self._pick_rep()
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
            self._queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the lead's owner or a manager may qualify it")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the lead's owner or a manager may convert it")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        opp = {
            "id": opp_id,
            "lead_id": lead["id"],
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        self.opps[opp_id] = opp
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    # ------------------------------------------------------------------ opps

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the opportunity's owner or a manager may advance it")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed")
        if stage != "lost" and stage != _STAGE_NEXT[opp["stage"]]:
            raise ValueError("invalid transition from %s to %s" % (opp["stage"], stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("a manager must move large deals into negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the opportunity's owner or a manager may discount it")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer an opportunity")
        user = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user.get("role") != "rep":
            raise ValueError("new_owner must be a known rep: %r" % (new_owner,))
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner already owns the opportunity")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new_owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

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
                weighted += opp["amount"] * _FORECAST_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
