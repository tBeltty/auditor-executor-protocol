"""crm.py — a small lead/opportunity CRM.

Implements the module specified in crm.md: class CRM and
class DuplicateLeadError(Exception) with an ``existing_id`` attribute.

Rules honored (from the spec):
- The acting user check (PermissionError for an unknown actor) runs first in
  every method.
- A failed call raises without mutating state and without appending to ``log``;
  a successful call appends exactly the log entries named in the spec.
- Per-method checks run in the order listed in the spec; the first failing
  check decides the exception.
- Load of a rep = leads owned with status "new"/"qualified" plus opportunities
  owned whose stage is not "won"/"lost". Only role "rep" users receive work.
"""

__all__ = ["CRM", "DuplicateLeadError"]


class DuplicateLeadError(Exception):
    """Raised when add_lead is called with an email a lead already has."""

    def __init__(self, existing_id, message="a lead with this email already exists"):
        super().__init__(message)
        self.existing_id = existing_id


_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_COMMON_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_FINAL_STAGES = {"won", "lost"}
# Stage rank for the prospect -> proposal -> negotiation -> won order.
_STAGE_RANK = {"prospect": 0, "proposal": 1, "negotiation": 2, "won": 3}
_VALID_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class CRM:
    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            self._users[rep["id"]] = {
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}   # lead id -> lead dict
        self.opps = {}    # opportunity id -> opportunity dict
        self.log = []     # list of (op, entity_id, actor_id)
        self._waiting = []  # FIFO queue of lead ids with no owner
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------
    # Shared helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_plain_int(value):
        """True for a real int, False for bools and non-ints."""
        return isinstance(value, int) and not isinstance(value, bool)

    def _is_known_user(self, user_id):
        return isinstance(user_id, str) and user_id in self._users

    def _require_known_actor(self, actor):
        # Runs first in every method that takes an actor.
        if not self._is_known_user(actor):
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_rep(self, user_id):
        return self._users[user_id]["role"] == "rep"

    def _is_manager(self, user_id):
        return self._users[user_id]["role"] == "manager"

    def _may_act(self, actor, owned_by):
        """The acting user must be the entity's owner or a manager."""
        return actor == owned_by or self._is_manager(actor)

    def _load(self, rep_id):
        """Owned leads ("new"/"qualified") + owned opportunities (open)."""
        if rep_id not in self._users or not self._is_rep(rep_id):
            return 0
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        """Lowest-load rep strictly below capacity; ties -> smallest id.

        Managers never own anything and are never candidates.
        """
        best = None
        for user_id in self._users:
            if not self._is_rep(user_id):
                continue
            load = self._load(user_id)
            if load >= self._users[user_id]["capacity"]:
                continue
            if best is None or (load, user_id) < best:
                best = (load, user_id)
        return best[1] if best is not None else None

    def _free_slots(self, rep_id):
        """Take waiting leads FIFO while rep_id's load is below capacity."""
        if rep_id is None or rep_id not in self._users or not self._is_rep(rep_id):
            return
        while self._waiting and self._load(rep_id) < self._users[rep_id]["capacity"]:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # add_lead
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email needs a non-empty part before the '@'")
        # The domain must contain a '.' that is neither its first nor its
        # last character.
        dots = [i for i, ch in enumerate(domain) if ch == "."]
        if not any(0 < i < len(domain) - 1 for i in dots):
            raise ValueError(
                "email domain must contain a '.' that is neither its first "
                "nor its last character"
            )
        return normalized

    def add_lead(self, email, name, source, actor):
        self._require_known_actor(actor)
        normalized_email = self._validate_email(email)
        if not isinstance(name, str):
            raise ValueError("name must be a string")
        stripped_name = name.strip()
        if not stripped_name:
            raise ValueError("name must be non-empty after strip()")
        if source not in _SOURCE_SCORES:
            raise ValueError("source must be 'web', 'referral' or 'event'")
        # Duplicate check compares normalized emails against stored leads.
        for lead in self.leads.values():
            if lead["email"] == normalized_email:
                raise DuplicateLeadError(lead["id"])
        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
        domain = normalized_email.split("@")[1]
        score = _SOURCE_SCORES[source]
        if domain not in _COMMON_DOMAINS:
            score += 15
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
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    # ------------------------------------------------------------------
    # qualify
    # ------------------------------------------------------------------

    def qualify(self, lead_id, actor):
        self._require_known_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not self._may_act(actor, lead["owner"]):
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # ------------------------------------------------------------------
    # convert
    # ------------------------------------------------------------------

    def convert(self, lead_id, amount, actor):
        self._require_known_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not (self._is_plain_int(amount) and amount > 0):
            raise ValueError("amount must be a positive int (not a bool)")
        lead = self.leads[lead_id]
        if not self._may_act(actor, lead["owner"]):
            raise PermissionError("actor must be the lead's owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        self.opps[opp_id] = opp
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    # ------------------------------------------------------------------
    # advance
    # ------------------------------------------------------------------

    def advance(self, opp_id, stage, actor):
        self._require_known_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _VALID_STAGES:
            raise ValueError("stage must be one of %s" % (", ".join(_VALID_STAGES),))
        opp = self.opps[opp_id]
        if not self._may_act(actor, opp["owner"]):
            raise PermissionError("actor must be the opportunity's owner or a manager")
        current = opp["stage"]
        if current in _FINAL_STAGES:
            raise ValueError("stage %r is final" % (current,))
        adjacent = stage != "lost" and _STAGE_RANK[stage] == _STAGE_RANK[current] + 1
        if not (stage == "lost" or adjacent):
            raise ValueError(
                "the new stage must be 'lost' or the immediate next stage"
            )
        if stage == "negotiation" and opp["amount"] > 50000 \
                and not self._is_manager(actor):
            raise PermissionError("moving to negotiation above 50000 requires a manager")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slots(opp["owner"])

    # ------------------------------------------------------------------
    # discount
    # ------------------------------------------------------------------

    def discount(self, opp_id, pct, actor):
        self._require_known_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_plain_int(pct) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int (not a bool) from 1 to 30")
        opp = self.opps[opp_id]
        if not self._may_act(actor, opp["owner"]):
            raise PermissionError("actor must be the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage %r is final" % (opp["stage"],))
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("a non-manager may discount at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ------------------------------------------------------------------
    # transfer
    # ------------------------------------------------------------------

    def transfer(self, opp_id, new_owner, actor):
        self._require_known_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only managers may transfer opportunities")
        if not self._is_known_user(new_owner) or not self._is_rep(new_owner):
            raise ValueError("new_owner must be the id of a known user with role 'rep'")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage %r is final" % (opp["stage"],))
        if opp["owner"] == new_owner:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new_owner's load is at capacity")
        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slots(previous_owner)

    # ------------------------------------------------------------------
    # forecast
    # ------------------------------------------------------------------

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage == "won":
                won += opp["amount"]
            elif stage in _FINAL_STAGES:
                pass  # lost opportunities contribute nothing
            else:
                open_count += 1
                weighted += opp["amount"] * _STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
