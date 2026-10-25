"""CRM module — implements the spec in /tmp/aep-lab/specs/crm.md.

Rules that drive every method below:

- An unknown ``actor`` raises PermissionError, checked first in every method that
  takes one (``forecast`` takes none).
- A failed call changes nothing and appends nothing to ``log``: all checks run
  before the first mutation.
- Load of a rep = leads it owns with status "new" or "qualified" + opportunities
  it owns whose stage is not "won" or "lost". Only reps receive work.
- Per-method checks run in the listed order; the first failing check decides
  the exception.
"""

# Sources, in the order the spec lists them.
SOURCES = ("web", "referral", "event")

_SCORE_BY_SOURCE = {"web": 10, "referral": 30, "event": 20}

# Domains that do not earn the +15 non-free-domain bonus.
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")

# All legal stages, and the two that end an opportunity.
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_FINAL_STAGES = ("won", "lost")

# The stage order that is not "lost": prospect -> proposal -> negotiation -> won.
_NEXT_STAGE = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}

_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}

# Leads that keep a rep's slot occupied.
_ACTIVE_LEAD_STATUSES = ("new", "qualified")


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id, message=None):
        super().__init__(message or "duplicate lead for %r" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.leads = {}
        self.opps = {}
        self.log = []
        self.reps = [dict(rep) for rep in reps]
        self._users = {}
        for rep in self.reps:
            self._users[rep["id"]] = {"id": rep["id"], "role": rep["role"],
                                      "capacity": rep["capacity"]}
        # FIFO queue of lead ids waiting for a rep slot (owner is None).
        self._waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ---------------------------------------------------------------- helpers

    def _check_actor(self, actor):
        """General rule: unknown actor -> PermissionError, checked first."""
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users.get(actor, {}).get("role") == "manager"

    def _rep_ids(self):
        return [uid for uid in self._users if self._users[uid]["role"] == "rep"]

    def _load(self, rep_id):
        """Number of active leads + open opportunities owned by rep_id."""
        leads = sum(1 for lead in self.leads.values()
                    if lead["owner"] == rep_id and lead["status"] in _ACTIVE_LEAD_STATUSES)
        opps = sum(1 for opp in self.opps.values()
                   if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES)
        return leads + opps

    def _capacity(self, rep_id):
        return self._users[rep_id]["capacity"]

    def _eligible_rep(self):
        """Lowest-load rep below capacity; ties broken by smallest id (str order)."""
        best = None
        for rep_id in self._rep_ids():
            if self._load(rep_id) < self._capacity(rep_id):
                key = (self._load(rep_id), rep_id)
                if best is None or key < best[0]:
                    best = (key, rep_id)
        return best[1] if best is not None else None

    def _free_slot(self, rep_id):
        """Give waiting leads to rep_id while its load is below its capacity."""
        while self._load(rep_id) < self._capacity(rep_id) and self._waiting:
            lead_id = self._waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        """Return the normalized email, or raise ValueError per add_lead check 1."""
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        # A '.' inside the domain: neither its first nor its last character.
        if "." not in domain[1:-1]:
            raise ValueError("email domain must contain a '.' that is neither "
                             "first nor last")
        return normalized, domain

    # ------------------------------------------------------------------ API

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        # 1. email
        normalized, domain = self._normalize_email(email)
        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str after strip()")
        # 3. source
        if source not in SOURCES:
            raise ValueError("unknown source: %r" % (source,))
        # 4. duplicate
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        # 5. id and score
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = _SCORE_BY_SOURCE[source] + (0 if domain in _FREE_DOMAINS else 15)
        # 6. owner: lowest-load rep below capacity, else the FIFO queue
        owner = self._eligible_rep()
        # 7. build, log
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
        # 1. the lead must exist
        lead = self._get_lead(lead_id)
        # 2. owner or manager
        if not (lead["owner"] == actor or self._is_manager(actor)):
            raise PermissionError("actor is not the lead's owner or a manager")
        # 3. status must be "new"
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        # 4. score threshold
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        # 1. the lead must exist
        lead = self._get_lead(lead_id)
        # 2. amount: positive int, not bool
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        # 3. owner or manager
        if not (lead["owner"] == actor or self._is_manager(actor)):
            raise PermissionError("actor is not the lead's owner or a manager")
        # 4. status must be "qualified"
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        # 5. the lead must have an owner
        if lead["owner"] is None:
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

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        # 1. the opportunity must exist
        opp = self._get_opp(opp_id)
        # 2. stage is a known stage
        if stage not in STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        # 3. owner or manager
        if not (opp["owner"] == actor or self._is_manager(actor)):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        # 4. current stage must not be final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed: %r" % (opp["stage"],))
        # 5. "lost" or the immediate next stage
        if stage != "lost" and stage != _NEXT_STAGE[opp["stage"]]:
            raise ValueError("cannot move from %r to %r" % (opp["stage"], stage))
        # 6. big deals need a manager to reach negotiation
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("amount above 50000 needs a manager to reach negotiation")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        # 1. the opportunity must exist
        opp = self._get_opp(opp_id)
        # 2. pct: int (not bool) from 1 to 30 inclusive
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        # 3. owner or manager
        if not (opp["owner"] == actor or self._is_manager(actor)):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        # 4. stage must not be final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed: %r" % (opp["stage"],))
        # 5. a rep may use at most 10
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("a non-manager may discount at most 10")
        # 6. cumulative discount of at most 30 percent of the original amount
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        # 1. the opportunity must exist
        opp = self._get_opp(opp_id)
        # 2. actor must be a manager
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        # 3. new_owner must be a known rep
        if not isinstance(new_owner, str) or new_owner not in self._users \
                or self._users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        # 4. stage must not be final
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is already closed: %r" % (opp["stage"],))
        # 5. must be a different owner
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the owner")
        # 6. new owner must have a free slot
        if self._load(new_owner) >= self._capacity(new_owner):
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
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHT[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}

    # ------------------------------------------------------- existence checks

    def _get_lead(self, lead_id):
        lead = self.leads.get(lead_id) if isinstance(lead_id, str) else None
        if lead is None:
            raise ValueError("no such lead: %r" % (lead_id,))
        return lead

    def _get_opp(self, opp_id):
        opp = self.opps.get(opp_id) if isinstance(opp_id, str) else None
        if opp is None:
            raise ValueError("no such opportunity: %r" % (opp_id,))
        return opp
