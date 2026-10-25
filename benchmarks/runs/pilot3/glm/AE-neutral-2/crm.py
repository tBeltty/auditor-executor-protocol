"""crm.py - lead/opportunity CRM per /tmp/aep-lab/specs/crm.md.

Implements CRM and DuplicateLeadError. Standard library only.
"""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__(existing_id)
        self.existing_id = existing_id


_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_VALID_SOURCES = frozenset(_SOURCE_SCORES)
_FREE_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})
_DOMAIN_BONUS = 15

_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_FINAL_STAGES = frozenset({"won", "lost"})
_VALID_STAGES = frozenset(_STAGE_ORDER) | frozenset({"lost"})
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

_GETS_OWNER_ROLE = "rep"
_ACTIVE_LEAD_STATUSES = frozenset({"new", "qualified"})


class CRM:
    def __init__(self, reps):
        self.users = {
            rep["id"]: {"id": rep["id"], "role": rep["role"], "capacity": rep["capacity"]}
            for rep in reps
        }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._wait_queue = []  # lead ids, FIFO
        self._next_lead_num = 1
        self._next_opp_num = 1

    # ------------------------------------------------------------------ #
    # internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _check_actor(self, actor):
        """Must run first in every method."""
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _owns(self, actor, owner_id):
        return owner_id is not None and actor == owner_id

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in _ACTIVE_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        candidates = [
            user
            for user in self.users.values()
            if user["role"] == _GETS_OWNER_ROLE
            and self._load(user["id"]) < user["capacity"]
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda user: (self._load(user["id"]), user["id"]))["id"]

    def _free_owner_slots(self, rep_id):
        """Assign waiting leads while rep load is below capacity. Log is "(assign",
        lead_id, "system") per assignment; actor is literally "system"."""
        if rep_id is None:
            return
        while self._wait_queue and self._load(rep_id) < self.users[rep_id]["capacity"]:
            lead_id = self._wait_queue.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------ #
    # add_lead                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _normalized_email_is_valid(email):
        if email.count("@") != 1:
            return False
        local, domain = email.split("@")
        if not local:
            return False
        # Domain must contain a "." that is neither its first nor its last char.
        return any(domain[i] == "." for i in range(1, len(domain) - 1))

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        # 1. email
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized_email = email.strip().lower()
        if not self._normalized_email_is_valid(normalized_email):
            raise ValueError("invalid email: %r" % (email,))
        # 2. name
        if not isinstance(name, str):
            raise ValueError("name must be a str")
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("name must be non-empty after strip()")
        # 3. source
        if source not in _VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        # 4. duplicate normalized email
        for lead in self.leads.values():
            if lead["email"] == normalized_email:
                raise DuplicateLeadError(lead["id"])
        # 5. id + score
        lead_id = "L%d" % self._next_lead_num
        self._next_lead_num += 1
        base_score = _SOURCE_SCORES[source]
        domain = normalized_email.split("@")[1]
        score = base_score + (_DOMAIN_BONUS if domain not in _FREE_DOMAINS else 0)
        # 6. owner
        owner = self._pick_owner()
        lead = {
            "id": lead_id,
            "email": normalized_email,
            "name": stripped_name,
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        if owner is None:
            self._wait_queue.append(lead_id)
        # 7. log + return
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    # ------------------------------------------------------------------ #
    # qualify                                                            #
    # ------------------------------------------------------------------ #

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        # 1. lead exists
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        # 2. owner or manager
        if not (self._is_manager(actor) or self._owns(actor, lead["owner"])):
            raise PermissionError("actor is neither the owner nor a manager")
        # 3. status
        if lead["status"] != "new":
            raise ValueError("lead status is %r, not 'new'" % (lead["status"],))
        # 4. score
        if lead["score"] < 30:
            raise ValueError("lead score %d is below 30" % (lead["score"],))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # ------------------------------------------------------------------ #
    # convert                                                            #
    # ------------------------------------------------------------------ #

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        # 1. lead exists
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        # 2. amount: positive int, not bool
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise ValueError("amount must be an int, not bool")
        if amount <= 0:
            raise ValueError("amount must be positive")
        # 3. owner or manager
        if not (self._is_manager(actor) or self._owns(actor, lead["owner"])):
            raise PermissionError("actor is neither the owner nor a manager")
        # 4. status qualified
        if lead["status"] != "qualified":
            raise ValueError("lead status is %r, not 'qualified'" % (lead["status"],))
        # 5. lead has an owner
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        opp_id = "O%d" % self._next_opp_num
        self._next_opp_num += 1
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

    # ------------------------------------------------------------------ #
    # advance                                                            #
    # ------------------------------------------------------------------ #

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        # 1. opportunity exists
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        # 2. stage valid
        if stage not in _VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        # 3. owner or manager
        if not (self._is_manager(actor) or self._owns(actor, opp["owner"])):
            raise PermissionError("actor is neither the owner nor a manager")
        # 4. current stage not final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is final: %r" % (opp["stage"],))
        # 5. lost or immediate next stage
        next_stage = _STAGE_ORDER[_STAGE_ORDER.index(opp["stage"]) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("cannot move from %r to %r" % (opp["stage"], stage))
        # 6. negotiation over 50000 requires a manager
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("moving to negotiation over 50000 requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_owner_slots(opp["owner"])

    # ------------------------------------------------------------------ #
    # discount                                                           #
    # ------------------------------------------------------------------ #

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        # 1. opportunity exists
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        # 2. pct: int (not bool), 1..30 inclusive
        if isinstance(pct, bool) or not isinstance(pct, int):
            raise ValueError("pct must be an int, not bool")
        if not 1 <= pct <= 30:
            raise ValueError("pct must be between 1 and 30")
        # 3. owner or manager
        if not (self._is_manager(actor) or self._owns(actor, opp["owner"])):
            raise PermissionError("actor is neither the owner nor a manager")
        # 4. stage not final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is final: %r" % (opp["stage"],))
        # 5. non-manager may discount at most 10
        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("non-manager discount above 10 not allowed")
        # 6. cumulative discount cap of 30 percent
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ------------------------------------------------------------------ #
    # transfer                                                           #
    # ------------------------------------------------------------------ #

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        # 1. opportunity exists
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        opp = self.opps[opp_id]
        # 2. actor must be a manager
        if not self._is_manager(actor):
            raise PermissionError("actor must be a manager")
        # 3. new owner is a known rep
        new_user = self.users.get(new_owner)
        if new_user is None or new_user["role"] != _GETS_OWNER_ROLE:
            raise ValueError("new_owner is not a known rep: %r" % (new_owner,))
        # 4. stage not final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is final: %r" % (opp["stage"],))
        # 5. must differ from current owner
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is the current owner")
        # 6. new owner load below capacity
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        # free the previous owner's slot exactly as in advance
        self._free_owner_slots(previous_owner)

    # ------------------------------------------------------------------ #
    # forecast                                                           #
    # ------------------------------------------------------------------ #

    def forecast(self):
        """No actor, no log entry."""
        open_opps = [opp for opp in self.opps.values() if opp["stage"] not in _FINAL_STAGES]
        weighted = sum(
            opp["amount"] * _STAGE_WEIGHTS[opp["stage"]] // 100 for opp in open_opps
        )
        won = sum(opp["amount"] for opp in self.opps.values() if opp["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
