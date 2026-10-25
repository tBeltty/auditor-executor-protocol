"""Minimal in-memory CRM.

Implements the module described in ``crm.md``: leads with ownership and a FIFO
waiting queue, opportunities with a fixed stage machine, discounts bounded by a
cumulative cap, manager-only transfers, and an audit log of every successful
mutation.  Python 3 standard library only.
"""

__all__ = ["CRM", "DuplicateLeadError"]

STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
ALL_STAGES = STAGE_ORDER + ("lost",)
FINAL_STAGES = ("won", "lost")
NEXT_STAGE = {
    "prospect": "proposal",
    "proposal": "negotiation",
    "negotiation": "won",
}
OPEN_LEAD_STATUSES = ("new", "qualified")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
PUBLIC_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
REP_DISCOUNT_LIMIT = 10
MAX_DISCOUNT = 30
NEGOTIATION_MANAGER_AMOUNT = 50000
# new_amount * 100 >= original_amount * 70, i.e. at most 30% off the original.
MIN_REMAINING_PERCENT = 70


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the normalized email.

    ``existing_id`` is the id of the lead that already owns the address.
    """

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__(
            "a lead with this email already exists: %r" % (existing_id,)
        )


def _lookup(mapping, key):
    """Return ``mapping[key]`` or ``None``; unhashable keys are simply absent."""
    try:
        return mapping.get(key)
    except TypeError:
        return None


class CRM:
    """Lead and opportunity bookkeeping for a small sales team.

    Public state is ``leads`` (id -> lead dict), ``opps`` (id -> opportunity
    dict) and ``log`` (list of ``(op, entity_id, actor_id)`` tuples).
    """

    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []
        self._lead_count = 0
        self._opp_count = 0

    # -- internal helpers -------------------------------------------------

    def _actor(self, actor):
        """Return the acting user; unknown actors are rejected first."""
        user = _lookup(self._users, actor)
        if user is None:
            raise PermissionError("unknown actor: %r" % (actor,))
        return user

    def _lead(self, lead_id):
        lead = _lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return lead

    def _opp(self, opp_id):
        opp = _lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return opp

    @staticmethod
    def _is_manager(user):
        return user["role"] == "manager"

    def _load(self, user_id):
        """Open leads plus non-final opportunities owned by ``user_id``."""
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in OPEN_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _next_owner(self):
        """Lowest-load rep with spare capacity; ties go to the smallest id."""
        best_id = None
        best_key = None
        for user in self._users.values():
            if user["role"] != "rep":
                continue
            load = self._load(user["id"])
            if load >= user["capacity"]:
                continue
            key = (load, user["id"])
            if best_key is None or key < best_key:
                best_key = key
                best_id = user["id"]
        return best_id

    def _assign_waiting(self, user_id):
        """Hand queued leads to ``user_id`` in FIFO order while it has room."""
        user = _lookup(self._users, user_id)
        if user is None:
            return
        while self._waiting and self._load(user_id) < user["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        """Validate ``email`` and return its stripped, lowercased form."""
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty part before '@'")
        if not any(domain[i] == "." for i in range(1, len(domain) - 1)):
            raise ValueError(
                "email domain must contain a '.' that is neither first nor last"
            )
        return normalized

    # -- lead intake ------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        """Create a lead (or queue it) and return its id."""
        # General rule: the actor is validated before any payload check.
        self._actor(actor)

        # 1. Email.
        normalized = self._normalize_email(email)

        # 2. Name.
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        # 3. Source.
        if source not in ("web", "referral", "event"):
            raise ValueError("source must be 'web', 'referral' or 'event'")

        # 4. Duplicate normalized email.
        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])

        # 5. Id and score.
        domain = normalized.partition("@")[2]
        score = SOURCE_SCORES[source]
        if domain not in PUBLIC_EMAIL_DOMAINS:
            score += 15
        self._lead_count += 1
        lead_id = "L%d" % self._lead_count

        # 6. Owner.
        owner = self._next_owner()

        # 7. Record.
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
        """Move a new lead to qualified once it is worth pursuing."""
        user = self._actor(actor)
        lead = self._lead(lead_id)
        if lead["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        """Turn a qualified lead into a prospect opportunity; return its id."""
        user = self._actor(actor)
        lead = self._lead(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        if lead["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may convert")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead must have an owner")
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

    # -- opportunity pipeline ---------------------------------------------

    def advance(self, opp_id, stage, actor):
        """Move an opportunity one step forward, or to 'lost'."""
        user = self._actor(actor)
        opp = self._opp(opp_id)
        if stage not in ALL_STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        if opp["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may advance")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if stage != "lost" and stage != NEXT_STAGE[opp["stage"]]:
            raise ValueError("stage must be 'lost' or the immediate next stage")
        if (
            stage == "negotiation"
            and opp["amount"] > NEGOTIATION_MANAGER_AMOUNT
            and not self._is_manager(user)
        ):
            raise PermissionError(
                "a manager is required to negotiate above %d"
                % NEGOTIATION_MANAGER_AMOUNT
            )

        owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            # The closed deal no longer consumes a slot.
            self._assign_waiting(owner)

    def discount(self, opp_id, pct, actor):
        """Apply a percentage discount, bounded cumulatively at 30% off list."""
        user = self._actor(actor)
        opp = self._opp(opp_id)
        if (
            isinstance(pct, bool)
            or not isinstance(pct, int)
            or not 1 <= pct <= MAX_DISCOUNT
        ):
            raise ValueError("pct must be an integer from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(user):
            raise PermissionError("only the owner or a manager may discount")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if not self._is_manager(user) and pct > REP_DISCOUNT_LIMIT:
            raise PermissionError("reps may discount at most 10 percent")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * MIN_REMAINING_PERCENT:
            raise ValueError("cumulative discount may not exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        """Reassign an open opportunity to another rep (managers only)."""
        user = self._actor(actor)
        opp = self._opp(opp_id)
        if not self._is_manager(user):
            raise PermissionError("only a manager may transfer")
        new_user = _lookup(self._users, new_owner)
        if new_user is None or new_user["role"] != "rep":
            raise ValueError("new_owner must be the id of a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already in a final stage")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner already owns this opportunity")
        if self._load(new_owner) >= new_user["capacity"]:
            raise ValueError("new_owner has no spare capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        # The previous owner's slot is free again.
        self._assign_waiting(previous_owner)

    # -- reporting ---------------------------------------------------------

    def forecast(self):
        """Return open count, weighted pipeline value and won revenue."""
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
                weighted += opp["amount"] * STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
