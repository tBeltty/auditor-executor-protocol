"""CRM module implemented per spec."""

STAGES = ("prospect", "proposal", "negotiation", "won")
FINAL_STAGES = ("won", "lost")
VALID_SOURCES = ("web", "referral", "event")
FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
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
        self.waiting = []  # FIFO of lead ids
        self._lead_seq = 0
        self._opp_seq = 0
        self._emails = {}

    # -- helpers ---------------------------------------------------------
    def _actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor: %r" % (actor,))
        return actor

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, user_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == user_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == user_id and opp["stage"] not in FINAL_STAGES:
                load += 1
        return load

    def _pick_owner(self):
        best = None
        for uid in sorted(self.users):
            user = self.users[uid]
            if user["role"] != "rep":
                continue
            load = self._load(uid)
            if load < user["capacity"]:
                if best is None or load < best[0]:
                    best = (load, uid)
        return None if best is None else best[1]

    def _assign_waiting(self, user_id):
        capacity = self.users[user_id]["capacity"]
        while self.waiting and self._load(user_id) < capacity:
            lead_id = self.waiting.pop(0)
            lead = self.leads[lead_id]
            lead["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    # -- API -------------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        parts = normalized.split("@")
        if len(parts) != 2 or not parts[0]:
            raise ValueError("invalid email")
        domain = parts[1]
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email domain")

        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in VALID_SOURCES:
            raise ValueError("invalid source")

        if normalized in self._emails:
            raise DuplicateLeadError(self._emails[normalized])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORE[source]
        if domain not in FREE_DOMAINS:
            score += 15

        owner = self._pick_owner()
        if owner is None:
            self.waiting.append(lead_id)

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
        self._emails[normalized] = lead_id
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("invalid amount")
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError("not owner or manager")
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
        self._actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if stage not in STAGES and stage != "lost":
            raise ValueError("invalid stage")
        if not self._is_manager(actor) and opp["owner"] != actor:
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost":
            if STAGES.index(stage) != STAGES.index(opp["stage"]) + 1:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("invalid pct")
        if not self._is_manager(actor) and opp["owner"] != actor:
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if pct > 10 and not self._is_manager(actor):
            raise PermissionError("discount above 10 requires manager")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        user = self.users.get(new_owner) if isinstance(new_owner, str) else None
        if user is None or user["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("already owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(previous)

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
            weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
