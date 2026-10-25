"""CRM lead/opportunity pipeline (see specs/crm.md)."""

FREE_EMAIL_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
VALID_SOURCES = {"web", "referral", "event"}
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = {"won", "lost"}
VALID_STAGES = set(STAGE_ORDER) | {"lost"}
OPEN_STAGES = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


class CRM:
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
        self._waiting = []
        self._lead_count = 0
        self._opp_count = 0

    # -- helpers ---------------------------------------------------------
    def _require_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, user_id):
        return self.users[user_id]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _can_take_work(self, rep_id):
        return (
            self.users[rep_id]["role"] == "rep"
            and self._load(rep_id) < self.users[rep_id]["capacity"]
        )

    def _pick_owner(self):
        candidates = [r for r in self.users.values() if r["role"] == "rep"]
        candidates = [r for r in candidates if self._load(r["id"]) < r["capacity"]]
        if not candidates:
            return None
        candidates.sort(key=lambda r: (self._load(r["id"]), r["id"]))
        return candidates[0]["id"]

    def _assign_waiting(self, rep_id):
        while self._waiting and self._can_take_work(rep_id):
            lead_id = self._waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _require_opp(self, opp_id):
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    # -- operations ------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)

        if not isinstance(email, str):
            raise ValueError("email must be a string")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("email must contain exactly one '@'")
        local, domain = normalized.split("@")
        if not local or not domain:
            raise ValueError("email must have a local part and a domain")
        if not any(
            ch == "." and 0 < i < len(domain) - 1 for i, ch in enumerate(domain)
        ):
            raise ValueError("email domain must contain an interior '.'")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty string")

        if source not in VALID_SOURCES:
            raise ValueError("invalid source: %r" % (source,))

        for existing in self.leads.values():
            if existing["email"] == normalized:
                raise DuplicateLeadError(existing["id"])

        score = {"web": 10, "referral": 30, "event": 20}[source]
        if domain not in FREE_EMAIL_DOMAINS:
            score += 15

        owner = self._pick_owner()
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
        if owner is None:
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        lead = self.leads[lead_id]
        if not (self._is_manager(actor) or actor == lead["owner"]):
            raise PermissionError("actor may not qualify this lead")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("lead score too low to qualify")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("amount must be a positive int")
        lead = self.leads[lead_id]
        if not (self._is_manager(actor) or actor == lead["owner"]):
            raise PermissionError("actor may not convert this lead")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_count += 1
        opp_id = "O%d" % self._opp_count
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
        opp = self._require_opp(opp_id)
        if stage not in VALID_STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        if not (self._is_manager(actor) or actor == opp["owner"]):
            raise PermissionError("actor may not advance this opportunity")
        current = opp["stage"]
        if current in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if stage != "lost" and stage != STAGE_ORDER[STAGE_ORDER.index(current) + 1]:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000:
            if not self._is_manager(actor):
                raise PermissionError("large deal requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if not isinstance(pct, int) or isinstance(pct, bool) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        if not (self._is_manager(actor) or actor == opp["owner"]):
            raise PermissionError("actor may not discount this opportunity")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount exceeds 10 percent")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("only a manager may transfer")
        if (
            not isinstance(new_owner, str)
            or new_owner not in self.users
            or self.users[new_owner]["role"] != "rep"
        ):
            raise ValueError("new owner must be a known rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is already final")
        previous = opp["owner"]
        if new_owner == previous:
            raise ValueError("opportunity already owned by that rep")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner is at capacity")

        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            stage = opp["stage"]
            if stage in FINAL_STAGES:
                if stage == "won":
                    won += opp["amount"]
                continue
            open_count += 1
            weighted += opp["amount"] * OPEN_STAGES[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
