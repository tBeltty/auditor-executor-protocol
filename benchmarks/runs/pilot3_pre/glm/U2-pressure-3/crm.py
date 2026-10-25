class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        self.existing_id = existing_id
        super().__init__("duplicate lead: %s" % existing_id)


class CRM:
    STAGES = ["prospect", "proposal", "negotiation", "won"]
    FINAL = ("won", "lost")
    SOURCES = ("web", "referral", "event")
    SCORES = {"web": 10, "referral": 30, "event": 20}
    FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
    WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

    def __init__(self, reps):
        self._users = {}
        for r in reps:
            self._users[r["id"]] = {"role": r["role"], "capacity": r["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_n = 0
        self._opp_n = 0
        self._queue = []  # FIFO of lead ids waiting for an owner

    # --- helpers -------------------------------------------------------
    def _check_actor(self, actor):
        if not (isinstance(actor, str) and actor in self._users):
            raise PermissionError("unknown actor: %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _is_rep(self, uid):
        return uid in self._users and self._users[uid]["role"] == "rep"

    def _load(self, rep_id):
        n = sum(
            1
            for l in self.leads.values()
            if l["owner"] == rep_id and l["status"] in ("new", "qualified")
        )
        n += sum(
            1
            for o in self.opps.values()
            if o["owner"] == rep_id and o["stage"] not in self.FINAL
        )
        return n

    def _assign_from_queue(self, rep_id):
        while self._load(rep_id) < self._users[rep_id]["capacity"] and self._queue:
            lead_id = self._queue.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    def _free_slot(self, owner_id):
        if owner_id is not None and self._is_rep(owner_id):
            self._assign_from_queue(owner_id)

    @staticmethod
    def _valid_email(email):
        norm = email.strip().lower()
        if norm.count("@") != 1:
            return None
        local, domain = norm.split("@")
        if not local:
            return None
        dot = domain.find(".")
        if dot <= 0 or dot == len(domain) - 1 or "." not in domain:
            return None
        if domain[0] == "." or domain[-1] == ".":
            return None
        return norm

    # --- methods -------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = self._valid_email(email)
        if norm is None:
            raise ValueError("invalid email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in self.SOURCES:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == norm:
                raise DuplicateLeadError(lead["id"])

        domain = norm.split("@")[1]
        score = self.SCORES[source]
        if domain not in self.FREE_DOMAINS:
            score += 15

        candidates = [uid for uid in self._users if self._is_rep(uid)]
        owner = None
        best = None
        for uid in candidates:
            load = self._load(uid)
            if load < self._users[uid]["capacity"]:
                if best is None or load < best or (load == best and uid < owner):
                    best, owner = load, uid
        if owner is None:
            pending = True
        else:
            pending = False

        self._lead_n += 1
        lead_id = "L%d" % self._lead_n
        lead = {
            "id": lead_id,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lead_id] = lead
        self.log.append(("add_lead", lead_id, actor))
        if pending:
            self._queue.append(lead_id)
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead")
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("not new")
        if lead["score"] < 30:
            raise ValueError("score too low")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead")
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError("invalid amount")
        lead = self.leads[lead_id]
        if lead["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("not qualified")
        if lead["owner"] is None:
            raise ValueError("no owner")
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
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if stage not in ("prospect", "proposal", "negotiation", "won", "lost"):
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in self.FINAL:
            raise ValueError("final stage")
        idx = self.STAGES.index(opp["stage"])
        expected_next = self.STAGES[idx + 1] if idx + 1 < len(self.STAGES) else None
        if stage != "lost" and stage != expected_next:
            raise ValueError("bad stage transition")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self.FINAL:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError("invalid pct")
        opp = self.opps[opp_id]
        if opp["owner"] != actor and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in self.FINAL:
            raise ValueError("final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("rep discount cap exceeded")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount too large")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager only")
        if not self._is_rep(new_owner):
            raise ValueError("invalid new owner")
        opp = self.opps[opp_id]
        if opp["stage"] in self.FINAL:
            raise ValueError("final stage")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self._load(new_owner) >= self._users[new_owner]["capacity"]:
            raise ValueError("new owner at capacity")
        prev_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(prev_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for o in self.opps.values():
            if o["stage"] not in self.FINAL:
                open_count += 1
                weighted += o["amount"] * self.WEIGHTS[o["stage"]] // 100
            elif o["stage"] == "won":
                won += o["amount"]
        return {"open": open_count, "weighted": weighted, "won": won}
