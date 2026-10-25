"""crm.py -- a miniature CRM: lead intake, routing, qualification and pipeline.

Public surface: :class:`CRM` and :class:`DuplicateLeadError`.
Every mutating method takes the acting user id (``actor``) and appends
tuples ``(op, entity_id, actor_id)`` to :attr:`CRM.log`.  A call that raises
changes nothing and logs nothing.
"""

_FINAL_STAGES = frozenset(("won", "lost"))
_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

_SOURCES = ("web", "referral", "event")
_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = frozenset(("gmail.com", "yahoo.com", "outlook.com"))

# A lead keeps its owner busy while it is in one of these statuses.
_ACTIVE_LEAD_STATUSES = frozenset(("new", "qualified"))

_MAX_DISCOUNT = 30
_REP_DISCOUNT_LIMIT = 10
_NEGOTIATION_THRESHOLD = 50000


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id=None, message=None):
        self.existing_id = existing_id
        if message is None:
            if existing_id is None:
                message = "duplicate lead"
            else:
                message = "duplicate lead, existing id: %s" % (existing_id,)
        super().__init__(message)


def _domain_has_interior_dot(domain):
    """True if ``domain`` holds a "." that is neither its first nor its last char."""
    for index in range(1, len(domain) - 1):
        if domain[index] == ".":
            return True
    return False


def _valid_normalized_email(email):
    """Validate an already normalized (stripped, lower-cased) email address."""
    if email.count("@") != 1:
        return False
    local, _, domain = email.partition("@")
    if not local:
        return False
    return _domain_has_interior_dot(domain)


class CRM:
    """Track leads and opportunities and route work to the representatives."""

    def __init__(self, reps):
        self.users = {}
        for rep in reps or ():
            # Store our own copy: later mutation of the caller's list must not
            # be able to change routing rules behind our back.
            self.users[rep["id"]] = dict(rep)
        self.leads = {}
        self.opps = {}
        self.log = []
        # Internal bookkeeping: FIFO of lead ids waiting for an open slot.
        self._waiting = []
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------ helpers

    def _known(self, user_id):
        """Membership test that tolerates unhashable ids: they are never known."""
        try:
            return user_id in self.users
        except TypeError:
            return False

    @staticmethod
    def _find(store, key):
        """Lookup that tolerates unhashable ids: they simply never match."""
        try:
            return store.get(key)
        except TypeError:
            return None

    def _require_actor(self, actor):
        """Every method checks this first: unknown actors are never allowed."""
        if not self._known(actor):
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, user_id):
        return self.users[user_id]["role"] == "manager"

    def _can_act_on(self, owner_id, actor):
        return owner_id == actor or self._is_manager(actor)

    def _load(self, rep_id):
        """Leads owned in status new/qualified plus open opportunities owned."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in _ACTIVE_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _reps_below_capacity(self):
        result = []
        for user_id, user in self.users.items():
            if user["role"] != "rep":
                continue
            if self._load(user_id) < user["capacity"]:
                result.append(user_id)
        return result

    def _pick_owner(self):
        """Lowest load among reps below capacity; ties resolved by id string order."""
        candidates = self._reps_below_capacity()
        if not candidates:
            return None
        return min(candidates, key=lambda user_id: (self._load(user_id), user_id))

    def _fill_slot(self, rep_id):
        """Hand the oldest waiting leads to ``rep_id`` while it has room."""
        if not self._known(rep_id) or self.users[rep_id]["role"] != "rep":
            return
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------- intake

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if not _valid_normalized_email(normalized):
            raise ValueError("invalid email: %r" % (email,))

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        if source not in _SOURCES:
            raise ValueError("unknown source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = _SOURCE_SCORES[source]
        domain = normalized.partition("@")[2]
        if domain not in _FREE_DOMAINS:
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

    # ---------------------------------------------------------------- qualify

    def qualify(self, lead_id, actor):
        self._require_actor(actor)

        lead = self._find(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not self._can_act_on(lead["owner"], actor):
            raise PermissionError("only the owner or a manager may qualify a lead")
        if lead["status"] != "new":
            raise ValueError("only a new lead can be qualified")
        if lead["score"] < 30:
            raise ValueError("lead score %d is below 30" % (lead["score"],))

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # --------------------------------------------------------------- conversion

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self._find(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._can_act_on(lead["owner"], actor):
            raise PermissionError("only the owner or a manager may convert a lead")
        if lead["status"] != "qualified":
            raise ValueError("only a qualified lead can be converted")
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

    # ---------------------------------------------------------------- advance

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)

        opp = self._find(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        if not self._can_act_on(opp["owner"], actor):
            raise PermissionError("only the owner or a manager may advance an opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is closed")
        if stage != "lost" and stage != _NEXT_STAGE[opp["stage"]]:
            raise ValueError("illegal stage transition: %s -> %s" % (opp["stage"], stage))
        manager = self._is_manager(actor)
        if stage == "negotiation" and opp["amount"] > _NEGOTIATION_THRESHOLD and not manager:
            raise PermissionError("a manager must move deals above 50000 into negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._fill_slot(opp["owner"])

    # ---------------------------------------------------------------- discount

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self._find(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= _MAX_DISCOUNT:
            raise ValueError("pct must be an int from 1 to 30")
        if not self._can_act_on(opp["owner"], actor):
            raise PermissionError("only the owner or a manager may discount an opportunity")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is closed")
        if not self._is_manager(actor) and pct > _REP_DISCOUNT_LIMIT:
            raise PermissionError("a rep may not discount more than 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ---------------------------------------------------------------- transfer

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self._find(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer an opportunity")
        if not self._known(new_owner) or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is closed")
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already belongs to that rep")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_slot(previous_owner)

    # ---------------------------------------------------------------- forecast

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage in _FINAL_STAGES:
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
