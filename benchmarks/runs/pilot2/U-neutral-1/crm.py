"""In-memory CRM with lead routing, opportunities, discounts and forecasting."""

FREEMAIL_DOMAINS = frozenset({"gmail.com", "yahoo.com", "outlook.com"})
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
SOURCE_VALUES = frozenset(SOURCE_SCORES)
STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = frozenset({"won", "lost"})
STAGE_VALUES = frozenset(STAGE_ORDER) | {"lost"}
OPEN_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = rep
        self.leads = {}
        self.opps = {}
        self.log = []
        self.waiting = []
        self._lead_seq = 0
        self._opp_seq = 0

    # ---------------------------------------------------------------- helpers

    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _check_owner_or_manager(self, owner, actor):
        if actor != owner and not self._is_manager(actor):
            raise PermissionError("actor %r may not act on %r" % (actor, owner))

    def _load(self, user_id):
        total = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                total += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                total += 1
        return total

    def _pick_owner(self):
        best = None
        best_load = None
        for user_id, user in self.users.items():
            if user["role"] != "rep":
                continue
            load = self._load(user_id)
            if load >= user["capacity"]:
                continue
            if best_load is None or load < best_load or (
                load == best_load and user_id < best
            ):
                best = user_id
                best_load = load
        return best

    def _free_slots(self, user_id):
        if user_id is None or user_id not in self.users:
            return
        capacity = self.users[user_id]["capacity"]
        while self.waiting and self._load(user_id) < capacity:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("email must have a non-empty local part")
        if "." not in domain:
            raise ValueError("email domain must contain a dot")
        if domain.startswith(".") or domain.endswith("."):
            raise ValueError("email domain dot may not be first or last")
        return normalized

    # ----------------------------------------------------------------- public

    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        normalized = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")
        if source not in SOURCE_VALUES:
            raise ValueError("unknown source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        domain = normalized.split("@", 1)[1]
        score = SOURCE_SCORES[source]
        if domain not in FREEMAIL_DOMAINS:
            score += 15
        owner = self._pick_owner()
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
            self.waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        self._check_owner_or_manager(lead["owner"], actor)
        if lead["status"] != "new":
            raise ValueError("lead %s is not new" % (lead_id,))
        if lead["score"] < 30:
            raise ValueError("lead %s score is too low" % (lead_id,))
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._check_owner_or_manager(lead["owner"], actor)
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

    def advance(self, opp_id, stage, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if stage not in STAGE_VALUES:
            raise ValueError("unknown stage: %r" % (stage,))
        self._check_owner_or_manager(opp["owner"], actor)
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if stage != "lost" and stage != STAGE_ORDER[STAGE_ORDER.index(current) + 1]:
            raise ValueError("illegal stage transition %s -> %s" % (current, stage))
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("discount-scale negotiation requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slots(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not _is_int(pct) or pct < 1 or pct > 30:
            raise ValueError("pct must be an int from 1 to 30")
        self._check_owner_or_manager(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("discount above 10 requires a manager")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount would exceed 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        target = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep: %r" % (new_owner,))
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity %s is final" % (opp_id,))
        if new_owner == opp["owner"]:
            raise ValueError("opportunity already owned by %s" % (new_owner,))
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner %s is at capacity" % (new_owner,))

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slots(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * OPEN_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
