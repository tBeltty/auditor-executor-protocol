"""crm.py — a minimal CRM with leads, opportunities, capacity-based ownership
and an audit log.

Implements the specification in /tmp/aep-lab/specs/crm.md.
"""

_FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_FINAL_STAGES = ("won", "lost")
_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    """Customer relationship manager.

    Attributes:
        leads: dict mapping lead id -> lead dict.
        opps: dict mapping opportunity id -> opportunity dict.
        log: list of (op, entity_id, actor_id) tuples, appended only by
            successful calls.
    """

    def __init__(self, reps):
        self.users = {}
        for user in reps:
            self.users[user["id"]] = user
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO queue of lead ids waiting for an owner
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internal helpers
    # ------------------------------------------------------------------

    def _check_actor(self, actor):
        """Raise PermissionError unless actor is a known user id."""
        try:
            known = actor in self.users
        except TypeError:
            known = False
        if not known:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _can_act(self, actor, owner):
        """True if actor is a manager or the given owner."""
        return self._is_manager(actor) or actor == owner

    def _load(self, rep_id):
        """Workload of a rep: active leads owned + open opportunities owned."""
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        """Rep with the lowest load among reps below capacity (ties: smallest
        id in string order). None if no rep qualifies."""
        eligible = []
        for user_id, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load < user["capacity"]:
                eligible.append((load, user_id))
        if not eligible:
            return None
        return min(eligible, key=lambda pair: (pair[0], pair[1]))[1]

    def _free_slot(self, rep_id):
        """Assign waiting queue leads to rep_id while load is below capacity."""
        if rep_id is None or rep_id not in self.users:
            return
        if self.users[rep_id]["role"] != "rep":
            return
        while self._waiting:
            if self._load(rep_id) >= self.users[rep_id]["capacity"]:
                break
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        """Create a lead; returns its id ("L<n>")."""
        self._check_actor(actor)

        # 1. email validation (on the normalized form)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty part before '@'")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email domain")

        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        # 3. source
        if source not in _SOURCE_SCORES:
            raise ValueError("invalid source")

        # 4. duplicate normalized email
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        # 5. id + score
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = _SOURCE_SCORES[source]
        if domain not in _FREE_DOMAINS:
            score += 15

        # 6. owner selection (or waiting queue)
        owner = self._pick_owner()

        # 7. store
        lead = {
            "id": lead_id,
            "email": normalized,
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
        """Mark a lead as qualified."""
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not self._can_act(actor, lead["owner"]):
            raise PermissionError("actor is not the lead's owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead status must be 'new'")
        if lead["score"] < 30:
            raise ValueError("lead score must be at least 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        """Convert a qualified lead into an opportunity; returns opp id "O<n>"."""
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not self._can_act(actor, lead["owner"]):
            raise PermissionError("actor is not the lead's owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead status must be 'qualified'")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
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

    def advance(self, opp_id, stage, actor):
        """Move an opportunity to its next stage (or to 'lost')."""
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        opp = self.opps[opp_id]
        if not self._can_act(actor, opp["owner"]):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if stage != "lost":
            next_stage = _STAGE_ORDER[_STAGE_ORDER.index(opp["stage"]) + 1]
            if stage != next_stage:
                raise ValueError("stage must be 'lost' or the immediate next stage")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError(
                    "moving to negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        """Apply a percentage discount to an open opportunity."""
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if (not isinstance(pct, int) or isinstance(pct, bool)
                or pct < 1 or pct > 30):
            raise ValueError("pct must be an int from 1 to 30")
        opp = self.opps[opp_id]
        if not self._can_act(actor, opp["owner"]):
            raise PermissionError("actor is not the opportunity's owner or a manager")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount is limited to 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        """Reassign an open opportunity to another rep (manager only)."""
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer an opportunity")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        opp = self.opps[opp_id]
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("opportunity stage is final")
        if opp["owner"] == new_owner:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new_owner has no free capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous_owner)

    def forecast(self):
        """Aggregate opportunity numbers; no actor, no log entry."""
        open_count = 0
        weighted = 0
        won_total = 0
        for opp in self.opps.values():
            if opp["stage"] == "won":
                won_total += opp["amount"]
            elif opp["stage"] in _FINAL_STAGES:
                pass  # lost opportunities are excluded everywhere
            else:
                open_count += 1
                weighted += opp["amount"] * _WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won_total}
