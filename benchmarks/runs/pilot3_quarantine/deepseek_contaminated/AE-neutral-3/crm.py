"""CRM implementation.

Implements the module described in ``specs/crm.md``:

* :class:`DuplicateLeadError` -- duplicate-email failure carrying ``existing_id``.
* :class:`CRM` -- leads, opportunities, activity log, load-aware assignment.

Only the Python standard library is used.
"""


class DuplicateLeadError(Exception):
    """Raised when a lead already exists for the normalized email."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead email (existing id: %r)" % (existing_id,))
        self.existing_id = existing_id


class CRM:
    """In-memory CRM with reps, managers, leads, opportunities and a log."""

    SOURCES = ("web", "referral", "event")
    SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
    FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
    STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
    STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
    FINAL_STAGES = ("won", "lost")
    WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
    MANAGER_DISCOUNT_LIMIT = 30
    REP_DISCOUNT_LIMIT = 10
    NEGOTIATION_MANAGER_THRESHOLD = 50000

    def __init__(self, reps):
        self.leads = {}
        self.opps = {}
        self.log = []

        self._users = {}
        self._rep_ids = []
        for rep in reps:
            user = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
            self._users[user["id"]] = user
            if user["role"] == "rep":
                self._rep_ids.append(user["id"])
        self._rep_ids.sort()

        self._waiting = []  # FIFO of lead ids without an owner
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self._users[actor]

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in self.FINAL_STAGES:
                load += 1
        return load

    def _select_owner(self):
        """Rep with lowest load below capacity; ties by smallest id string."""
        best = None
        best_load = None
        for rep_id in self._rep_ids:  # already sorted, so ties keep smallest id
            load = self._load(rep_id)
            capacity = self._users[rep_id]["capacity"]
            if load >= capacity:
                continue
            if best is None or load < best_load:
                best = rep_id
                best_load = load
        return best

    def _assign_waiting(self, rep_id):
        capacity = self._users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _check_ownership(self, owner, actor):
        if owner != actor and not self._is_manager(actor):
            raise PermissionError("actor %r may not act on this record" % (actor,))

    # ------------------------------------------------------------------
    # leads
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, _, domain = normalized.partition("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if not any(
            char == "." and 0 < index < len(domain) - 1
            for index, char in enumerate(domain)
        ):
            raise ValueError("email domain must contain an inner '.'")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in self.SOURCES:
            raise ValueError("unknown source: %r" % (source,))

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        score = self.SOURCE_SCORES[source]
        if domain not in self.FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._select_owner()

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
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
        self._require_actor(actor)
        lead = self._get_lead(lead_id)
        self._check_ownership(lead["owner"], actor)
        if lead["status"] != "new":
            raise ValueError("lead %s is not new" % (lead_id,))
        if lead["score"] < 30:
            raise ValueError("lead %s does not score high enough" % (lead_id,))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._get_lead(lead_id)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._check_ownership(lead["owner"], actor)
        if lead["status"] != "qualified":
            raise ValueError("lead %s is not qualified" % (lead_id,))
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

    # ------------------------------------------------------------------
    # opportunities
    # ------------------------------------------------------------------
    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if stage not in self.STAGES:
            raise ValueError("unknown stage: %r" % (stage,))
        self._check_ownership(opp["owner"], actor)
        current = opp["stage"]
        if current in self.FINAL_STAGES:
            raise ValueError("opportunity %s is already final" % (opp_id,))
        next_stage = self.STAGE_ORDER[self.STAGE_ORDER.index(current) + 1]
        if stage != "lost" and stage != next_stage:
            raise ValueError("cannot move %s from %s to %s" % (opp_id, current, stage))
        if (
            stage == "negotiation"
            and opp["amount"] > self.NEGOTIATION_MANAGER_THRESHOLD
            and not self._is_manager(actor)
        ):
            raise PermissionError("large deals need a manager to reach negotiation")

        owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self.FINAL_STAGES:
            self._assign_waiting(owner)

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        self._check_ownership(opp["owner"], actor)
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if not self._is_manager(actor) and pct > self.REP_DISCOUNT_LIMIT:
            raise PermissionError("non-managers may discount at most 10 percent")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount may not exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._get_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if (
            not isinstance(new_owner, str)
            or new_owner not in self._users
            or self._users[new_owner]["role"] != "rep"
        ):
            raise ValueError("new_owner must be a known rep")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the owner")
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new_owner is at capacity")

        previous_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous_owner)

    def forecast(self):
        open_opps = [
            opp for opp in self.opps.values() if opp["stage"] not in self.FINAL_STAGES
        ]
        weighted = sum(
            opp["amount"] * self.WEIGHTS[opp["stage"]] // 100 for opp in open_opps
        )
        won = sum(
            opp["amount"] for opp in self.opps.values() if opp["stage"] == "won"
        )
        return {"open": len(open_opps), "weighted": weighted, "won": won}
