"""crm.py - minimal CRM module implementing the behaviour in specs/crm.md.

Standard library only.  Every mutating method validates fully before touching
state so that a failed call changes nothing and appends nothing to ``log``.
"""

FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = ("web", "referral", "event")
BASE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
ALL_STAGES = STAGE_ORDER + ("lost",)
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}
MANAGER_MAX_DISCOUNT = 30
REP_MAX_DISCOUNT = 10
NEGOTIATION_APPROVAL_THRESHOLD = 50000
MAX_CUMULATIVE_DISCOUNT_PCT = 30


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id, message=None):
        self.existing_id = existing_id
        super().__init__(message or "duplicate lead: %s" % (existing_id,))


class CRM:
    def __init__(self, reps):
        self.reps = {}
        for rep in reps:
            self.reps[rep["id"]] = {
                "id": rep["id"],
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._email_index = {}
        self._lead_count = 0
        self._opp_count = 0

    # ------------------------------------------------------------------ utils
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.reps:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.reps[actor]["role"] == "manager"

    def _is_owner_or_manager(self, actor, owner):
        return actor == owner or self._is_manager(actor)

    @staticmethod
    def _lookup(mapping, entity_id):
        """Return the entity, or None when the id cannot name one.

        Ids are strings, so anything else is simply unknown -- and an
        unhashable value must not leak a TypeError where the spec promises
        ValueError for a missing entity.
        """
        if not isinstance(entity_id, str):
            return None
        return mapping.get(entity_id)

    def _load(self, rep_id):
        if rep_id is None:
            return 0
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _pick_rep(self):
        best = None
        for rep_id in sorted(self.reps):
            rep = self.reps[rep_id]
            if rep["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load >= rep["capacity"]:
                continue
            if best is None or load < best[0]:
                best = (load, rep_id)
        return None if best is None else best[1]

    def _free_slot(self, rep_id):
        if rep_id is None or rep_id not in self.reps:
            return
        capacity = self.reps[rep_id]["capacity"]
        while self.waiting and self._load(rep_id) < capacity:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # --------------------------------------------------------------- commands
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
        if "." not in domain[1:-1]:
            raise ValueError("email domain must contain an inner '.'")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in SOURCES:
            raise ValueError("source must be one of %s" % (SOURCES,))

        existing_id = self._email_index.get(normalized)
        if existing_id is not None:
            raise DuplicateLeadError(existing_id)

        score = BASE_SCORES[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_rep()

        self._lead_count += 1
        lead_id = "L%d" % self._lead_count
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
        self._email_index[normalized] = lead_id
        if owner is None:
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)

        lead = self._lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not self._is_owner_or_manager(actor, lead["owner"]):
            raise PermissionError("not allowed to qualify %s" % (lead_id,))
        if lead["status"] != "new":
            raise ValueError("lead %s is not new" % (lead_id,))
        if lead["score"] < 30:
            raise ValueError("lead %s score below 30" % (lead_id,))

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self._lookup(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if not self._is_owner_or_manager(actor, lead["owner"]):
            raise PermissionError("not allowed to convert %s" % (lead_id,))
        if lead["status"] != "qualified":
            raise ValueError("lead %s is not qualified" % (lead_id,))
        if lead["owner"] is None:
            raise ValueError("lead %s has no owner" % (lead_id,))

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

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)

        opp = self._lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in ALL_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not self._is_owner_or_manager(actor, opp["owner"]):
            raise PermissionError("not allowed to advance %s" % (opp_id,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))

        if stage != "lost":
            current_index = STAGE_ORDER.index(opp["stage"])
            next_stage = STAGE_ORDER[current_index + 1]
            if stage != next_stage:
                raise ValueError("invalid transition %s -> %s" % (opp["stage"], stage))

        if stage == "negotiation" and opp["amount"] > NEGOTIATION_APPROVAL_THRESHOLD:
            if not self._is_manager(actor):
                raise PermissionError("negotiation above threshold needs a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self._lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        if not self._is_owner_or_manager(actor, opp["owner"]):
            raise PermissionError("not allowed to discount %s" % (opp_id,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if not self._is_manager(actor) and pct > REP_MAX_DISCOUNT:
            raise PermissionError("reps may discount at most %d" % (REP_MAX_DISCOUNT,))

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * (100 - MAX_CUMULATIVE_DISCOUNT_PCT):
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self._lookup(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("transfer requires a manager")
        target = self.reps.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new_owner must be a rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if new_owner == opp["owner"]:
            raise ValueError("new_owner is already the owner")
        if self._load(new_owner) >= target["capacity"]:
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
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
