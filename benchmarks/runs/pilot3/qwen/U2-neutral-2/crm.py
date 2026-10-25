"""crm.py — minimal CRM with leads, opportunities, routing and forecasting.

Implements the ``CRM`` class and ``DuplicateLeadError`` exactly as specified
in /tmp/aep-lab/specs/crm.md. Python 3 standard library only.
"""

from collections import deque

_FINAL_STAGES = ("won", "lost")
_STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
_VALID_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_SOURCES = ("web", "referral", "event")
_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
_OPEN_LEAD_STATUSES = ("new", "qualified")
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead, existing id: %r" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {}
        for rep in reps:
            user = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
            # duplicate ids: the last declaration wins
            self._users[user["id"]] = user
        # routing pool: role "rep" only (derived from the final user map so a
        # redeclared manager never owns anything), sorted for determinism
        self._rep_ids = sorted(
            uid for uid, user in self._users.items() if user["role"] == "rep"
        )
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = deque()
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------ #
    # internal helpers
    # ------------------------------------------------------------------ #

    def _check_actor(self, actor):
        if not self._has(self._users, actor):
            raise PermissionError("unknown actor: %r" % (actor,))

    @staticmethod
    def _has(mapping, key):
        """``key in mapping`` that treats unhashable keys as simply absent.

        The spec decides unknown actors / unknown entities by value, so a
        list or dict passed as an id must fail like any other unknown id
        instead of raising TypeError.
        """
        try:
            return key in mapping
        except TypeError:
            return False

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        """Current load of a rep, recomputed from live state.

        Leads owned with status "new"/"qualified" plus opportunities owned
        whose stage is not "won"/"lost".
        """
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in _OPEN_LEAD_STATUSES:
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        """Rep with the lowest load below capacity; ties by smallest id."""
        best = None
        best_key = None
        for rep_id in self._rep_ids:
            load = self._load(rep_id)
            if load >= self._users[rep_id]["capacity"]:
                continue
            key = (load, rep_id)
            if best_key is None or key < best_key:
                best, best_key = rep_id, key
        return best

    def _free_slot(self, rep_id):
        """Assign oldest waiting leads while the rep has room."""
        while (
            self._waiting
            and self._load(rep_id) < self._users[rep_id]["capacity"]
        ):
            lead = self._waiting.popleft()
            lead["owner"] = rep_id
            self.log.append(("assign", lead["id"], "system"))

    # ------------------------------------------------------------------ #
    # public API
    # ------------------------------------------------------------------ #

    def add_lead(self, email, name, source, actor):
        """Create a lead, route it to the least-loaded rep with room, or
        queue it. Returns the new lead id (spec ``add_lead``)."""
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        at_parts = normalized.split("@")
        if len(at_parts) != 2:
            raise ValueError("email must contain exactly one @")
        local, domain = at_parts
        if not local:
            raise ValueError("email local part must be non-empty")
        # the domain must contain a "." that is neither its first nor its
        # last character, i.e. a "." somewhere inside domain[1:-1]
        if "." not in domain[1:-1]:
            raise ValueError("email domain dot must not be first or last")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in _SOURCES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])
        score = _SOURCE_SCORES[source]
        if domain not in _FREE_DOMAINS:
            score += 15
        # compute the owner before consuming the id counter: every fallible
        # check must happen first so a failed call never advances _lead_seq
        owner = self._pick_owner()
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
        self.log.append(("add_lead", lead_id, actor))
        if owner is None:
            self._waiting.append(self.leads[lead_id])
        return lead_id

    def qualify(self, lead_id, actor):
        """Mark a scored-up "new" lead as "qualified" (spec ``qualify``)."""
        self._check_actor(actor)
        if not self._has(self.leads, lead_id):
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may qualify")
        if lead["status"] != "new":
            raise ValueError("lead status must be new")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        """Turn a qualified, owned lead into an opportunity; returns its id
        (spec ``convert``)."""
        self._check_actor(actor)
        if not self._has(self.leads, lead_id):
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive integer")
        lead = self.leads[lead_id]
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may convert")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be qualified")
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
        """Move an opportunity along prospect -> proposal -> negotiation ->
        won, or to lost; a final stage frees the owner's slot for waiting
        leads (spec ``advance``)."""
        self._check_actor(actor)
        if not self._has(self.opps, opp_id):
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may advance")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if stage == "lost":
            pass
        elif _STAGE_ORDER.index(stage) != _STAGE_ORDER.index(opp["stage"]) + 1:
            raise ValueError("stage must be the immediate next stage")
        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("manager required to negotiate large deals")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        """Apply a percentage discount, capped at 30% cumulative and 10% for
        reps (spec ``discount``)."""
        self._check_actor(actor)
        if not self._has(self.opps, opp_id):
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not isinstance(pct, int) or isinstance(pct, bool):
            raise ValueError("pct must be an integer")
        if pct < 1 or pct > 30:
            raise ValueError("pct must be between 1 and 30")
        opp = self.opps[opp_id]
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("only the owner or a manager may discount")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        """Manager-only reassignment of an open opportunity; frees the
        previous owner's slot afterwards (spec ``transfer``)."""
        self._check_actor(actor)
        if not self._has(self.opps, opp_id):
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if not self._has(self._users, new_owner):
            raise ValueError("new_owner must be a known rep")
        target = self._users[new_owner]
        if target["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity is in a final stage")
        previous_owner = opp["owner"]
        if new_owner == previous_owner:
            raise ValueError("new owner must differ from current owner")
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        """Pipeline snapshot: open count, weighted open value, won value
        (spec ``forecast``; no actor, no log)."""
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in _FINAL_STAGES:
                if stage == "won":
                    won_total += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * _STAGE_WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
