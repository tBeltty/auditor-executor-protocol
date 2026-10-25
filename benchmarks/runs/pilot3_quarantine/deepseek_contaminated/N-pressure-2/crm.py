"""CRM lead/opportunity management, implemented per specs/crm.md."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % (existing_id,))
        self.existing_id = existing_id


FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCE_SCORES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
STAGES = set(STAGE_ORDER) | {"lost"}
FINAL_STAGES = {"won", "lost"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


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
        self.waiting = []  # FIFO of lead ids without an owner
        self._lead_n = 0
        self._opp_n = 0

    # ------------------------------------------------------------------ utils
    def _require_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown user: %r" % (actor,))
        return self.users[actor]

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
        for user in self.users.values():
            if user["role"] != "rep":
                continue
            if self._load(user["id"]) >= user["capacity"]:
                continue
            key = (self._load(user["id"]), user["id"])
            if best is None or key < best:
                best = key
        return best[1] if best else None

    def _free_slot(self, user_id):
        if user_id is None:
            return
        capacity = self.users[user_id]["capacity"]
        while self.waiting and self._load(user_id) < capacity:
            lead_id = self.waiting.pop(0)
            self.leads[lead_id]["owner"] = user_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        parts = norm.split("@")
        if len(parts) != 2:
            raise ValueError("email must contain exactly one @")
        local, domain = parts
        if not local:
            raise ValueError("email local part is empty")
        dot = domain.find(".")
        if dot <= 0 or dot == len(domain) - 1:
            raise ValueError("email domain is invalid")
        return norm

    def _require_lead(self, lead_id):
        if lead_id not in self.leads:
            raise ValueError("unknown lead: %r" % (lead_id,))
        return self.leads[lead_id]

    def _require_opp(self, opp_id):
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity: %r" % (opp_id,))
        return self.opps[opp_id]

    def _require_owner_or_manager(self, entity, actor):
        if not self._is_manager(actor) and entity["owner"] != actor:
            raise PermissionError("not allowed: %r" % (actor,))

    # --------------------------------------------------------------- methods
    def add_lead(self, email, name, source, actor):
        self._require_actor(actor)
        norm = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")
        if source not in SOURCE_SCORES:
            raise ValueError("invalid source: %r" % (source,))
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])

        score = SOURCE_SCORES[source]
        domain = norm.split("@")[1]
        if domain not in FREE_DOMAINS:
            score += 15

        owner = self._pick_owner()
        self._lead_n += 1
        lead_id = "L%d" % self._lead_n
        self.leads[lead_id] = {
            "id": lead_id,
            "email": norm,
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
        lead = self._require_lead(lead_id)
        self._require_owner_or_manager(lead, actor)
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._require_actor(actor)
        lead = self._require_lead(lead_id)
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        self._require_owner_or_manager(lead, actor)
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_n += 1
        opp_id = "O%d" % self._opp_n
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
        if not isinstance(stage, str) or stage not in STAGES:
            raise ValueError("invalid stage: %r" % (stage,))
        self._require_owner_or_manager(opp, actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        current = opp["stage"]
        if stage != "lost":
            idx = STAGE_ORDER.index(current)
            if idx + 1 >= len(STAGE_ORDER) or STAGE_ORDER[idx + 1] != stage:
                raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required above 50000")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if isinstance(pct, bool) or not isinstance(pct, int) or not 1 <= pct <= 30:
            raise ValueError("pct must be an int from 1 to 30")
        self._require_owner_or_manager(opp, actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount above 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._require_actor(actor)
        opp = self._require_opp(opp_id)
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        user = self.users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new owner is current owner")
        if self._load(new_owner) >= user["capacity"]:
            raise ValueError("new owner is at capacity")

        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(previous)

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
