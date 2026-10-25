"""A small CRM: leads, opportunities, a FIFO assignment queue and forecasting.

Every mutating method follows the same contract:

* the acting user is validated first (``PermissionError`` for unknown ids);
* the remaining checks run in the order required by the specification, so the
  first failing check decides the exception;
* a failed call leaves ``leads``, ``opps``, the waiting queue and ``log``
  untouched, while a successful call appends exactly the documented log
  entries.
"""

from collections import deque

FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = ("web", "referral", "event")
BASE_SCORES = {"web": 10, "referral": 30, "event": 20}

#: Open stages in pipeline order; "won" and "lost" are final.
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
STAGES = STAGE_ORDER + ("lost",)
NEXT_STAGE = dict(zip(STAGE_ORDER, STAGE_ORDER[1:]))

WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

MANAGER_NEGOTIATION_LIMIT = 50000
REP_DISCOUNT_LIMIT = 10
MAX_DISCOUNT_PCT = 30
MIN_REMAINING_PCT = 70

LEAD_LOAD_STATUSES = ("new", "qualified")


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


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
        self._waiting = deque()

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        """Every method starts here: the actor must be a known user id."""
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return actor

    def _require_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _require_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _may_act_on(self, owner_id, actor):
        """True when ``actor`` is a manager or owns the entity."""
        return self._is_manager(actor) or owner_id == actor

    def _loads(self):
        """Load per user id: open leads plus open opportunities owned."""
        loads = dict.fromkeys(self.users, 0)
        for lead in self.leads.values():
            owner = lead["owner"]
            if lead["status"] in LEAD_LOAD_STATUSES and owner in loads:
                loads[owner] += 1
        for opp in self.opps.values():
            owner = opp["owner"]
            if opp["stage"] not in FINAL_STAGES and owner in loads:
                loads[owner] += 1
        return loads

    def _load(self, user_id):
        if not isinstance(user_id, str):
            return 0
        return self._loads().get(user_id, 0)

    def _find_lead_by_email(self, normalized):
        """Id of the lead already using ``normalized``, or None."""
        for lead in self.leads.values():
            if lead["email"] == normalized:
                return lead["id"]
        return None

    def _next_owner(self):
        """Least loaded rep below capacity; ties broken by smallest id."""
        loads = self._loads()
        best = None
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            load = loads[user["id"]]
            if load >= user["capacity"]:
                continue
            candidate = (load, user["id"])
            if best is None or candidate < best:
                best = candidate
        return None if best is None else best[1]

    def _free_slot(self, owner_id):
        """Assign waiting leads to a rep that just lost some load."""
        if not isinstance(owner_id, str) or owner_id not in self.users:
            return
        capacity = self.users[owner_id]["capacity"]
        load = self._load(owner_id)
        while self._waiting and load < capacity:
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = owner_id
            self.log.append(("assign", lead_id, "system"))
            load += 1

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not any(char == "." and 0 < index < len(domain) - 1
                   for index, char in enumerate(domain)):
            raise ValueError("email domain needs a '.' that is not first or last")
        return normalized

    @staticmethod
    def _score(source, domain):
        score = BASE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15
        return score

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        """Create a lead; returns its id ("L1", "L2", ...)."""
        self._require_actor(actor)
        normalized = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        existing_id = self._find_lead_by_email(normalized)
        if existing_id is not None:
            raise DuplicateLeadError(existing_id)

        domain = normalized.partition("@")[2]
        owner = self._next_owner()
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": name.strip(),
            "source": source,
            "score": self._score(source, domain),
            "owner": owner,
            "status": "new",
        }
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        """Move a new lead with a score of at least 30 to "qualified"."""
        self._require_actor(actor)
        lead = self._require_lead(lead_id)
        if not self._may_act_on(lead["owner"], actor):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead status is not 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score is below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        """Turn a qualified lead into a prospect opportunity; returns its id."""
        self._require_actor(actor)
        lead = self._require_lead(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._may_act_on(lead["owner"], actor):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead status is not 'qualified'")
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
        """Move an opportunity one step forward, or to "lost", from any open stage."""
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if stage not in STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not self._may_act_on(opp["owner"], actor):
            raise PermissionError("actor may not advance this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if stage != "lost" and NEXT_STAGE.get(opp["stage"]) != stage:
            raise ValueError("invalid stage transition")
        if (stage == "negotiation"
                and opp["amount"] > MANAGER_NEGOTIATION_LIMIT
                and not self._is_manager(actor)):
            raise PermissionError("manager required for negotiation over 50000")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        """Reduce an open opportunity's amount by ``pct`` percent."""
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if (isinstance(pct, bool) or not isinstance(pct, int)
                or not 1 <= pct <= MAX_DISCOUNT_PCT):
            raise ValueError("pct must be an int from 1 to 30")
        if not self._may_act_on(opp["owner"], actor):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if pct > REP_DISCOUNT_LIMIT and not self._is_manager(actor):
            raise PermissionError("non-managers may discount at most 10")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * MIN_REMAINING_PCT:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        """Reassign an open opportunity to another rep (managers only)."""
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer opportunities")
        if (not isinstance(new_owner, str) or new_owner not in self.users
                or self.users[new_owner]["role"] != "rep"):
            raise ValueError("new owner must be a known rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        """Open count, weighted pipeline value and closed-won total."""
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
