"""Independent reference implementation written only from /tmp/aep-lab/specs/crm.md.

Used exclusively as a differential oracle in the audit. Deliberately written
independently of the delivery's crm.py.
"""


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__(existing_id)
        self.existing_id = existing_id


SOURCES = ("web", "referral", "event")
BASE = {"web": 10, "referral": 30, "event": 20}
CONSUMER = ("gmail.com", "yahoo.com", "outlook.com")
ORDER = ("prospect", "proposal", "negotiation", "won")
FINAL = ("won", "lost")
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class RefCRM:
    def __init__(self, reps):
        self.users = {r["id"]: {"id": r["id"], "role": r["role"], "capacity": r["capacity"]} for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self.queue = []          # FIFO waiting queue of lead ids
        self.lead_n = 0
        self.opp_n = 0

    # -- helpers -----------------------------------------------------
    def need_actor(self, actor):
        if not isinstance(actor, str) or actor not in self.users:
            raise PermissionError(actor)

    def is_mgr(self, actor):
        return self.users[actor]["role"] == "manager"

    def load(self, rep):
        n = 0
        for l in self.leads.values():
            if l["owner"] == rep and l["status"] in ("new", "qualified"):
                n += 1
        for o in self.opps.values():
            if o["owner"] == rep and o["stage"] not in FINAL:
                n += 1
        return n

    def eligible(self):
        best = None
        for rid, u in self.users.items():
            if u["role"] != "rep":
                continue
            ld = self.load(rid)
            if ld < u["capacity"]:
                if best is None or (ld, rid) < best:
                    best = (ld, rid)
        return None if best is None else best[1]

    def grant(self, rep):
        while self.queue and self.load(rep) < self.users[rep]["capacity"]:
            lid = self.queue.pop(0)
            self.leads[lid]["owner"] = rep
            self.log.append(("assign", lid, "system"))

    def lead(self, lid):
        if not isinstance(lid, str) or lid not in self.leads:
            raise ValueError(lid)
        return self.leads[lid]

    def opp(self, oid):
        if not isinstance(oid, str) or oid not in self.opps:
            raise ValueError(oid)
        return self.opps[oid]

    # -- API ---------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self.need_actor(actor)
        if not isinstance(email, str):
            raise ValueError(email)
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError(email)
        local, domain = norm.split("@")
        if local == "":
            raise ValueError(email)
        if domain == "":
            raise ValueError(email)
        # spec: domain must contain a "." that is neither the first nor the
        # last character of the domain.
        if not any(ch == "." and 0 < i < len(domain) - 1 for i, ch in enumerate(domain)):
            raise ValueError(email)
        if not isinstance(name, str) or name.strip() == "":
            raise ValueError(name)
        if source not in SOURCES:
            raise ValueError(source)
        for l in self.leads.values():
            if l["email"] == norm:
                raise DuplicateLeadError(l["id"])
        score = BASE[source]
        if domain not in CONSUMER:
            score += 15
        owner = self.eligible()
        self.lead_n += 1
        lid = "L%d" % self.lead_n
        self.leads[lid] = {
            "id": lid,
            "email": norm,
            "name": name.strip(),
            "source": source,
            "score": score,
            "owner": owner,
            "status": "new",
        }
        if owner is None:
            self.queue.append(lid)
        self.log.append(("add_lead", lid, actor))
        return lid

    def qualify(self, lid, actor):
        self.need_actor(actor)
        l = self.lead(lid)
        if l["owner"] != actor and not self.is_mgr(actor):
            raise PermissionError(actor)
        if l["status"] != "new":
            raise ValueError(lid)
        if l["score"] < 30:
            raise ValueError(lid)
        l["status"] = "qualified"
        self.log.append(("qualify", lid, actor))

    def convert(self, lid, amount, actor):
        self.need_actor(actor)
        l = self.lead(lid)
        if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
            raise ValueError(amount)
        if l["owner"] != actor and not self.is_mgr(actor):
            raise PermissionError(actor)
        if l["status"] != "qualified":
            raise ValueError(lid)
        if l["owner"] is None:
            raise ValueError(lid)
        self.opp_n += 1
        oid = "O%d" % self.opp_n
        self.opps[oid] = {
            "id": oid,
            "lead_id": lid,
            "owner": l["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        l["status"] = "converted"
        self.log.append(("convert", oid, actor))
        return oid

    def advance(self, oid, stage, actor):
        self.need_actor(actor)
        o = self.opp(oid)
        if stage not in ORDER and stage != "lost":
            raise ValueError(stage)
        if o["owner"] != actor and not self.is_mgr(actor):
            raise PermissionError(actor)
        if o["stage"] in FINAL:
            raise ValueError(oid)
        if stage != "lost" and stage != ORDER[ORDER.index(o["stage"]) + 1]:
            raise ValueError(stage)
        if stage == "negotiation" and o["amount"] > 50000 and not self.is_mgr(actor):
            raise PermissionError(actor)
        o["stage"] = stage
        self.log.append(("advance", oid, actor))
        if stage in FINAL:
            self.grant(o["owner"])

    def discount(self, oid, pct, actor):
        self.need_actor(actor)
        o = self.opp(oid)
        if not isinstance(pct, int) or isinstance(pct, bool) or not (1 <= pct <= 30):
            raise ValueError(pct)
        if o["owner"] != actor and not self.is_mgr(actor):
            raise PermissionError(actor)
        if o["stage"] in FINAL:
            raise ValueError(oid)
        if not self.is_mgr(actor) and pct > 10:
            raise PermissionError(actor)
        new = o["amount"] * (100 - pct) // 100
        if new * 100 < o["original_amount"] * 70:
            raise ValueError(pct)
        o["amount"] = new
        self.log.append(("discount", oid, actor))

    def transfer(self, oid, new_owner, actor):
        self.need_actor(actor)
        o = self.opp(oid)
        if not self.is_mgr(actor):
            raise PermissionError(actor)
        if not isinstance(new_owner, str) or new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError(new_owner)
        if o["stage"] in FINAL:
            raise ValueError(oid)
        if new_owner == o["owner"]:
            raise ValueError(new_owner)
        if self.load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError(new_owner)
        prev = o["owner"]
        o["owner"] = new_owner
        self.log.append(("transfer", oid, actor))
        self.grant(prev)

    def forecast(self):
        open_n = 0
        weighted = 0
        won = 0
        for o in self.opps.values():
            if o["stage"] in WEIGHTS:
                open_n += 1
                weighted += o["amount"] * WEIGHTS[o["stage"]] // 100
            elif o["stage"] == "won":
                won += o["amount"]
        return {"open": open_n, "weighted": weighted, "won": won}
