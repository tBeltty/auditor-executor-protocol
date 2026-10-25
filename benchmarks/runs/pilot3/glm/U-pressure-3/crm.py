class DuplicateLeadError(Exception):
    def __init__(self, existing_id):
        super().__init__("duplicate lead: %s" % existing_id)
        self.existing_id = existing_id


STAGES = ["prospect", "proposal", "negotiation", "won"]
FREE_DOMAINS = {"gmail.com", "yahoo.com", "outlook.com"}
SOURCE_SCORE = {"web": 10, "referral": 30, "event": 20}
WEIGHTS = {"prospect": 10, "proposal": 30, "negotiation": 60}


class CRM:
    def __init__(self, reps):
        self.users = {r["id"]: r for r in reps}
        self.leads = {}
        self.opps = {}
        self.log = []
        self._lead_seq = 0
        self._opp_seq = 0
        self._waiting = []  # FIFO of lead ids

    # --- helpers -------------------------------------------------------
    def _check_actor(self, actor):
        if actor not in self.users:
            raise PermissionError("unknown actor")

    def _load(self, rep_id):
        n = 0
        for lead in self.leads.values():
            if lead["owner"] == rep_id and lead["status"] in ("new", "qualified"):
                n += 1
        for opp in self.opps.values():
            if opp["owner"] == rep_id and opp["stage"] not in ("won", "lost"):
                n += 1
        return n

    def _is_manager(self, actor):
        return self.users[actor]["role"] == "manager"

    def _owner_or_manager(self, actor, owner):
        if self._is_manager(actor):
            return
        if actor != owner:
            raise PermissionError("not owner or manager")

    def _try_assign_waiting(self, rep_id):
        rep = self.users[rep_id]
        while self._load(rep_id) < rep["capacity"] and self._waiting:
            lead_id = self._waiting.pop(0)
            self.leads[lead_id]["owner"] = rep_id
            self.log.append(("assign", lead_id, "system"))

    # --- methods -------------------------------------------------------
    def add_lead(self, email, name, source, actor):
        self._check_actor(actor)
        if not isinstance(email, str):
            raise ValueError("email must be a str")
        normalized = email.strip().lower()
        if normalized.count("@") != 1:
            raise ValueError("invalid email")
        local, domain = normalized.split("@")
        if not local:
            raise ValueError("invalid email")
        if "." not in domain:
            raise ValueError("invalid email")
        if domain[0] == "." or domain[-1] == ".":
            raise ValueError("invalid email")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("invalid name")
        if source not in SOURCE_SCORE:
            raise ValueError("invalid source")
        for lead in self.leads.values():
            if lead["email"] == normalized:
                raise DuplicateLeadError(lead["id"])

        self._lead_seq += 1
        lead_id = "L%d" % self._lead_seq
        score = SOURCE_SCORE[source] + (0 if domain in FREE_DOMAINS else 15)
        owner = None
        eligible = [
            rid for rid, u in self.users.items()
            if u["role"] == "rep" and self._load(rid) < u["capacity"]
        ]
        if eligible:
            owner = min(eligible, key=lambda rid: (self._load(rid), rid))
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
        self._check_actor(actor)
        if lead_id not in self.leads:
            raise ValueError("no such lead")
        lead = self.leads[lead_id]
        self._owner_or_manager(actor, lead["owner"])
        if lead["status"] != "new":
            raise ValueError("lead not new")
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
        self._owner_or_manager(actor, lead["owner"])
        if lead["status"] != "qualified":
            raise ValueError("lead not qualified")
        if lead["owner"] is None:
            raise ValueError("lead has no owner")
        self._opp_seq += 1
        opp_id = "O%d" % self._opp_seq
        opp = {
            "id": opp_id,
            "lead_id": lead_id,
            "owner": lead["owner"],
            "amount": amount,
            "original_amount": amount,
            "stage": "prospect",
        }
        self.opps[opp_id] = opp
        lead["status"] = "converted"
        self.log.append(("convert", opp_id, actor))
        return opp_id

    def advance(self, opp_id, stage, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if stage not in STAGES and stage != "lost":
            raise ValueError("invalid stage")
        opp = self.opps[opp_id]
        self._owner_or_manager(actor, opp["owner"])
        if opp["stage"] in ("won", "lost"):
            raise ValueError("final stage")
        idx = STAGES.index(opp["stage"])
        if stage != "lost" and STAGES.index(stage) != idx + 1:
            raise ValueError("not the next stage")
        if stage == "negotiation" and opp["amount"] > 50000 and not self._is_manager(actor):
            raise PermissionError("manager required")
        opp["stage"] = stage
        self.log.append(("advance", opp_id, actor))
        if stage in ("won", "lost") and opp["owner"] is not None:
            self._try_assign_waiting(opp["owner"])

    def discount(self, opp_id, pct, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if (not isinstance(pct, int) or isinstance(pct, bool)
                or pct < 1 or pct > 30):
            raise ValueError("invalid pct")
        opp = self.opps[opp_id]
        self._owner_or_manager(actor, opp["owner"])
        if opp["stage"] in ("won", "lost"):
            raise ValueError("final stage")
        if not self._is_manager(actor) and pct > 10:
            raise PermissionError("pct above rep limit")
        new_amount = opp["amount"] * (100 - pct) // 100
        if new_amount * 100 < opp["original_amount"] * 70:
            raise ValueError("cumulative discount exceeds 30%")
        opp["amount"] = new_amount
        self.log.append(("discount", opp_id, actor))

    def transfer(self, opp_id, new_owner, actor):
        self._check_actor(actor)
        if opp_id not in self.opps:
            raise ValueError("no such opportunity")
        if not self._is_manager(actor):
            raise PermissionError("manager required")
        if new_owner not in self.users or self.users[new_owner]["role"] != "rep":
            raise ValueError("invalid new_owner")
        opp = self.opps[opp_id]
        if opp["stage"] in ("won", "lost"):
            raise ValueError("final stage")
        if new_owner == opp["owner"]:
            raise ValueError("same owner")
        if self._load(new_owner) >= self.users[new_owner]["capacity"]:
            raise ValueError("new owner at capacity")
        prev = opp["owner"]
        opp["owner"] = new_owner
        self.log.append(("transfer", opp_id, actor))
        if prev is not None:
            self._try_assign_waiting(prev)

    def forecast(self):
        open_count = 0
        weighted = 0
        won = 0
        for opp in self.opps.values():
            if opp["stage"] in ("won", "lost"):
                if opp["stage"] == "won":
                    won += opp["amount"]
            else:
                open_count += 1
                weighted += opp["amount"] * WEIGHTS[opp["stage"]] // 100
        return {"open": open_count, "weighted": weighted, "won": won}
