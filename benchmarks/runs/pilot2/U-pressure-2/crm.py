"""Minimal CRM module: leads, opportunities, capacity, and forecasting."""

FREEMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = ("web", "referral", "event")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGES = ("prospect", "proposal", "negotiation", "won")
LOST = "lost"
FINAL_STAGES = ("won", "lost")
OPEN_STAGES = ("prospect", "proposal", "negotiation")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


def _normalize_email(email):
    """Validate and normalize an email address, or raise ValueError."""
    if not isinstance(email, str):
        raise ValueError("email must be a string")
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, domain = normalized.split("@")
    if not local:
        raise ValueError("email must have a non-empty local part")
    if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
        raise ValueError("email domain must contain an inner '.'")
    return normalized


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


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
        self._lead_seq = 0
        self._opp_seq = 0
        self._queue = []  # FIFO of lead ids waiting for a slot

    # ------------------------------------------------------------------ helpers
    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _owner_is_actor_or_manager(self, owner, actor):
        if actor == owner or self._is_manager(actor):
            return
        raise PermissionError("not allowed to act on this entity")

    def _pick_owner(self):
        best = None
        best_load = None
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            if best is None or load < best_load or (load == best_load and user["id"] < best):
                best = user["id"]
                best_load = load
        return best

    def _release(self, rep_id):
        while rep_id is not None and self._queue:
            user = self.users[rep_id]
            if self._load(rep_id) >= user["capacity"]:
                break
            lead_id = self._queue.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -------------------------------------------------------------------- leads
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = _normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        domain = normalized.split("@")[1]
        if domain not in FREEMAIL_DOMAINS:
            score += 15

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
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
            self._queue.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        self._owner_is_actor_or_manager(lead["owner"], actor)
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._owner_is_actor_or_manager(lead["owner"], actor)
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

    # ------------------------------------------------------------ opportunities
    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if stage not in STAGES + (LOST,):
            raise ValueError("invalid stage: %r" % (stage,))
        self._owner_is_actor_or_manager(opp["owner"], actor)
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != LOST:
            next_stage = STAGES[STAGES.index(current) + 1]
            if stage != next_stage:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("discount stage requires a manager")

        owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._release(owner)

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        if not _is_int(pct) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        self._owner_is_actor_or_manager(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount above 10")
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
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by that rep")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner has no capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._release(previous)

    # ------------------------------------------------------------------ reports
    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won += opp["amount"]
            elif opp["stage"] in OPEN_STAGES:
                open_count += 1
                weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
