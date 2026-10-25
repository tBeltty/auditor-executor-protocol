"""crm.py — a tiny CRM with leads, opportunities, permissions and forecasting.

Implements the spec in /tmp/aep-lab/specs/crm.md.
"""

_STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
_FINAL_STAGES = frozenset(("won", "lost"))
_VALID_STAGES = frozenset(("prospect", "proposal", "negotiation", "won", "lost"))
_FREE_DOMAINS = frozenset(("gmail.com", "yahoo.com", "outlook.com"))
_SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
_STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised by add_lead when a lead with the same normalized email exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self._users = {r["id"]: dict(r) for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._waiting = []  # FIFO queue of lead ids with no owner
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in _FINAL_STAGES:
                n += 1
        return n

    def _check_owner_or_manager(self, entity, actor):
        if actor != entity["owner"] and not self._is_manager(actor):
            raise PermissionError(
                "actor %r is not the owner or a manager" % (actor,))

    def _assign_waiting(self, rep_id):
        """Free rep_id's slot: assign FIFO waiting leads while load < capacity."""
        if rep_id is None or rep_id not in self._users:
            return
        while self._waiting:
            if self._load(rep_id) >= self._users[rep_id]["capacity"]:
                break
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------
    # add_lead
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email local part must be non-empty")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email domain")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in _SOURCE_SCORES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = _SOURCE_SCORES[source]
        if domain not in _FREE_DOMAINS:
            score += 15

        candidates = [
            uid
            for uid, user in self._users.items()
            if user["role"] == "rep" and self._load(uid) < user["capacity"]
        ]
        if candidates:
            owner = min(candidates, key=lambda uid: (self._load(uid), uid))
        else:
            owner = None

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

    # ------------------------------------------------------------------
    # qualify
    # ------------------------------------------------------------------
    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        self._check_owner_or_manager(lead, actor)
        if lead["status"] != "new":
            raise ValueError("lead status is %r, not 'new'" % (lead["status"],))
        if lead["score"] < 30:
            raise ValueError("lead score %d is below 30" % (lead["score"],))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # ------------------------------------------------------------------
    # convert
    # ------------------------------------------------------------------
    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._check_owner_or_manager(lead, actor)
        if lead["status"] != "qualified":
            raise ValueError("lead status is %r, not 'qualified'"
                             % (lead["status"],))
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

    # ------------------------------------------------------------------
    # advance
    # ------------------------------------------------------------------
    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in _VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        self._check_owner_or_manager(opp, actor)
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage %r is final" % (opp["stage"],))
        idx = _STAGE_ORDER.index(opp["stage"])
        if stage != "lost" and stage != _STAGE_ORDER[idx + 1]:
            raise ValueError("cannot move from %r to %r"
                             % (opp["stage"], stage))
        if (stage == "negotiation" and opp["amount"] > 50000
                and not self._is_manager(actor)):
            raise PermissionError(
                "moving to negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in _FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    # ------------------------------------------------------------------
    # discount
    # ------------------------------------------------------------------
    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if (not isinstance(pct, int) or isinstance(pct, bool)
                or not (1 <= pct <= 30)):
            raise ValueError("pct must be an int from 1 to 30")
        self._check_owner_or_manager(opp, actor)
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage %r is final" % (opp["stage"],))
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError(
                "non-manager discount is limited to 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ------------------------------------------------------------------
    # transfer
    # ------------------------------------------------------------------
    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in _FINAL_STAGES:
            raise ValueError("stage %r is final" % (opp["stage"],))
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from the current owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    # ------------------------------------------------------------------
    # forecast
    # ------------------------------------------------------------------
    def forecast(self):
        open_opps = [o for o in self.opps.values()
                     if o["stage"] not in _FINAL_STAGES]
        weighted = sum(o["amount"] * _STAGE_WEIGHTS[o["stage"]] // 100
                       for o in open_opps)
        won_total = sum(o["amount"] for o in self.opps.values()
                        if o["stage"] == "won")
        return {"open": len(open_opps), "weighted": weighted,
                "won": won_total}
