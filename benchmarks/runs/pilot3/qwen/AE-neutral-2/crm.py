"""CRM module — implements the spec in /tmp/aep-lab/specs/crm.md.

Standard library only. See the spec for the contract of every method:
checks run in the order listed, a failed call changes nothing and appends
nothing to ``log``, and a successful call appends exactly the named entries.
"""


class DuplicateLeadError(Exception):
    """Raised by add_lead when a lead with the same normalized email exists."""

    def __init__(self, existing_id):
        super().__init__("lead with same email already exists: %r" % (existing_id,))
        self.existing_id = existing_id


_SOURCES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_FINAL = ("won", "lost")
_NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


def _normalize_email(email):
    """Return the normalized email, or None when it violates the spec rules."""
    norm = email.strip().lower()
    if norm.count("@") != 1:
        return None
    local, domain = norm.split("@")
    if not local:
        return None
    # the domain must contain a "." that is neither its first nor its last char
    if not any(i != 0 and i != len(domain) - 1 for i, ch in enumerate(domain) if ch == "."):
        return None
    return norm


class CRM:
    def __init__(self, reps):
        self._users = {user["id"]: user for user in reps}
        self._reps = [user["id"] for user in reps if user["role"] == "rep"]
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO of lead ids with owner None
        self._lead_seq = 0
        self._opp_seq = 0

    # ---- internals (not part of the public spec surface) ----

    def _check_actor(self, actor):
        # General rule: unknown actor -> PermissionError, checked first.
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor_id):
        return self._users[actor_id]["role"] == "manager"

    def _check_owner_or_manager(self, actor_id, owner_id):
        if actor_id != owner_id and not self._is_manager(actor_id):
            raise PermissionError(
                "actor %r is neither the owner nor a manager" % (actor_id,)
            )

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL:
                n += 1
        return n

    def _find_lead(self, lead_id):
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("no such lead: %r" % (lead_id,))
        return lead

    def _find_opp(self, opp_id):
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("no such opportunity: %r" % (opp_id,))
        return opp

    def _free_slot(self, rep_id):
        """Assign oldest waiting leads to rep_id while its load is below capacity."""
        capacity = self._users[rep_id]["capacity"]
        while self._load(rep_id) < capacity and self._waiting:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ---- public API ----

    def add_lead(self, email, name, source, actor):
        # General rule: the actor check runs before any method-specific check.
        self._check_actor(actor)

        # 1. email
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = _normalize_email(email)
        if norm is None:
            raise ValueError("invalid email: %r" % (email,))
        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str after strip")
        # 3. source
        if source not in _SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        # 4. duplicate
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])
        # 5. id and score
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = _SOURCES[source]
        domain = norm.split("@")[1]
        if domain not in _FREE_DOMAINS:
            score += 15
        # 6. owner: lowest-load rep below capacity; ties: smallest id in string order
        owner = None
        best = None
        for rep_id in self._reps:
            load = self._load(rep_id)
            if load < self._users[rep_id]["capacity"]:
                key = (load, rep_id)
                if best is None or key < best:
                    best = key
                    owner = rep_id
        # 7. create the lead
        lead = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        # 1. lead exists
        lead = self._find_lead(lead_id)
        # 2. owner or manager
        self._check_owner_or_manager(actor, lead["owner"])
        # 3. status new
        if lead["status"] != "new":
            raise ValueError("lead %s is not new" % (lead_id,))
        # 4. score threshold
        if lead["score"] < 30:
            raise ValueError("lead %s score %d is below 30" % (lead_id, lead["score"]))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        # 1. lead exists
        lead = self._find_lead(lead_id)
        # 2. amount: positive int, not bool
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        # 3. owner or manager
        self._check_owner_or_manager(actor, lead["owner"])
        # 4. status qualified
        if lead["status"] != "qualified":
            raise ValueError("lead %s is not qualified" % (lead_id,))
        # 5. must have an owner
        if lead["owner"] is None:
            raise ValueError("lead %s has no owner" % (lead_id,))
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
        # 1. opp exists
        opp = self._find_opp(opp_id)
        # 2. stage is one of the known stages
        if stage not in _STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        # 3. owner or manager
        self._check_owner_or_manager(actor, opp["owner"])
        current = opp["stage"]
        # 4. current stage must not be final
        if current in _FINAL:
            raise ValueError("opportunity %s is final at %s" % (opp_id, current))
        # 5. lost, or the immediate next stage
        if stage != "lost" and _NEXT[current] != stage:
            raise ValueError("cannot move %s from %s to %s" % (opp_id, current, stage))
        # 6. negotiation gate for big deals
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("amount over 50000 requires a manager to negotiate")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        # 1. opp exists
        opp = self._find_opp(opp_id)
        # 2. pct: int (not bool) in 1..30
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        # 3. owner or manager
        self._check_owner_or_manager(actor, opp["owner"])
        # 4. stage not final
        if opp["stage"] in _FINAL:
            raise ValueError("opportunity %s is final at %s" % (opp_id, opp["stage"]))
        # 5. rep cap of 10
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("a rep may discount at most 10")
        # 6. cumulative discount of at most 30% of the original amount
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        # 1. opp exists
        opp = self._find_opp(opp_id)
        # 2. actor must be a manager
        if not self._is_manager(actor):
            raise PermissionError("transfer requires a manager")
        # 3. new_owner must be a known rep
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known rep: %r" % (new_owner,))
        # 4. stage not final
        if opp["stage"] in _FINAL:
            raise ValueError("opportunity %s is final at %s" % (opp_id, opp["stage"]))
        # 5. must differ from the current owner
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the owner: %r" % (new_owner,))
        # 6. target load below capacity
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new_owner %s is at capacity" % (new_owner,))
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

    def forecast(self):
        open_n = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won_total += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_n += 1
                weighted += opp["amount"] * _WEIGHTS[stage] // 100
        return {"open": open_n, "weighted": weighted, "won": won_total}
