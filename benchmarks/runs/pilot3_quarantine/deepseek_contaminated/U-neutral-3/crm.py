"""CRM module: leads, opportunities and assignment rules.

Python standard library only.
"""

SOURCES = ("web", "referral", "event")
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
FINAL_STAGES = ("won", "lost")
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


def _is_valid_email_domain(domain):
    """True if domain contains a dot that is neither first nor last char."""
    last = len(domain) - 1
    for index, char in enumerate(domain):
        if char == "." and 0 < index < last:
            return True
    return False


def _normalize_email(email):
    if not isinstance(email, str):
        raise ValueError("email must be a str")
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, domain = normalized.split("@")
    if not local:
        raise ValueError("email must have a non-empty local part")
    if not domain or not _is_valid_email_domain(domain):
        raise ValueError("email must have a valid domain")
    return normalized


class CRM(object):
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = rep
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # -- internal helpers -------------------------------------------------
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _is_rep(self, actor):
        return self.users[actor]["role"] == "rep"

    def _deals_with(self, actor, owner):
        """True when actor is the owner or a manager."""
        return actor == owner or self._is_manager(actor)

    def _get_lead(self, lead_id):
        """Lead lookup that reports a missing entity as ValueError later."""
        if not isinstance(lead_id, str):
            return None
        return self.leads.get(lead_id)

    def _get_opp(self, opp_id):
        """Opportunity lookup that reports a missing entity as ValueError later."""
        if not isinstance(opp_id, str):
            return None
        return self.opps.get(opp_id)

    def _load(self, user_id):
        rep = self.users.get(user_id)
        if rep is None or rep["role"] != "rep":
            return 0
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best = None
        best_key = None
        for rep_id, rep in self.users.items():
            if rep["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load >= rep["capacity"]:
                continue
            key = (load, rep_id)
            if best_key is None or key < best_key:
                best = rep_id
                best_key = key
        return best

    def _free_slot(self, rep_id):
        if rep_id is None or rep_id not in self.users:
            return
        rep = self.users[rep_id]
        if rep["role"] != "rep":
            return
        while self.waiting and self._load(rep_id) < rep["capacity"]:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -- operations -------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        normalized = _normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORE[source]
        domain = normalized.split("@")[1]
        if domain not in FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
        if owner is None:
            self.waiting.append(lead_id)
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self._get_lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not self._deals_with(actor, lead["owner"]):
            raise PermissionError("not allowed")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self._get_lead(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._deals_with(actor, lead["owner"]):
            raise PermissionError("not allowed")
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
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not self._deals_with(actor, opp["owner"]):
            raise PermissionError("not allowed")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost" and stage != STAGE_ORDER[STAGE_ORDER.index(current) + 1]:
            raise ValueError("invalid transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not self._deals_with(actor, opp["owner"]):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount too large for a rep")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self._get_opp(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        target = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by that rep")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
                continue
            if stage == "lost":
                continue
            open_count += 1
            weighted += opp["amount"] * WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
