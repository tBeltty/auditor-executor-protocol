"""CRM module implemented per the provided specification."""

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
OPEN_LEAD_STATUSES = ("new", "qualified")
FINAL_STAGES = ("won", "lost")
STAGE_WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


def _get(mapping, key):
    """Return mapping[key], or None when key is not a usable id string."""
    if not isinstance(key, str):
        return None
    return mapping.get(key)


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
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = []

    # ------------------------------------------------------------------ utils
    def _user(self, actor):
        user = self.reps.get(actor) if isinstance(actor, str) else None
        if user is None:
            raise PermissionError("unknown actor: %r" % (actor,))
        return user

    def _is_manager(self, actor):
        user = self.reps.get(actor)
        return user is not None and user["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in OPEN_LEAD_STATUSES:
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _choose_rep(self):
        candidates = []
        for rep_id, rep in self.reps.items():
            if rep["role"] != "rep":
                continue
            load = self._load(rep_id)
            if load < rep["capacity"]:
                candidates.append((load, rep_id))
        if not candidates:
            return None
        candidates.sort()
        return candidates[0][1]

    def _fill_waiting(self, rep_id):
        capacity = self.reps[rep_id]["capacity"]
        while self._load(rep_id) < capacity and self._waiting:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # -------------------------------------------------------------- add_lead
    def add_lead(self, email, name, source, actor):
        self._user(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, _, domain = normalized.partition("@")
        if not local or not domain:
            raise ValueError("invalid email")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if not isinstance(source, str) or source not in SOURCE_SCORES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORES[source]
        if domain not in FREE_DOMAINS:
            score += 15
        owner = self._choose_rep()
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

    # --------------------------------------------------------------- qualify
    def qualify(self, lead_id, actor):
        self._user(actor)
        lead = _get(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "new":
            raise ValueError("lead not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # --------------------------------------------------------------- convert
    def convert(self, lead_id, amount, actor):
        self._user(actor)
        lead = _get(self.leads, lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if lead["status"] != "qualified":
            raise ValueError("lead not qualified")
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

    # --------------------------------------------------------------- advance
    def advance(self, opp_id, stage, actor):
        self._user(actor)
        opp = _get(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if stage not in STAGES:
            raise ValueError("invalid stage")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost" and stage != self._next_stage(opp["stage"]):
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")

        owner = opp["owner"]
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill_waiting(owner)

    @staticmethod
    def _next_stage(stage):
        index = STAGES.index(stage)
        return STAGES[index + 1] if index + 1 < len(STAGES) else None

    # -------------------------------------------------------------- discount
    def discount(self, opp_id, pct, actor):
        self._user(actor)
        opp = _get(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not allowed")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("discount too large for rep")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # -------------------------------------------------------------- transfer
    def transfer(self, opp_id, new_owner, actor):
        self._user(actor)
        opp = _get(self.opps, opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        target = _get(self.reps, new_owner)
        if target is None or target["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owned by new owner")
        if self._load(new_owner) >= target["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill_waiting(previous)

    # -------------------------------------------------------------- forecast
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
            weighted += opp["amount"] * STAGE_WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
