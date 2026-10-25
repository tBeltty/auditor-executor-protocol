"""A small CRM implementing exactly the behaviour described in the specification.

Public surface:
    CRM(reps)
    DuplicateLeadError(Exception) with attribute ``existing_id``
"""


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % (existing_id,))


class CRM:
    SOURCES = ("web", "referral", "event")
    FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
    STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
    STAGES = frozenset(("prospect", "proposal", "negotiation", "won", "lost"))
    FINAL_STAGES = frozenset(("won", "lost"))
    SCORE_BY_SOURCE = {"web": 10, "referral": 30, "event": 20}
    WEIGHT_BY_STAGE = {"prospect": 10, "proposal": 30, "negotiation": 60}

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
        self._waiting = []  # lead ids, FIFO
        self._lead_seq = 0
        self._opp_seq = 0

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return self.users[actor]

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in self.FINAL_STAGES:
                load += 1
        return load

    def _owner_can_act(self, owner, actor):
        return owner == actor or self._is_manager(actor)

    def _choose_owner(self):
        best_key = None
        best_id = None
        for rep in self.users.values():
            if rep["role"] != "rep":
                continue
            load = self._load(rep["id"])
            if load < rep["capacity"]:
                key = (load, rep["id"])
                if best_key is None or key < best_key:
                    best_key = key
                    best_id = rep["id"]
        return best_id

    def _fill_slots(self, rep_id):
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalized_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("email domain must contain an interior '.'")
        return normalized

    def _get_lead(self, lead_id):
        if not isinstance(lead_id, str) or lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _get_opp(self, opp_id):
        if not isinstance(opp_id, str) or opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        # 1. email
        normalized = self._normalized_email(email)

        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        clean_name = name.strip()

        # 3. source
        if not isinstance(source, str) or source not in self.SOURCES:
            raise ValueError("source must be web, referral or event")

        # 4. duplicate (same normalized email)
        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])

        # 5. id and score
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        domain = normalized.split("@", 1)[1]
        score = self.SCORE_BY_SOURCE[source]
        if domain not in self.FREE_EMAIL_DOMAINS:
            score += 15

        # 6. owner
        owner = self._choose_owner()

        # 7. record
        self.leads[lead_id] = {
            "id": lead_id,
            "email": normalized,
            "name": clean_name,
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
        self._require_actor(actor)

        lead = self._get_lead(lead_id)

        if not self._owner_can_act(lead["owner"], actor):
            raise PermissionError("actor may not qualify this lead")

        if lead["status"] != "new":
            raise ValueError("lead is not new")

        if lead["score"] < 30:
            raise ValueError("lead score is below 30")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self._get_lead(lead_id)

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive integer")

        if not self._owner_can_act(lead["owner"], actor):
            raise PermissionError("actor may not convert this lead")

        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")

        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        owner = lead["owner"]
        self.opps[opp_id] = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": owner,
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)

        opp = self._get_opp(opp_id)

        if not isinstance(stage, str) or stage not in self.STAGES:
            raise ValueError("unknown stage: %r" % (stage,))

        if not self._owner_can_act(opp["owner"], actor):
            raise PermissionError("actor may not advance this opportunity")

        current = opp["stage"]
        if current in self.FINAL_STAGES:
            raise ValueError("opportunity is already final")

        if stage != "lost":
            index = self.STAGE_ORDER.index(current)
            if stage != self.STAGE_ORDER[index + 1]:
                raise ValueError("not the immediate next stage")

        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("negotiation above 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in self.FINAL_STAGES:
            self._fill_slots(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self._get_opp(opp_id)

        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an integer from 1 to 30")

        if not self._owner_can_act(opp["owner"], actor):
            raise PermissionError("actor may not discount this opportunity")

        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")

        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-managers may discount at most 10")

        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)

        opp = self._get_opp(opp_id)

        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")

        if (
            not isinstance(new_owner, str)
            or new_owner not in self.users
            or self.users[new_owner]["role"] != "rep"
        ):
            raise ValueError("new owner must be a known rep")

        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")

        if new_owner == opp["owner"]:
            raise ValueError("new owner is already the owner")

        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_slots(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in self.FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * self.WEIGHT_BY_STAGE[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
