"""crm.py - a tiny CRM: leads, opportunities, capacity-aware routing.

Public API (see the specification this module implements):

    class DuplicateLeadError(Exception)   with attribute ``existing_id``
    class CRM

Every action method takes the acting user's id as ``actor`` and validates it
before anything else: an unknown actor raises ``PermissionError``.  A call that
raises changes no state and appends nothing to ``log``.
"""

SOURCES = {"web": 10, "referral": 30, "event": 20}
SOURCE_NAMES = ("web", "referral", "event")
FREE_MAILBOX_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})

STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
STAGE_FLOW = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
STAGE_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}

# A lead still occupies its owner's slot in these statuses.
LOAD_STATUSES = ("new", "qualified")

NEGOTIATION_MANAGER_THRESHOLD = 50000
MAX_DISCOUNT_PCT = 30
REP_MAX_DISCOUNT_PCT = 10
FLOOR_PCT = 70


class DuplicateLeadError(Exception):
    """Raised when a lead with an already-known normalized email is added."""

    def __init__(self, existing_id, message=None):
        if message is None:
            message = "duplicate lead: %s already exists" % (existing_id,)
        super().__init__(message)
        self.existing_id = existing_id


def _normalize_email(email):
    """Return (normalized_email, domain), or raise ValueError per rule 1."""
    if not isinstance(email, str):
        raise ValueError("email must be a str")
    normalized = email.strip().lower()
    if normalized.count("@") != 1:
        raise ValueError("email must contain exactly one '@'")
    local, domain = normalized.split("@")
    if not local:
        raise ValueError("email needs a non-empty local part")
    if not any(0 < i < len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
        raise ValueError("email domain needs a '.' that is not first or last")
    return normalized, domain


class CRM:
    """Leads/opportunities store with capacity-aware ownership rules."""

    def __init__(self, reps):
        self._users = {}
        for user in reps:
            uid = user["id"]
            self._users[uid] = {
                "id": uid,
                "role": user["role"],
                "capacity": user["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO of lead ids that could not be assigned
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #

    def _require_actor(self, actor):
        """General rule: unknown actor -> PermissionError, checked first."""
        try:
            known = actor in self._users
        except TypeError:
            known = False
        if not known:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _capacity(self, rep_id):
        return self._users[rep_id]["capacity"]

    def _is_rep(self, user_id):
        try:
            user = self._users.get(user_id)
        except TypeError:
            return False
        return user is not None and user["role"] == "rep"

    def _load(self, rep_id):
        """Open work owned by ``rep_id``: new/qualified leads + open opps."""
        count = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in LOAD_STATUSES:
                count += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                count += 1
        return count

    def _pick_rep(self):
        """Lowest-load rep with spare capacity; ties by smallest id."""
        best_key = None
        best_id = None
        for uid in self._users:
            if self._users[uid]["role"] != "rep":
                continue
            load = self._load(uid)
            if load >= self._capacity(uid):
                continue
            key = (load, uid)
            if best_key is None or key < best_key:
                best_key = key
                best_id = uid
        return best_id

    def _free_slot(self, rep_id):
        """Pull waiting leads into ``rep_id``'s open slots, oldest first."""
        if rep_id not in self._users:
            return
        while self._waiting and self._load(rep_id) < self._capacity(rep_id):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------ #
    # add_lead
    # ------------------------------------------------------------------ #

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        # 1. email
        normalized, domain = _normalize_email(email)
        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        # 3. source
        if source not in SOURCE_NAMES:
            raise ValueError("source must be one of web, referral or event")
        # 4. duplicate
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        # 5. id + score
        score = SOURCES[source] + (0 if domain in FREE_MAILBOX_DOMAINS else 15)

        # 6. owner (or waiting queue)
        owner = self._pick_rep()

        # 7. commit
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
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

    # ------------------------------------------------------------------ #
    # qualify
    # ------------------------------------------------------------------ #

    def qualify(self, lead_id, actor):
        self._require_actor(actor)

        lead = self._lead_or_raise(lead_id)  # 1
        if not (self._is_manager(actor) or lead["owner"] == actor):  # 2
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":  # 3
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:  # 4
            raise ValueError("lead score must be at least 30")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # ------------------------------------------------------------------ #
    # convert
    # ------------------------------------------------------------------ #

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self._lead_or_raise(lead_id)  # 1
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:  # 2
            raise ValueError("amount must be a positive int")
        if not (self._is_manager(actor) or lead["owner"] == actor):  # 3
            raise PermissionError("only the owner or a manager may convert")
        if lead["status"] != "qualified":  # 4
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:  # 5
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        self.opps[opp_id] = {
            "id": opp_id,
            "lead_id": lead["id"],
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    # ------------------------------------------------------------------ #
    # advance
    # ------------------------------------------------------------------ #

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)

        opp = self._opp_or_raise(opp_id)  # 1
        if stage not in STAGES:  # 2
            raise ValueError("unknown stage: %r" % (stage,))
        if not (self._is_manager(actor) or opp["owner"] == actor):  # 3
            raise PermissionError("only the owner or a manager may advance")
        current = opp["stage"]
        if current in FINAL_STAGES:  # 4
            raise ValueError("opportunity is already closed")
        if stage != "lost":  # 5
            if stage not in STAGE_FLOW or STAGE_FLOW.index(stage) != STAGE_FLOW.index(current) + 1:
                raise ValueError("not the next stage")
        if stage == "negotiation" and opp["amount"] > NEGOTIATION_MANAGER_THRESHOLD:  # 6
            if not self._is_manager(actor):
                raise PermissionError("manager approval required above 50000")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    # ------------------------------------------------------------------ #
    # discount
    # ------------------------------------------------------------------ #

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self._opp_or_raise(opp_id)  # 1
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= MAX_DISCOUNT_PCT:  # 2
            raise ValueError("pct must be an int from 1 to 30")
        if not (self._is_manager(actor) or opp["owner"] == actor):  # 3
            raise PermissionError("only the owner or a manager may discount")
        if opp["stage"] in FINAL_STAGES:  # 4
            raise ValueError("opportunity is already closed")
        if not self._is_manager(actor) and pct > REP_MAX_DISCOUNT_PCT:  # 5
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100  # 6
        if new_amount * 100 < opp["original_amount"] * FLOOR_PCT:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ------------------------------------------------------------------ #
    # transfer
    # ------------------------------------------------------------------ #

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self._opp_or_raise(opp_id)  # 1
        if not self._is_manager(actor):  # 2
            raise PermissionError("only a manager may transfer")
        if not self._is_rep(new_owner):  # 3
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:  # 4
            raise ValueError("opportunity is already closed")
        if new_owner == opp["owner"]:  # 5
            raise ValueError("new_owner is already the owner")
        if self._load(new_owner) >= self._capacity(new_owner):  # 6
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    # ------------------------------------------------------------------ #
    # forecast
    # ------------------------------------------------------------------ #

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
                weighted += opp["amount"] * STAGE_WEIGHT[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}

    # ------------------------------------------------------------------ #
    # lookups
    # ------------------------------------------------------------------ #

    def _lead_or_raise(self, lead_id):
        try:
            lead = self.leads.get(lead_id)
        except TypeError:
            lead = None
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    def _opp_or_raise(self, opp_id):
        try:
            opp = self.opps.get(opp_id)
        except TypeError:
            opp = None
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp
