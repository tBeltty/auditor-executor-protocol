class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__(existing_id)
        self.existing_id = existing_id

ORDER = ["prospect", "proposal", "negotiation", "won"]
FINAL = ("won", "lost")
FREE = ("gmail.com", "yahoo.com", "outlook.com")

class CRM:
    def __init__(self, reps):
        self.users = {r["id"]: dict(r) for r in reps}
        self.leads, self.opps, self.log, self.queue = {}, {}, [], []
        self.nl = self.no = 0

    def _actor(self, a):
        if a not in self.users:
            raise PermissionError(a)

    def _mgr(self, a):
        return self.users[a]["role"] == "manager"

    def _load(self, rid):
        n = sum(1 for l in self.leads.values() if l["owner"] == rid and l["status"] in ("new", "qualified"))
        return n + sum(1 for o in self.opps.values() if o["owner"] == rid and o["stage"] not in FINAL)

    def _free(self, rid):
        cap = self.users[rid]["capacity"]
        while self.queue and self._load(rid) < cap:
            lead = self.queue.pop(0)
            lead["owner"] = rid
            self.log.append(("assign", lead["id"], "system"))

    def add_lead(self, email, name, source, actor):
        self._actor(actor)
        if not isinstance(email, str):
            raise ValueError("email")
        e = email.strip().lower()
        if e.count("@") != 1:
            raise ValueError("email")
        local, dom = e.split("@")
        if not local or "." not in dom[1:-1]:
            raise ValueError("email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("name")
        if source not in ("web", "referral", "event"):
            raise ValueError("source")
        for l in self.leads.values():
            if l["email"] == e:
                raise DuplicateLeadError(l["id"])
        self.nl += 1
        score = {"web": 10, "referral": 30, "event": 20}[source] + (0 if dom in FREE else 15)
        cands = [(self._load(r["id"]), r["id"]) for r in self.users.values()
                 if r["role"] == "rep" and self._load(r["id"]) < r["capacity"]]
        owner = min(cands)[1] if cands else None
        lead = {"id": "L%d" % self.nl, "email": e, "name": name.strip(), "source": source,
                "score": score, "owner": owner, "status": "new"}
        self.leads[lead["id"]] = lead
        if owner is None:
            self.queue.append(lead)
        self.log.append(("add_lead", lead["id"], actor))
        return lead["id"]

    def _lead(self, lid):
        if lid not in self.leads:
            raise ValueError("lead")
        return self.leads[lid]

    def qualify(self, lead_id, actor):
        self._actor(actor)
        l = self._lead(lead_id)
        if actor != l["owner"] and not self._mgr(actor):
            raise PermissionError(actor)
        if l["status"] != "new":
            raise ValueError("status")
        if l["score"] < 30:
            raise ValueError("score")
        l["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._actor(actor)
        l = self._lead(lead_id)
        if type(amount) is not int or amount <= 0:
            raise ValueError("amount")
        if actor != l["owner"] and not self._mgr(actor):
            raise PermissionError(actor)
        if l["status"] != "qualified":
            raise ValueError("status")
        if l["owner"] is None:
            raise ValueError("owner")
        self.no += 1
        o = {"id": "O%d" % self.no, "lead_id": lead_id, "owner": l["owner"], "amount": amount,
             "original_amount": amount, "stage": "prospect"}
        self.opps[o["id"]] = o
        l["status"] = "converted"
        self.log.append(("convert", o["id"], actor))
        return o["id"]

    def _opp(self, oid):
        if oid not in self.opps:
            raise ValueError("opp")
        return self.opps[oid]

    def advance(self, opp_id, stage, actor):
        self._actor(actor)
        o = self._opp(opp_id)
        if stage not in ORDER + ["lost"]:
            raise ValueError("stage")
        if actor != o["owner"] and not self._mgr(actor):
            raise PermissionError(actor)
        if o["stage"] in FINAL:
            raise ValueError("final")
        if stage != "lost" and ORDER.index(stage) != ORDER.index(o["stage"]) + 1:
            raise ValueError("transition")
        if stage == "negotiation" and o["amount"] > 50000 and not self._mgr(actor):
            raise PermissionError(actor)
        o["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL:
            self._free(o["owner"])

    def discount(self, opp_id, pct, actor):
        self._actor(actor)
        o = self._opp(opp_id)
        if type(pct) is not int or not 1 <= pct <= 30:
            raise ValueError("pct")
        if actor != o["owner"] and not self._mgr(actor):
            raise PermissionError(actor)
        if o["stage"] in FINAL:
            raise ValueError("final")
        if pct > 10 and not self._mgr(actor):
            raise PermissionError(actor)
        new = o["amount"] * (100 - pct) // 100
        if new * 100 < o["original_amount"] * 70:
            raise ValueError("floor")
        o["amount"] = new
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._actor(actor)
        o = self._opp(opp_id)
        if not self._mgr(actor):
            raise PermissionError(actor)
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("new_owner")
        if o["stage"] in FINAL:
            raise ValueError("final")
        if new_owner == o["owner"]:
            raise ValueError("same")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("capacity")
        old = o["owner"]
        o["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._free(old)

    def forecast(self):
        w = {"prospect": 10, "proposal": 30, "negotiation": 60}
        op = [o for o in self.opps.values() if o["stage"] not in FINAL]
        return {"open": len(op), "weighted": sum(o["amount"] * w[o["stage"]] // 100 for o in op),
                "won": sum(o["amount"] for o in self.opps.values() if o["stage"] == "won")}
