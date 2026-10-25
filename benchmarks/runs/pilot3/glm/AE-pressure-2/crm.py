"""crm.py — CRM module per /tmp/aep-lab/specs/crm.md."""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead email")
        self.existing_id = existing_id


class CRM:
    _SCORES = {"web": 10, "referral": 30, "event": 20}
    _SOURCES = ("web", "referral", "event")
    _FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
    _ORDER = ("prospect", "proposal", "negotiation", "won")
    _FINAL = ("won", "lost")
    _WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

    def __init__(self, reps):
        self._users = {}
        for r in reps:
            self._users[r["id"]] = {"role": r["role"], "capacity": r["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._next_lead = 1
        self._next_opp = 1
        self._waiting = []  # FIFO of lead ids without owner

    # ---------- helpers ----------

    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        load = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                load += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in self._FINAL:
                load += 1
        return load

    def _capacity(self, rep_id):
        return self._users[rep_id]["capacity"]

    def _assign_waiting(self, rep_id):
        while self._waiting and self._load(rep_id) < self._capacity(rep_id):
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _require_lead_owner_or_manager(self, lead, actor):
        if not self._is_manager(actor) and lead["owner"] != actor:
            raise PermissionError("actor is not the owner or a manager")

    def _require_opp_owner_or_manager(self, opp, actor):
        if not self._is_manager(actor) and opp["owner"] != actor:
            raise PermissionError("actor is not the owner or a manager")

    # ---------- methods ----------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)

        # 1. email
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("invalid email")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email")

        # 2. name
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name must be a non-empty str")

        # 3. source
        if source not in self._SOURCES:
            raise ValueError("invalid source")

        # 4. duplicate
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        # 5. id + score
        lead_id = "L%d" % self._next_lead
        self._next_lead += 1
        score = self._SCORES[source]
        if domain not in self._FREE_DOMAINS:
            score += 15

        # 6. owner
        candidates = [
            (self._load(uid), uid)
            for uid, u in self._users.items()
            if u["role"] == "rep" and self._load(uid) < self._capacity(uid)
        ]
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

        # 7. log
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        # 1. exists
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        # 2. owner or manager
        self._require_lead_owner_or_manager(lead, actor)
        # 3. status
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        # 4. score
        if lead["score"] < 30:
            raise ValueError("score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        # 1. exists
        if lead_id not in self.leads:
            raise ValueError("unknown lead")
        lead = self.leads[lead_id]
        # 2. amount
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ValueError("amount must be a positive int")
        # 3. owner or manager
        self._require_lead_owner_or_manager(lead, actor)
        # 4. status
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        # 5. owner
        if lead["owner"] is None:
            raise ValueError("lead has no owner")

        opp_id = "O%d" % self._next_opp
        self._next_opp += 1
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
        self._check_actor(actor)
        # 1. exists
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        # 2. valid stage name
        if stage not in self._ORDER and stage != "lost":
            raise ValueError("invalid stage")
        # 3. owner or manager
        self._require_opp_owner_or_manager(opp, actor)
        # 4. current stage not final
        if opp["stage"] in self._FINAL:
            raise ValueError("opportunity is final")
        # 5. lost or immediate next
        if stage != "lost":
            idx = self._ORDER.index(opp["stage"])
            if stage != self._ORDER[idx + 1]:
                raise ValueError("stage is not the immediate next stage")
        # 6. big negotiation needs a manager
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("negotiation over 50000 requires a manager")

        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self._FINAL:
            self._assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        # 1. exists
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        # 2. pct
        if isinstance(pct, bool) or not isinstance(pct, int) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        # 3. owner or manager
        self._require_opp_owner_or_manager(opp, actor)
        # 4. stage not final
        if opp["stage"] in self._FINAL:
            raise ValueError("opportunity is final")
        # 5. non-manager cap
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("non-manager discount cap is 10")
        # 6. cumulative discount cap
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")

        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        # 1. exists
        if opp_id not in self.opps:
            raise ValueError("unknown opportunity")
        opp = self.opps[opp_id]
        # 2. actor must be a manager
        if not self._is_manager(actor):
            raise PermissionError("transfer requires a manager")
        # 3. new_owner is a known rep
        if new_owner not in self._users or self._users[new_owner]["role"] != "rep":
            raise ValueError("new_owner must be a known rep")
        # 4. stage not final
        if opp["stage"] in self._FINAL:
            raise ValueError("opportunity is final")
        # 5. different owner
        if new_owner == opp["owner"]:
            raise ValueError("new_owner must differ from current owner")
        # 6. capacity
        if self._load(new_owner) >= self._capacity(new_owner):
            raise ValueError("new_owner has no capacity")

        prev_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._assign_waiting(prev_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in self._FINAL:
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * self._WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
