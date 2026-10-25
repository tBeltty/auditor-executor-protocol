class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead email, existing lead %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
    FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
    STAGE_ORDER = ("prospect", "proposal", "negotiation", "won")
    STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
    FINAL_STAGES = ("won", "lost")
    WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}

    def __init__(self, reps):
        self.users = {}
        for r in reps:
            self.users[r["id"]] = {"role": r["role"], "capacity": r["capacity"]}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_counter = 0
        self._opp_counter = 0
        self._waiting = []  # FIFO of lead ids with no owner
        self._emails = {}   # normalized email -> lead id

    # ---- helpers -------------------------------------------------------
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor %r" % (actor,))

    def _load(self, rep_id):
        u = self.users[rep_id]
        if u["role"] != "rep":
            return 0
        n = 0
        for l in self.leads.values():
            if l["owner"] == rep_id and l["status"] in ("new", "qualified"):
                n += 1
        for o in self.opps.values():
            if o["owner"] == rep_id and o["stage"] not in self.FINAL_STAGES:
                n += 1
        return n

    def _pick_owner(self):
        best = None
        best_load = None
        for rid in sorted(self.users):
            u = self.users[rid]
            if u["role"] != "rep":
                continue
            load = self._load(rid)
            if load < u["capacity"]:
                if best is None or load < best_load:
                    best = rid
                    best_load = load
        return best

    def _free_slot(self, rep_id):
        if rep_id is None:
            return
        while self._waiting:
            if self._load(rep_id) >= self.users[rep_id]["capacity"]:
                break
            lid = self._waiting.pop(0)
            self.leads[lid]["owner"] = rep_id
            self.log.append(("assign", lid, "system"))

    # ---- methods -------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("invalid email")
        if "." not in domain or domain.startswith(".") or domain.endswith("."):
            raise ValueError("invalid email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in self.SOURCE_SCORE:
            raise ValueError("invalid source")
        if norm in self._emails:
            raise DuplicateLeadError(self._emails[norm])
        self._lead_counter += 1
        lid = "L%d" % self._lead_counter
        score = self.SOURCE_SCORE[source]
        if domain not in self.FREE_DOMAINS:
            score += 15
        owner = self._pick_owner()
        lead = {
            "id": lid,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        self.leads[lid] = lead
        self._emails[norm] = lid
        if owner is None:
            self._waiting.append(lid)
        self.log.append(("add_lead", lid, actor))
        return lid

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if lead["owner"] != actor and self.users[actor]["role"] != "manager":
            raise PermissionError("not the owner or a manager")
        if lead["status"] != "new":
            raise ValueError("lead is not new")
        if lead["score"] < 30:
            raise ValueError("score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if (not isinstance(amount, int) or isinstance(amount, bool)
                or amount <= 0):
            raise ValueError("amount must be a positive int")
        if lead["owner"] != actor and self.users[actor]["role"] != "manager":
            raise PermissionError("not the owner or a manager")
        if lead["status"] != "qualified":
            raise ValueError("lead is not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_counter += 1
        oid = "O%d" % self._opp_counter
        self.opps[oid] = {
            "id": oid,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        lead["status"] = "converted"
        self.log.append(("convert", oid, actor))
        return oid

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if stage not in self.STAGES:
            raise ValueError("invalid stage")
        if opp["owner"] != actor and self.users[actor]["role"] != "manager":
            raise PermissionError("not the owner or a manager")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        if stage != "lost":
            idx = self.STAGE_ORDER.index(opp["stage"])
            if stage != self.STAGE_ORDER[idx + 1]:
                raise ValueError("stage is not the next stage")
        if (stage == "negotiation" and opp["amount"] > 50000
                and self.users[actor]["role"] != "manager"):
            raise PermissionError("manager required for large deals")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in self.FINAL_STAGES:
            self._free_slot(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if (not isinstance(pct, int) or isinstance(pct, bool)
                or not (1 <= pct <= 30)):
            raise ValueError("pct must be an int between 1 and 30")
        if opp["owner"] != actor and self.users[actor]["role"] != "manager":
            raise PermissionError("not the owner or a manager")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        if self.users[actor]["role"] != "manager" and pct > 10:
            raise PermissionError("non-manager discount above 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount above 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if self.users[actor]["role"] != "manager":
            raise PermissionError("only managers transfer")
        nu = self.users.get(new_owner)
        if nu is None or nu["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in self.FINAL_STAGES:
            raise ValueError("opportunity is final")
        if new_owner == opp["owner"]:
            raise ValueError("new_owner equals current owner")
        if self._load(new_owner) >= nu["capacity"]:
            raise ValueError("new_owner at capacity")
        prev = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free_slot(prev)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for o in self.opps.values():
            stage = o["stage"]
            if stage == "won":
                won += o["amount"]
            elif stage == "lost":
                continue
            else:
                open_count += 1
                weighted += o["amount"] * self.WEIGHTS[stage] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
