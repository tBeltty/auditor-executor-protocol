"""CRM module implementing the spec in /tmp/aep-lab/specs/crm.md."""

FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCES = {"web": 10, "referral": 30, "event": 20}
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL_STAGES = {"won", "lost"}
VALID_STAGES = {"prospect", "proposal", "negotiation", "won", "lost"}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead")
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.users = {}
        for r in reps:
            self.users[r["id"]] = {"role": r["role"], "capacity": r["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_n = 0
        self._opp_n = 0
        self._waiting = []  # FIFO queue of lead ids

    # ---- helpers -------------------------------------------------------
    def _check_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError("unknown actor")

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in FINAL_STAGES:
                n += 1
        return n

    def _assign_waiting(self, rep_id):
        capacity = self.users[rep_id]["capacity"]
        while self._waiting and self._load(rep_id) < capacity:
            lead = self.leads[self._waiting.pop(0)]
            lead["owner"] = rep_id
            self.log.append(("assign", lead["id"], "system"))

    def _check_owner_or_manager(self, owner, actor):
        if actor != owner and not self._is_manager(actor):
            raise PermissionError("not owner or manager")

    # ---- add_lead ------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
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
        if source not in SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_n += 1
        lead_id = "L{}".format(self._lead_n)
        score = SOURCES[source]
        if domain not in FREE_DOMAINS:
            score += 15

        owner = None
        candidates = [
            uid for uid, u in self.users.items()
            if u["role"] == "rep" and self._load(uid) < u["capacity"]
        ]
        if candidates:
            owner = min(candidates, key=lambda uid: (self._load(uid), uid))

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

    # ---- qualify -------------------------------------------------------
    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("lead not found")
        lead = self.leads[lead_id]
        self._check_owner_or_manager(lead["owner"], actor)
        if lead["status"] != "new":
            raise ValueError("lead not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    # ---- convert -------------------------------------------------------
    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("lead not found")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("invalid amount")
        lead = self.leads[lead_id]
        self._check_owner_or_manager(lead["owner"], actor)
        if lead["status"] != "qualified":
            raise ValueError("lead not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        self._opp_n += 1
        opp_id = "O{}".format(self._opp_n)
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

    # ---- advance -------------------------------------------------------
    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("opportunity not found")
        if stage not in VALID_STAGES:
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        self._check_owner_or_manager(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("final stage")
        idx = STAGE_ORDER.index(opp["stage"])
        if stage != "lost" and stage != STAGE_ORDER[idx + 1]:
            raise ValueError("invalid stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 \
                and not self._is_manager(actor):
            raise PermissionError("manager required")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES and opp["owner"] is not None:
            self._assign_waiting(opp["owner"])

    # ---- discount ------------------------------------------------------
    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("opportunity not found")
        if not isinstance(pct, int) or isinstance(pct, bool) \
                or pct < 1 or pct > 30:
            raise ValueError("invalid pct")
        opp = self.opps[opp_id]
        self._check_owner_or_manager(opp["owner"], actor)
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("pct too high for non-manager")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount too deep")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    # ---- transfer ------------------------------------------------------
    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("opportunity not found")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("invalid new owner")
        opp = self.opps[opp_id]
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("final stage")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner at capacity")
        previous = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if previous is not None:
            self._assign_waiting(previous)

    # ---- forecast ------------------------------------------------------
    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] not in FINAL_STAGES:
                open_count += 1
                weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
            elif opp["stage"] == "won":
                won += opp["amount"]
        return {"open": open_count, "weighted": weighted, "won": won}
