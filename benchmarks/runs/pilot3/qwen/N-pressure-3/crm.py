"""CRM module per specs/crm.md."""

FREE_DOMAINS = ("gmail.com", "yahoo.com", "outlook.com")
SOURCES = {"web": 10, "referral": 30, "event": 20}
STAGES = ("prospect", "proposal", "negotiation", "won", "lost")
FINAL_STAGES = ("won", "lost")
STAGE_ORDER = ["prospect", "proposal", "negotiation", "won"]
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


def _is_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead for %s" % existing_id)
        self.existing_id = existing_id


class CRM:
    def __init__(self, reps):
        self.leads = {}
        self.opps = {}
        self.log = []
        self._users = {}
        self._waiting = []  # FIFO of lead ids with no owner
        self._lead_seq = 0
        self._opp_seq = 0
        for r in reps:
            self._users[r["id"]] = r

    # -- helpers ---------------------------------------------------------

    def _check_actor(self, actor):
        if actor not in self._users:
            raise PermissionError("unknown actor %r" % (actor,))

    def _is_manager(self, actor):
        return self._users[actor]["role"] == "manager"

    def _load(self, rep_id):
        n = sum(
            1
            for ld in self.leads.values()
            if ld["owner"] == rep_id and ld["status"] in ("new", "qualified")
        )
        n += sum(
            1
            for o in self.opps.values()
            if o["owner"] == rep_id and o["stage"] not in FINAL_STAGES
        )
        return n

    def _capacity(self, rep_id):
        return self._users[rep_id]["capacity"]

    def _pick_rep(self):
        cands = [
            rid for rid, u in self._users.items()
            if u["role"] == "rep" and self._load(rid) < self._capacity(rid)
        ]
        if not cands:
            return None
        return min(cands, key=lambda rid: (self._load(rid), rid))

    def _fill(self, rep_id):
        while self._load(rep_id) < self._capacity(rep_id) and self._waiting:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    @staticmethod
    def _normalize_email(email):
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        norm = email.strip().lower()
        if norm.count("@") != 1:
            raise ValueError("email must contain exactly one @")
        local, domain = norm.split("@")
        if not local:
            raise ValueError("empty local part")
        if not domain:
            raise ValueError("empty domain")
        if "." not in domain or domain[0] == "." or domain[-1] == ".":
            raise ValueError("bad domain")
        return norm

    # -- API -------------------------------------------------------------

    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        norm = self._normalize_email(email)
        if not isinstance(name, str) or not name.strip():
            raise ValueError("bad name")
        if source not in SOURCES:
            raise ValueError("bad source")
        for ld in self.leads.values():
            if ld["email"] == norm:
                err = DuplicateLeadError(ld["id"])
                raise err
        domain = norm.split("@", 1)[1]
        score = SOURCES[source] + (0 if domain in FREE_DOMAINS else 15)
        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        owner = self._pick_rep()
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
            self._waiting.append(lead_id)
        self.log.append(("add_lead", lead_id, actor))
        return lead_id

    def qualify(self, lead_id, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "new":
            raise ValueError("lead not new")
        if lead["score"] < 30:
            raise ValueError("score below 30")
        lead["status"] = "qualified"
        self.log.append(("qualify", lead_id, actor))

    def convert(self, lead_id, amount, actor):
        self._check_actor(actor)
        lead = self.leads.get(lead_id)
        if lead is None:
            raise ValueError("unknown lead")
        if not _is_int(amount) or amount <= 0:
            raise ValueError("amount must be a positive int")
        if actor != lead["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if lead["status"] != "qualified":
            raise ValueError("lead not qualified")
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
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if stage not in STAGES:
            raise ValueError("bad stage")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("current stage is final")
        if stage != "lost":
            expected = STAGE_ORDER[STAGE_ORDER.index(opp["stage"]) + 1]
            if stage != expected:
                raise ValueError("not the next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required for negotiation above 50000")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in FINAL_STAGES:
            self._fill(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not _is_int(pct) or not (1 <= pct <= 30):
            raise ValueError("pct must be an int from 1 to 30")
        if actor != opp["owner"] and not self._is_manager(actor):
            raise PermissionError("not owner or manager")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("stage is final")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("reps may discount at most 10")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30 percent")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        opp = self.opps.get(opp_id)
        if opp is None:
            raise ValueError("unknown opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        user = self._users.get(new_owner)
        if user is None or user["role"] != "rep":
            raise ValueError("new_owner must be a rep")
        if opp["stage"] in FINAL_STAGES:
            raise ValueError("stage is final")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self._load(new_owner) >= self._capacity(new_owner):
            raise ValueError("new owner at capacity")
        old_owner = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        self._fill(old_owner)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for o in self.opps.values():
            if o["stage"] in FINAL_STAGES:
                if o["stage"] == "won":
                    won += o["amount"]
            else:
                open_count += 1
                weighted += o["amount"] * WEIGHTS[o["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
