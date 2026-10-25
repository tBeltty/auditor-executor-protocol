"""crm.py — minimal CRM module per /tmp/aep-lab/specs/crm.md."""

from collections import deque

_REP = "rep"
_MANAGER = "manager"
_SOURCES = ("web", "referral", "event")
_SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
_BIG_DOMAIN_BONUS = 15
_BIG_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_STAGES = ("prospect", "proposal", "negotiation", "won")
_FINAL_STAGES = ("won", "lost")
_NEXT = {"prospect": "proposal", "proposal": "negotiation", "negotiation": "won"}
_STAGE_WEIGHT = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id, message="a lead with this email already exists"):
        super().__init__(message)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {
            rep["id"]: {"role": rep["role"], "capacity": rep["capacity"]}
            for rep in reps
        }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_counter = 0
        self._opp_counter = 0
        self._waiting = deque()

    # -- helpers -----------------------------------------------------------

    def _is_manager(self, actor):
        return self._users[actor]["role"] == _MANAGER

    def _require_actor(self, actor):
        # Checked first in every method that takes an actor.
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _load(self, user_id):
        """Load of a rep: owned 'new'/'qualified' leads + owned open opps."""
        user = self._users.get(user_id)
        if user is None or user["role"] != _REP:
            return 0
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in _FINAL_STAGES:
                total += 1
        return total

    def _is_valid_email(self, email):
        """email already normalized (stripped, lowercased)."""
        parts = email.split("@")
        if len(parts) != 2:
            return False
        local, domain = parts
        if not local:
            return False
        if "." not in domain:
            return False
        return any(0 < i < len(domain) - 1 for i, c in enumerate(domain) if c == ".")

    def _pick_owner(self):
        candidates = []
        for user_id, user in self._users.items():
            if user["role"] == _REP:
                load = self._load(user_id)
                if load < user["capacity"]:
                    candidates.append((load, user_id))
        if not candidates:
            return None
        return min(candidates)[1]

    def _assign_waiting(self, rep_id):
        """Free a rep's slot: assign oldest waiting leads while below capacity."""
        while (
            rep_id in self._users
            and self._users[rep_id]["role"] == _REP
            and self._waiting
            and self._load(rep_id) < self._users[rep_id]["capacity"]
        ):
            lead_id = self._waiting.popleft()
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _owner_or_manager(self, actor, owner):
        if actor != owner and not self._is_manager(actor):
            raise PermissionError(
                "actor %r is not the owner %r or a manager" % (actor, owner)
            )

    # -- API ---------------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)  # first: actor must be a known user
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if not self._is_valid_email(normalized):
            raise ValueError(
                "email must contain exactly one '@', a non-empty local part, "
                "and a domain with an inner '.'"
            )
        domain = normalized.split("@")[1]
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string after strip")
        if source not in _SOURCES:
            raise ValueError(
                "source must be one of %r" % (_SOURCES,)
            )
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(existing_id=lead["id"])
        self._lead_counter += 1
        lead_id = "L%d" % self._lead_counter
        score = _SOURCE_SCORE[source]
        if domain not in _BIG_DOMAINS:
            score += _BIG_DOMAIN_BONUS
        owner = self._pick_owner()
        if owner is None:
            self._waiting.append(lead_id)
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
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        self._owner_or_manager(actor, lead["owner"])
        if lead["status"] != "new":
            raise ValueError("lead %r has status %r, not 'new'" % (lead_id, lead["status"]))
        if lead["score"] < 30:
            raise ValueError("lead %r score %d is below 30" % (lead_id, lead["score"]))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int, not a bool")
        self._owner_or_manager(actor, lead["owner"])
        if lead["status"] != "qualified":
            raise ValueError("lead %r must be 'qualified', got %r" % (lead_id, lead["status"]))
        if lead["owner"] is None:
            raise ValueError("lead %r has no owner" % (lead_id,))
        self._opp_counter += 1
        opp_id = "O%d" % self._opp_counter
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
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGES and stage != "lost":
            raise ValueError(
                "stage must be one of prospect, proposal, negotiation, won, lost"
            )
        self._owner_or_manager(actor, opp["owner"])
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity %r is already final" % (opp_id,))
        if stage != "lost" and _NEXT[opp["stage"]] != stage:
            raise ValueError(
                "cannot move %r from %r to %r" % (opp_id, opp["stage"], stage)
            )
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError(
                "moving to negotiation over 50000 requires a manager"
            )
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES and opp["owner"] is not None:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        self._owner_or_manager(actor, opp["owner"])
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity %r is already final" % (opp_id,))
        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("discount above 10 requires a manager")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError(
                "cumulative discount would exceed 30 percent of the original amount"
            )
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("transfer requires a manager")
        target = self._users.get(new_owner)
        if target is None or target["role"] != _REP:
            raise ValueError(
                "new_owner must be a known user with role 'rep'"
            )
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity %r is already final" % (opp_id,))
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new_owner %r has no free capacity" % (new_owner,))

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if previous_owner is not None:
            self._assign_waiting(previous_owner)

    def forecast(self):
        open_opps = [o for o in self.opps.values() if o["stage"] not in _FINAL_STAGES]
        weighted = sum(
            o["amount"] * _STAGE_WEIGHT[o["stage"]] // 100 for o in open_opps
        )
        won = sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted, "won": won}
