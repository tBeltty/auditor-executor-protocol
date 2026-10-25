"""Small CRM domain model."""

STAGES = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
SOURCES = ("web", "referral", "event")
FREE_EMAIL_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")


class DuplicateLeadError(Exception):
    """Raised when a lead with the same normalized email already exists."""

    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % existing_id)


class CRM:
    def __init__(self, reps):
        self.users = {}
        for rep in reps:
            self.users[rep["id"]] = {
                "role": rep["role"],
                "capacity": rep["capacity"],
            }
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = []

    # ------------------------------------------------------------------ helpers
    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _fill_slot(self, rep_id):
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # ------------------------------------------------------------------- actions
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = normalized.split("@")
        if not local or "." not in domain[1:-1]:
            raise ValueError("invalid email")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")

        if source not in SOURCES:
            raise ValueError("invalid source")

        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq

        score = {"web": 10, "referral": 30, "event": 20}[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        candidates = []
        for user_id, info in self.users.items():
            if info["role"] == "rep" and self._load(user_id) < info["capacity"]:
                candidates.append((self._load(user_id), user_id))
        owner = min(candidates)[1] if candidates else None

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

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not (self._is_manager(actor) or lead["owner"] == actor):
            raise PermissionError("actor cannot qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score is too low")

        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)

        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead: %r" % (lead_id,))

        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")

        if not (self._is_manager(actor) or lead["owner"] == actor):
            raise PermissionError("actor cannot convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
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
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if stage not in STAGES and stage != "lost":
            raise ValueError("invalid stage: %r" % (stage,))

        if not (self._is_manager(actor) or opp["owner"] == actor):
            raise PermissionError("actor cannot advance this opportunity")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")

        if stage != "lost":
            index = STAGES.index(opp["stage"])
            if index + 1 >= len(STAGES) or STAGES[index + 1] != stage:
                raise ValueError("invalid stage transition")

        if (
            stage == "negotiation"
            and opp["amount"] > 50000
            and not self._is_manager(actor)
        ):
            raise PermissionError("manager required for large negotiation")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))

        if stage in FINAL_STAGES:
            self._fill_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")

        if not (self._is_manager(actor) or opp["owner"] == actor):
            raise PermissionError("actor cannot discount this opportunity")

        if opp["stage"] in FINAL_STAGES:
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

        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity: %r" % (opp_id,))

        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")

        info = self.users.get(new_owner)
        if info is None or info["role"] != "rep":
            raise ValueError("new owner must be a rep")

        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")

        if new_owner == opp["owner"]:
            raise ValueError("new owner is the current owner")

        if self._load(new_owner) >= info["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))

        self._fill_slot(previous)

    def forecast(self):
        weights = {"prospect": 10, "proposal": 30, "negotiation": 60}
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in FINAL_STAGES:
                if opp["stage"] == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * weights[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
